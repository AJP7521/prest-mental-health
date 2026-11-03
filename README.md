# Mental Health Skills

A local Vue + FastAPI prototype for short, optional breathing and grounding exercises, with SQLite session history. Use fictional data only. Crisis-support controls are explicitly fictional demonstrations and do not connect to assistance.

## Project files

- `frontend/`: Vue interface and Vite development server.
- `backend/`: FastAPI API, SQLite persistence, and API tests.
- `AGENTS.md`: Project requirements.
- `Part-1-report.md`: Earlier research and design report; its implementation status describes the workspace before this application was added.
- `prompts.md`: Planning and implementation prompts used during development.

## Launch after downloading from GitHub

Install Python 3.10+ and Node.js 22.12+ (including npm). On Windows, enable Python's **Add Python to PATH** installer option.

Download this repository using **Code → Download ZIP** and extract it, or clone it:

```sh
git clone https://github.com/AJP7521/prest-mental-health.git
cd prest-mental-health
```

Open a terminal in the extracted or cloned project folder (the folder containing `launch.py`). On macOS or Linux, run:

```sh
python3 launch.py
```

On Windows, run:

```powershell
py launch.py
```

The launcher creates a Python virtual environment, installs dependencies, builds Vue, and starts FastAPI. Internet access is required for dependency installation. Once the terminal says **Application startup complete**, open **http://127.0.0.1:8000**. Keep the terminal open while using the app; press **Ctrl+C** to stop. Run the same command to launch again or after downloading updates.

Each person runs their own copy on their computer, with their own local SQLite history. The GitHub repository page itself does not run the application. The launcher uses port 8000 by default. If it is unavailable, choose another localhost port:

```sh
PORT=8001 python3 launch.py
```

In PowerShell, run `$env:PORT = "8001"` and then `py launch.py`. If dependency installation fails, check your internet connection and installed Python/Node versions, then retry.

## Development with live reload

Requires Node.js 20.19+ or 22.12+ and Python 3.10+.

