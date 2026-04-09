-- =====================================================
-- ESTIF BINGO 24/7 - COMMISSION LOGGING & SETTINGS
-- Migration: 002_add_commission_log.sql
-- Description: Adds commission tracking and settings table
-- Updated: Added support for string-based cartela IDs
-- =====================================================

-- ==================== COMMISSION LOGS TABLE ====================
-- Tracks every win percentage change by admin
CREATE TABLE IF NOT EXISTS commission_logs (
    id SERIAL PRIMARY KEY,
    old_percentage INTEGER NOT NULL,
    new_percentage INTEGER NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE commission_logs IS 'Logs all win percentage changes by admins';

-- ==================== GAME SETTINGS TABLE ====================
-- Store runtime configurable settings
-- UPDATED: total_cartelas changed to 75 (types) and added cartelas_json_path
CREATE TABLE IF NOT EXISTS game_settings (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

COMMENT ON TABLE game_settings IS 'Runtime game settings (win percentage, etc.)';

-- Insert default settings (UPDATED values)
INSERT INTO game_settings (key, value, description) VALUES 
    ('win_percentage', '75', 'Current game win percentage (70,75,76,80)'),
    ('selection_time', '50', 'Cartela selection time in seconds'),
    ('draw_interval', '4000', 'Number draw interval in milliseconds'),
    ('next_round_delay', '6000', 'Delay between rounds in milliseconds'),
    ('bet_amount', '10', 'Cost per cartela in ETB'),
    ('max_cartelas', '4', 'Maximum cartelas per player per round'),
    ('total_cartelas', '75', 'Total available cartela types (B1-B15, I16-I30, N31-N45, G46-G60, O61-O75)'),
    ('total_cartela_variations', '1000', 'Total cartela variations loaded from JSON'),
    ('cartelas_json_path', 'data/cartelas.json', 'Path to cartelas.json file'),
    ('default_sound_pack', 'pack1', 'Default sound pack for new players'),
    ('maintenance_mode', 'false', 'Put game in maintenance mode')
ON CONFLICT (key) DO NOTHING;

-- ==================== ADMIN ACTIONS LOG TABLE ====================
-- Track all admin actions for audit purposes
CREATE TABLE IF NOT EXISTS admin_actions (
    id SERIAL PRIMARY KEY,
    admin_email VARCHAR(100),
    action_type VARCHAR(50),
    action_details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE admin_actions IS 'Audit log of all admin actions';

-- ==================== CARTELA VARIATIONS TABLE ====================
-- NEW: Store cartela variations for quick access
CREATE TABLE IF NOT EXISTS cartela_variations (
    id SERIAL PRIMARY KEY,
    cartela_id VARCHAR(20) UNIQUE NOT NULL,
    letter CHAR(1) NOT NULL,
    number INTEGER NOT NULL,
    variation INTEGER NOT NULL,
    grid JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE cartela_variations IS 'Stores all cartela variations for quick lookup';

-- Indexes for cartela_variations
CREATE INDEX IF NOT EXISTS idx_cartela_variations_id ON cartela_variations(cartela_id);
CREATE INDEX IF NOT EXISTS idx_cartela_variations_letter ON cartela_variations(letter);
CREATE INDEX IF NOT EXISTS idx_cartela_variations_number ON cartela_variations(number);

-- ==================== WINNER DETAILS TABLE ====================
-- NEW: Store detailed winner information per round
CREATE TABLE IF NOT EXISTS winner_details (
    id SERIAL PRIMARY KEY,
    round_id INTEGER REFERENCES game_rounds(round_id),
    telegram_id BIGINT NOT NULL,
    username VARCHAR(50),
    cartela_id VARCHAR(20),
    winning_pattern VARCHAR(50),
    winning_lines TEXT[],
    amount_won DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE winner_details IS 'Detailed winner information per round';

-- Indexes for winner_details
CREATE INDEX IF NOT EXISTS idx_winner_details_round ON winner_details(round_id);
CREATE INDEX IF NOT EXISTS idx_winner_details_telegram ON winner_details(telegram_id);
CREATE INDEX IF NOT EXISTS idx_winner_details_cartela ON winner_details(cartela_id);

-- ==================== DAILY STATS MATERIALIZED VIEW ====================
-- Pre-aggregated daily statistics for faster reporting
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_game_stats AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_games,
    SUM(total_pool) as total_bet,
    SUM(winner_reward) as total_won,
    SUM(admin_commission) as total_commission,
    AVG(win_percentage) as avg_win_percentage,
    AVG(total_players) as avg_players,
    AVG(total_cartelas) as avg_cartelas
FROM game_rounds
GROUP BY DATE(timestamp)
ORDER BY DATE(timestamp) DESC;

-- Index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_game_stats(date);

COMMENT ON MATERIALIZED VIEW daily_game_stats IS 'Pre-aggregated daily statistics for faster reporting';

-- ==================== CARTELA STATS VIEW ====================
-- NEW: View for cartela popularity statistics
CREATE OR REPLACE VIEW cartela_stats_view AS
SELECT 
    cartela_id,
    COUNT(*) as times_selected,
    COUNT(CASE WHEN type = 'win' THEN 1 END) as times_won,
    ROUND(COUNT(CASE WHEN type = 'win' THEN 1 END)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 2) as win_percentage
FROM game_transactions
WHERE cartela_id IS NOT NULL
GROUP BY cartela_id
ORDER BY times_selected DESC;

COMMENT ON VIEW cartela_stats_view IS 'Statistics for each cartela (popularity and win rate)';

-- ==================== FUNCTIONS ====================

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_daily_stats()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_game_stats;
    RAISE NOTICE 'Daily game stats refreshed';
END;
$$;

-- Function to log commission changes
CREATE OR REPLACE FUNCTION log_commission_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.value != NEW.value AND NEW.key = 'win_percentage' THEN
        INSERT INTO commission_logs (old_percentage, new_percentage, changed_by)
        VALUES (OLD.value::INTEGER, NEW.value::INTEGER, current_user);
    END IF;
    RETURN NEW;
END;
$$;

-- Trigger to automatically log commission changes
DROP TRIGGER IF EXISTS trigger_commission_log ON game_settings;
CREATE TRIGGER trigger_commission_log
    AFTER UPDATE ON game_settings
    FOR EACH ROW
    EXECUTE FUNCTION log_commission_change();

-- Function to get total commission for a date range
CREATE OR REPLACE FUNCTION get_total_commission(start_date DATE, end_date DATE)
RETURNS DECIMAL(10,2)
LANGUAGE plpgsql
AS $$
DECLARE
    total DECIMAL(10,2);
BEGIN
    SELECT COALESCE(SUM(admin_commission), 0)
    INTO total
    FROM game_rounds
    WHERE DATE(timestamp) BETWEEN start_date AND end_date;
    
    RETURN total;
END;
$$;

-- Function to get player statistics (UPDATED for string cartela IDs)
CREATE OR REPLACE FUNCTION get_player_stats(telegram_id BIGINT)
RETURNS TABLE(
    total_bets DECIMAL(10,2),
    total_wins DECIMAL(10,2),
    games_played INTEGER,
    games_won INTEGER,
    net_result DECIMAL(10,2),
    favorite_cartela VARCHAR(20),
    total_cartelas_used INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as total_bets,
        COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END), 0) as total_wins,
        COUNT(CASE WHEN type = 'bet' THEN 1 END) as games_played,
        COUNT(CASE WHEN type = 'win' THEN 1 END) as games_won,
        COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END), 0) - 
        COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as net_result,
        (SELECT cartela FROM game_transactions 
         WHERE telegram_id = $1 AND type = 'bet' 
         GROUP BY cartela 
         ORDER BY COUNT(*) DESC 
         LIMIT 1) as favorite_cartela,
        COUNT(DISTINCT cartela) as total_cartelas_used
    FROM game_transactions
    WHERE telegram_id = $1;
END;
$$;

-- Function to get top winners (UPDATED for string cartela IDs)
CREATE OR REPLACE FUNCTION get_top_winners(limit_count INTEGER DEFAULT 10)
RETURNS TABLE(
    telegram_id BIGINT,
    username VARCHAR(50),
    total_won DECIMAL(10,2),
    total_wins INTEGER,
    favorite_cartela VARCHAR(20)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.telegram_id,
        MAX(t.username) as username,
        SUM(t.amount) as total_won,
        COUNT(*) as total_wins,
        (SELECT cartela FROM game_transactions 
         WHERE telegram_id = t.telegram_id AND type = 'win'
         GROUP BY cartela 
         ORDER BY COUNT(*) DESC 
         LIMIT 1) as favorite_cartela
    FROM game_transactions t
    WHERE t.type = 'win'
    GROUP BY t.telegram_id
    ORDER BY total_won DESC
    LIMIT limit_count;
END;
$$;

-- Function to get round details with winners (UPDATED for string cartela IDs)
CREATE OR REPLACE FUNCTION get_round_details(round_number INTEGER)
RETURNS TABLE(
    round_id INTEGER,
    total_pool DECIMAL(10,2),
    winner_reward DECIMAL(10,2),
    winners JSONB,
    winner_cartelas JSONB,
    timestamp TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.round_id,
        r.total_pool,
        r.winner_reward,
        r.winners,
        r.winner_cartelas,
        r.timestamp
    FROM game_rounds r
    WHERE r.round_number = round_number
    ORDER BY r.round_id DESC
    LIMIT 1;
END;
$$;

-- ==================== UPDATED INDEXES ====================
-- Additional indexes for new tables
CREATE INDEX IF NOT EXISTS idx_commission_logs_changed_at ON commission_logs(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_actions_created_at ON admin_actions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions(admin_email);
CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_game_settings_key ON game_settings(key);
CREATE INDEX IF NOT EXISTS idx_winner_details_round_id ON winner_details(round_id);
CREATE INDEX IF NOT EXISTS idx_winner_details_telegram_id ON winner_details(telegram_id);
CREATE INDEX IF NOT EXISTS idx_winner_details_cartela_id ON winner_details(cartela_id);
CREATE INDEX IF NOT EXISTS idx_winner_details_amount ON winner_details(amount_won DESC);

-- ==================== VERIFICATION ====================
DO $$
DECLARE
    table_count INTEGER;
    view_count INTEGER;
    function_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('game_settings', 'commission_logs', 'admin_actions', 'cartela_variations', 'winner_details');
    
    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = 'public'
    AND table_name IN ('daily_game_stats', 'cartela_stats_view');
    
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_type = 'FUNCTION';
    
    RAISE NOTICE '✅ Migration 002_add_commission_log.sql completed successfully';
    RAISE NOTICE '   - Created/Updated tables: %', table_count;
    RAISE NOTICE '   - Created views: %', view_count;
    RAISE NOTICE '   - Created functions: %', function_count;
    RAISE NOTICE '   - Updated settings for 4 max cartelas, 75 cartela types, 1000 variations';
END $$;