-- ============================================================
-- Idea Stress-Test Engine — Usage Tracking + Device Limits
-- Run in Supabase SQL editor (or psql against your DB)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Device Usage (rolling counters) ──────────────────────────
CREATE TABLE IF NOT EXISTS device_usage (
    device_id      TEXT PRIMARY KEY,
    first_seen     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen      TIMESTAMPTZ,
    visit_count    INT NOT NULL DEFAULT 0,
    analysis_count INT NOT NULL DEFAULT 0
);

-- ── Usage Events (time-series audit trail) ───────────────────
CREATE TABLE IF NOT EXISTS usage_events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id   TEXT NOT NULL,
    event_type  TEXT NOT NULL,   -- page_view | analysis_submit | analysis_blocked
    idea_chars  INT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_events_device_id
    ON usage_events(device_id);

CREATE INDEX IF NOT EXISTS idx_usage_events_created_at
    ON usage_events(created_at);

CREATE INDEX IF NOT EXISTS idx_usage_events_type_created_at
    ON usage_events(event_type, created_at);
