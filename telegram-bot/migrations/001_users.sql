-- =====================================================
-- MIGRATION: 001_users.sql
-- Description: Create users table for Estif Bingo 24/7 Bot
-- Version: 3.0.0
-- Date: 2024
-- =====================================================

-- ==================== DROP EXISTING (CLEAN START) ====================
-- Uncomment if you need to recreate
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP FUNCTION IF EXISTS update_last_seen();

-- ==================== CREATE USERS TABLE ====================
CREATE TABLE IF NOT EXISTS users (
    -- Primary identifiers
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(64),
    first_name VARCHAR(64),
    last_name VARCHAR(64),
    phone VARCHAR(20) UNIQUE,
    
    -- Balance & Financial
    balance DECIMAL(12,2) DEFAULT 0.00 CHECK (balance >= 0),
    total_deposited DECIMAL(12,2) DEFAULT 0.00 CHECK (total_deposited >= 0),
    total_withdrawn DECIMAL(12,2) DEFAULT 0.00 CHECK (total_withdrawn >= 0),
    total_won DECIMAL(12,2) DEFAULT 0.00 CHECK (total_won >= 0),
    total_bet DECIMAL(12,2) DEFAULT 0.00 CHECK (total_bet >= 0),
    
    -- Game Statistics
    games_played INTEGER DEFAULT 0 CHECK (games_played >= 0),
    games_won INTEGER DEFAULT 0 CHECK (games_won >= 0),
    games_lost INTEGER DEFAULT 0 CHECK (games_lost >= 0),
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    highest_win DECIMAL(12,2) DEFAULT 0.00 CHECK (highest_win >= 0),
    
    -- Referral System
    referral_code VARCHAR(8) UNIQUE,
    referred_by BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    referral_count INTEGER DEFAULT 0 CHECK (referral_count >= 0),
    referral_earnings DECIMAL(12,2) DEFAULT 0.00 CHECK (referral_earnings >= 0),
    
    -- Registration & Status
    registered BOOLEAN DEFAULT FALSE,
    joined_group BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    
    -- Preferences
    lang VARCHAR(2) DEFAULT 'en' CHECK (lang IN ('en', 'am')),
    sound_pack VARCHAR(20) DEFAULT 'pack1',
    sound_enabled BOOLEAN DEFAULT TRUE,
    animations_enabled BOOLEAN DEFAULT TRUE,
    auto_select_cartelas BOOLEAN DEFAULT FALSE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    theme VARCHAR(20) DEFAULT 'dark',
    
    -- Game Session
    current_game_session UUID,
    cartelas_selected INTEGER DEFAULT 0,
    last_round_played INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_game_at TIMESTAMP WITH TIME ZONE,
    last_deposit_at TIMESTAMP WITH TIME ZONE,
    last_withdrawal_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    device_info TEXT,
    ip_address INET,
    user_agent TEXT,
    notes TEXT
);

