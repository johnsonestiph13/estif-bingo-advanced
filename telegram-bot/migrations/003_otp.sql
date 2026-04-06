-- =====================================================
-- MIGRATION: 003_otp.sql
-- Description: Create OTP codes table for bingo login
-- =====================================================

-- Create OTP codes table
CREATE TABLE IF NOT EXISTS otp_codes (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    otp TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    attempts INTEGER DEFAULT 0
);

-- Add comments
COMMENT ON TABLE otp_codes IS 'One-time passwords for Bingo game login';
COMMENT ON COLUMN otp_codes.otp IS '6-digit OTP code';
COMMENT ON COLUMN otp_codes.expires_at IS 'Expiration timestamp (5 minutes from creation)';
COMMENT ON COLUMN otp_codes.attempts IS 'Number of failed verification attempts';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_otp_telegram_expires ON otp_codes(telegram_id, expires_at);

-- Create function to clean expired OTPs automatically
CREATE OR REPLACE FUNCTION clean_expired_otp()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM otp_codes WHERE expires_at < NOW()
    RETURNING COUNT(*) INTO deleted_count;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job to clean expired OTPs (runs every hour)
-- Note: This requires pg_cron extension. If not available, run manually.
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('clean-expired-otp', '0 * * * *', 'SELECT clean_expired_otp()');

-- Create function to limit OTP attempts
CREATE OR REPLACE FUNCTION check_otp_attempts()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.attempts >= 5 THEN
        DELETE FROM otp_codes WHERE telegram_id = NEW.telegram_id;
        RAISE EXCEPTION 'Too many failed attempts. Please request new OTP.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for OTP attempts
DROP TRIGGER IF EXISTS trigger_check_otp_attempts ON otp_codes;
CREATE TRIGGER trigger_check_otp_attempts
    BEFORE UPDATE OF attempts ON otp_codes
    FOR EACH ROW
    EXECUTE FUNCTION check_otp_attempts();

-- Create view for active OTPs
CREATE OR REPLACE VIEW active_otps AS
SELECT 
    telegram_id,
    expires_at,
    EXTRACT(EPOCH FROM (expires_at - NOW())) / 60 AS minutes_remaining,
    attempts
FROM otp_codes
WHERE expires_at > NOW();

-- Verification
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 003_otp.sql completed';
    RAISE NOTICE '   - Created otp_codes table';
    RAISE NOTICE '   - Created indexes';
    RAISE NOTICE '   - Created OTP cleanup function';
    RAISE NOTICE '   - Created attempt limiter trigger';
    RAISE NOTICE '   - Created active_otps view';
END $$;