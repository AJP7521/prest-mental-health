import httpx
from fastapi.testclient import TestClient
from backend import coaching
from backend.main import create_app
from backend.tests.test_api import sign_in, HEADERS


def test_luna_request(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only')
    monkeypatch.setenv('OPENAI_MODEL', 'old-model')
    real_client = httpx.Client
    def handler(request):
        import json
        body = json.loads(request.content)
        assert body['model'] == 'gpt-6-luna'
        assert body['reasoning'] == {'effort': 'none'}
        assert body['store'] is False
        assert body['max_output_tokens'] == 250
        return httpx.Response(200, json={'output':[{'type':'message','content':[{'type':'output_text','text':'Try an exercise whenever you like.'}]}]})
    monkeypatch.setattr(coaching.httpx, 'Client', lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    assert coaching.reply([{'role':'user','content':'Fictional example'}]) == 'Try an exercise whenever you like.'


def test_chat_missing_key_isolation_limits_and_failure(tmp_path, monkeypatch):
    from backend import key_store
    monkeypatch.setattr(key_store, 'KEY_FILE', tmp_path / 'missing-key')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    app = create_app(tmp_path / 'chat.sqlite3')
    with TestClient(app, headers=HEADERS) as a, TestClient(app, headers=HEADERS) as b:
        assert a.get('/api/chat/messages').status_code == 401
        sign_in(a)
        b.post('/api/auth/register', json={'username':'other','password':'fictional-pass-123','display_name':'Other'})
        assert a.get('/api/coaching').json() == {'mode':'unavailable','model':'gpt-6-luna'}
        assert a.post('/api/chat/messages', json={'content':'Hello'}).status_code == 503
        monkeypatch.setenv('OPENAI_API_KEY', 'test-only')
        monkeypatch.setattr(coaching, 'reply', lambda messages: 'Optional suggestion.')
        assert a.post('/api/chat/messages', json={'content':'  '}).status_code == 422
        r=a.post('/api/chat/messages', json={'content':'Fictional question'})
        assert r.status_code == 200
        assert r.json()[-1]['model'] == 'gpt-6-luna'
        assert b.get('/api/chat/messages').json() == []
        b.delete('/api/chat/messages')
        assert len(a.get('/api/chat/messages').json()) == 2
        def fail(messages):
            raise ValueError('secret-should-never-appear')
        monkeypatch.setattr(coaching, 'reply', fail)
        r=a.post('/api/chat/messages', json={'content':'Test failure'})
        assert r.status_code == 502 and 'secret' not in r.text
        assert a.get('/api/chat/messages').json()[-1]['content'] == 'Test failure'
        for _ in range(4):
            a.post('/api/chat/messages', json={'content':'Test failure'})
        a.delete('/api/chat/messages')
        assert a.get('/api/chat/messages').json() == []
        assert a.post('/api/chat/messages', json={'content':'Limit test'}).status_code == 429
