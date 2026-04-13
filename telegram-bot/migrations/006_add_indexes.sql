-- =====================================================
-- MIGRATION: 006_add_indexes.sql
-- Description: Additional performance indexes for all tables
-- Version: 3.0.0
-- Date: 2024
-- =====================================================

-- ==================== USERS TABLE INDEXES ====================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_registered_lang ON users(registered, lang);
CREATE INDEX IF NOT EXISTS idx_users_registered_balance ON users(registered, balance DESC);
CREATE INDEX IF NOT EXISTS idx_users_balance_status ON users(balance, is_active, is_banned);
CREATE INDEX IF NOT EXISTS idx_users_created_registered ON users(created_at, registered);
CREATE INDEX IF NOT EXISTS idx_users_last_seen_active ON users(last_seen DESC) WHERE is_active = TRUE;

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_users_active ON users(telegram_id) WHERE registered = TRUE AND is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_active_balance ON users(balance DESC) WHERE is_active = TRUE AND is_banned = FALSE;
CREATE INDEX IF NOT EXISTS idx_users_recent_active ON users(last_seen DESC) WHERE last_seen > NOW() - INTERVAL '7 days';

-- Index for referral system
CREATE INDEX IF NOT EXISTS idx_users_referral_code_active ON users(referral_code) WHERE registered = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by) WHERE referred_by IS NOT NULL;

-- Index for game statistics queries
CREATE INDEX IF NOT EXISTS idx_users_games_stats ON users(games_played DESC, games_won DESC, total_won DESC);
CREATE INDEX IF NOT EXISTS idx_users_win_rate ON users(games_won, games_played) WHERE games_played > 0;

