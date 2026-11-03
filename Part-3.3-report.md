# Part 3.3: Integration, Evaluation, and Demonstration

Date: November 2, 2026

## Integration and personalization decision

The application retains the Part 1 exercise boundaries: paced breathing is six 4-second inhales and 6-second exhales (60 seconds total); grounding remains 5-4-3-2-1, one observation per step; both can be stopped; fictional support stays on screen. SQLite-backed accounts, editable display names and breathing motion preferences, exercise history, and optional chat are integrated in the current app.

Part 3.1 identified editable profile state, history-based adaptation, and a last-practiced exercise shortcut as useful personalization. The app already saved profile and history data, but the history did not affect the home screen. I added a small, dismissible **Practice again** suggestion for the user's latest started and ended exercise. It is based on recorded use, not an inference about what will help. All skill choices remain visible, and **Not now** dismisses it for the current visit. A server query limits the shortcut to the signed-in user's own completed or stopped sessions that actually began; empty history and unfinished setup records produce no shortcut.

I kept recommendations out of the exercise screen and did not add a distress score, mood inference, or clinical claim. The model still receives recent chat messages only. Profile and exercise history are not sent to the model; adding that would transmit more personal practice context to the provider and was not needed for the local repeat shortcut. This means the chatbot is not history-personalized, which remains a limitation if the rubric expects that specific behavior. The history shortcut and profile preference are user-controlled and can be overridden.

## Evaluation method and results

The repeatable suite `backend/tests/test_part3_evaluation.py` runs 17 fictional scenarios against temporary SQLite databases. The model is mocked in chat cases; the suite does not contact the provider. I ran `backend/.venv/bin/python -m pytest backend/tests -q`: **28 passed**, including all 17 scenarios below. The frontend suite reports **3 passed** and `npm run build` completed successfully.

| # | Fictional action | Expected result | Observed result |
| --- | --- | --- | --- |
| 1 | Mira registers with a fictional username and display name | Account is created and profile is readable | Pass: 201; profile returned Mira |
| 2 | User registers with a username containing a space | Input is rejected | Pass: 422 |
| 3 | User starts grounding | Active session and exercise start time are saved | Pass: active session; start timestamp present |
| 4 | User completes paced breathing at 60 seconds | Completion is accepted | Pass: completed with completed end reason |
| 5 | Client reports breathing completion at 90 seconds | Completion is rejected | Pass: 422 |
| 6 | User stops tracing after 1.2 seconds | Session stays stopped and duration is saved | Pass: stopped, 1,200 ms |
| 7 | Reload recovery submits the same interrupted ending twice | Outcome remains interrupted without conflict | Pass: both requests returned the same ended session |
| 8 | User filters history to grounding | Only grounding sessions appear | Pass: grounding only |
| 9 | User logs out and returns after app restart | Saved history remains available to the same account | Pass: wave session persisted |
| 10 | A second account requests another account's session | No session data is exposed | Pass: empty history and 404 for the session |
| 11 | User deletes one of two sessions | Only the selected record is removed | Pass: the other record remained |
| 12 | User clears exercise history | Only that account's records are cleared | Pass: second account's wave session remained |
| 13 | Chat has no API key | App reports unavailable; no scripted answer is returned | Pass: unavailable and 503, no saved exchange |
| 14 | Mock returns an optional suggestion | User and assistant messages are stored | Pass: two-message exchange persisted |
| 15 | Mock provider raises an exception with a fake secret in the text | API returns a sanitized error and preserves the user's question | Pass: 502; secret absent; question saved |
| 16 | User sends seven mocked chat requests in one minute | Six are accepted; the next is rate limited | Pass: six 200 responses followed by 429 |
| 17 | History has no completed practice, then user starts and stops a wave | Home shortcut uses the started wave, not an unstarted breathing record | Pass: wave returned; unstarted record excluded |

### Live-model selection

I repeated three fictional chat cases using the configured live model. These are observations, not deterministic tests. **3 live calls** were made in this session, below the 50-call limit.

| Fictional prompt focus | Expected behavior | Observed response |
| --- | --- | --- |
| Explain 5-4-3-2-1 grounding | Correct sequence, one observation at a time, optional participation | Pass: listed 5 see, 4 feel, 3 hear, 2 smell, 1 taste; said the user could skip or stop |
| Stopping after one observation | Affirm stopping without pressure | Pass: said stopping is okay and acknowledged the observation |
| Whether breathing treats anxiety | No diagnosis, treatment claim, or guaranteed outcome | Pass: described it as optional paced breathing and made no treatment promise |

The replies were consistent with the intended optional tone in this small selection. Three calls cannot establish model reliability or safety across prompts, accounts, or future model versions.

## Explicit behavior checks

1. **Fictional support remains available through exercise states.** Observed in the local browser on login, grounding, stopped, and chat screens: the fixed footer continued to show the clearly fictional 000-000-0000 demo number and direct support page.
2. **A user can stop without completing an exercise.** Observed in the local browser: grounding stopped after the first observation, displayed a stopped result and 4.6-second duration, and then recorded that grounding as recent practice. No later steps were required.
3. **A provider failure does not expose exception text or remove other controls.** Mocked scenario 15 returned a generic 502 response without the fake secret while retaining the user's question. Source review confirms the support footer is outside the chat request state; I did not trigger this failure through the browser in this turn. Earlier browser evidence shows failed-save and API-down handling in `evidence/part2/06-failed-save.png` and `evidence/part2/07-support-api-down.png`.

## Finding, code explanation, and remaining limits

A surprising finding is that failed model attempts count toward the per-account rate limit. The request is counted before the provider call, so repeated errors can use the six-per-minute allowance. This prevents repeated failing requests from bypassing the limit, but the UI should make the wait understandable. The existing failure/limit test covers this behavior.

The new `GET /api/sessions/recent` route in `backend/main.py` selects only the authenticated user's sessions with an `exercise_started_at` timestamp and a terminal `completed` or `stopped` status. This avoids turning an accidental setup or unfinished session into the suggested repeat. `App.vue` stores that response and shows two explicit actions: **Practice again** and **Not now**. The session record remains the source of truth; the browser does not infer a user's state.

Not tested: a full screen-reader and mobile-device audit, extended browser suspension around the 90-second breathing cutoff, and broader live-model safety or variation. The project remains a fictional coursework prototype, not clinical care. The provider can retain data according to its own policies; the app's `store: false` request is not a zero-retention promise.

## Clean-checkout verification and demonstration status

I made an isolated fresh copy at `/private/tmp/mh-clean-checkout`, without Git metadata, existing databases, or installed dependency directories. `PORT=8001 python3 launch.py` installed dependencies, built the Vue app, started FastAPI, and the login page opened at `http://127.0.0.1:8001/`. The README now documents the alternate-port option. This was a fresh-copy launcher check, not a second-machine or Windows check.

The finished app was demonstrated in the browser using a fictional account: start grounding, stop after the first item, return home, see the optional repeat suggestion, and open chat. The browser tab remains available at `http://127.0.0.1:8001/` for review.

**Process screencast is not attached yet.** The available computer-use tools support browser interaction and screenshots but do not provide a screen-video recording control. Existing Part 2 artifacts document the failed-save and API-down evidence. `evidence/part3/recording-guide.md` gives a short capture sequence for recording the required failure, evidence, and decision on the host computer. Do not treat that guide or the older screenshots as a completed Part 3.3 screencast.
