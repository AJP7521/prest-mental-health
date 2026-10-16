# Project Prompts

Reusable prompts for Part 1 research and design, followed by a conversation transcript. The reusable prompts are suggestions, not a record of work already performed. Copy the shared context before the prompt you want to use.

## Shared context

```text
Read AGENTS.md, README.md, and Part-1-report.md. Work within Part 1: research and design; a working application is not required.

Plan for Vue in frontend/, FastAPI in backend/, SQLite persistence, and localhost development. FastAPI owns API routes, database access, session records, skill history, conversation history, and error handling. Vue owns navigation, skill selection, exercise progression, breathing animations, stop controls, support controls, and loading states.

Support paced breathing with a 4-second inhale and 6-second exhale for 60 seconds total, always below 90 seconds. Support grounding in this order: five things seen, four felt, three heard, two smelled, and one tasted. Present one grounding item at a time.

Users choose their exercise and may stop or return at any point. Suggestions remain optional. Exercise screens emphasize the current action with minimal text. Clearly labeled fictional crisis-support access stays visible on every screen without menus, model responses, or extra navigation steps. Do not imply that demonstration support connects to real assistance.

Use synthetic data. Distinguish requirements, proposals, verified findings, and outstanding questions. Do not claim that research or implementation is complete without evidence.
```

## Research the exercises

```text
Find credible sources about paced breathing and 5-4-3-2-1 grounding. Cite the sources and summarize their relevance and limitations. Distinguish evidence about the general techniques from evidence for this project's exact timing and sequence. Do not present design requirements as clinically validated facts. Produce concise research notes and identify questions still requiring investigation.
```

## Design the user flow

```text
Describe the flow from skill selection through each exercise to completion or stopping. Include loading and error states. Specify the current action, available controls, and transitions for each screen. Preserve user choice, visible fictional support access, and the ability to stop or return. Keep the design within the Part 1 scope.
```

## Draft wireframes and interface copy

```text
Draft text wireframes and concise interface copy for skill selection, paced breathing, each grounding stage, completion, stopped sessions, loading, errors, and fictional support. Show one grounding item at a time. Include accessible labels, keyboard behavior, and a reduced-motion alternative. Label support as a demonstration and avoid promises of treatment or guaranteed outcomes.
```

## Plan the architecture and data model

```text
Propose the frontend and backend directory structure, API contracts, and minimal SQLite schema. Describe session, skill-history, and conversation-history responsibilities. Distinguish active, completed, and stopped sessions. Identify required versus optional data, retention and deletion decisions, and error behavior. Ensure stopping an exercise does not depend on a successful network request. Use fictional examples and do not implement the application yet.
```

## Review the design

```text
Review the proposed design against AGENTS.md. Check breathing duration, grounding order, one-item-at-a-time presentation, optional participation, stop and return controls, and fictional support visibility on every screen. Check accessibility and loading or error behavior. Report concrete gaps with references to the relevant files; distinguish confirmed issues from open questions.
```

## Update the Part 1 report

```text
Update Part-1-report.md using the actual research and design artifacts available in the workspace. Include sources, design decisions, architecture, current status, and remaining work. Separate completed work from proposals. Preserve accurate requirements and do not invent test results, research findings, or implemented features.
```

## Conversation transcript

User messages and assistant replies through the request to save this conversation, including progress updates. Tool calls, tool outputs, and environment metadata are omitted. Earlier statements describe the workspace at the time of each reply.

### 1. Create the initial documentation

**User:**

create a READ.md and AGENTS.md

**Assistant — progress:**

I’ll check the workspace and create both files to fit the project.

**Assistant:**

Created both files:

- [READ.md](/Users/prest/Desktop/ChatGPT/mental-health/READ.md): Project overview and getting-started steps.
- [AGENTS.md](/Users/prest/Desktop/ChatGPT/mental-health/AGENTS.md): Agent instructions, data privacy practices, and verification expectations.

Both reflect the workspace’s current empty state.

### 2. Create the first report

**User:**

create a repord.md

**Assistant — progress:**

I’ll create `repord.md` with a short report on the workspace’s current status.

**Assistant:**

Created [repord.md](/Users/prest/Desktop/ChatGPT/mental-health/repord.md) with the project requirements, technical design, current status, and suggested next steps.

### 3. Create the named Part 1 report

**User:**

create a report.md and name it "Part-1-report.md"

**Assistant — progress:**

I’ll rename the existing report to `Part-1-report.md`.

**Assistant — progress:**

The earlier report is no longer in the workspace. I’ll create `Part-1-report.md` from the current project requirements.

**Assistant:**

Created [Part-1-report.md](/Users/prest/Desktop/ChatGPT/mental-health/Part-1-report.md) with the project requirements, proposed design, architecture, and remaining work.

### 4. Create the prompts file

**User:**

create a prompts file

**Assistant — progress:**

I’ll create `prompts.md` with reusable prompts for the project’s research and design work.

**Assistant:**

Created [prompts.md](/Users/prest/Desktop/ChatGPT/mental-health/prompts.md) with reusable prompts for research, user flows, wireframes, architecture, design reviews, and report updates.

### 5. Save the conversation

**User:**

push this conversation to prompts.md.

**Assistant — progress:**

I’ll append this conversation’s user messages and assistant replies to `prompts.md`, keeping the reusable prompts already there.