-- Full-text search indexes (if using PostgreSQL full-text)
CREATE INDEX IF NOT EXISTS idx_users_username_gin ON users USING gin(username gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_users_phone_gin ON users USING gin(phone gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_users_first_name_gin ON users USING gin(first_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_users_last_name_gin ON users USING gin(last_name gin_trgm_ops);

-- ==================== PENDING WITHDRAWALS TABLE INDEXES ====================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram_status ON pending_withdrawals(telegram_id, status);
CREATE INDEX IF NOT EXISTS idx_withdrawals_status_requested ON pending_withdrawals(status, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram_date ON pending_withdrawals(telegram_id, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawals_method_status ON pending_withdrawals(method, status);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_withdrawals_pending_recent ON pending_withdrawals(telegram_id, requested_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_withdrawals_pending_oldest ON pending_withdrawals(requested_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_withdrawals_approved_recent ON pending_withdrawals(approved_at DESC) WHERE status = 'approved';

-- Index for amount queries
CREATE INDEX IF NOT EXISTS idx_withdrawals_amount_range ON pending_withdrawals(amount, status);
CREATE INDEX IF NOT EXISTS idx_withdrawals_amount_high ON pending_withdrawals(amount DESC) WHERE amount > 1000;

-- Index for withdrawal ID lookups
CREATE INDEX IF NOT EXISTS idx_withdrawals_withdrawal_id ON pending_withdrawals(withdrawal_id);

-- ==================== OTP CODES TABLE INDEXES ====================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_otp_telegram_expires ON otp_codes(telegram_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_otp_telegram_purpose ON otp_codes(telegram_id, purpose);
CREATE INDEX IF NOT EXISTS idx_otp_purpose_expires ON otp_codes(purpose, expires_at);

-- Partial indexes for active OTPs
CREATE INDEX IF NOT EXISTS idx_otp_active ON otp_codes(telegram_id) WHERE is_used = FALSE AND expires_at > NOW();
CREATE INDEX IF NOT EXISTS idx_otp_blocked ON otp_codes(blocked_until) WHERE is_blocked = TRUE AND blocked_until > NOW();

-- Index for cleanup operations
CREATE INDEX IF NOT EXISTS idx_otp_cleanup ON otp_codes(expires_at) WHERE is_used = FALSE;
CREATE INDEX IF NOT EXISTS idx_otp_expired_used ON otp_codes(expires_at) WHERE is_used = TRUE;

-- ==================== AUTH CODES TABLE INDEXES ====================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_auth_telegram_purpose ON auth_codes(telegram_id, purpose);
CREATE INDEX IF NOT EXISTS idx_auth_expires_used ON auth_codes(expires_at, used);
CREATE INDEX IF NOT EXISTS idx_auth_code_active ON auth_codes(code, expires_at) WHERE used = FALSE AND expires_at > NOW();

-- Partial indexes for active codes
CREATE INDEX IF NOT EXISTS idx_auth_active_codes ON auth_codes(telegram_id) WHERE used = FALSE AND expires_at > NOW();
CREATE INDEX IF NOT EXISTS idx_auth_unused_expiring ON auth_codes(expires_at) WHERE used = FALSE;

-- Index for code lookup with metadata
CREATE INDEX IF NOT EXISTS idx_auth_code_metadata ON auth_codes USING gin(metadata);

-- ==================== SETTINGS TABLE INDEXES ====================

-- Category and public settings indexes
CREATE INDEX IF NOT EXISTS idx_settings_category_public ON settings(category, is_public);
CREATE INDEX IF NOT EXISTS idx_settings_editable ON settings(is_editable) WHERE is_editable = TRUE;

-- ==================== COMMISSION LOGS TABLE INDEXES ====================

-- Composite indexes for analysis
CREATE INDEX IF NOT EXISTS idx_commission_date_percentage ON commission_logs(changed_at DESC, old_percentage, new_percentage);
CREATE INDEX IF NOT EXISTS idx_commission_round ON commission_logs(round_number) WHERE round_number IS NOT NULL;

-- Index for revenue analysis
CREATE INDEX IF NOT EXISTS idx_commission_admin_earnings ON commission_logs(admin_commission DESC) WHERE admin_commission IS NOT NULL;

-- ==================== GAME TRANSACTIONS TABLE INDEXES ====================

-- Create game_transactions table if not exists (from database.py)
CREATE TABLE IF NOT EXISTS game_transactions (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    username VARCHAR(50),
    type VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    cartela VARCHAR(20),
    round INTEGER,
    note TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game transactions indexes
CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram_type ON game_transactions(telegram_id, type);
CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram_date ON game_transactions(telegram_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_game_transactions_type_amount ON game_transactions(type, amount);
CREATE INDEX IF NOT EXISTS idx_game_transactions_round ON game_transactions(round) WHERE round IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_game_transactions_date_range ON game_transactions(timestamp) WHERE timestamp > NOW() - INTERVAL '30 days';

-- Partial indexes for win/loss analysis
CREATE INDEX IF NOT EXISTS idx_game_transactions_wins ON game_transactions(telegram_id, amount) WHERE type = 'win';
CREATE INDEX IF NOT EXISTS idx_game_transactions_bets ON game_transactions(telegram_id, amount) WHERE type = 'bet';

-- ==================== GAME ROUNDS TABLE INDEXES ====================

-- Create game_rounds table if not exists
CREATE TABLE IF NOT EXISTS game_rounds (
    round_id SERIAL PRIMARY KEY,
    round_number INTEGER NOT NULL,
    total_players INTEGER DEFAULT 0,
    total_cartelas INTEGER DEFAULT 0,
    total_pool DECIMAL(10,2) DEFAULT 0,
    winner_reward DECIMAL(10,2) DEFAULT 0,
    admin_commission DECIMAL(10,2) DEFAULT 0,
    winners JSONB DEFAULT '[]',
    winner_cartelas JSONB DEFAULT '[]',
    win_percentage INTEGER DEFAULT 80,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game rounds indexes
CREATE INDEX IF NOT EXISTS idx_game_rounds_number ON game_rounds(round_number DESC);
CREATE INDEX IF NOT EXISTS idx_game_rounds_timestamp ON game_rounds(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_game_rounds_win_percentage ON game_rounds(win_percentage);
CREATE INDEX IF NOT EXISTS idx_game_rounds_pool ON game_rounds(total_pool DESC) WHERE total_pool > 0;

-- ==================== WITHDRAWAL HISTORY TABLE INDEXES ====================

-- Create withdrawal_history table if not exists
CREATE TABLE IF NOT EXISTS withdrawal_history (
    id BIGSERIAL PRIMARY KEY,
    withdrawal_id VARCHAR(50) NOT NULL,
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    amount DECIMAL(12,2),
    note TEXT,
    performed_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Withdrawal history indexes
CREATE INDEX IF NOT EXISTS idx_withdrawal_history_withdrawal ON withdrawal_history(withdrawal_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_history_telegram_action ON withdrawal_history(telegram_id, action);
CREATE INDEX IF NOT EXISTS idx_withdrawal_history_created ON withdrawal_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawal_history_status_change ON withdrawal_history(old_status, new_status);

-- ==================== OTP LOGS TABLE INDEXES ====================

-- Create otp_logs table if not exists
CREATE TABLE IF NOT EXISTS otp_logs (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT,
    action VARCHAR(50) NOT NULL,
    otp_masked VARCHAR(10),
    purpose VARCHAR(50),
    success BOOLEAN,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OTP logs indexes
CREATE INDEX IF NOT EXISTS idx_otp_logs_telegram_action ON otp_logs(telegram_id, action);
CREATE INDEX IF NOT EXISTS idx_otp_logs_created ON otp_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_otp_logs_purpose_success ON otp_logs(purpose, success);
CREATE INDEX IF NOT EXISTS idx_otp_logs_ip ON otp_logs(ip_address);

-- ==================== SETTINGS HISTORY TABLE INDEXES ====================

-- Create settings_history table if not exists
CREATE TABLE IF NOT EXISTS settings_history (
    id BIGSERIAL PRIMARY KEY,
    setting_id INTEGER REFERENCES settings(id) ON DELETE CASCADE,
    setting_key VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    reason TEXT
);

-- Settings history indexes
CREATE INDEX IF NOT EXISTS idx_settings_history_key ON settings_history(setting_key);
CREATE INDEX IF NOT EXISTS idx_settings_history_changed_at ON settings_history(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_settings_history_changed_by ON settings_history(changed_by);

-- ==================== VERIFICATION CODES TABLE INDEXES ====================

-- Create verification_codes table if not exists
CREATE TABLE IF NOT EXISTS verification_codes (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    type VARCHAR(30) DEFAULT 'phone',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE,
    attempts INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE
);

-- Verification codes indexes
CREATE INDEX IF NOT EXISTS idx_verification_telegram_type ON verification_codes(telegram_id, type);
CREATE INDEX IF NOT EXISTS idx_verification_code_expires ON verification_codes(code, expires_at);
CREATE INDEX IF NOT EXISTS idx_verification_unverified ON verification_codes(telegram_id) WHERE is_verified = FALSE;

-- ==================== FULL-TEXT SEARCH INDEXES ====================

-- Create full-text search indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_search_gin ON users USING gin(
    to_tsvector('english', COALESCE(username, '') || ' ' || 
                COALESCE(first_name, '') || ' ' || 
                COALESCE(last_name, '') || ' ' || 
                COALESCE(phone, ''))
);

-- Create full-text search function
CREATE OR REPLACE FUNCTION search_users(search_query TEXT)
RETURNS TABLE(
    telegram_id BIGINT,
    username VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    phone VARCHAR,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.telegram_id,
        u.username,
        u.first_name,
        u.last_name,
        u.phone,
        ts_rank(
            to_tsvector('english', COALESCE(u.username, '') || ' ' || 
                       COALESCE(u.first_name, '') || ' ' || 
                       COALESCE(u.last_name, '') || ' ' || 
                       COALESCE(u.phone, '')),
            plainto_tsquery('english', search_query)
        ) AS relevance
    FROM users u
    WHERE 
        to_tsvector('english', COALESCE(u.username, '') || ' ' || 
                   COALESCE(u.first_name, '') || ' ' || 
                   COALESCE(u.last_name, '') || ' ' || 
                   COALESCE(u.phone, '')) @@ plainto_tsquery('english', search_query)
        AND u.registered = TRUE
    ORDER BY relevance DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;

-- ==================== INDEX MAINTENANCE FUNCTIONS ====================

-- Function to get index usage statistics
CREATE OR REPLACE FUNCTION get_index_usage_stats()
RETURNS TABLE(
    schema_name TEXT,
    table_name TEXT,
    index_name TEXT,
    index_size TEXT,
    idx_scan BIGINT,
    idx_tup_read BIGINT,
    idx_tup_fetch BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname::TEXT,
        tablename::TEXT,
        indexname::TEXT,
        pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size,
        idx_scan,
        idx_tup_read,
        idx_tup_fetch
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
    ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to reindex all tables (maintenance)
CREATE OR REPLACE FUNCTION reindex_all_tables()
RETURNS TEXT AS $$
DECLARE
    table_rec RECORD;
    reindex_count INTEGER := 0;
BEGIN
    FOR table_rec IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN ('users', 'pending_withdrawals', 'otp_codes', 'auth_codes', 
                          'game_transactions', 'game_rounds', 'settings', 'commission_logs')
    LOOP
        EXECUTE format('REINDEX TABLE %I', table_rec.tablename);
        reindex_count := reindex_count + 1;
    END LOOP;
    
    RETURN format('Reindexed %s tables successfully', reindex_count);
END;
$$ LANGUAGE plpgsql;

-- ==================== ANALYZE ALL TABLES ====================

-- Analyze tables to update statistics
ANALYZE users;
ANALYZE pending_withdrawals;
ANALYZE otp_codes;
ANALYZE auth_codes;
ANALYZE settings;
ANALYZE commission_logs;
ANALYZE game_transactions;
ANALYZE game_rounds;
ANALYZE withdrawal_history;
ANALYZE otp_logs;
ANALYZE settings_history;
ANALYZE verification_codes;

-- ==================== VERIFICATION ====================
DO $$
DECLARE
    index_count INTEGER;
    table_count INTEGER;
BEGIN
    -- Count indexes created
    SELECT COUNT(*) INTO index_count 
    FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND indexname LIKE 'idx_%';
    
    -- Count tables
    SELECT COUNT(*) INTO table_count 
    FROM pg_tables 
    WHERE schemaname = 'public';
    
    RAISE NOTICE '✅ Migration 006_add_indexes.sql completed successfully';
    RAISE NOTICE '   - Created/verified % performance indexes', index_count;
    RAISE NOTICE '   - Indexes on % tables', table_count;
    RAISE NOTICE '   - Added composite indexes for common queries';
    RAISE NOTICE '   - Added partial indexes for active records';
    RAISE NOTICE '   - Added full-text search indexes';
    RAISE NOTICE '   - Created search_users function';
    RAISE NOTICE '   - Created index maintenance functions';
    RAISE NOTICE '   - Updated statistics on all tables';
    
    -- Show index usage stats preview
    RAISE NOTICE '📊 Index usage statistics available via get_index_usage_stats()';
    RAISE NOTICE '🔧 Maintenance: SELECT reindex_all_tables() to rebuild indexes';
END $$;