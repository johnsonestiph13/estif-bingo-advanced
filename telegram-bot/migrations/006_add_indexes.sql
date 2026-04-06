-- =====================================================
-- MIGRATION: 006_add_indexes.sql
-- Description: Additional performance indexes
-- =====================================================

-- Additional indexes for better query performance

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_registered_lang ON users(registered, lang);
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram_status ON pending_withdrawals(telegram_id, status);
CREATE INDEX IF NOT EXISTS idx_otp_telegram_expires ON otp_codes(telegram_id, expires_at);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_users_active ON users(telegram_id) WHERE registered = TRUE;
CREATE INDEX IF NOT EXISTS idx_withdrawals_pending_recent ON pending_withdrawals(telegram_id, requested_at) WHERE status = 'pending';

-- Index for full-text search on phone (if needed)
-- CREATE INDEX IF NOT EXISTS idx_users_phone_gin ON users USING gin(phone gin_trgm_ops);

-- Analyze tables to update statistics
ANALYZE users;
ANALYZE pending_withdrawals;
ANALYZE otp_codes;
ANALYZE auth_codes;
ANALYZE settings;
ANALYZE commission_logs;

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 006_add_indexes.sql completed';
    RAISE NOTICE '   - Added composite indexes';
    RAISE NOTICE '   - Added partial indexes';
    RAISE NOTICE '   - Updated statistics';
END $$;