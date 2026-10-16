from fastapi.testclient import TestClient
from backend.main import create_app


def test_sessions_persist_and_terminal_states_are_protected(tmp_path):
    path = tmp_path / 'test.sqlite3'
    with TestClient(create_app(path)) as client:
        assert client.get('/api/health').json() == {'status': 'ok'}
        assert len(client.get('/api/skills').json()) == 2
        assert client.post('/api/sessions', json={'skill': 'unknown'}).status_code == 422
        session = client.post('/api/sessions', json={'skill': 'breathing'}).json()
        url = f"/api/sessions/{session['id']}"
        stopped = client.patch(url, json={'status': 'stopped'}).json()
        assert stopped['ended_at'] is not None
        assert client.patch(url, json={'status': 'stopped'}).json() == stopped
        assert client.patch(url, json={'status': 'completed'}).status_code == 409
        assert client.patch('/api/sessions/missing', json={'status': 'stopped'}).status_code == 404
    with TestClient(create_app(path)) as client:
        assert client.get('/api/sessions').json()[0]['status'] == 'stopped'
        assert client.get('/api/sessions?skill=grounding').json() == []


def test_messages_completion_and_deletion(tmp_path):
    with TestClient(create_app(tmp_path / 'test.sqlite3')) as client:
        session = client.post('/api/sessions', json={'skill': 'grounding'}).json()
        url = f"/api/sessions/{session['id']}"
        assert client.post(url + '/messages', json={'role': 'user', 'content': 'Fictional example'}).status_code == 201
        assert client.post(url + '/messages', json={'role': 'user', 'content': ''}).status_code == 422
        assert len(client.get(url + '/messages').json()) == 1
        assert client.patch(url, json={'status': 'completed'}).json()['status'] == 'completed'
        assert client.get('/api/sessions?limit=0').status_code == 422
        assert client.delete('/api/sessions').status_code == 204
        assert client.get('/api/sessions').json() == []
        assert client.get(url + '/messages').status_code == 404
