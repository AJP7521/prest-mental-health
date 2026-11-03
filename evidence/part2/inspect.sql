-- Run against evidence/part2/verification.sqlite3 (or your own local database).
PRAGMA table_info(sessions);
PRAGMA table_info(messages);
SELECT id, skill, status, started_at, exercise_started_at, ended_at,
       elapsed_ms, end_reason,
       ROUND((julianday(ended_at)-julianday(exercise_started_at))*86400,3) AS server_seconds
FROM sessions ORDER BY started_at;
SELECT id, session_id, role, content, created_at, source, model
FROM messages ORDER BY id;
PRAGMA integrity_check;
PRAGMA foreign_key_check;
