-- =====================================================
-- MIGRATION: 004_auth_codes.sql
-- Description: Create auth codes table for game link authentication
-- =====================================================

-- Create auth codes table
CREATE TABLE IF NOT EXISTS auth_codes (
    code TEXT PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    used BOOLEAN DEFAULT FALSE
);

-- Add comments
COMMENT ON TABLE auth_codes IS 'One-time authentication codes for game access';
COMMENT ON COLUMN auth_codes.code IS 'Unique authentication code (URL-safe token)';
COMMENT ON COLUMN auth_codes.used IS 'Whether the code has been consumed';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_auth_expires ON auth_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_telegram ON auth_codes(telegram_id);
CREATE INDEX IF NOT EXISTS idx_auth_telegram_unused ON auth_codes(telegram_id, used) WHERE used = FALSE;
CREATE INDEX IF NOT EXISTS idx_auth_code_active ON auth_codes(code, expires_at) WHERE used = FALSE AND expires_at > NOW();

-- Create function to generate unique auth code
CREATE OR REPLACE FUNCTION generate_auth_code()
RETURNS TEXT AS $$
DECLARE
    new_code TEXT;
    code_exists BOOLEAN;
BEGIN
    LOOP
        -- Generate URL-safe random string (32 characters)
        new_code := encode(gen_random_bytes(24), 'base64');
        new_code := replace(replace(new_code, '/', '_'), '+', '-');
        new_code := substring(new_code, 1, 32);
        
        -- Check if code already exists
        SELECT EXISTS(SELECT 1 FROM auth_codes WHERE code = new_code) INTO code_exists;
        
        EXIT WHEN NOT code_exists;
    END LOOP;
    
    RETURN new_code;
END;
$$ LANGUAGE plpgsql;

-- Create function to clean expired auth codes
CREATE OR REPLACE FUNCTION clean_expired_auth_codes()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_codes WHERE expires_at < NOW() OR used = TRUE
    RETURNING COUNT(*) INTO deleted_count;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create view for active auth codes
CREATE OR REPLACE VIEW active_auth_codes AS
SELECT 
    code,
    telegram_id,
    expires_at,
    EXTRACT(EPOCH FROM (expires_at - NOW())) / 60 AS minutes_remaining
FROM auth_codes
WHERE expires_at > NOW() AND used = FALSE;

-- Create function to validate and consume auth code
CREATE OR REPLACE FUNCTION consume_auth_code(p_code TEXT)
RETURNS BIGINT AS $$
DECLARE
    v_telegram_id BIGINT;
BEGIN
    SELECT telegram_id INTO v_telegram_id
    FROM auth_codes
    WHERE code = p_code AND expires_at > NOW() AND used = FALSE;
    
    IF v_telegram_id IS NULL THEN
        RETURN NULL;
    END IF;
    
    UPDATE auth_codes SET used = TRUE WHERE code = p_code;
    
    RETURN v_telegram_id;
END;
$$ LANGUAGE plpgsql;

-- Verification
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 004_auth_codes.sql completed';
    RAISE NOTICE '   - Created auth_codes table';
    RAISE NOTICE '   - Created indexes';
    RAISE NOTICE '   - Created generate_auth_code function';
    RAISE NOTICE '   - Created cleanup function';
    RAISE NOTICE '   - Created consume_auth_code function';
    RAISE NOTICE '   - Created active_auth_codes view';
END $$;