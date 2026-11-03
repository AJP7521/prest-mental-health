"""Local-only skill exercise API. Use synthetic data."""
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
import os
import hashlib
import hmac
import secrets
import time
import re
from pathlib import Path
import sqlite3
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from . import coaching
except ImportError:
    import coaching

class ChatCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

SKILLS = [
    {"id": "wave", "name": "Trace a wave", "duration_seconds": None},
    {"id": "breathing", "name": "Paced breathing", "duration_seconds": 60},
    {"id": "grounding", "name": "5-4-3-2-1 grounding", "duration_seconds": None},
]

class SessionCreate(BaseModel):
    skill: Literal["breathing", "grounding", "wave"]

class SessionUpdate(BaseModel):
    status: Literal["completed", "stopped"]
    elapsed_ms: int | None = Field(default=None, ge=0, le=86400000)
    end_reason: Literal["completed", "stopped", "interrupted"] | None = None

class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=10, max_length=128)

class Registration(Credentials):
    display_name: str = Field(min_length=1, max_length=60)

class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=60)
    animate_breathing: bool = True


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

def create_app(database_path=None):
    db_path = Path(database_path or os.getenv("DATABASE_PATH", Path(__file__).with_name("data.sqlite3")))

    @contextmanager
    def database():
        connection = sqlite3.connect(db_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @asynccontextmanager
    async def lifespan(app):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with database() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL, password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL, animate_breathing INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS guide_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL,
                    model TEXT
                );
                CREATE TABLE IF NOT EXISTS guide_requests (
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    requested_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS guide_usage ON guide_requests(user_id, requested_at);
                CREATE INDEX IF NOT EXISTS guide_history ON guide_messages(user_id, id);
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    skill TEXT NOT NULL CHECK(skill IN ('breathing','grounding','wave')),
                    status TEXT NOT NULL CHECK(status IN ('active','completed','stopped')),
                    started_at TEXT NOT NULL,
                    ended_at TEXT
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
            # Additive migration preserves existing local sessions and messages.
            for table, columns in {
                'sessions': {'user_id': 'TEXT REFERENCES users(id)', 'exercise_started_at': 'TEXT', 'elapsed_ms': 'INTEGER', 'end_reason': 'TEXT'},
                'messages': {'source': 'TEXT', 'model': 'TEXT'},
            }.items():
                existing = {row['name'] for row in db.execute(f'PRAGMA table_info({table})')}
                for column, kind in columns.items():
                    if column not in existing:
                        db.execute(f'ALTER TABLE {table} ADD COLUMN {column} {kind}')
            db.execute('CREATE INDEX IF NOT EXISTS sessions_user_history ON sessions(user_id, started_at DESC)')
        # Rebuild older CHECK constraints without dropping dependent legacy messages.
        with sqlite3.connect(db_path) as db:
            schema = db.execute("SELECT sql FROM sqlite_master WHERE name = 'sessions'").fetchone()[0]
            if "'wave'" not in schema:
                db.execute('PRAGMA foreign_keys = OFF')
                db.execute('BEGIN IMMEDIATE')
                db.execute("""CREATE TABLE sessions_updated (
                    id TEXT PRIMARY KEY,
                    skill TEXT NOT NULL CHECK(skill IN ('breathing','grounding','wave')),
                    status TEXT NOT NULL CHECK(status IN ('active','completed','stopped')),
                    started_at TEXT NOT NULL, ended_at TEXT,
                    user_id TEXT REFERENCES users(id), exercise_started_at TEXT,
                    elapsed_ms INTEGER, end_reason TEXT
                )""")
                db.execute('INSERT INTO sessions_updated SELECT id, skill, status, started_at, ended_at, user_id, exercise_started_at, elapsed_ms, end_reason FROM sessions')
                db.execute('DROP TABLE sessions')
                db.execute('ALTER TABLE sessions_updated RENAME TO sessions')
                db.execute('CREATE INDEX sessions_user_history ON sessions(user_id, started_at DESC)')
                if db.execute('PRAGMA foreign_key_check').fetchone():
                    raise RuntimeError('Session migration failed integrity check')
        yield

    app = FastAPI(title="Mental Health Skills — Local Prototype", lifespan=lifespan)

    def now():
        return datetime.now(timezone.utc).isoformat()

    def get_session(db, session_id, user):
        row = db.execute("SELECT * FROM sessions WHERE id = ? AND user_id = ?", (session_id, user["id"])).fetchone()
        if row is None:
            raise HTTPException(404, "Session not found")
        return dict(row)

    @app.middleware("http")
    async def same_origin_mutations(request: Request, call_next):
        # Browsers cannot add this header cross-origin without a CORS preflight.
        # This app deliberately does not enable cross-origin access.
        if request.url.path.startswith('/api/') and request.method in ('POST', 'PATCH', 'DELETE'):
            if request.headers.get('x-requested-with') != 'mental-health-app':
                return JSONResponse(status_code=403, content={'detail': 'Use the application to make changes.'})
        response = await call_next(request)
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    def public_profile(row):
        return {key: (bool(row[key]) if key == 'animate_breathing' else row[key])
                for key in ('id', 'username', 'display_name', 'animate_breathing', 'created_at', 'updated_at')}

    def current_user(request: Request):
        token = request.cookies.get('practice_session', '')
        with database() as db:
            row = db.execute("SELECT users.* FROM users JOIN auth_sessions ON users.id = auth_sessions.user_id WHERE token_hash = ? AND expires_at > ?",
                             (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        if row is None:
            raise HTTPException(401, 'Please log in to access your profile and history.')
        return dict(row)

    def sign_in(db, user_id, request, response):
        old = request.cookies.get('practice_session', '')
        db.execute('DELETE FROM auth_sessions WHERE token_hash = ? OR expires_at <= ?',
                   (hashlib.sha256(old.encode()).hexdigest(), int(time.time())))
        token = secrets.token_urlsafe(32)
        db.execute('INSERT INTO auth_sessions VALUES (?, ?, ?)',
                   (hashlib.sha256(token.encode()).hexdigest(), user_id, int(time.time()) + 604800))
        response.set_cookie('practice_session', token, max_age=604800, httponly=True,
                            samesite='strict', secure=request.url.scheme == 'https', path='/')

    @app.post('/api/auth/register', status_code=201)
    def register(body: Registration, request: Request, response: Response):
        username = body.username.strip().lower()
        if not re.fullmatch(r'[a-z0-9_]{3,40}', username):
            raise HTTPException(422, 'Username must contain 3–40 letters, numbers, or underscores.')
        if not body.display_name.strip():
            raise HTTPException(422, 'Enter a display name.')
        salt = secrets.token_hex(16)
        digest = password_hash(body.password, salt)
        with database() as db:
            user_id = str(uuid4())
            try:
                db.execute('INSERT INTO users (id, username, display_name, password_hash, salt, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (user_id, username, body.display_name.strip(), digest, salt, now(), now()))
            except sqlite3.IntegrityError:
                raise HTTPException(409, 'That username is already in use.')
            sign_in(db, user_id, request, response)
            return public_profile(db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone())

    @app.post('/api/auth/login')
    def login(body: Credentials, request: Request, response: Response):
        with database() as db:
            row = db.execute('SELECT * FROM users WHERE username = ?', (body.username.strip().lower(),)).fetchone()
            digest = password_hash(body.password, row['salt'] if row else '00' * 16)
            if row is None or not hmac.compare_digest(digest, row['password_hash']):
                raise HTTPException(401, 'Incorrect username or password.')
            sign_in(db, row['id'], request, response)
            return public_profile(row)

    @app.post('/api/auth/logout', status_code=204)
    def logout(request: Request, response: Response):
        with database() as db:
            db.execute('DELETE FROM auth_sessions WHERE token_hash = ?',
                       (hashlib.sha256(request.cookies.get('practice_session', '').encode()).hexdigest(),))
        response.delete_cookie('practice_session', path='/')

    @app.get('/api/profile')
    def profile(user=Depends(current_user)):
        return public_profile(user)

    @app.patch('/api/profile')
    def update_profile(body: ProfileUpdate, user=Depends(current_user)):
        if not body.display_name.strip():
            raise HTTPException(422, 'Enter a display name.')
        with database() as db:
            db.execute('UPDATE users SET display_name = ?, animate_breathing = ?, updated_at = ? WHERE id = ?',
                       (body.display_name.strip(), body.animate_breathing, now(), user['id']))
            return public_profile(db.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone())

    @app.exception_handler(sqlite3.Error)
    async def database_error(request, error):
        return JSONResponse(status_code=503, content={"detail": "History storage is unavailable. You can still stop your exercise."})

    @app.get("/api/health")
    def health():
        with database() as db:
            db.execute("SELECT 1")
        return {"status": "ok"}

    @app.get('/api/coaching')
    def coaching_configuration():
        return coaching.configuration()

    @app.get('/api/chat/messages')
    def chat_history(user=Depends(current_user)):
        with database() as db:
            return [dict(row) for row in db.execute('SELECT * FROM (SELECT id, role, content, created_at, model FROM guide_messages WHERE user_id = ? ORDER BY id DESC LIMIT 100) ORDER BY id', (user['id'],))]

    @app.delete('/api/chat/messages', status_code=204)
    def clear_chat(user=Depends(current_user)):
        with database() as db:
            db.execute('DELETE FROM guide_messages WHERE user_id = ?', (user['id'],))

    @app.post('/api/chat/messages')
    def chat(body: ChatCreate, user=Depends(current_user)):
        if not body.content.strip():
            raise HTTPException(422, 'Enter a fictional practice question.')
        if coaching.configuration()['mode'] != 'live':
            raise HTTPException(503, 'Live chat is not configured. Run python3 backend/setup_api_key.py in your terminal, then refresh the connection.')
        with database() as db:
            db.execute('BEGIN IMMEDIATE')
            timestamp = time.time()
            db.execute('DELETE FROM guide_requests WHERE requested_at < ?', (timestamp - 3600,))
            minute = db.execute('SELECT COUNT(*) FROM guide_requests WHERE user_id = ? AND requested_at > ?', (user['id'], timestamp - 60)).fetchone()[0]
            hour = db.execute('SELECT COUNT(*) FROM guide_requests WHERE user_id = ?', (user['id'],)).fetchone()[0]
            if minute >= 6 or hour >= 20:
                raise HTTPException(429, 'Chat limit reached. Try later, or return to the exercises.')
            db.execute('INSERT INTO guide_requests VALUES (?, ?)', (user['id'], timestamp))
            cursor = db.execute("INSERT INTO guide_messages (user_id, role, content, created_at) VALUES (?, 'user', ?, ?)", (user['id'], body.content.strip(), now()))
            question_id = cursor.lastrowid
            context = [dict(row) for row in db.execute('SELECT role, content FROM (SELECT id, role, content FROM guide_messages WHERE user_id = ? ORDER BY id DESC LIMIT 12) ORDER BY id', (user['id'],))]
        try:
            answer = coaching.reply(context)
        except Exception as error:
            raise HTTPException(502, coaching.failure_message(error)) from None
        with database() as db:
            # A clear while awaiting a reply must not recreate deleted conversation.
            if not db.execute('SELECT 1 FROM guide_messages WHERE id = ? AND user_id = ?', (question_id, user['id'])).fetchone():
                raise HTTPException(409, 'This conversation was cleared.')
            db.execute("INSERT INTO guide_messages (user_id, role, content, created_at, model) VALUES (?, 'assistant', ?, ?, ?)", (user['id'], answer, now(), coaching.MODEL))
        return chat_history(user)

    @app.get("/api/skills")
    def skills():
        return SKILLS

    @app.post("/api/sessions", status_code=201)
    def start_session(body: SessionCreate, user=Depends(current_user)):
        with database() as db:
            session_id = str(uuid4())
            db.execute("INSERT INTO sessions (id, skill, status, started_at, ended_at, user_id) VALUES (?, ?, 'active', ?, NULL, ?)", (session_id, body.skill, now(), user['id']))
            return get_session(db, session_id, user)

    @app.get("/api/sessions")
    def history(skill: Literal["breathing", "grounding", "wave"] | None = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user)):
        with database() as db:
            rows = db.execute("SELECT * FROM sessions WHERE user_id = ? AND (? IS NULL OR skill = ?) ORDER BY started_at DESC, id DESC LIMIT ? OFFSET ?", (user["id"], skill, skill, limit, offset)).fetchall()
            return [dict(row) for row in rows]

    @app.get('/api/sessions/recent')
    def recent_practice(user=Depends(current_user)):
        """Return the latest actually-started exercise for an optional repeat shortcut."""
        with database() as db:
            row = db.execute("""SELECT * FROM sessions
                WHERE user_id = ? AND exercise_started_at IS NOT NULL
                  AND status IN ('completed', 'stopped')
                ORDER BY exercise_started_at DESC, id DESC LIMIT 1""", (user['id'],)).fetchone()
            return dict(row) if row else None

    @app.post("/api/sessions/{session_id}/begin")
    def begin(session_id: str, user=Depends(current_user)):
        with database() as db:
            session = get_session(db, session_id, user)
            if session['status'] != 'active':
                raise HTTPException(409, 'Session already ended')
            db.execute("UPDATE sessions SET exercise_started_at = COALESCE(exercise_started_at, ?) WHERE id = ?", (now(), session_id))
            return get_session(db, session_id, user)

    @app.patch("/api/sessions/{session_id}")
    def finish_session(session_id: str, body: SessionUpdate, user=Depends(current_user)):
        with database() as db:
            session = get_session(db, session_id, user)
            reason = body.end_reason or body.status
            if (body.status == 'completed') != (reason == 'completed'):
                raise HTTPException(422, 'Outcome and reason do not match')
            if body.status == 'completed' and body.elapsed_ms is not None and session['skill'] == 'breathing' and not 60000 <= body.elapsed_ms < 90000:
                raise HTTPException(422, 'Breathing completion must measure 60 to under 90 seconds')
            db.execute("UPDATE sessions SET status = ?, ended_at = ?, elapsed_ms = ?, end_reason = ? WHERE id = ? AND status = 'active'", (body.status, now(), body.elapsed_ms, reason, session_id))
            session = get_session(db, session_id, user)
            if session["status"] != body.status:
                raise HTTPException(409, "A finished session cannot change status")
            return session

    @app.delete("/api/sessions/{session_id}", status_code=204)
    def delete_session(session_id: str, user=Depends(current_user)):
        with database() as db:
            get_session(db, session_id, user)
            db.execute("DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, user['id']))

    @app.delete("/api/sessions", status_code=204)
    def clear_history(user=Depends(current_user)):
        with database() as db:
            db.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))

    # Register after API routes so the built Vue app shares their origin.
    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app

app = create_app()
