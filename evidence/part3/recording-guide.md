# Part 3.3 recording guide

The repository does not contain the required process screencast yet. Use this guide to capture it on the host computer; keep all account names and exercise/chat content fictional.

## Suggested single recording (about 3–5 minutes)

1. Start with the locally running app and show the login screen and always-visible fictional support control.
2. Register a fictional account, open **My profile**, turn off the breathing animation, save, and return home. Briefly explain that the display name and animation preference are stored in SQLite and that reduced-motion settings still take precedence.
3. Start 5-4-3-2-1 grounding, advance once, then stop. Return home and show the recent-practice shortcut. Choose **Not now** to demonstrate override. Mention the saved session supplies the shortcut; it is not a clinical recommendation.
4. For the failure section, start a session and leave the exercise screen open. Stop FastAPI in its terminal, then use **Stop and return** in the browser. Show the local stopped outcome, save error, and persistent support control.
5. Point to `frontend/src/App.vue`'s `finish()` catch path and the interrupted-session checkpoint/recovery behavior. Explain the decision: preserve the user's ability to stop immediately and label uncertain persistence honestly; do not mark a failed save as a successful completion.
6. Restart FastAPI and reload or sign in again. Show history/recovery if the checkpoint is available. End by identifying one limitation: abrupt closure can still defeat a browser departure request.

## Capture notes

- On macOS, use the system Screenshot controls (Shift-Command-5) and select screen recording. Use the whole app and terminal in view when each is relevant; do not expose an API key or personal database.
- Save the recording under `evidence/part3/` and add its filename, duration, and the marked sections to `Part-3.3-report.md`.
- For failure evidence, the previous Part 2 captures at `evidence/part2/06-failed-save.png`, `evidence/part2/07-support-api-down.png`, and the associated console/backend logs are available as references. The recording should capture the current Part 3 app state rather than reuse those screenshots as if they were new.
