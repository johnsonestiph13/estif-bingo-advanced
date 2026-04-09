-- =====================================================
-- ESTIF BINGO 24/7 - TELEGRAM INTEGRATION TABLES
-- Migration: 003_add_telegram_tables.sql
-- Description: Tables for Telegram bot integration
-- Updated: Added support for string-based cartela IDs
-- =====================================================

-- ==================== TELEGRAM USERS TABLE ====================
-- Main table for Telegram user data
CREATE TABLE IF NOT EXISTS telegram_users (
    telegram_id BIGINT PRIMARY KEY,
    phone VARCHAR(20),
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'en',
    balance DECIMAL(10,2) DEFAULT 0,
    total_deposited DECIMAL(10,2) DEFAULT 0,
    total_withdrawn DECIMAL(10,2) DEFAULT 0,
    total_won DECIMAL(10,2) DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    referral_code VARCHAR(20) UNIQUE,
    referred_by BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE telegram_users IS 'Main table for Telegram user data and game stats';

-- ==================== TELEGRAM LINKS TABLE ====================
-- Maps Telegram user IDs to game accounts (backward compatibility)
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
    processed_at TIMESTAMP,
    processed_by BIGINT
);

COMMENT ON TABLE pending_registrations IS 'Stores pending Telegram user registrations';

-- ==================== OTP CODES TABLE ====================
-- Stores one-time passwords for Bingo login
CREATE TABLE IF NOT EXISTS otp_codes (
    telegram_id BIGINT PRIMARY KEY,
    otp VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attempts INTEGER DEFAULT 0
);

COMMENT ON TABLE otp_codes IS 'Stores OTP codes for Bingo game login';

-- ==================== AUTH TOKENS TABLE ====================
-- Stores one-time authentication codes for game access
CREATE TABLE IF NOT EXISTS auth_tokens (
    token VARCHAR(64) PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP
);

COMMENT ON TABLE auth_tokens IS 'One-time authentication tokens for game access';

-- ==================== REFERRALS TABLE ====================
-- Tracks referral relationships and bonuses
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    bonus_amount DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(referrer_id, referred_id)
);

COMMENT ON TABLE referrals IS 'Tracks referral relationships and bonuses';

