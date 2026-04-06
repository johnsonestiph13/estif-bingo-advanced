-- =====================================================
-- MIGRATION: 002_withdrawals.sql
-- Description: Create pending_withdrawals table
-- =====================================================

-- Create pending withdrawals table
CREATE TABLE IF NOT EXISTS pending_withdrawals (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    account TEXT NOT NULL,
    method TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    processed_by TEXT,
    rejection_reason TEXT
);

-- Add comments
COMMENT ON TABLE pending_withdrawals IS 'Pending withdrawal requests from users';
COMMENT ON COLUMN pending_withdrawals.status IS 'Status: pending, approved, rejected, failed';
COMMENT ON COLUMN pending_withdrawals.method IS 'Payment method: CBE, ABBISINIYA, TELEBIRR, MPESA';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram ON pending_withdrawals(telegram_id);
CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON pending_withdrawals(status);
CREATE INDEX IF NOT EXISTS idx_withdrawals_requested_at ON pending_withdrawals(requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawals_pending ON pending_withdrawals(status, requested_at) WHERE status = 'pending';

-- Add status constraint
ALTER TABLE pending_withdrawals 
    DROP CONSTRAINT IF EXISTS chk_withdrawal_status;

ALTER TABLE pending_withdrawals 
    ADD CONSTRAINT chk_withdrawal_status 
    CHECK (status IN ('pending', 'approved', 'rejected', 'failed'));

-- Add method constraint
ALTER TABLE pending_withdrawals 
    DROP CONSTRAINT IF EXISTS chk_withdrawal_method;

ALTER TABLE pending_withdrawals 
    ADD CONSTRAINT chk_withdrawal_method 
    CHECK (method IN ('CBE', 'ABBISINIYA', 'TELEBIRR', 'MPESA'));

-- Create function to automatically update processed_at
CREATE OR REPLACE FUNCTION update_processed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('approved', 'rejected', 'failed') AND OLD.status = 'pending' THEN
        NEW.processed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for processed_at
DROP TRIGGER IF EXISTS trigger_update_processed_at ON pending_withdrawals;
CREATE TRIGGER trigger_update_processed_at
    BEFORE UPDATE ON pending_withdrawals
    FOR EACH ROW
    EXECUTE FUNCTION update_processed_at();

-- Create view for pending withdrawals summary
CREATE OR REPLACE VIEW pending_withdrawals_summary AS
SELECT 
    COUNT(*) as total_pending,
    COALESCE(SUM(amount), 0) as total_amount_pending,
    MIN(requested_at) as oldest_request,
    MAX(requested_at) as newest_request
FROM pending_withdrawals
WHERE status = 'pending';

-- Verification
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002_withdrawals.sql completed';
    RAISE NOTICE '   - Created pending_withdrawals table';
    RAISE NOTICE '   - Created indexes and constraints';
    RAISE NOTICE '   - Created processed_at trigger';
    RAISE NOTICE '   - Created pending_withdrawals_summary view';
END $$;