-- ==================== ADD TABLE COMMENTS ====================
COMMENT ON TABLE users IS 'Registered users of Estif Bingo 24/7 bot';
COMMENT ON COLUMN users.telegram_id IS 'Telegram user ID (primary key)';
COMMENT ON COLUMN users.username IS 'Telegram username';
COMMENT ON COLUMN users.first_name IS 'User first name';
COMMENT ON COLUMN users.last_name IS 'User last name';
COMMENT ON COLUMN users.phone IS 'User phone number (unique)';
COMMENT ON COLUMN users.balance IS 'Current user balance in ETB';
COMMENT ON COLUMN users.total_deposited IS 'Total lifetime deposits in ETB';
COMMENT ON COLUMN users.total_withdrawn IS 'Total lifetime withdrawals in ETB';
COMMENT ON COLUMN users.total_won IS 'Total winnings from games in ETB';
COMMENT ON COLUMN users.total_bet IS 'Total amount bet on games in ETB';
COMMENT ON COLUMN users.games_played IS 'Total number of games played';
COMMENT ON COLUMN users.games_won IS 'Total number of games won';
COMMENT ON COLUMN users.games_lost IS 'Total number of games lost';
COMMENT ON COLUMN users.current_streak IS 'Current winning/losing streak';
COMMENT ON COLUMN users.best_streak IS 'Best winning streak achieved';
COMMENT ON COLUMN users.highest_win IS 'Highest single win amount in ETB';
COMMENT ON COLUMN users.referral_code IS 'Unique referral code for inviting friends';
COMMENT ON COLUMN users.referred_by IS 'Telegram ID of user who referred this user';
COMMENT ON COLUMN users.referral_count IS 'Number of successful referrals';
COMMENT ON COLUMN users.referral_earnings IS 'Total earnings from referrals in ETB';
COMMENT ON COLUMN users.registered IS 'Whether user completed phone registration';
COMMENT ON COLUMN users.joined_group IS 'Whether user joined required Telegram group';
COMMENT ON COLUMN users.is_active IS 'Whether user account is active';
COMMENT ON COLUMN users.is_banned IS 'Whether user is banned from the bot';
COMMENT ON COLUMN users.ban_reason IS 'Reason for ban if applicable';
COMMENT ON COLUMN users.lang IS 'User language preference (en/am)';
COMMENT ON COLUMN users.sound_pack IS 'Selected sound pack for game';
COMMENT ON COLUMN users.sound_enabled IS 'Whether sound effects are enabled';
COMMENT ON COLUMN users.animations_enabled IS 'Whether animations are enabled';
COMMENT ON COLUMN users.auto_select_cartelas IS 'Whether to auto-select cartelas';
COMMENT ON COLUMN users.notifications_enabled IS 'Whether to send notifications';
COMMENT ON COLUMN users.theme IS 'UI theme preference (dark/light)';
COMMENT ON COLUMN users.current_game_session IS 'UUID of current active game session';
COMMENT ON COLUMN users.cartelas_selected IS 'Number of cartelas selected in current round';
COMMENT ON COLUMN users.last_round_played IS 'Last round number played';
COMMENT ON COLUMN users.last_seen IS 'Last time user interacted with bot';
COMMENT ON COLUMN users.last_game_at IS 'Last time user played a game';
COMMENT ON COLUMN users.last_deposit_at IS 'Last time user made a deposit';
COMMENT ON COLUMN users.last_withdrawal_at IS 'Last time user made a withdrawal';

-- ==================== CREATE INDEXES ====================
-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by);

-- Status indexes
CREATE INDEX IF NOT EXISTS idx_users_registered ON users(registered);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned);
CREATE INDEX IF NOT EXISTS idx_users_joined_group ON users(joined_group);

-- Time-based indexes
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_users_last_game_at ON users(last_game_at DESC);

-- Financial indexes
CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance DESC);
CREATE INDEX IF NOT EXISTS idx_users_total_won ON users(total_won DESC);
CREATE INDEX IF NOT EXISTS idx_users_total_deposited ON users(total_deposited DESC);

-- Game statistics indexes
CREATE INDEX IF NOT EXISTS idx_users_games_played ON users(games_played DESC);
CREATE INDEX IF NOT EXISTS idx_users_games_won ON users(games_won DESC);
CREATE INDEX IF NOT EXISTS idx_users_win_rate ON users(games_won, games_played);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_active_registered ON users(telegram_id, registered, is_active);
CREATE INDEX IF NOT EXISTS idx_users_balance_status ON users(balance, is_active, is_banned);
CREATE INDEX IF NOT EXISTS idx_users_referral_stats ON users(referral_code, referral_count, referral_earnings);

-- Partial indexes for active users only
CREATE INDEX IF NOT EXISTS idx_users_active_balance ON users(balance DESC) WHERE is_active = TRUE AND is_banned = FALSE;
CREATE INDEX IF NOT EXISTS idx_users_active_last_seen ON users(last_seen DESC) WHERE is_active = TRUE;

-- ==================== CREATE FUNCTIONS ====================

-- Update last_seen automatically
CREATE OR REPLACE FUNCTION update_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_seen = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update updated_at automatically
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Calculate win rate function
CREATE OR REPLACE FUNCTION calculate_win_rate(user_id BIGINT)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    win_rate DECIMAL(5,2);
BEGIN
    SELECT CASE 
        WHEN games_played > 0 THEN (games_won::DECIMAL / games_played::DECIMAL) * 100
        ELSE 0
    END INTO win_rate
    FROM users
    WHERE telegram_id = user_id;
    
    RETURN COALESCE(win_rate, 0);
END;
$$ LANGUAGE plpgsql STABLE;

