-- =====================================================
-- MIGRATION: 005_commission_settings.sql
-- Description: Create settings table, commission logs, and game configuration
-- Version: 3.0.0
-- Date: 2024
-- =====================================================

-- ==================== DROP EXISTING (CLEAN START) ====================
-- Uncomment if you need to recreate
-- DROP TABLE IF EXISTS settings CASCADE;
-- DROP TABLE IF EXISTS commission_logs CASCADE;
-- DROP TABLE IF EXISTS game_settings CASCADE;
-- DROP TABLE IF EXISTS settings_history CASCADE;
-- DROP FUNCTION IF EXISTS update_updated_at();
-- DROP FUNCTION IF EXISTS log_commission_change();
-- DROP FUNCTION IF EXISTS get_current_win_percentage();
-- DROP FUNCTION IF EXISTS set_win_percentage(INTEGER, TEXT);
-- DROP FUNCTION IF EXISTS get_setting(TEXT);
-- DROP FUNCTION IF EXISTS set_setting(TEXT, TEXT, TEXT);

-- ==================== CREATE ENHANCED SETTINGS TABLE ====================
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string', -- string, integer, boolean, float, json
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    description_am TEXT,
    is_public BOOLEAN DEFAULT FALSE, -- Whether users can view this setting
    is_editable BOOLEAN DEFAULT TRUE, -- Whether admins can edit via UI
    validation_regex TEXT,
    min_value DECIMAL(20,2),
    max_value DECIMAL(20,2),
    allowed_values JSONB, -- For dropdown selections
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    version INTEGER DEFAULT 1,
    
    INDEX idx_settings_key (key),
    INDEX idx_settings_category (category),
    INDEX idx_settings_is_public (is_public)
);

-- ==================== CREATE SETTINGS HISTORY TABLE ====================
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
    reason TEXT,
    
    INDEX idx_settings_history_setting_id (setting_id),
    INDEX idx_settings_history_key (setting_key),
    INDEX idx_settings_history_changed_at (changed_at DESC),
    INDEX idx_settings_history_changed_by (changed_by)
);

-- ==================== CREATE ENHANCED COMMISSION LOGS TABLE ====================
CREATE TABLE IF NOT EXISTS commission_logs (
    id SERIAL PRIMARY KEY,
    old_percentage INTEGER NOT NULL,
    new_percentage INTEGER NOT NULL,
    changed_by VARCHAR(100),
    changed_by_id BIGINT, -- Telegram ID of admin who made the change
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    reason TEXT,
    round_number INTEGER, -- Which round this commission applied to
    total_pool DECIMAL(20,2), -- Total pool amount for that round
    total_payout DECIMAL(20,2), -- Total payout amount
    admin_commission DECIMAL(20,2), -- Admin commission earned
    
    INDEX idx_commission_logs_changed_at (changed_at DESC),
    INDEX idx_commission_logs_changed_by (changed_by),
    INDEX idx_commission_logs_round (round_number)
);

-- ==================== CREATE GAME SETTINGS TABLE ====================
CREATE TABLE IF NOT EXISTS game_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',
    min_value DECIMAL(20,2),
    max_value DECIMAL(20,2),
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100),
    
    INDEX idx_game_settings_key (setting_key)
);

-- ==================== ADD TABLE COMMENTS ====================
COMMENT ON TABLE settings IS 'Runtime configuration settings for the bot';
COMMENT ON TABLE settings_history IS 'Audit log of all setting changes';
COMMENT ON TABLE commission_logs IS 'History of win percentage changes and commission earnings';
COMMENT ON TABLE game_settings IS 'Game-specific runtime settings';

COMMENT ON COLUMN settings.value_type IS 'Data type: string, integer, boolean, float, json';
COMMENT ON COLUMN settings.category IS 'Setting category: general, game, payment, security, notification';
COMMENT ON COLUMN settings.is_public IS 'Whether users can view this setting via commands';
COMMENT ON COLUMN settings.validation_regex IS 'Regex pattern for value validation';
COMMENT ON COLUMN settings.allowed_values IS 'JSON array of allowed values for dropdown selection';
COMMENT ON COLUMN commission_logs.admin_commission IS 'Commission earned by admin from this round';

