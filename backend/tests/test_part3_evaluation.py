"""Repeatable Part 3 evaluation cases using fictional data and mocked replies."""
import pytest
from fastapi.testclient import TestClient

from backend import coaching
from backend.main import create_app
from backend.tests.test_api import HEADERS, sign_in


@pytest.mark.parametrize("scenario", [
    "01_register_and_sign_in",
    "02_invalid_username_rejected",
    "03_start_grounding_session",
    "04_complete_breathing_at_60_seconds",
    "05_reject_breathing_at_90_seconds",
    "06_stop_exercise_early",
    "07_recover_interrupted_session_idempotently",
    "08_filter_history_by_skill",
    "09_history_survives_restart",
    "10_other_account_cannot_read_session",
    "11_delete_one_session",
    "12_clear_only_current_account_history",
    "13_unconfigured_model_is_honestly_unavailable",
    "14_mocked_reply_is_saved",
    "15_provider_failure_is_sanitized",
    "16_mocked_rate_limit_is_enforced",
    "17_recent_practice_shortcut_uses_only_started_history",
])
def test_fictional_evaluation_scenarios(scenario, tmp_path, monkeypatch):
    path = tmp_path / f"{scenario}.sqlite3"
    app = create_app(path)
    with TestClient(app, headers=HEADERS) as client:
        if scenario == "01_register_and_sign_in":
            response = client.post('/api/auth/register', json={
                'username': 'Fictional_User', 'password': 'fictional-password-123', 'display_name': 'Mira'
            })
            assert response.status_code == 201
            assert client.get('/api/profile').json()['display_name'] == 'Mira'
        elif scenario == "02_invalid_username_rejected":
            response = client.post('/api/auth/register', json={
                'username': 'bad name', 'password': 'fictional-password-123', 'display_name': 'Mira'
            })
            assert response.status_code == 422
        else:
            sign_in(client)

        if scenario == "03_start_grounding_session":
            created = client.post('/api/sessions', json={'skill': 'grounding'})
            assert created.status_code == 201 and created.json()['status'] == 'active'
            assert client.post(f"/api/sessions/{created.json()['id']}/begin").json()['exercise_started_at']
        elif scenario in ("04_complete_breathing_at_60_seconds", "05_reject_breathing_at_90_seconds"):
            session = client.post('/api/sessions', json={'skill': 'breathing'}).json()
            url = f"/api/sessions/{session['id']}"
            client.post(url + '/begin')
            elapsed = 60000 if scenario.startswith('04') else 90000
            response = client.patch(url, json={'status': 'completed', 'elapsed_ms': elapsed})
            assert response.status_code == (200 if elapsed == 60000 else 422)
            if elapsed == 60000:
                assert response.json()['end_reason'] == 'completed'
        elif scenario == "06_stop_exercise_early":
            session = client.post('/api/sessions', json={'skill': 'wave'}).json()
            client.post(f"/api/sessions/{session['id']}/begin")
            ended = client.patch(f"/api/sessions/{session['id']}", json={
                'status': 'stopped', 'end_reason': 'stopped', 'elapsed_ms': 1200
            }).json()
            assert (ended['status'], ended['end_reason'], ended['elapsed_ms']) == ('stopped', 'stopped', 1200)
        elif scenario == "07_recover_interrupted_session_idempotently":
            session = client.post('/api/sessions', json={'skill': 'grounding'}).json()
            url = f"/api/sessions/{session['id']}"
            client.post(url + '/begin')
            payload = {'status': 'stopped', 'end_reason': 'interrupted', 'elapsed_ms': 3500}
            first = client.patch(url, json=payload)
            second = client.patch(url, json=payload)
            assert first.status_code == second.status_code == 200
            assert first.json() == second.json() and second.json()['end_reason'] == 'interrupted'
        elif scenario == "08_filter_history_by_skill":
            for skill in ('breathing', 'grounding'):
                client.post('/api/sessions', json={'skill': skill})
            assert [s['skill'] for s in client.get('/api/sessions?skill=grounding').json()] == ['grounding']
        elif scenario == "09_history_survives_restart":
            session = client.post('/api/sessions', json={'skill': 'wave'}).json()
            client.post(f"/api/sessions/{session['id']}/begin")
            client.patch(f"/api/sessions/{session['id']}", json={'status': 'completed', 'elapsed_ms': 2000})
            client.post('/api/auth/logout')
            with TestClient(create_app(path), headers=HEADERS) as restarted:
                sign_in(restarted)
                assert restarted.get('/api/sessions').json()[0]['skill'] == 'wave'
        elif scenario == "10_other_account_cannot_read_session":
            session = client.post('/api/sessions', json={'skill': 'breathing'}).json()
            with TestClient(app, headers=HEADERS) as other:
                assert other.post('/api/auth/register', json={
                    'username': 'other_user', 'password': 'fictional-password-456', 'display_name': 'Noah'
                }).status_code == 201
                assert other.get('/api/sessions').json() == []
                assert other.get(f"/api/sessions/{session['id']}").status_code == 404
                assert other.get('/api/sessions/recent').json() is None
        elif scenario == "11_delete_one_session":
            first = client.post('/api/sessions', json={'skill': 'breathing'}).json()
            second = client.post('/api/sessions', json={'skill': 'wave'}).json()
            assert client.delete(f"/api/sessions/{first['id']}").status_code == 204
            assert [s['id'] for s in client.get('/api/sessions').json()] == [second['id']]
        elif scenario == "12_clear_only_current_account_history":
            client.post('/api/sessions', json={'skill': 'grounding'})
            with TestClient(app, headers=HEADERS) as other:
                other.post('/api/auth/register', json={
                    'username': 'other_user', 'password': 'fictional-password-456', 'display_name': 'Noah'
                })
                other_session = other.post('/api/sessions', json={'skill': 'wave'}).json()
                assert client.delete('/api/sessions').status_code == 204
                assert client.get('/api/sessions').json() == []
                assert other.get('/api/sessions').json()[0]['id'] == other_session['id']
        elif scenario == "13_unconfigured_model_is_honestly_unavailable":
            from backend import key_store
            monkeypatch.setattr(key_store, 'KEY_FILE', tmp_path / 'no-key')
            monkeypatch.delenv('OPENAI_API_KEY', raising=False)
            assert client.get('/api/coaching').json()['mode'] == 'unavailable'
            assert client.post('/api/chat/messages', json={'content': 'Fictional question'}).status_code == 503
            assert client.get('/api/chat/messages').json() == []
        elif scenario == "14_mocked_reply_is_saved":
            monkeypatch.setattr(coaching, 'configuration', lambda: {'mode': 'live', 'model': coaching.MODEL})
            monkeypatch.setattr(coaching, 'reply', lambda messages: 'You can choose an exercise or skip this suggestion.')
            result = client.post('/api/chat/messages', json={'content': 'Fictional practice question'})
            assert result.status_code == 200
            assert [message['role'] for message in result.json()] == ['user', 'assistant']
            assert result.json()[-1]['content'].startswith('You can choose')
        elif scenario == "15_provider_failure_is_sanitized":
            monkeypatch.setattr(coaching, 'configuration', lambda: {'mode': 'live', 'model': coaching.MODEL})
            monkeypatch.setattr(coaching, 'reply', lambda messages: (_ for _ in ()).throw(RuntimeError('private-secret-value')))
            response = client.post('/api/chat/messages', json={'content': 'Fictional request'})
            assert response.status_code == 502
            assert 'private-secret-value' not in response.text
            assert client.get('/api/chat/messages').json()[0]['content'] == 'Fictional request'
        elif scenario == "16_mocked_rate_limit_is_enforced":
            monkeypatch.setattr(coaching, 'configuration', lambda: {'mode': 'live', 'model': coaching.MODEL})
            monkeypatch.setattr(coaching, 'reply', lambda messages: 'Optional mock reply.')
            responses = [client.post('/api/chat/messages', json={'content': 'Fictional question'}) for _ in range(7)]
            assert [r.status_code for r in responses] == [200] * 6 + [429]
        elif scenario == "17_recent_practice_shortcut_uses_only_started_history":
            assert client.get('/api/sessions/recent').json() is None
            unstarted = client.post('/api/sessions', json={'skill': 'breathing'}).json()
            started = client.post('/api/sessions', json={'skill': 'wave'}).json()
            client.post(f"/api/sessions/{started['id']}/begin")
            client.patch(f"/api/sessions/{started['id']}", json={'status': 'stopped', 'elapsed_ms': 1500})
            recent = client.get('/api/sessions/recent').json()
            assert recent['id'] == started['id'] and recent['skill'] == 'wave'
            assert recent['id'] != unstarted['id']