-- Update game statistics function
CREATE OR REPLACE FUNCTION update_game_stats(
    user_id BIGINT,
    won BOOLEAN,
    amount_won DECIMAL DEFAULT 0,
    amount_bet DECIMAL DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET 
        games_played = games_played + 1,
        total_bet = total_bet + amount_bet,
        last_game_at = NOW(),
        current_streak = CASE 
            WHEN won THEN ABS(current_streak) + 1
            ELSE -1 * (ABS(current_streak) + 1)
        END,
        best_streak = CASE 
            WHEN won AND (ABS(current_streak) + 1) > best_streak 
            THEN ABS(current_streak) + 1
            ELSE best_streak
        END
    WHERE telegram_id = user_id;
    
    IF won AND amount_won > 0 THEN
        UPDATE users 
        SET 
            games_won = games_won + 1,
            total_won = total_won + amount_won,
            highest_win = GREATEST(highest_win, amount_won)
        WHERE telegram_id = user_id;
    ELSE
        UPDATE users 
        SET games_lost = games_lost + 1
        WHERE telegram_id = user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ==================== CREATE TRIGGERS ====================

-- Trigger for last_seen update
DROP TRIGGER IF EXISTS trigger_update_last_seen ON users;
CREATE TRIGGER trigger_update_last_seen
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_last_seen();

-- Trigger for updated_at update
DROP TRIGGER IF EXISTS trigger_update_updated_at ON users;
CREATE TRIGGER trigger_update_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ==================== CREATE VIEWS ====================

-- Active users view
CREATE OR REPLACE VIEW active_users AS
SELECT 
    telegram_id,
    username,
    first_name,
    last_name,
    phone,
    balance,
    games_played,
    games_won,
    calculate_win_rate(telegram_id) as win_rate,
    last_seen,
    last_game_at
FROM users
WHERE is_active = TRUE 
    AND is_banned = FALSE 
    AND registered = TRUE;

-- Leaderboard view
CREATE OR REPLACE VIEW leaderboard AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY total_won DESC) as rank,
    telegram_id,
    username,
    first_name,
    last_name,
    total_won,
    games_played,
    games_won,
    calculate_win_rate(telegram_id) as win_rate,
    highest_win,
    best_streak
FROM users
WHERE registered = TRUE 
    AND is_active = TRUE 
    AND total_won > 0
ORDER BY total_won DESC;

-- User summary view
CREATE OR REPLACE VIEW user_summary AS
SELECT 
    telegram_id,
    username,
    first_name,
    last_name,
    phone,
    balance,
    total_deposited,
    total_withdrawn,
    total_won,
    (total_won - total_bet) as net_profit,
    games_played,
    games_won,
    calculate_win_rate(telegram_id) as win_rate,
    current_streak,
    best_streak,
    highest_win,
    referral_count,
    referral_earnings,
    last_seen,
    created_at
FROM users
WHERE registered = TRUE;

-- ==================== SEED DATA (OPTIONAL) ====================
-- Insert default admin user if not exists
INSERT INTO users (telegram_id, username, first_name, registered, is_active, lang)
VALUES (7160486597, 'admin', 'Admin', TRUE, TRUE, 'en')
ON CONFLICT (telegram_id) DO NOTHING;

-- ==================== VERIFICATION ====================
DO $$
BEGIN
    -- Verify table exists
    ASSERT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'users'
    ), 'Table users does not exist';
    
    -- Verify columns
    ASSERT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'telegram_id'
    ), 'Column telegram_id does not exist';
    
    -- Verify indexes
    ASSERT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_users_phone'
    ), 'Index idx_users_phone does not exist';
    
    -- Verify triggers
    ASSERT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trigger_update_last_seen'
    ), 'Trigger trigger_update_last_seen does not exist';
    
    -- Verify functions
    ASSERT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'calculate_win_rate'
    ), 'Function calculate_win_rate does not exist';
    
    -- Verify views
    ASSERT EXISTS (
        SELECT 1 FROM pg_views 
        WHERE viewname = 'active_users'
    ), 'View active_users does not exist';
    
    RAISE NOTICE '✅ Migration 001_users.sql completed successfully';
    RAISE NOTICE '   - Created users table with enhanced columns';
    RAISE NOTICE '   - Created indexes for performance';
    RAISE NOTICE '   - Created triggers for auto-updates';
    RAISE NOTICE '   - Created functions for calculations';
    RAISE NOTICE '   - Created views for common queries';
    RAISE NOTICE '   - Added seed data for admin user';
    
    -- Print table statistics
    RAISE NOTICE '📊 Table Statistics:';
    RAISE NOTICE '   - Total columns: (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = ''users'')';
    RAISE NOTICE '   - Total indexes: (SELECT COUNT(*) FROM pg_indexes WHERE tablename = ''users'')';
    RAISE NOTICE '   - Total triggers: (SELECT COUNT(*) FROM pg_trigger WHERE tgrelid = ''users''::regclass)';
    
END $$;