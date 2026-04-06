-- =====================================================
-- MIGRATION: 005_commission_settings.sql
-- Description: Create settings table and commission logs
-- =====================================================

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by TEXT
);

-- Add comments
COMMENT ON TABLE settings IS 'Runtime configuration settings';
COMMENT ON COLUMN settings.key IS 'Setting key (e.g., win_percentage)';
COMMENT ON COLUMN settings.value IS 'Setting value';

-- Insert default settings
INSERT INTO settings (key, value, description) VALUES 
    ('win_percentage', '75', 'Current game win percentage (70,75,76,80)'),
    ('maintenance_mode', 'false', 'Enable maintenance mode'),
    ('game_enabled', 'true', 'Enable/disable game access'),
    ('min_deposit', '10', 'Minimum deposit amount in ETB'),
    ('max_deposit', '100000', 'Maximum deposit amount in ETB'),
    ('min_withdrawal', '50', 'Minimum withdrawal amount in ETB'),
    ('max_withdrawal', '10000', 'Maximum withdrawal amount in ETB'),
    ('welcome_bonus', '30', 'Welcome bonus amount in ETB'),
    ('referral_bonus', '10', 'Referral bonus amount in ETB'),
    ('contact_email', 'support@estif.com', 'Support email address')
ON CONFLICT (key) DO NOTHING;

-- Create commission logs table
CREATE TABLE IF NOT EXISTS commission_logs (
    id SERIAL PRIMARY KEY,
    old_percentage INTEGER NOT NULL,
    new_percentage INTEGER NOT NULL,
    changed_by TEXT,
    changed_at TIMESTAMP DEFAULT NOW(),
    ip_address INET
);

-- Add comments
COMMENT ON TABLE commission_logs IS 'History of win percentage changes';

-- Create index for commission logs
CREATE INDEX IF NOT EXISTS idx_commission_logs_changed_at ON commission_logs(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_commission_logs_changed_by ON commission_logs(changed_by);

-- Add constraint for win percentage values
ALTER TABLE commission_logs 
    DROP CONSTRAINT IF EXISTS chk_win_percentage;

ALTER TABLE commission_logs 
    ADD CONSTRAINT chk_win_percentage 
    CHECK (old_percentage IN (70, 75, 76, 80) AND new_percentage IN (70, 75, 76, 80));

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for settings updated_at
DROP TRIGGER IF EXISTS trigger_settings_updated_at ON settings;
CREATE TRIGGER trigger_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Create function to log commission changes
CREATE OR REPLACE FUNCTION log_commission_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.key = 'win_percentage' AND NEW.value != OLD.value THEN
        INSERT INTO commission_logs (old_percentage, new_percentage, changed_by)
        VALUES (OLD.value::INTEGER, NEW.value::INTEGER, current_user);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for commission logging
DROP TRIGGER IF EXISTS trigger_commission_log ON settings;
CREATE TRIGGER trigger_commission_log
    AFTER UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION log_commission_change();

-- Create view for current game settings
CREATE OR REPLACE VIEW current_game_settings AS
SELECT 
    key,
    value,
    description
FROM settings
WHERE key IN ('win_percentage', 'game_enabled', 'maintenance_mode', 'min_deposit', 'max_deposit', 'min_withdrawal', 'max_withdrawal', 'welcome_bonus', 'referral_bonus');

-- Create function to get current win percentage
CREATE OR REPLACE FUNCTION get_current_win_percentage()
RETURNS INTEGER AS $$
DECLARE
    win_perc INTEGER;
BEGIN
    SELECT value::INTEGER INTO win_perc
    FROM settings
    WHERE key = 'win_percentage';
    
    RETURN COALESCE(win_perc, 75);
END;
$$ LANGUAGE plpgsql;

-- Create function to set win percentage with validation
CREATE OR REPLACE FUNCTION set_win_percentage(p_percentage INTEGER, p_changed_by TEXT DEFAULT 'system')
RETURNS BOOLEAN AS $$
BEGIN
    -- Validate percentage
    IF p_percentage NOT IN (70, 75, 76, 80) THEN
        RAISE EXCEPTION 'Invalid win percentage. Allowed values: 70, 75, 76, 80';
    END IF;
    
    -- Update setting
    UPDATE settings 
    SET value = p_percentage::TEXT, updated_by = p_changed_by
    WHERE key = 'win_percentage';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create view for commission statistics
CREATE OR REPLACE VIEW commission_statistics AS
SELECT 
    COUNT(*) as total_changes,
    MIN(changed_at) as first_change,
    MAX(changed_at) as last_change,
    old_percentage,
    COUNT(*) as change_count
FROM commission_logs
GROUP BY old_percentage
ORDER BY old_percentage;

-- Verification
DO $$
DECLARE
    win_perc INTEGER;
BEGIN
    win_perc := get_current_win_percentage();
    RAISE NOTICE '✅ Migration 005_commission_settings.sql completed';
    RAISE NOTICE '   - Created settings table';
    RAISE NOTICE '   - Created commission_logs table';
    RAISE NOTICE '   - Inserted default settings';
    RAISE NOTICE '   - Created triggers for auditing';
    RAISE NOTICE '   - Created helper functions';
    RAISE NOTICE '   - Current win percentage: %', win_perc;
END $$;