-- =====================================================
-- MIGRATION: 001_users.sql
-- Description: Create users table for bot
-- =====================================================

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    balance DECIMAL(12,2) DEFAULT 0,
    total_deposited DECIMAL(12,2) DEFAULT 0,
    registered BOOLEAN DEFAULT FALSE,
    joined_group BOOLEAN DEFAULT FALSE,
    lang TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE users IS 'Registered users of the bot';
COMMENT ON COLUMN users.telegram_id IS 'Telegram user ID (primary key)';
COMMENT ON COLUMN users.balance IS 'Current user balance in ETB';
COMMENT ON COLUMN users.total_deposited IS 'Total lifetime deposits in ETB';
COMMENT ON COLUMN users.registered IS 'Whether user completed registration';
COMMENT ON COLUMN users.lang IS 'User language preference (en/am)';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_registered ON users(registered);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC);

-- Create function to update last_seen automatically
CREATE OR REPLACE FUNCTION update_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_seen = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for last_seen update
DROP TRIGGER IF EXISTS trigger_update_last_seen ON users;
CREATE TRIGGER trigger_update_last_seen
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_last_seen();

-- Verification
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001_users.sql completed';
    RAISE NOTICE '   - Created users table';
    RAISE NOTICE '   - Created indexes';
    RAISE NOTICE '   - Created last_seen trigger';
END $$;