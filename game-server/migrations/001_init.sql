-- Migration 001_init.sql
-- Core tables for Estif Bingo game server
-- Updated to support string-based cartela IDs (e.g., "B1_001", "O15_188")

-- ==================== GAME ROUNDS TABLE ====================
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

-- ==================== GAME TRANSACTIONS TABLE ====================
-- UPDATED: cartela column changed from INTEGER to VARCHAR(20)
-- Now supports string IDs like "B1_001", "O15_188"
CREATE TABLE IF NOT EXISTS game_transactions (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    username VARCHAR(50),
    type VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    cartela VARCHAR(20),          -- Changed from INTEGER to VARCHAR(20)
    round INTEGER,
    note TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== ACTIVE ROUND SELECTIONS TABLE ====================
-- UPDATED: cartela_number column changed from INTEGER to VARCHAR(20)
-- Used for crash recovery
CREATE TABLE IF NOT EXISTS active_round_selections (
    round_number INTEGER NOT NULL,
    cartela_number VARCHAR(20) NOT NULL,  -- Changed from INTEGER to VARCHAR(20)
    telegram_id BIGINT NOT NULL,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (round_number, cartela_number)
);

-- ==================== INDEXES ====================
-- Game rounds indexes
CREATE INDEX IF NOT EXISTS idx_game_rounds_timestamp ON game_rounds(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_game_rounds_round_number ON game_rounds(round_number DESC);

-- Game transactions indexes
CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram ON game_transactions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_game_transactions_timestamp ON game_transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_game_transactions_type ON game_transactions(type);
CREATE INDEX IF NOT EXISTS idx_game_transactions_round ON game_transactions(round);

-- Active round selections indexes
CREATE INDEX IF NOT EXISTS idx_active_round_selections_round ON active_round_selections(round_number);
CREATE INDEX IF NOT EXISTS idx_active_round_selections_cartela ON active_round_selections(cartela_number);
CREATE INDEX IF NOT EXISTS idx_active_round_selections_telegram ON active_round_selections(telegram_id);

-- ==================== HELPER VIEWS (Optional) ====================

-- View for player statistics
CREATE OR REPLACE VIEW player_stats_view AS
SELECT 
    telegram_id,
    username,
    COUNT(CASE WHEN type = 'bet' THEN 1 END) as total_bets,
    COUNT(CASE WHEN type = 'win' THEN 1 END) as total_wins,
    COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as total_bet_amount,
    COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END), 0) as total_won_amount,
    COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END) - 
             SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as net_profit,
    MAX(timestamp) as last_activity
FROM game_transactions
GROUP BY telegram_id, username;

-- View for daily summary
CREATE OR REPLACE VIEW daily_summary_view AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_rounds,
    SUM(total_pool) as total_pool,
    SUM(winner_reward) as total_payout,
    SUM(admin_commission) as total_commission,
    AVG(win_percentage) as avg_win_percentage,
    COUNT(DISTINCT jsonb_array_length(winners)) as unique_winners
FROM game_rounds
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- ==================== MIGRATION NOTES ====================
-- If upgrading from an older version with INTEGER cartela IDs,
-- run these migration queries:
--
-- ALTER TABLE game_transactions ALTER COLUMN cartela TYPE VARCHAR(20);
-- ALTER TABLE active_round_selections ALTER COLUMN cartela_number TYPE VARCHAR(20);
-- DROP INDEX IF EXISTS idx_active_round_selections_round;
-- CREATE INDEX idx_active_round_selections_cartela ON active_round_selections(cartela_number);

-- ==================== END OF MIGRATION ====================