From the project root, set up and start the backend:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite (normally http://127.0.0.1:5173). Vite proxies `/api` to the backend on port 8000. API documentation is available at http://127.0.0.1:8000/docs. Keep both services bound to localhost; accounts and history are local to this server. This remains a localhost coursework prototype, not a public hosting setup.

SQLite creates `backend/data.sqlite3` on first startup. Set `DATABASE_PATH` to use a different location. Runtime data and dependency directories are ignored by Git.

## Behavior

- Breathing runs locally for six cycles of 4 seconds in and 6 seconds out, totaling 60 seconds.
- Trace a wave offers a draggable wave with mouse, touch, and keyboard controls. It is self-paced, has no scoring or automatic completion, and saves completed/stopped outcomes in history.
- Grounding presents 15 observations individually: five seen, four felt, three heard, two smelled, and one tasted.
- Users can stop immediately, even if saving fails. Completed, stopped, and interrupted outcomes are distinguished, with measured exercise duration.
- History is private to the signed-in account, filters by exercise, and pages through 20 sessions at a time. Deleting history removes only that account’s sessions and associated messages.
- Fictional crisis-support access stays fixed at the bottom of every screen, with a direct standalone `/support.html` route.
- Motion follows the system reduced-motion preference.

A failed save shows an error. A best-effort departure request and per-tab checkpoint allow reload recovery as interrupted; abrupt closure can still leave an unfinished record. This is not a durable offline queue. Browser suspension may delay callbacks; elapsed time uses a monotonic clock, and a breathing callback delayed to 90 seconds or more is treated as interrupted.

## Accounts and profiles

On the login page, choose **Create an account**, enter a username (3–40 letters, numbers, or underscores), a fictional display name, and a password (10–128 characters). Registration signs you in. Returning users can log in with the same username and password.

**My profile** lets you update your display name and choose animated or text-only breathing. Both are saved in SQLite and restored on later visits. System reduced-motion preferences take precedence over animation. **My history** shows each exercise’s date, outcome, and duration; filter by exercise and use pagination for older sessions.

The home screen may offer an optional shortcut to repeat the most recent started exercise. It uses only the signed-in account's saved session history, excludes unfinished setup sessions, and leaves all exercise choices available. Dismiss it with **Not now**.

Accounts, profiles, exercise records, and legacy conversations live in `backend/data.sqlite3` (or `DATABASE_PATH`). Keep that database to retain profiles across application restarts. Accounts belong to this server installation, not to a cloud account or another computer’s copy.

Passwords use salted scrypt hashes. Login tokens are random, stored as hashes in SQLite, and sent in HttpOnly, SameSite=Strict cookies that expire after seven days. Logging out revokes the current token without deleting the profile or history. Cookies use Secure when served over HTTPS. API writes require `X-Requested-With: mental-health-app`; the frontend supplies this header. History endpoints check ownership on the backend.

Existing anonymous history remains preserved with no account owner and is not exposed or automatically assigned to newly registered accounts. No records are deleted during migration. Password reset/recovery, login rate limiting, account deletion, and production hosting hardening are not implemented; continue to use localhost and fictional data.

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Create account with username, password, display_name |
| POST | `/api/auth/login` | Log in with username and password |
| POST | `/api/auth/logout` | Revoke current login |
| GET | `/api/profile` | Read signed-in profile |
| PATCH | `/api/profile` | Update display_name and animate_breathing |

Session and message routes below require login. `GET /api/sessions` also accepts a nonnegative `offset` for pagination. The API never accepts a client-selected owner for a session.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| GET | `/api/skills` | Skill definitions |
| POST | `/api/sessions` | Start a session with `skill` set to `breathing`, `grounding`, or `wave` |
| GET | `/api/sessions` | History; optional `skill` filter and `limit` of 1–100 |
| GET | `/api/sessions/recent` | Most recent started and ended exercise for the signed-in account, or `null` |
| PATCH | `/api/sessions/{id}` | Set `status` to `completed` or `stopped` |
| DELETE | `/api/sessions/{id}` | Delete one owned session and its messages |
| DELETE | `/api/sessions` | Delete all sessions and associated messages |

Chat with Waves is available as a separate home-screen card, using `gpt-6-luna` via the Responses API with reasoning disabled, at most 250 output tokens, and `store: false`. It uses a locally saved API key or `OPENAI_API_KEY` in the backend environment; old `OPENAI_MODEL` settings are ignored. Missing credentials show unavailable status, never scripted replies. Save the key once with `python3 backend/setup_api_key.py`, using hidden terminal input. The backend reads `backend/.openai-api-key` automatically, including after restarts. This is a plaintext local file with owner-only permissions on macOS/Linux, excluded from Git; do not share it or include it in project archives. An exported `OPENAI_API_KEY` overrides the file. Delete the file to remove the saved key. API credits and model access are required. No credentials belong in the frontend or repository.

Chat sends up to 12 recent messages to OpenAI and stores conversation history per account in SQLite. Use fictional information only. The chat screen displays the latest 100 messages and lets the user delete their full chat history. Provider retention is governed by OpenAI; `store: false` is not a zero-retention promise. Requests, including failed provider attempts, are limited to 6 per minute and 20 per hour per account. Limits are not reset by deleting history. Leaving chat does not cancel an already-sent provider request.

Chat API: `GET /api/coaching` reports configuration; authenticated `GET`, `POST` (`{"content":"fictional question"}`), and `DELETE /api/chat/messages` handle conversations. Older exercise-associated messages remain preserved in SQLite.

`POST /api/sessions/{id}/begin` records exercise start. Ending PATCH requests accept `elapsed_ms` and `end_reason` (`completed`, `stopped`, or `interrupted`, with interrupted using status stopped).

See [Part 2 report](Part-2-report.md) for earlier browser screenshots, SQLite exports, measured results, and limitations. See [Part 3.3 report](Part-3.3-report.md) for the current evaluation, personalization decision, and demonstration evidence.

## Verification

```sh
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm test
npm run build
```

The backend tests use temporary databases, including 17 fictional Part 3 evaluation scenarios with mocked model replies. Frontend tests check breathing boundaries and grounding sequence. `npm run build` produces `frontend/dist`; FastAPI serves that directory when it exists at startup, alongside `/api`. The launcher builds it before starting FastAPI. Live-model observations, if any, are recorded separately in the Part 3.3 report.

## Technical references

- [Vue quick start](https://vuejs.org/guide/quick-start.html)
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)


New chat replies reveal word by word with a brief wave animation. Reduced-motion settings show the full text immediately, and Show full reply skips the reveal. Read new replies aloud is enabled by default; users can turn it off, replay any assistant response, or stop speech. Browser speech synthesis supplies the voice (availability varies by browser/device); this does not call an OpenAI audio API. Speech stops when leaving chat or the page.

Chat voice settings include a device voice selector, a 0.5×–1.5× speaking-speed slider, and a preview button. Voice and speed are saved in browser local storage. Changing settings stops current speech; replay uses the new settings. Unavailable saved voices fall back to the browser default.
