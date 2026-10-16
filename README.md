# Mental Health Skills

A local Vue + FastAPI prototype for short, optional breathing and grounding exercises, with SQLite session history. Use fictional data only. Crisis-support controls are explicitly fictional demonstrations and do not connect to assistance.

## Project files

- `frontend/`: Vue interface and Vite development server.
- `backend/`: FastAPI API, SQLite persistence, and API tests.
- `AGENTS.md`: Project requirements.
- `Part-1-report.md`: Earlier research and design report; its implementation status describes the workspace before this application was added.
- `prompts.md`: Reusable prompts and the saved conversation transcript.

## Run locally

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

Open the URL printed by Vite (normally http://127.0.0.1:5173). Vite proxies `/api` to the backend on port 8000. API documentation is available at http://127.0.0.1:8000/docs. Keep both services bound to localhost; this prototype has no authentication or multi-user isolation.

SQLite creates `backend/data.sqlite3` on first startup. Set `DATABASE_PATH` to use a different location. Runtime data and dependency directories are ignored by Git.

## Behavior

- Breathing runs locally for six cycles of 4 seconds in and 6 seconds out, totaling 60 seconds.
- Grounding presents 15 observations individually: five seen, four felt, three heard, two smelled, and one tasted.
- Users can stop immediately, even if saving fails. Completed and stopped sessions are recorded separately.
- History lists up to 50 recent sessions and allows deletion of all stored sessions and their messages.
- Fictional crisis-support access stays fixed at the bottom of every screen.
- Motion follows the system reduced-motion preference.

A failed save shows an error; there is no offline synchronization. Closing or reloading the page during an exercise can leave an active record, displayed as “Not recorded as finished.” Browser suspension may delay the completion callback, but elapsed time is measured from the start rather than counting timer ticks.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| GET | `/api/skills` | Skill definitions |
| POST | `/api/sessions` | Start a session with `skill` set to `breathing` or `grounding` |
| GET | `/api/sessions` | History; optional `skill` filter and `limit` of 1–100 |
| PATCH | `/api/sessions/{id}` | Set `status` to `completed` or `stopped` |
| GET / POST | `/api/sessions/{id}/messages` | Read/store fictional conversation history; POST takes `role` and `content` |
| DELETE | `/api/sessions` | Delete all sessions and associated messages |

Conversation-history storage is available through the API. No chatbot or model integration is included, and the exercise interface does not solicit free-text health information. Records remain on disk until deleted; no automatic retention policy is implemented.

## Verification

```sh
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm test
npm run build
```

The backend tests use temporary databases. Frontend tests check breathing boundaries and grounding sequence. `npm run build` produces `frontend/dist`; Vite's development proxy is not included in those static assets, so serving that build requires a separate `/api` reverse proxy.

## Technical references

- [Vue quick start](https://vuejs.org/guide/quick-start.html)
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
