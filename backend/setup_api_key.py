"""Run in your terminal to save the key without echoing it or putting it in shell history."""
import getpass
import sys
from key_store import save_api_key


def main():
    if not sys.stdin.isatty():
        raise SystemExit('Run this script directly in your terminal for hidden key entry.')
    try:
        key = getpass.getpass('Paste your OpenAI API key, then press Return (input is hidden): ')
        save_api_key(key)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit('\nCancelled; no key saved.')
    except (OSError, ValueError):
        raise SystemExit('Could not save the key. Check the entry and backend folder permissions.')
    print('API key saved locally. The chatbot will use it automatically, including after restarts.')
    print('Open Chat with Waves and choose Refresh connection.')


if __name__ == '__main__':
    main()
