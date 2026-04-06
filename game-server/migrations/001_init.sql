-- =====================================================
-- ESTIF BINGO 24/7 - INITIAL DATABASE SCHEMA
-- Migration: 001_init.sql
-- Description: Core tables for game server
-- =====================================================

-- ==================== GAME ROUNDS TABLE ====================
-- Stores complete information about each completed round
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
    win_percentage INTEGER DEFAULT 75,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments for documentation
COMMENT ON TABLE game_rounds IS 'Stores completed game rounds history';
COMMENT ON COLUMN game_rounds.winners IS 'JSON array of winner usernames';
COMMENT ON COLUMN game_rounds.winner_cartelas IS 'JSON array of winning cartela details (username, cartelaId, winningLines)';

-- ==================== GAME TRANSACTIONS TABLE ====================
-- Logs all balance-affecting actions within the game
CREATE TABLE IF NOT EXISTS game_transactions (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    username VARCHAR(50),
    type VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    cartela INTEGER,
    round INTEGER,
    note TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction type check constraint
ALTER TABLE game_transactions ADD CONSTRAINT chk_transaction_type 
    CHECK (type IN ('bet', 'win', 'refund', 'admin_add', 'admin_remove'));

COMMENT ON TABLE game_transactions IS 'Logs all game-related balance transactions';
COMMENT ON COLUMN game_transactions.type IS 'Transaction type: bet, win, refund, admin_add, admin_remove';

-- ==================== ACTIVE ROUND SELECTIONS TABLE ====================
-- Used for crash recovery - preserves cartela selections if server restarts
CREATE TABLE IF NOT EXISTS active_round_selections (
    round_number INTEGER NOT NULL,
    cartela_number INTEGER NOT NULL,
    telegram_id BIGINT NOT NULL,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (round_number, cartela_number)
);

COMMENT ON TABLE active_round_selections IS 'Stores active cartela selections for crash recovery';

-- ==================== INDEXES ====================
-- Performance indexes for common queries
CREATE INDEX IF NOT EXISTS idx_game_rounds_timestamp ON game_rounds(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_game_rounds_round_number ON game_rounds(round_number DESC);
CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram ON game_transactions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_game_transactions_timestamp ON game_transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_game_transactions_type ON game_transactions(type);
CREATE INDEX IF NOT EXISTS idx_active_round_selections_round ON active_round_selections(round_number);
CREATE INDEX IF NOT EXISTS idx_active_round_selections_telegram ON active_round_selections(telegram_id);

-- ==================== PARTIAL INDEXES ====================
-- For better performance on recent data
CREATE INDEX IF NOT EXISTS idx_game_rounds_recent ON game_rounds(timestamp DESC) WHERE timestamp > NOW() - INTERVAL '30 days';
CREATE INDEX IF NOT EXISTS idx_game_transactions_recent ON game_transactions(timestamp DESC) WHERE timestamp > NOW() - INTERVAL '30 days';

-- ==================== VERIFICATION ====================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001_init.sql completed successfully';
    RAISE NOTICE '   - Created game_rounds table';
    RAISE NOTICE '   - Created game_transactions table';
    RAISE NOTICE '   - Created active_round_selections table';
    RAISE NOTICE '   - Created all indexes';
END $$;