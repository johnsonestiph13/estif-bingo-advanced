-- =====================================================
-- ESTIF BINGO 24/7 - TELEGRAM INTEGRATION TABLES
-- Migration: 003_add_telegram_tables.sql
-- Description: Tables for Telegram bot integration
-- =====================================================

-- ==================== TELEGRAM LINKS TABLE ====================
-- Maps Telegram user IDs to game accounts
CREATE TABLE IF NOT EXISTS telegram_links (
    telegram_id BIGINT PRIMARY KEY,
    phone VARCHAR(20),
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE telegram_links IS 'Links Telegram users to game accounts';

-- ==================== PENDING REGISTRATIONS TABLE ====================
-- Stores registration requests awaiting admin approval
CREATE TABLE IF NOT EXISTS pending_registrations (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    phone VARCHAR(20),
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    processed_at TIMESTAMP
);

COMMENT ON TABLE pending_registrations IS 'Stores pending Telegram user registrations';

-- ==================== OTP CODES TABLE ====================
-- Stores one-time passwords for Bingo login
CREATE TABLE IF NOT EXISTS otp_codes (
    telegram_id BIGINT PRIMARY KEY,
    otp VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE otp_codes IS 'Stores OTP codes for Bingo game login';

-- ==================== AUTH TOKENS TABLE ====================
-- Stores one-time authentication codes for game access
CREATE TABLE IF NOT EXISTS auth_tokens (
    token VARCHAR(64) PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE auth_tokens IS 'One-time authentication tokens for game access';

-- ==================== INDEXES ====================
CREATE INDEX IF NOT EXISTS idx_telegram_links_phone ON telegram_links(phone);
CREATE INDEX IF NOT EXISTS idx_pending_registrations_status ON pending_registrations(status);
CREATE INDEX IF NOT EXISTS idx_pending_registrations_telegram ON pending_registrations(telegram_id);
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires ON otp_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_telegram ON auth_tokens(telegram_id);

-- ==================== CLEANUP FUNCTIONS ====================

-- Function to clean expired OTP codes
CREATE OR REPLACE FUNCTION clean_expired_otp()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM otp_codes WHERE expires_at < NOW()
    RETURNING COUNT(*) INTO deleted_count;
    
    RETURN deleted_count;
END;
$$;

-- Function to clean expired auth tokens
CREATE OR REPLACE FUNCTION clean_expired_auth_tokens()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_tokens WHERE expires_at < NOW()
    RETURNING COUNT(*) INTO deleted_count;
    
    RETURN deleted_count;
END;
$$;

-- ==================== VERIFICATION ====================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 003_add_telegram_tables.sql completed successfully';
    RAISE NOTICE '   - Created telegram_links table';
    RAISE NOTICE '   - Created pending_registrations table';
    RAISE NOTICE '   - Created otp_codes table';
    RAISE NOTICE '   - Created auth_tokens table';
    RAISE NOTICE '   - Created cleanup functions';
END $$;