"""Short live exercise guidance; credentials remain local to the backend."""
import httpx

try:
    from .key_store import get_api_key
except ImportError:
    from key_store import get_api_key

MODEL = 'gpt-6-luna'
INSTRUCTIONS = '''You are Waves, an optional exercise guide for a fictional classroom prototype.
Use at most three short sentences. Help users choose or understand the app's exercises.
Paced breathing: six cycles of inhale 4 seconds, exhale 6 seconds, 60 seconds total.
Grounding: 5 things seen, 4 felt, 3 heard, 2 smelled, 1 tasted, one observation at a time.
Trace a wave: drag a pebble with a finger or mouse or use arrow keys, at any pace, without scoring.
Offer suggestions only. Users may skip or stop at any time. Do not diagnose, prescribe,
claim treatment benefits, or act as a therapist. Do not claim to operate the interface.
For crisis questions, clearly identify the on-screen support as fictional and not actual help;
encourage immediate real-world help if needed, without inventing phone numbers or links.
Do not solicit personal information. Use fictional practice information only.'''


def configuration():
    return {'mode': 'live' if get_api_key() else 'unavailable', 'model': MODEL}


def reply(messages):
    with httpx.Client(timeout=15) as client:
        response = client.post('https://api.openai.com/v1/responses',
            headers={'Authorization': 'Bearer ' + get_api_key()},
            json={'model': MODEL, 'instructions': INSTRUCTIONS, 'input': messages,
                  'reasoning': {'effort': 'none'}, 'max_output_tokens': 250, 'store': False})
        response.raise_for_status()
        payload = response.json()
    text = '\n'.join(part['text'] for item in payload.get('output', []) if item.get('type') == 'message'
                     for part in item.get('content', []) if part.get('type') == 'output_text')
    if not text.strip():
        raise ValueError('Empty response')
    return text[:2000]


def failure_message(error):
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        if status == 401:
            return 'OpenAI rejected the API key. Update the backend API key and restart.'
        if status == 429:
            try:
                details = error.response.json().get('error', {})
                message = str(details).lower()
            except ValueError:
                message = ''
            if any(word in message for word in ('quota', 'billing', 'credit')):
                return 'OpenAI API quota is unavailable. Check API credits, billing, and spending limits.'
            return 'OpenAI is rate limiting requests. Wait before trying again.'
        if status in (403, 404):
            return 'GPT-6 Luna is not accessible with this API key. Check model access and project permissions.'
        if status == 400:
            return 'OpenAI rejected the request configuration.'
    if isinstance(error, httpx.TimeoutException):
        return 'The reply timed out. You can try again or return to the exercises.'
    if isinstance(error, httpx.RequestError):
        return 'Could not connect to OpenAI. Check the backend network and certificate settings.'
    return 'Reply unavailable. You can try again or return to the exercises.'