-- ==================== DEPOSITS TABLE ====================
-- Tracks deposit requests and history
CREATE TABLE IF NOT EXISTS deposits (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    screenshot_url TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by BIGINT,
    approved_at TIMESTAMP,
    rejected_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE deposits IS 'Tracks deposit requests and history';

-- ==================== WITHDRAWALS TABLE ====================
-- Tracks withdrawal requests and history
CREATE TABLE IF NOT EXISTS withdrawals (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    withdrawal_method VARCHAR(50),
    account_info JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    processed_by BIGINT,
    processed_at TIMESTAMP,
    rejected_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE withdrawals IS 'Tracks withdrawal requests and history';

-- ==================== NOTIFICATIONS TABLE ====================
-- Stores notifications for users
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    title VARCHAR(200),
    message TEXT,
    type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

COMMENT ON TABLE notifications IS 'Stores notifications for users';

-- ==================== INDEXES ====================
-- Telegram users indexes
CREATE INDEX IF NOT EXISTS idx_telegram_users_phone ON telegram_users(phone);
CREATE INDEX IF NOT EXISTS idx_telegram_users_username ON telegram_users(username);
CREATE INDEX IF NOT EXISTS idx_telegram_users_referral_code ON telegram_users(referral_code);
CREATE INDEX IF NOT EXISTS idx_telegram_users_referred_by ON telegram_users(referred_by);
CREATE INDEX IF NOT EXISTS idx_telegram_users_balance ON telegram_users(balance DESC);
CREATE INDEX IF NOT EXISTS idx_telegram_users_games_won ON telegram_users(games_won DESC);
CREATE INDEX IF NOT EXISTS idx_telegram_users_last_active ON telegram_users(last_active DESC);

-- Telegram links indexes
CREATE INDEX IF NOT EXISTS idx_telegram_links_phone ON telegram_links(phone);
CREATE INDEX IF NOT EXISTS idx_telegram_links_username ON telegram_links(username);

-- Pending registrations indexes
CREATE INDEX IF NOT EXISTS idx_pending_registrations_status ON pending_registrations(status);
CREATE INDEX IF NOT EXISTS idx_pending_registrations_telegram ON pending_registrations(telegram_id);
CREATE INDEX IF NOT EXISTS idx_pending_registrations_requested ON pending_registrations(requested_at);

-- OTP codes indexes
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires ON otp_codes(expires_at);

-- Auth tokens indexes
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_telegram ON auth_tokens(telegram_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_used ON auth_tokens(used);

-- Referrals indexes
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);

-- Deposits indexes
CREATE INDEX IF NOT EXISTS idx_deposits_telegram ON deposits(telegram_id);
CREATE INDEX IF NOT EXISTS idx_deposits_status ON deposits(status);
CREATE INDEX IF NOT EXISTS idx_deposits_created ON deposits(created_at DESC);

-- Withdrawals indexes
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram ON withdrawals(telegram_id);
CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON withdrawals(status);
CREATE INDEX IF NOT EXISTS idx_withdrawals_created ON withdrawals(created_at DESC);

-- Notifications indexes
CREATE INDEX IF NOT EXISTS idx_notifications_telegram ON notifications(telegram_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

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

-- Function to clean old notifications
CREATE OR REPLACE FUNCTION clean_old_notifications(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM notifications 
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND is_read = TRUE
    RETURNING COUNT(*) INTO deleted_count;
    
    RETURN deleted_count;
END;
$$;

-- ==================== HELPER FUNCTIONS ====================

-- Function to update user last active timestamp
CREATE OR REPLACE FUNCTION update_last_active()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.last_active = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

-- Trigger to automatically update last_active on telegram_users
DROP TRIGGER IF EXISTS trigger_update_last_active ON telegram_users;
CREATE TRIGGER trigger_update_last_active
    BEFORE UPDATE ON telegram_users
    FOR EACH ROW
    EXECUTE FUNCTION update_last_active();

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_full_stats(telegram_id BIGINT)
RETURNS TABLE(
    balance DECIMAL(10,2),
    total_deposited DECIMAL(10,2),
    total_withdrawn DECIMAL(10,2),
    total_won DECIMAL(10,2),
    games_played INTEGER,
    games_won INTEGER,
    win_rate DECIMAL(5,2),
    referral_count BIGINT,
    total_referral_bonus DECIMAL(10,2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.balance,
        u.total_deposited,
        u.total_withdrawn,
        u.total_won,
        u.games_played,
        u.games_won,
        CASE WHEN u.games_played > 0 
             THEN ROUND((u.games_won::DECIMAL / u.games_played) * 100, 2)
             ELSE 0 
        END as win_rate,
        COUNT(DISTINCT r.referred_id) as referral_count,
        COALESCE(SUM(r.bonus_amount), 0) as total_referral_bonus
    FROM telegram_users u
    LEFT JOIN referrals r ON r.referrer_id = u.telegram_id AND r.status = 'completed'
    WHERE u.telegram_id = $1
    GROUP BY u.telegram_id;
END;
$$;

-- ==================== VERIFICATION ====================
DO $$
DECLARE
    table_count INTEGER;
    function_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('telegram_users', 'telegram_links', 'pending_registrations', 
                       'otp_codes', 'auth_tokens', 'referrals', 'deposits', 
                       'withdrawals', 'notifications');
    
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_type = 'FUNCTION';
    
    RAISE NOTICE '✅ Migration 003_add_telegram_tables.sql completed successfully';
    RAISE NOTICE '   - Created/Updated tables: %', table_count;
    RAISE NOTICE '   - Created functions: %', function_count;
    RAISE NOTICE '   - Tables include: users, links, registrations, OTP, auth, referrals, deposits, withdrawals, notifications';
END $$;