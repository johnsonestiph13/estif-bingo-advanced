-- =====================================================
-- MIGRATION: 004_auth_codes.sql
-- Description: Create auth codes table for game link authentication
-- Version: 3.0.0
-- Date: 2024
-- =====================================================

-- ==================== DROP EXISTING (CLEAN START) ====================
-- Uncomment if you need to recreate
-- DROP TABLE IF EXISTS auth_codes CASCADE;
-- DROP TABLE IF EXISTS auth_code_logs CASCADE;
-- DROP FUNCTION IF EXISTS generate_auth_code();
-- DROP FUNCTION IF EXISTS clean_expired_auth_codes();
-- DROP FUNCTION IF EXISTS consume_auth_code(TEXT);
-- DROP FUNCTION IF EXISTS validate_auth_code(TEXT);

-- ==================== CREATE AUTH CODES TABLE ====================
CREATE TABLE IF NOT EXISTS auth_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    username VARCHAR(64),
    first_name VARCHAR(64),
    last_name VARCHAR(64),
    
    -- Code properties
    purpose VARCHAR(50) DEFAULT 'game_access',
    code_type VARCHAR(30) DEFAULT 'one_time', -- one_time, multi_use, temporary
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    used BOOLEAN DEFAULT FALSE,
    max_uses INTEGER DEFAULT 1,
    use_count INTEGER DEFAULT 0,
    
    -- Security
    ip_address INET,
    user_agent TEXT,
    exchange_attempts INTEGER DEFAULT 0,
    last_exchange_attempt TIMESTAMP WITH TIME ZONE,
    
    -- Additional data
    metadata JSONB DEFAULT '{}'::jsonb,
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason TEXT,
    
    -- Indexes
    INDEX idx_auth_code_code (code),
    INDEX idx_auth_code_telegram (telegram_id),
    INDEX idx_auth_code_expires (expires_at),
    INDEX idx_auth_code_used (used),
    INDEX idx_auth_code_purpose (purpose),
    INDEX idx_auth_code_active (is_active),
    INDEX idx_auth_code_revoked (is_revoked)
);

-- ==================== CREATE AUTH CODE LOGS TABLE ====================
CREATE TABLE IF NOT EXISTS auth_code_logs (
    id BIGSERIAL PRIMARY KEY,
    code_id INTEGER REFERENCES auth_codes(id) ON DELETE SET NULL,
    code_masked VARCHAR(20), -- Masked code for logging (e.g., a1b2****c3d4)
    telegram_id BIGINT,
    action VARCHAR(50) NOT NULL, -- generate, exchange, expire, revoke, fail
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_auth_logs_code_id (code_id),
    INDEX idx_auth_logs_telegram (telegram_id),
    INDEX idx_auth_logs_created (created_at),
    INDEX idx_auth_logs_action (action)
);

-- ==================== ADD TABLE COMMENTS ====================
COMMENT ON TABLE auth_codes IS 'Authentication codes for web app game access (JWT exchange)';
COMMENT ON TABLE auth_code_logs IS 'Audit log for all authentication code activities';

COMMENT ON COLUMN auth_codes.code IS 'Unique authentication code (URL-safe token)';
COMMENT ON COLUMN auth_codes.purpose IS 'Purpose: game_access, admin_access, api_access';
COMMENT ON COLUMN auth_codes.code_type IS 'Type: one_time, multi_use, temporary';
COMMENT ON COLUMN auth_codes.max_uses IS 'Maximum number of times this code can be used';
COMMENT ON COLUMN auth_codes.use_count IS 'Current number of times this code has been used';
COMMENT ON COLUMN auth_codes.is_revoked IS 'Whether the code has been manually revoked';
COMMENT ON COLUMN auth_codes.metadata IS 'Additional JSON data (game session, cartelas, etc.)';

-- ==================== CREATE FUNCTIONS ====================

-- Generate unique auth code
CREATE OR REPLACE FUNCTION generate_auth_code()
RETURNS TEXT AS $$
DECLARE
    new_code TEXT;
    code_exists BOOLEAN;
    chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    i INTEGER;
BEGIN
    LOOP
        -- Generate 32-character random string
        new_code := '';
        FOR i IN 1..32 LOOP
            new_code := new_code || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
        END LOOP;
        
        -- Check if code already exists
        SELECT EXISTS(SELECT 1 FROM auth_codes WHERE code = new_code) INTO code_exists;
        
        EXIT WHEN NOT code_exists;
    END LOOP;
    
    RETURN new_code;
END;
$$ LANGUAGE plpgsql;

