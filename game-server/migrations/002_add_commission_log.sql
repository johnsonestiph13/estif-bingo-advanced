-- =====================================================
-- ESTIF BINGO 24/7 - COMMISSION LOGGING & SETTINGS
-- Migration: 002_add_commission_log.sql
-- Description: Adds commission tracking and settings table
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
CREATE TABLE IF NOT EXISTS game_settings (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

COMMENT ON TABLE game_settings IS 'Runtime game settings (win percentage, etc.)';

-- Insert default settings
INSERT INTO game_settings (key, value, description) VALUES 
    ('win_percentage', '75', 'Current game win percentage (70,75,76,80)'),
    ('selection_time', '50', 'Cartela selection time in seconds'),
    ('draw_interval', '4000', 'Number draw interval in milliseconds'),
    ('next_round_delay', '6000', 'Delay between rounds in milliseconds'),
    ('bet_amount', '10', 'Cost per cartela in ETB'),
    ('max_cartelas', '2', 'Maximum cartelas per player per round'),
    ('total_cartelas', '400', 'Total available cartelas')
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

-- Function to get player statistics
CREATE OR REPLACE FUNCTION get_player_stats(telegram_id BIGINT)
RETURNS TABLE(
    total_bets DECIMAL(10,2),
    total_wins DECIMAL(10,2),
    games_played INTEGER,
    games_won INTEGER,
    net_result DECIMAL(10,2)
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
        COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as net_result
    FROM game_transactions
    WHERE telegram_id = $1;
END;
$$;

-- ==================== UPDATED INDEXES ====================
-- Additional indexes for new tables
CREATE INDEX IF NOT EXISTS idx_commission_logs_changed_at ON commission_logs(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_actions_created_at ON admin_actions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions(admin_email);
CREATE INDEX IF NOT EXISTS idx_game_settings_key ON game_settings(key);

-- ==================== VERIFICATION ====================
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('game_settings', 'commission_logs', 'admin_actions');
    
    RAISE NOTICE '✅ Migration 002_add_commission_log.sql completed successfully';
    RAISE NOTICE '   - Created commission_logs table';
    RAISE NOTICE '   - Created game_settings table';
    RAISE NOTICE '   - Created admin_actions table';
    RAISE NOTICE '   - Created daily_game_stats materialized view';
    RAISE NOTICE '   - Created helper functions and triggers';
    RAISE NOTICE '   - Tables count: %', table_count;
END $$;