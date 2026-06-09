-- Migration 012: add whatsapp contact field to affiliates
-- Applied directly via Supabase MCP on 2026-06-09; this file documents the change.
ALTER TABLE affiliates ADD COLUMN IF NOT EXISTS whatsapp TEXT;
