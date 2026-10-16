# Project Purpose

This application is designed to support short, structured exercises for mental health skills.

## Requirements

Use:

Vue for the frontend 
FastAPI for the backend
SQLite for persistence
localhost for development

Maintain seperate frontend and backend directories.

# Part 1: Research and Design

Working application is not required.

## Supported Skills

## 1. Paced Breathing

Inhale for 4 seconds
Exhale for 6 seconds
Repeat for 60 seconds

## 2. 5-4-3-2-1 Grounding

Keep this sequence:

1. 5 things the user can see
2. 4 things the user can feel
3. 3 things the user can hear
4. 2 things the user can smell
1. 1 thing the user can taste

Present one thing at a time.

Always provide a way to stop or return.

## Research Requirements

Paced breathing should remain below 90 seconds.
Target time is 60 seconds.

Crisis-support access must be fiction, not real.
Do not hide crisis-support information behind:

Menus
Model reponses
Multiple navigation steps

User must have the option to stop. Do not force completion.

Model can offer suggestions, but must not force anything on the user.

## Design Principles

During exercises, the display should only show the action needed for the current exercise. Avoid menus or large amounts of information during the exercise.

Crisis-support access must remain available at ALL TIMES. Every screen should show it no matter what.

FastAPI must handle:

API routed
SQLite access
Session records
Skill history
Conversation history
Error handeling

Vue must handle:

Navigation
Skill selection interface
Breating animations
Exercise progression
Stop controls
Crisis-support controls
Loading states