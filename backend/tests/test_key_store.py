import stat
import pytest
from backend import key_store


def test_saved_key_survives_reload_and_environment_override(tmp_path, monkeypatch):
    monkeypatch.setattr(key_store, 'KEY_FILE', tmp_path / '.openai-api-key')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert key_store.get_api_key() == ''
    key_store.save_api_key('  fictional-key-one  ')
    assert key_store.get_api_key() == 'fictional-key-one'
    assert stat.S_IMODE(key_store.KEY_FILE.stat().st_mode) == 0o600
    key_store.save_api_key('fictional-key-two')
    assert key_store.get_api_key() == 'fictional-key-two'
    monkeypatch.setenv('OPENAI_API_KEY', 'environment-key')
    assert key_store.get_api_key() == 'environment-key'
    monkeypatch.delenv('OPENAI_API_KEY')
    assert key_store.get_api_key() == 'fictional-key-two'
    with pytest.raises(ValueError):
        key_store.save_api_key('bad\nkey')
    assert key_store.get_api_key() == 'fictional-key-two'
    assert list(tmp_path.glob('.openai-key-*')) == []
