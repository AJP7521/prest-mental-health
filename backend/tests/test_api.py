from fastapi.testclient import TestClient
from backend.main import create_app

HEADERS = {'X-Requested-With': 'mental-health-app'}
ACCOUNT = {'username': 'demo_user', 'password': 'fictional-password-123', 'display_name': 'Demo'}

def sign_in(client):
    client.headers.update(HEADERS)
    result = client.post('/api/auth/register', json=ACCOUNT)
    if result.status_code == 409:
        result = client.post('/api/auth/login', json=ACCOUNT)
    assert result.status_code in (200, 201)



def test_sessions_persist_and_terminal_states_are_protected(tmp_path):
    path = tmp_path / 'test.sqlite3'
    with TestClient(create_app(path)) as client:
        sign_in(client)
        assert client.get('/api/health').json() == {'status': 'ok'}
        assert len(client.get('/api/skills').json()) == 3
        assert client.post('/api/sessions', json={'skill': 'unknown'}).status_code == 422
        session = client.post('/api/sessions', json={'skill': 'breathing'}).json()
        url = f"/api/sessions/{session['id']}"
        stopped = client.patch(url, json={'status': 'stopped'}).json()
        assert stopped['ended_at'] is not None
        assert client.patch(url, json={'status': 'stopped'}).json() == stopped
        assert client.patch(url, json={'status': 'completed'}).status_code == 409
        assert client.patch('/api/sessions/missing', json={'status': 'stopped'}).status_code == 404
    with TestClient(create_app(path)) as client:
        sign_in(client)
        assert client.get('/api/sessions').json()[0]['status'] == 'stopped'
        assert client.get('/api/sessions?skill=grounding').json() == []


def test_timing_and_restart(tmp_path):
    path = tmp_path / 'part2.sqlite3'
    with TestClient(create_app(path)) as client:
        sign_in(client)
        session = client.post('/api/sessions', json={'skill': 'breathing'}).json()
        url = '/api/sessions/' + session['id']
        assert client.post(url + '/begin').json()['exercise_started_at']
        assert client.patch(url, json={'status': 'completed', 'elapsed_ms': 1000}).status_code == 422
        assert client.patch(url, json={'status': 'completed', 'elapsed_ms': 90000}).status_code == 422
        ended = client.patch(url, json={'status': 'completed', 'elapsed_ms': 60012}).json()
        assert ended['elapsed_ms'] == 60012
        assert ended['end_reason'] == 'completed'
        assert client.post(url + '/begin').status_code == 409
        assert client.patch(url, json={'status': 'stopped', 'end_reason': 'interrupted', 'elapsed_ms': 100}).status_code == 409
    with TestClient(create_app(path)) as client:
        sign_in(client)
        assert client.get('/api/sessions').json()[0] == ended


def test_existing_database_migrates_without_losing_history(tmp_path):
    import sqlite3
    path = tmp_path / 'legacy.sqlite3'
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, skill TEXT, status TEXT, started_at TEXT, ended_at TEXT)")
        db.execute("INSERT INTO sessions VALUES ('old', 'breathing', 'completed', '2026-10-01', '2026-10-01')")
    with TestClient(create_app(path)) as client:
        sign_in(client)
        assert client.get('/api/sessions').json() == []
        with sqlite3.connect(path) as db:
            assert db.execute("SELECT id, user_id FROM sessions WHERE id = 'old'").fetchone() == ('old', None)
        assert client.post('/api/sessions', json={'skill': 'breathing'}).status_code == 201


def test_wave_migration_preserves_sessions_and_legacy_messages(tmp_path):
    import sqlite3
    path = tmp_path / 'wave-migration.sqlite3'
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE sessions (id TEXT PRIMARY KEY, skill TEXT NOT NULL CHECK(skill IN ('breathing','grounding')), status TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT);
            INSERT INTO sessions VALUES ('old', 'grounding', 'completed', '2026-10-01', '2026-10-01');
            CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE, role TEXT, content TEXT, created_at TEXT);
            INSERT INTO messages VALUES (1, 'old', 'user', 'Legacy fictional message', '2026-10-01');
        """)
    with TestClient(create_app(path)) as client:
        sign_in(client)
        for outcome in ('completed', 'stopped'):
            response = client.post('/api/sessions', json={'skill': 'wave'})
            assert response.status_code == 201
            url = '/api/sessions/' + response.json()['id']
            assert client.post(url + '/begin').status_code == 200
            assert client.patch(url, json={'status': outcome, 'elapsed_ms': 2500}).json()['status'] == outcome
        assert len(client.get('/api/sessions?skill=wave').json()) == 2
    with TestClient(create_app(path)) as client:
        sign_in(client)
        assert len(client.get('/api/sessions?skill=wave').json()) == 2
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT skill FROM sessions WHERE id = 'old'").fetchone() == ('grounding',)
        assert db.execute('SELECT content FROM messages WHERE id = 1').fetchone() == ('Legacy fictional message',)
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
