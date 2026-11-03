"""Local-only credential storage, excluded from version control."""
import os
from pathlib import Path
import tempfile

KEY_FILE = Path(__file__).with_name('.openai-api-key')


def get_api_key():
    override = os.getenv('OPENAI_API_KEY', '').strip()
    if override:
        return override
    try:
        return KEY_FILE.read_text(encoding='utf-8').strip()
    except OSError:
        return ''


def save_api_key(value):
    key = value.strip()
    if not key or any(char.isspace() for char in key):
        raise ValueError('Enter a nonempty API key without spaces or line breaks.')
    # Create with owner-only permissions before writing; replace atomically.
    fd, temporary = tempfile.mkstemp(prefix='.openai-key-', dir=KEY_FILE.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(key + '\n')
        os.replace(temporary, KEY_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
