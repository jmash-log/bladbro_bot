-- Cycle Companion schema
-- SQLite. Run once at first startup.

PRAGMA foreign_keys = ON;

-- Users (one for now, but schema is future-proof)
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- Periods: the core record
CREATE TABLE IF NOT EXISTS periods (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    start_date  TEXT NOT NULL,   -- YYYY-MM-DD
    end_date    TEXT,            -- YYYY-MM-DD, NULL until ended
    status      TEXT DEFAULT 'confirmed',
    source      TEXT DEFAULT 'manual',   -- manual | whatsapp | backfill
    created_at  TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Cycle gaps: computed, for the "uncertain" flagging
CREATE TABLE IF NOT EXISTS cycle_gaps (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    prev_start  TEXT NOT NULL,
    next_start  TEXT NOT NULL,
    gap_days    INTEGER NOT NULL,
    status      TEXT DEFAULT 'uncertain',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Symptoms: free-form, linked to a date
CREATE TABLE IF NOT EXISTS symptoms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    date        TEXT NOT NULL,
    symptom     TEXT NOT NULL,
    severity    INTEGER,          -- 1-3, NULL if not given
    created_at  TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Reminders: for the WhatsApp phase
CREATE TABLE IF NOT EXISTS reminders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    message     TEXT NOT NULL,
    scheduled   TEXT NOT NULL,    -- ISO datetime
    sent        INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Settings: per-user preferences
CREATE TABLE IF NOT EXISTS settings (
    user_id     INTEGER PRIMARY KEY,
    timezone    TEXT DEFAULT 'Asia/Kolkata',
    reminder_hour INTEGER DEFAULT 9,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
