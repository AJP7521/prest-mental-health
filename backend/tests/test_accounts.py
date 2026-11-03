import sqlite3
from fastapi.testclient import TestClient
from backend.main import create_app

HEADERS = {'X-Requested-With': 'mental-health-app'}
ALICE = {'username': 'alice', 'password': 'fictional-password-123', 'display_name': 'Alice Demo'}
BOB = {**ALICE, 'username': 'bob', 'display_name': 'Bob Demo'}


def test_profile_login_logout_and_restart(tmp_path):
    path = tmp_path / 'accounts.sqlite3'
    with TestClient(create_app(path), headers=HEADERS) as client:
        assert client.get('/api/profile').status_code == 401
        assert client.post('/api/sessions', json={'skill': 'breathing'}).status_code == 401
        registered = client.post('/api/auth/register', json=ALICE)
        assert registered.status_code == 201
        assert 'HttpOnly' in registered.headers['set-cookie']
        assert 'SameSite=strict' in registered.headers['set-cookie']
        assert 'password_hash' not in registered.json()
        assert client.post('/api/auth/register', json=ALICE).status_code == 409
        assert client.patch('/api/profile', json={'display_name': 'Updated Alice', 'animate_breathing': False}).status_code == 200
        sid = client.post('/api/sessions', json={'skill': 'grounding'}).json()['id']
        assert client.patch('/api/sessions/' + sid, json={'status': 'completed', 'elapsed_ms': 12000}).status_code == 200
        token = client.cookies.get('practice_session')
    with TestClient(create_app(path), headers=HEADERS) as client:
        client.cookies.set('practice_session', token)
        assert client.get('/api/profile').json()['animate_breathing'] is False
        assert client.get('/api/sessions').json()[0]['id'] == sid
        assert client.post('/api/auth/logout').status_code == 204
        client.cookies.clear()
        client.cookies.set('practice_session', token)
        assert client.get('/api/profile').status_code == 401
        client.cookies.clear()
        assert client.post('/api/auth/login', json={**ALICE, 'password': 'wrong-password'}).status_code == 401
        assert client.post('/api/auth/login', json=ALICE).status_code == 200
        assert client.get('/api/profile').json()['display_name'] == 'Updated Alice'
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT password_hash FROM users').fetchone()[0] != ALICE['password']
        assert db.execute('SELECT token_hash FROM auth_sessions').fetchone()[0] != token


def test_accounts_cannot_read_change_or_delete_each_others_data(tmp_path):
    app = create_app(tmp_path / 'isolation.sqlite3')
    with TestClient(app, headers=HEADERS) as alice, TestClient(app, headers=HEADERS) as bob:
        alice.post('/api/auth/register', json=ALICE)
        bob.post('/api/auth/register', json=BOB)
        sid = alice.post('/api/sessions', json={'skill': 'breathing'}).json()['id']
        url = '/api/sessions/' + sid
        assert bob.get('/api/sessions').json() == []
        for method, suffix, payload in [('post', '/begin', {}), ('patch', '', {'status': 'stopped'})]:
            kwargs = {'json': payload} if payload is not None else {}
            assert getattr(bob, method)(url + suffix, **kwargs).status_code == 404
        assert bob.delete('/api/sessions').status_code == 204
        assert len(alice.get('/api/sessions').json()) == 1


def test_filters_pagination_expiry_and_csrf(tmp_path):
    path = tmp_path / 'filters.sqlite3'
    with TestClient(create_app(path), headers=HEADERS) as client:
        client.post('/api/auth/register', json=ALICE)
        for skill in ['breathing', 'grounding', 'breathing']:
            client.post('/api/sessions', json={'skill': skill})
        assert len(client.get('/api/sessions?skill=breathing').json()) == 2
        first = client.get('/api/sessions?limit=1').json()[0]['id']
        assert client.get('/api/sessions?limit=1&offset=1').json()[0]['id'] != first
        assert client.get('/api/sessions?offset=-1').status_code == 422
        assert client.delete('/api/sessions', headers={'X-Requested-With': ''}).status_code == 403
        with sqlite3.connect(path) as db:
            db.execute('UPDATE auth_sessions SET expires_at = 0')
        assert client.get('/api/profile').status_code == 401


def test_delete_single_session_is_owned_and_cascades(tmp_path):
    path = tmp_path / 'delete.sqlite3'
    app = create_app(path)
    with TestClient(app, headers=HEADERS) as alice, TestClient(app, headers=HEADERS) as bob:
        alice.post('/api/auth/register', json=ALICE)
        bob.post('/api/auth/register', json=BOB)
        sid = alice.post('/api/sessions', json={'skill': 'grounding'}).json()['id']
        other = alice.post('/api/sessions', json={'skill': 'breathing'}).json()['id']
        url = '/api/sessions/' + sid
        with sqlite3.connect(path) as db:
            db.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES (?, 'user', 'Legacy conversation', '2026-10-01')", (sid,))
        assert bob.delete(url).status_code == 404
        assert alice.delete(url, headers={'X-Requested-With': ''}).status_code == 403
        assert alice.delete(url).status_code == 204
        assert [s['id'] for s in alice.get('/api/sessions').json()] == [other]
        assert alice.delete(url).status_code == 404
        with sqlite3.connect(path) as db:
            assert db.execute('SELECT COUNT(*) FROM messages WHERE session_id = ?', (sid,)).fetchone()[0] == 0
    with TestClient(create_app(path), headers=HEADERS) as client:
        client.post('/api/auth/login', json=ALICE)
        assert [s['id'] for s in client.get('/api/sessions').json()] == [other]