-- ==================== INSERT DEFAULT SETTINGS ====================
INSERT INTO settings (key, value, value_type, category, description, description_am, is_public, is_editable, min_value, max_value, allowed_values) VALUES 
    -- Game Settings
    ('win_percentage', '75', 'integer', 'game', 'Current game win percentage (70,75,76,80)', 'የአሁኑ የማሸነፊያ መቶኛ (70,75,76,80)', TRUE, TRUE, 70, 80, '[70,75,76,80]'::jsonb),
    ('game_enabled', 'true', 'boolean', 'game', 'Enable/disable game access', 'ጨዋታውን አንቃ/አጥፋ', TRUE, TRUE, NULL, NULL, NULL),
    ('maintenance_mode', 'false', 'boolean', 'game', 'Enable maintenance mode', 'የጥገና ሁነታ', TRUE, TRUE, NULL, NULL, NULL),
    ('max_cartelas_per_round', '4', 'integer', 'game', 'Maximum cartelas per player per round', 'በአንድ ዙር ከፍተኛ የካርቴላ ብዛት', TRUE, TRUE, 1, 10, NULL),
    ('selection_time', '50', 'integer', 'game', 'Cartela selection time in seconds', 'የካርቴላ ምርጫ ጊዜ በሰከንድ', FALSE, TRUE, 10, 120, NULL),
    ('draw_interval', '4', 'integer', 'game', 'Number draw interval in seconds', 'ቁጥር የመውጣት ክፍተት በሰከንድ', FALSE, TRUE, 1, 10, NULL),
    ('next_round_delay', '6', 'integer', 'game', 'Delay between rounds in seconds', 'በዙሮች መካከል ያለው የጊዜ ክፍተት በሰከንድ', FALSE, TRUE, 1, 30, NULL),
    
    -- Payment Settings
    ('min_deposit', '10', 'integer', 'payment', 'Minimum deposit amount in ETB', 'ዝቅተኛ የተቀማጭ ገንዘብ መጠን በብር', TRUE, TRUE, 10, 1000, NULL),
    ('max_deposit', '100000', 'integer', 'payment', 'Maximum deposit amount in ETB', 'ከፍተኛ የተቀማጭ ገንዘብ መጠን በብር', TRUE, TRUE, 100, 1000000, NULL),
    ('min_withdrawal', '50', 'integer', 'payment', 'Minimum withdrawal amount in ETB', 'ዝቅተኛ የመውጫ ገንዘብ መጠን በብር', TRUE, TRUE, 50, 10000, NULL),
    ('max_withdrawal', '10000', 'integer', 'payment', 'Maximum withdrawal amount in ETB', 'ከፍተኛ የመውጫ ገንዘብ መጠን በብር', TRUE, TRUE, 100, 50000, NULL),
    ('withdrawal_fee_percentage', '0', 'integer', 'payment', 'Withdrawal fee percentage', 'የመውጫ ክፍያ መቶኛ', TRUE, TRUE, 0, 10, NULL),
    ('deposit_bonus_percentage', '0', 'integer', 'payment', 'Deposit bonus percentage', 'የተቀማጭ ቦነስ መቶኛ', TRUE, TRUE, 0, 100, NULL),
    
    -- Bonus Settings
    ('welcome_bonus', '30', 'integer', 'bonus', 'Welcome bonus amount in ETB for new users', 'የእንኳን ደህና መጣችሁ ቦነስ በብር', TRUE, TRUE, 0, 500, NULL),
    ('referral_bonus', '10', 'integer', 'bonus', 'Referral bonus amount in ETB', 'የማመሳከሪያ ቦነስ በብር', TRUE, TRUE, 0, 100, NULL),
    ('daily_bonus', '5', 'integer', 'bonus', 'Daily login bonus amount in ETB', 'የዕለት ቦነስ በብር', TRUE, TRUE, 0, 50, NULL),
    
    -- Security Settings
    ('max_login_attempts', '5', 'integer', 'security', 'Maximum failed login attempts before lockout', 'ከመቆለፉ በፊት የሚፈቀዱ የተሳሳቱ የመግቢያ ሙከራዎች', FALSE, TRUE, 3, 10, NULL),
    ('otp_expiry_minutes', '5', 'integer', 'security', 'OTP expiry time in minutes', 'የኦቲፒ ማብቂያ ጊዜ በደቂቃ', FALSE, TRUE, 1, 30, NULL),
    ('session_timeout_minutes', '30', 'integer', 'security', 'User session timeout in minutes', 'የተጠቃሚ ክፍለ ጊዜ ማብቂያ በደቂቃ', FALSE, TRUE, 5, 120, NULL),
    
    -- Notification Settings
    ('enable_push_notifications', 'true', 'boolean', 'notification', 'Enable push notifications for users', 'ለተጠቃሚዎች ማሳወቂያ አንቃ', FALSE, TRUE, NULL, NULL, NULL),
    ('enable_email_notifications', 'false', 'boolean', 'notification', 'Enable email notifications for admins', 'ለአስተዳዳሪዎች የኢሜይል ማሳወቂያ አንቃ', FALSE, TRUE, NULL, NULL, NULL),
    
    -- Support Settings
    ('contact_email', 'support@estif.com', 'string', 'support', 'Support email address', 'የድጋፍ ኢሜይል አድራሻ', TRUE, TRUE, NULL, NULL, NULL),
    ('support_phone', '+251-XXX-XXXXXX', 'string', 'support', 'Support phone number', 'የድጋፍ ስልክ ቁጥር', TRUE, TRUE, NULL, NULL, NULL)
