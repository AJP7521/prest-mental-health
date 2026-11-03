# Part 2 Report: Working Skill, Persistence, and Failure Evidence

Repository: https://github.com/AJP7521/prest-mental-health

October 25, 2026

This report is a historical checkpoint from before account/profile integration and Chat with Waves. The current application includes those later changes; use the README and Part 3.3 report for current behavior.

## Exercises and Implementations

The initial application has two exercises: paced breathing and 5-4-3-2-1 grounding. They were selected to match the project requirements for short, structured skills practice.

## Paced Breathing

This exercise displays a bubble with a timer in the middle. When the user breathes in, the bubble expands, and compresses when the user breathes out. The time counts up and down and can be seen on screen so the user knows when to breathe in and out.

## 5-4-3-2-1 Grounding

Present one item at a time, preserving this sequence:

1. Five things the user can see.
2. Four things the user can feel.
3. Three things the user can hear.
4. Two things the user can smell.
5. One thing the user can taste.

The proposed interface lets the user advance at their own pace without requiring written responses. Stop and return controls remain available throughout.

## User experience

Users choose their preferred exercise from the skill-selection screen. During an exercise, the screen emphasizes the current action and avoids menus or large amounts of information. Completing an exercise is optional; model suggestions must never force participation.

## Crisis Support

Crisis-support access remains visible on every screen, including loading and error states, without depending on a menu, model response, or multiple navigation steps. The specification requires fictional support access for the prototype. Label it clearly as a demonstration so it does not imply a connection to real assistance.

## Remaining limitations (I had Codex document this so I know what to finish for Part 3)

- Live-model behavior remains unverified without credentials. The current evidence cannot satisfy a requirement specifically demanding an observed runtime model response.
- No class-specific Network-panel capture or full HAR was collected; request evidence uses access logs and browser-console capture instead.
- Timing is client-reported, not tamper-resistant. Background tabs, sleep, or a suspended browser can delay callbacks. The UI targets 60 seconds and treats a callback arriving at 90 seconds or later as interrupted, but cannot guarantee real-time scheduling while the browser is suspended.
- Abrupt process termination or closing a tab can defeat the departure request. Session storage may disappear when the tab closes; a record may remain explicitly unfinished. Recovery is one pending record per tab, not a durable offline queue; starting another session before recovery may replace the checkpoint.
- Failure recovery records interrupted, not an unverified completed outcome. `ended_at` then reflects recovery time. There is no cross-device sync, authentication, multi-user isolation, encryption at rest, or automatic retention policy.
- Existing API clients can still submit legacy outcomes without a measured duration; those are not evidence of measured completion. The new interface supplies duration.
- Accessibility was checked through visible labels, focus behavior, persistent support, and existing reduced-motion styling, but no full screen-reader, mobile-device, or cross-browser audit was performed.
- This is a fictional classroom prototype, not a clinical service or working crisis-support channel. Model output quality and safety are not comprehensively evaluated.
