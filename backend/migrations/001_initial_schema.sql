-- ============================================================
-- Idea Stress-Test Engine — Initial Schema
-- Run in Supabase SQL editor (or psql against your DB)
-- ============================================================

-- Enable UUID extension (Supabase has this by default)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    tier        VARCHAR(10) NOT NULL DEFAULT 'free',   -- free | paid
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Ideas ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ideas (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    raw_text    TEXT NOT NULL,
    embedding   JSONB,                 -- float array for similarity dedup
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Analyses ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analyses (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idea_id      UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending',
    tier         VARCHAR(10) NOT NULL DEFAULT 'free',
    result_json  JSONB,
    error        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_analyses_idea_id ON analyses(idea_id);
CREATE INDEX IF NOT EXISTS idx_analyses_status   ON analyses(status);

-- ── Search Cache ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS search_cache (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash   VARCHAR(64) UNIQUE NOT NULL,
    query_text   TEXT NOT NULL,
    results_json JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_search_cache_hash ON search_cache(query_hash);
-- Auto-purge rows older than 24 hours via Supabase cron or pg_cron
-- ALTER TABLE search_cache ENABLE ROW LEVEL SECURITY; -- add when auth is wired

-- ── Score History ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS score_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id     UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    viability_score INTEGER NOT NULL,
    breakdown_json  JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);