-- Generate prefixed auth code (e.g., BINGO-xxxx-xxxx)
CREATE OR REPLACE FUNCTION generate_prefixed_auth_code(prefix TEXT DEFAULT 'BINGO')
RETURNS TEXT AS $$
DECLARE
    new_code TEXT;
    code_exists BOOLEAN;
    part1 TEXT;
    part2 TEXT;
    chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    i INTEGER;
BEGIN
    LOOP
        -- Generate two 6-character parts
        part1 := '';
        part2 := '';
        FOR i IN 1..6 LOOP
            part1 := part1 || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
            part2 := part2 || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
        END LOOP;
        
        new_code := upper(prefix) || '-' || part1 || '-' || part2;
        
        -- Check if code already exists
        SELECT EXISTS(SELECT 1 FROM auth_codes WHERE code = new_code) INTO code_exists;
        
        EXIT WHEN NOT code_exists;
    END LOOP;
    
    RETURN new_code;
END;
$$ LANGUAGE plpgsql;

-- Clean expired auth codes
CREATE OR REPLACE FUNCTION clean_expired_auth_codes()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired and old used codes (older than 7 days)
    WITH deleted AS (
        DELETE FROM auth_codes 
        WHERE expires_at < NOW() 
           OR (used = TRUE AND created_at < NOW() - INTERVAL '7 days')
           OR (is_revoked = TRUE AND revoked_at < NOW() - INTERVAL '7 days')
        RETURNING id, code, telegram_id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    -- Log cleanup
    IF deleted_count > 0 THEN
        INSERT INTO auth_code_logs (action, success, metadata)
        VALUES ('cleanup', TRUE, jsonb_build_object('deleted_count', deleted_count));
    END IF;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Validate and consume auth code (with enhanced security)
CREATE OR REPLACE FUNCTION consume_auth_code(
    p_code TEXT,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS TABLE(
    telegram_id BIGINT,
    username VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    metadata JSONB,
    is_valid BOOLEAN,
    message TEXT
) AS $$
DECLARE
    v_record RECORD;
    v_now TIMESTAMP WITH TIME ZONE := NOW();
BEGIN
    -- Look up the code
    SELECT 
        a.id,
        a.telegram_id,
        a.username,
        a.first_name,
        a.last_name,
        a.expires_at,
        a.used,
        a.use_count,
        a.max_uses,
        a.is_active,
        a.is_revoked,
        a.metadata,
        u.username as user_username,
        u.first_name as user_first_name,
        u.last_name as user_last_name
    INTO v_record
    FROM auth_codes a
    LEFT JOIN users u ON a.telegram_id = u.telegram_id
    WHERE a.code = p_code;
    
    -- Code not found
    IF v_record.id IS NULL THEN
        -- Log failed attempt
        INSERT INTO auth_code_logs (code_masked, action, success, error_message, ip_address, user_agent)
        VALUES (mask_string(p_code), 'exchange', FALSE, 'Code not found', p_ip_address, p_user_agent);
        
        RETURN QUERY SELECT NULL::BIGINT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::JSONB, FALSE, 'Invalid or expired authentication code';
        RETURN;
    END IF;
    
    -- Check if revoked
    IF v_record.is_revoked THEN
        INSERT INTO auth_code_logs (code_id, code_masked, telegram_id, action, success, error_message, ip_address, user_agent)
        VALUES (v_record.id, mask_string(p_code), v_record.telegram_id, 'exchange', FALSE, 'Code has been revoked', p_ip_address, p_user_agent);
        
        RETURN QUERY SELECT v_record.telegram_id, v_record.user_username, v_record.user_first_name, v_record.user_last_name, v_record.metadata, FALSE, 'This authentication code has been revoked';
        RETURN;
    END IF;
    
    -- Check if active
    IF NOT v_record.is_active THEN
        INSERT INTO auth_code_logs (code_id, code_masked, telegram_id, action, success, error_message, ip_address, user_agent)
        VALUES (v_record.id, mask_string(p_code), v_record.telegram_id, 'exchange', FALSE, 'Code is inactive', p_ip_address, p_user_agent);
        
        RETURN QUERY SELECT v_record.telegram_id, v_record.user_username, v_record.user_first_name, v_record.user_last_name, v_record.metadata, FALSE, 'This authentication code is inactive';
        RETURN;
    END IF;
    
    -- Check expiration
    IF v_record.expires_at < v_now THEN
        INSERT INTO auth_code_logs (code_id, code_masked, telegram_id, action, success, error_message, ip_address, user_agent)
        VALUES (v_record.id, mask_string(p_code), v_record.telegram_id, 'exchange', FALSE, 'Code expired', p_ip_address, p_user_agent);
        
        RETURN QUERY SELECT v_record.telegram_id, v_record.user_username, v_record.user_first_name, v_record.user_last_name, v_record.metadata, FALSE, 'Authentication code has expired';
        RETURN;
    END IF;
    
    -- Check usage limits
    IF v_record.used AND v_record.max_uses <= v_record.use_count THEN
        INSERT INTO auth_code_logs (code_id, code_masked, telegram_id, action, success, error_message, ip_address, user_agent)
        VALUES (v_record.id, mask_string(p_code), v_record.telegram_id, 'exchange', FALSE, 'Usage limit exceeded', p_ip_address, p_user_agent);
        
        RETURN QUERY SELECT v_record.telegram_id, v_record.user_username, v_record.user_first_name, v_record.user_last_name, v_record.metadata, FALSE, 'This authentication code has reached its usage limit';
        RETURN;
    END IF;
    
    -- Update usage
    UPDATE auth_codes 
    SET 
        use_count = use_count + 1,
        used = (use_count + 1 >= max_uses),
        used_at = CASE WHEN (use_count + 1 >= max_uses) THEN v_now ELSE used_at END,
        last_exchange_attempt = v_now,
        exchange_attempts = exchange_attempts + 1,
        ip_address = COALESCE(p_ip_address, ip_address),
        user_agent = COALESCE(p_user_agent, user_agent)
    WHERE id = v_record.id;
    
    -- Log successful exchange
    INSERT INTO auth_code_logs (code_id, code_masked, telegram_id, action, success, ip_address, user_agent)
    VALUES (v_record.id, mask_string(p_code), v_record.telegram_id, 'exchange', TRUE, p_ip_address, p_user_agent);
    
    -- Return user info
    RETURN QUERY SELECT 
        v_record.telegram_id,
        COALESCE(v_record.user_username, v_record.username),
        COALESCE(v_record.user_first_name, v_record.first_name),
        COALESCE(v_record.user_last_name, v_record.last_name),
        v_record.metadata,
        TRUE,
        'Authentication successful';
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Helper function to mask strings for logging
CREATE OR REPLACE FUNCTION mask_string(input_string TEXT, visible_chars INTEGER DEFAULT 4)
RETURNS TEXT AS $$
DECLARE
    len INTEGER;
BEGIN
    IF input_string IS NULL THEN
        RETURN NULL;
    END IF;
    
    len := length(input_string);
    
    IF len <= visible_chars THEN
        RETURN repeat('*', len);
    END IF;
    
    RETURN left(input_string, visible_chars) || repeat('*', len - visible_chars);
END;
$$ LANGUAGE plpgsql;

-- Create auth code with metadata
CREATE OR REPLACE FUNCTION create_auth_code(
    p_telegram_id BIGINT,
    p_purpose VARCHAR DEFAULT 'game_access',
    p_expiry_minutes INTEGER DEFAULT 5,
    p_max_uses INTEGER DEFAULT 1,
    p_metadata JSONB DEFAULT '{}'::jsonb,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    new_code TEXT;
    expiry_time TIMESTAMP WITH TIME ZONE;
    user_record RECORD;
BEGIN
    -- Get user info
    SELECT username, first_name, last_name INTO user_record
    FROM users
    WHERE telegram_id = p_telegram_id;
    
    -- Generate code
    IF p_purpose = 'game_access' THEN
        new_code := generate_prefixed_auth_code('BINGO');
    ELSE
        new_code := generate_auth_code();
    END IF;
    
    -- Calculate expiry
    expiry_time := NOW() + (p_expiry_minutes || ' minutes')::INTERVAL;
    
    -- Insert code
    INSERT INTO auth_codes (
        code, telegram_id, username, first_name, last_name,
        purpose, expires_at, max_uses, metadata, ip_address, user_agent
    ) VALUES (
        new_code, p_telegram_id, user_record.username, user_record.first_name, user_record.last_name,
        p_purpose, expiry_time, p_max_uses, p_metadata, p_ip_address, p_user_agent
    );
    
    -- Log generation
    INSERT INTO auth_code_logs (code_id, code_masked, telegram_id, action, success, ip_address, user_agent)
    VALUES (currval('auth_codes_id_seq'), mask_string(new_code), p_telegram_id, 'generate', TRUE, p_ip_address, p_user_agent);
    
    RETURN new_code;
END;
$$ LANGUAGE plpgsql;

-- Revoke auth code
CREATE OR REPLACE FUNCTION revoke_auth_code(
    p_code TEXT,
    p_reason TEXT DEFAULT NULL,
    p_revoked_by TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_code_id INTEGER;
BEGIN
    UPDATE auth_codes 
    SET 
        is_revoked = TRUE,
        revoked_at = NOW(),
        revoked_reason = p_reason,
        is_active = FALSE,
        notes = COALESCE(notes || E'\n', '') || 'Revoked by: ' || COALESCE(p_revoked_by, 'system') || '. Reason: ' || COALESCE(p_reason, 'No reason provided')
    WHERE code = p_code
    RETURNING id INTO v_code_id;
    
    IF v_code_id IS NOT NULL THEN
        INSERT INTO auth_code_logs (code_id, code_masked, action, success, metadata)
        VALUES (v_code_id, mask_string(p_code), 'revoke', TRUE, jsonb_build_object('reason', p_reason, 'revoked_by', p_revoked_by));
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ==================== CREATE VIEWS ====================

-- Active auth codes view
CREATE OR REPLACE VIEW active_auth_codes AS
SELECT 
    code,
    telegram_id,
    username,
    purpose,
    code_type,
    expires_at,
    use_count,
    max_uses,
    EXTRACT(EPOCH FROM (expires_at - NOW())) / 60 AS minutes_remaining,
    CASE 
        WHEN max_uses > 1 THEN (max_uses - use_count) || ' uses remaining'
        ELSE 'Single use'
    END AS usage_info,
    metadata
FROM auth_codes
WHERE expires_at > NOW() 
    AND used = FALSE 
    AND is_active = TRUE 
    AND is_revoked = FALSE
ORDER BY expires_at ASC;

-- Auth codes statistics view
CREATE OR REPLACE VIEW auth_code_statistics AS
SELECT 
    purpose,
    COUNT(*) as total_generated,
    COUNT(CASE WHEN used THEN 1 END) as total_used,
    COUNT(CASE WHEN used = FALSE AND expires_at > NOW() THEN 1 END) as active_codes,
    COUNT(CASE WHEN used = FALSE AND expires_at < NOW() THEN 1 END) as expired_codes,
    COUNT(CASE WHEN is_revoked THEN 1 END) as revoked_codes,
    AVG(use_count) as avg_uses,
    MAX(use_count) as max_uses
FROM auth_codes
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY purpose;

-- User auth codes summary view
CREATE OR REPLACE VIEW user_auth_codes_summary AS
SELECT 
    telegram_id,
    username,
    COUNT(*) as total_codes,
    COUNT(CASE WHEN used THEN 1 END) as used_codes,
    COUNT(CASE WHEN used = FALSE AND expires_at > NOW() THEN 1 END) as active_codes,
    MAX(created_at) as last_code_generated,
    MAX(used_at) as last_code_used
FROM auth_codes
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY telegram_id, username
ORDER BY total_codes DESC;

-- Recent auth activity view
CREATE OR REPLACE VIEW recent_auth_activity AS
SELECT 
    l.created_at,
    l.action,
    l.success,
    l.telegram_id,
    a.username,
    a.purpose,
    l.error_message,
    l.ip_address
FROM auth_code_logs l
LEFT JOIN auth_codes a ON l.code_id = a.id
WHERE l.created_at > NOW() - INTERVAL '24 hours'
ORDER BY l.created_at DESC
LIMIT 100;

-- ==================== CREATE SCHEDULED JOB ====================
DO $$
BEGIN
    -- Note: This requires pg_cron extension
    -- To enable: CREATE EXTENSION IF NOT EXISTS pg_cron;
    
    -- Schedule cleanup every hour
    -- PERFORM cron.schedule('clean-expired-auth-codes', '0 * * * *', 'SELECT clean_expired_auth_codes()');
    
    -- Schedule cleanup of logs (keep 30 days)
    -- PERFORM cron.schedule('clean-old-auth-logs', '0 2 * * *', 'DELETE FROM auth_code_logs WHERE created_at < NOW() - INTERVAL ''30 days''');
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pg_cron not available - scheduled cleanup not configured';
END $$;

-- ==================== VERIFICATION ====================
DO $$
DECLARE
    test_code TEXT;
    test_result RECORD;
BEGIN
    RAISE NOTICE '✅ Migration 004_auth_codes.sql completed successfully';
    RAISE NOTICE '   - Created auth_codes table with enhanced fields';
    RAISE NOTICE '   - Created auth_code_logs table for auditing';
    RAISE NOTICE '   - Created functions: generate_auth_code(), generate_prefixed_auth_code()';
    RAISE NOTICE '   - Created enhanced consume_auth_code() with validation';
    RAISE NOTICE '   - Created create_auth_code() helper function';
    RAISE NOTICE '   - Created revoke_auth_code() for manual revocation';
    RAISE NOTICE '   - Created views for monitoring and statistics';
    
    -- Test code generation
    SELECT generate_prefixed_auth_code('TEST') INTO test_code;
    RAISE NOTICE '📊 Test generated code: %', test_code;
    RAISE NOTICE '📊 Masked code: %', mask_string(test_code);
    
END $$;