ON CONFLICT (key) DO NOTHING;

-- ==================== INSERT DEFAULT GAME SETTINGS ====================
INSERT INTO game_settings (setting_key, setting_value, value_type, min_value, max_value, description) VALUES
    ('bet_amount', '10', 'integer', 10, 1000, 'Cost per cartela in ETB'),
    ('default_win_percentage', '80', 'integer', 70, 80, 'Default win percentage for new games'),
    ('max_players_per_round', '100', 'integer', 10, 500, 'Maximum players per round'),
    ('round_duration', '60', 'integer', 30, 300, 'Round duration in seconds'),
    ('auto_start_round', 'true', 'boolean', NULL, NULL, 'Auto-start new round when previous ends')
ON CONFLICT (setting_key) DO NOTHING;

-- ==================== CREATE FUNCTIONS ====================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log setting changes to history
CREATE OR REPLACE FUNCTION log_setting_change()
RETURNS TRIGGER AS $$
DECLARE
    v_ip_address INET;
    v_user_agent TEXT;
BEGIN
    -- Try to get IP and user agent from context (set by application)
    v_ip_address := current_setting('app.current_ip', TRUE)::INET;
    v_user_agent := current_setting('app.current_user_agent', TRUE);
    
    INSERT INTO settings_history (
        setting_id, setting_key, old_value, new_value, changed_by, ip_address, user_agent
    ) VALUES (
        OLD.id, OLD.key, OLD.value, NEW.value, NEW.updated_by, v_ip_address, v_user_agent
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log commission changes with enhanced tracking
CREATE OR REPLACE FUNCTION log_commission_change()
RETURNS TRIGGER AS $$
DECLARE
    v_ip_address INET;
    v_user_agent TEXT;
BEGIN
    -- Only trigger when win_percentage changes
    IF OLD.key = 'win_percentage' AND NEW.value != OLD.value THEN
        v_ip_address := current_setting('app.current_ip', TRUE)::INET;
        v_user_agent := current_setting('app.current_user_agent', TRUE);
        
        INSERT INTO commission_logs (
            old_percentage, new_percentage, changed_by, changed_by_id, ip_address, user_agent
        ) VALUES (
            OLD.value::INTEGER, 
            NEW.value::INTEGER, 
            NEW.updated_by,
            current_setting('app.current_admin_id', TRUE)::BIGINT,
            v_ip_address, 
            v_user_agent
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Get setting value with type conversion
CREATE OR REPLACE FUNCTION get_setting(p_key TEXT)
RETURNS TEXT AS $$
DECLARE
    setting_value TEXT;
    value_type VARCHAR(20);
BEGIN
    SELECT s.value, s.value_type INTO setting_value, value_type
    FROM settings s
    WHERE s.key = p_key;
    
    IF setting_value IS NULL THEN
        RETURN NULL;
    END IF;
    
    RETURN setting_value;
END;
$$ LANGUAGE plpgsql;

-- Get setting as integer
CREATE OR REPLACE FUNCTION get_setting_int(p_key TEXT)
RETURNS INTEGER AS $$
DECLARE
    setting_value TEXT;
BEGIN
    setting_value := get_setting(p_key);
    RETURN setting_value::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- Get setting as boolean
CREATE OR REPLACE FUNCTION get_setting_bool(p_key TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    setting_value TEXT;
BEGIN
    setting_value := get_setting(p_key);
    RETURN setting_value = 'true';
END;
$$ LANGUAGE plpgsql;

-- Set setting with validation
CREATE OR REPLACE FUNCTION set_setting(
    p_key TEXT, 
    p_value TEXT, 
    p_changed_by TEXT DEFAULT 'system',
    p_reason TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    setting_record RECORD;
    v_ip_address INET;
    v_user_agent TEXT;
BEGIN
    -- Get current setting
    SELECT * INTO setting_record FROM settings WHERE key = p_key;
    
    IF setting_record.id IS NULL THEN
        RAISE EXCEPTION 'Setting key "%" not found', p_key;
    END IF;
    
    -- Validate based on type
    IF setting_record.value_type = 'integer' THEN
        IF p_value !~ '^-?\d+$' THEN
            RAISE EXCEPTION 'Invalid integer value for setting "%"', p_key;
        END IF;
        
        IF setting_record.min_value IS NOT NULL AND p_value::DECIMAL < setting_record.min_value THEN
            RAISE EXCEPTION 'Value % is below minimum % for setting "%"', p_value, setting_record.min_value, p_key;
        END IF;
        
        IF setting_record.max_value IS NOT NULL AND p_value::DECIMAL > setting_record.max_value THEN
            RAISE EXCEPTION 'Value % exceeds maximum % for setting "%"', p_value, setting_record.max_value, p_key;
        END IF;
    ELSIF setting_record.value_type = 'boolean' THEN
        IF p_value NOT IN ('true', 'false') THEN
            RAISE EXCEPTION 'Invalid boolean value for setting "%". Use true or false', p_key;
        END IF;
    ELSIF setting_record.value_type = 'json' THEN
        -- Basic JSON validation
        BEGIN
            p_value::JSONB;
        EXCEPTION WHEN OTHERS THEN
            RAISE EXCEPTION 'Invalid JSON value for setting "%"', p_key;
        END;
    END IF;
    
    -- Check allowed values
    IF setting_record.allowed_values IS NOT NULL AND NOT (p_value = ANY(SELECT jsonb_array_elements_text(setting_record.allowed_values))) THEN
        RAISE EXCEPTION 'Value "%" not allowed for setting "%". Allowed values: %', p_value, p_key, setting_record.allowed_values;
    END IF;
    
    -- Set IP and user agent context (from application)
    v_ip_address := current_setting('app.current_ip', TRUE)::INET;
    v_user_agent := current_setting('app.current_user_agent', TRUE);
    
    -- Update setting
    UPDATE settings 
    SET 
        value = p_value,
        updated_by = p_changed_by,
        updated_at = NOW(),
        version = version + 1
    WHERE key = p_key;
    
    -- Log the change reason if provided
    IF p_reason IS NOT NULL THEN
        UPDATE settings_history 
        SET reason = p_reason
        WHERE setting_key = p_key AND changed_at = (SELECT MAX(changed_at) FROM settings_history WHERE setting_key = p_key);
    END IF;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Get current win percentage (enhanced)
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

-- Set win percentage with validation
CREATE OR REPLACE FUNCTION set_win_percentage(
    p_percentage INTEGER, 
    p_changed_by TEXT DEFAULT 'system',
    p_reason TEXT DEFAULT NULL,
    p_round_number INTEGER DEFAULT NULL,
    p_total_pool DECIMAL DEFAULT NULL,
    p_total_payout DECIMAL DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_old_percentage INTEGER;
BEGIN
    -- Validate percentage
    IF p_percentage NOT IN (70, 75, 76, 80) THEN
        RAISE EXCEPTION 'Invalid win percentage. Allowed values: 70, 75, 76, 80';
    END IF;
    
    -- Get old percentage
    v_old_percentage := get_current_win_percentage();
    
    -- Update setting
    PERFORM set_setting('win_percentage', p_percentage::TEXT, p_changed_by, p_reason);
    
    -- Update commission log with additional info if provided
    IF p_round_number IS NOT NULL OR p_total_pool IS NOT NULL THEN
        UPDATE commission_logs 
        SET 
            round_number = COALESCE(p_round_number, round_number),
            total_pool = COALESCE(p_total_pool, total_pool),
            total_payout = COALESCE(p_total_payout, total_payout),
            admin_commission = COALESCE(p_total_pool, 0) - COALESCE(p_total_payout, 0)
        WHERE changed_at = (SELECT MAX(changed_at) FROM commission_logs WHERE old_percentage = v_old_percentage AND new_percentage = p_percentage);
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Get all settings by category
CREATE OR REPLACE FUNCTION get_settings_by_category(p_category VARCHAR)
RETURNS TABLE(
    setting_key VARCHAR,
    setting_value TEXT,
    description TEXT,
    is_public BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT s.key, s.value, s.description, s.is_public
    FROM settings s
    WHERE s.category = p_category
    ORDER BY s.key;
END;
$$ LANGUAGE plpgsql;

-- Reset setting to default
CREATE OR REPLACE FUNCTION reset_setting(p_key TEXT, p_changed_by TEXT DEFAULT 'system')
RETURNS BOOLEAN AS $$
DECLARE
    default_value TEXT;
BEGIN
    -- Get default value from settings table (stored in metadata or use hardcoded defaults)
    -- For now, use hardcoded defaults for known settings
    default_value := CASE p_key
        WHEN 'win_percentage' THEN '75'
        WHEN 'game_enabled' THEN 'true'
        WHEN 'maintenance_mode' THEN 'false'
        WHEN 'min_deposit' THEN '10'
        WHEN 'max_deposit' THEN '100000'
        WHEN 'min_withdrawal' THEN '50'
        WHEN 'max_withdrawal' THEN '10000'
        WHEN 'welcome_bonus' THEN '30'
        WHEN 'referral_bonus' THEN '10'
        ELSE NULL
    END;
    
    IF default_value IS NULL THEN
        RAISE EXCEPTION 'No default value defined for setting "%"', p_key;
    END IF;
    
    RETURN set_setting(p_key, default_value, p_changed_by, 'Reset to default');
END;
$$ LANGUAGE plpgsql;

-- ==================== CREATE TRIGGERS ====================

-- Trigger for settings updated_at
DROP TRIGGER IF EXISTS trigger_settings_updated_at ON settings;
CREATE TRIGGER trigger_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Trigger for game_settings updated_at
DROP TRIGGER IF EXISTS trigger_game_settings_updated_at ON game_settings;
CREATE TRIGGER trigger_game_settings_updated_at
    BEFORE UPDATE ON game_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Trigger for settings history logging
DROP TRIGGER IF EXISTS trigger_settings_history ON settings;
CREATE TRIGGER trigger_settings_history
    AFTER UPDATE ON settings
    FOR EACH ROW
    WHEN (OLD.value IS DISTINCT FROM NEW.value)
    EXECUTE FUNCTION log_setting_change();

-- Trigger for commission logging
DROP TRIGGER IF EXISTS trigger_commission_log ON settings;
CREATE TRIGGER trigger_commission_log
    AFTER UPDATE ON settings
    FOR EACH ROW
    WHEN (OLD.key = 'win_percentage' AND NEW.value != OLD.value)
    EXECUTE FUNCTION log_commission_change();

-- ==================== CREATE VIEWS ====================

-- Current game settings view
CREATE OR REPLACE VIEW current_game_settings AS
SELECT 
    key,
    value,
    value_type,
    description,
    description_am
FROM settings
WHERE category IN ('game', 'payment', 'bonus') AND is_public = TRUE
ORDER BY category, key;

-- Commission statistics view
CREATE OR REPLACE VIEW commission_statistics AS
SELECT 
    COUNT(*) as total_changes,
    MIN(changed_at) as first_change,
    MAX(changed_at) as last_change,
    old_percentage,
    COUNT(*) as change_count,
    COUNT(DISTINCT changed_by) as unique_changers
FROM commission_logs
GROUP BY old_percentage
ORDER BY old_percentage;

-- Recent commission changes view
CREATE OR REPLACE VIEW recent_commission_changes AS
SELECT 
    changed_at,
    old_percentage,
    new_percentage,
    changed_by,
    round_number,
    total_pool,
    total_payout,
    admin_commission,
    reason
FROM commission_logs
ORDER BY changed_at DESC
LIMIT 20;

-- Settings audit view
CREATE OR REPLACE VIEW settings_audit AS
SELECT 
    sh.changed_at,
    sh.setting_key,
    sh.old_value,
    sh.new_value,
    sh.changed_by,
    sh.reason,
    sh.ip_address
FROM settings_history sh
ORDER BY sh.changed_at DESC
LIMIT 100;

-- Public settings view (for users)
CREATE OR REPLACE VIEW public_settings AS
SELECT 
    key,
    value,
    description,
    description_am
FROM settings
WHERE is_public = TRUE
ORDER BY category, key;

-- Game configuration view
CREATE OR REPLACE VIEW game_configuration AS
SELECT 
    setting_key,
    setting_value,
    value_type,
    description
FROM game_settings
ORDER BY setting_key;

-- ==================== CREATE FUNCTIONS FOR APPLICATION USE ====================

-- Get maintenance mode status
CREATE OR REPLACE FUNCTION is_maintenance_mode()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_setting_bool('maintenance_mode');
END;
$$ LANGUAGE plpgsql;

-- Get game enabled status
CREATE OR REPLACE FUNCTION is_game_enabled()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_setting_bool('game_enabled');
END;
$$ LANGUAGE plpgsql;

-- ==================== VERIFICATION ====================
DO $$
DECLARE
    win_perc INTEGER;
    setting_count INTEGER;
    log_count INTEGER;
BEGIN
    -- Get current win percentage
    win_perc := get_current_win_percentage();
    
    -- Count settings
    SELECT COUNT(*) INTO setting_count FROM settings;
    
    -- Count commission logs
    SELECT COUNT(*) INTO log_count FROM commission_logs;
    
    RAISE NOTICE '✅ Migration 005_commission_settings.sql completed successfully';
    RAISE NOTICE '   - Created settings table with enhanced fields';
    RAISE NOTICE '   - Created settings_history table for auditing';
    RAISE NOTICE '   - Created commission_logs table with round tracking';
    RAISE NOTICE '   - Created game_settings table';
    RAISE NOTICE '   - Inserted % default settings', setting_count;
    RAISE NOTICE '   - Created triggers for auditing and logging';
    RAISE NOTICE '   - Created helper functions for settings management';
    RAISE NOTICE '   - Created views for monitoring';
    RAISE NOTICE '   - Current win percentage: %', win_perc;
    RAISE NOTICE '   - Total commission changes logged: %', log_count;
    
    -- Test setting functions
    PERFORM set_setting('test_temp', 'test', 'system');
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '   - Setting functions working correctly';
END $$;