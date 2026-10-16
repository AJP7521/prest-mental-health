"""Local-only skill exercise API. Use synthetic data."""
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

SKILLS = [
    {"id": "breathing", "name": "Paced breathing", "duration_seconds": 60},
    {"id": "grounding", "name": "5-4-3-2-1 grounding", "duration_seconds": None},
]

class SessionCreate(BaseModel):
    skill: Literal["breathing", "grounding"]

class SessionUpdate(BaseModel):
    status: Literal["completed", "stopped"]

class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


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
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    skill TEXT NOT NULL CHECK(skill IN ('breathing','grounding')),
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
        yield

    app = FastAPI(title="Mental Health Skills — Local Prototype", lifespan=lifespan)

    def now():
        return datetime.now(timezone.utc).isoformat()

    def get_session(db, session_id):
        row = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Session not found")
        return dict(row)

    @app.exception_handler(sqlite3.Error)
    async def database_error(request, error):
        return JSONResponse(status_code=503, content={"detail": "History storage is unavailable. You can still stop your exercise."})

    @app.get("/api/health")
    def health():
        with database() as db:
            db.execute("SELECT 1")
        return {"status": "ok"}

    @app.get("/api/skills")
    def skills():
        return SKILLS

    @app.post("/api/sessions", status_code=201)
    def start_session(body: SessionCreate):
        with database() as db:
            session_id = str(uuid4())
            db.execute("INSERT INTO sessions VALUES (?, ?, 'active', ?, NULL)", (session_id, body.skill, now()))
            return get_session(db, session_id)

    @app.get("/api/sessions")
    def history(skill: Literal["breathing", "grounding"] | None = None, limit: int = Query(50, ge=1, le=100)):
        with database() as db:
            rows = db.execute("SELECT * FROM sessions WHERE (? IS NULL OR skill = ?) ORDER BY started_at DESC LIMIT ?", (skill, skill, limit)).fetchall()
            return [dict(row) for row in rows]

    @app.patch("/api/sessions/{session_id}")
    def finish_session(session_id: str, body: SessionUpdate):
        with database() as db:
            db.execute("UPDATE sessions SET status = ?, ended_at = ? WHERE id = ? AND status = 'active'", (body.status, now(), session_id))
            session = get_session(db, session_id)
            if session["status"] != body.status:
                raise HTTPException(409, "A finished session cannot change status")
            return session

    @app.get("/api/sessions/{session_id}/messages")
    def messages(session_id: str):
        with database() as db:
            get_session(db, session_id)
            return [dict(row) for row in db.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id", (session_id,))]

    @app.post("/api/sessions/{session_id}/messages", status_code=201)
    def add_message(session_id: str, body: MessageCreate):
        with database() as db:
            get_session(db, session_id)
            cursor = db.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)", (session_id, body.role, body.content, now()))
            return dict(db.execute("SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)).fetchone())

    @app.delete("/api/sessions", status_code=204)
    def clear_history():
        with database() as db:
            db.execute("DELETE FROM sessions")

    return app

app = create_app()
