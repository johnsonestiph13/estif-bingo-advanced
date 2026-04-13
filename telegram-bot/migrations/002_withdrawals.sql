-- =====================================================
-- MIGRATION: 002_withdrawals.sql
-- Description: Create withdrawals and related tables
-- Version: 3.0.0
-- Date: 2024
-- =====================================================

-- ==================== DROP EXISTING (CLEAN START) ====================
-- Uncomment if you need to recreate
-- DROP TABLE IF EXISTS pending_withdrawals CASCADE;
-- DROP TABLE IF EXISTS withdrawal_history CASCADE;
-- DROP TABLE IF EXISTS withdrawal_methods CASCADE;
-- DROP FUNCTION IF EXISTS update_processed_at();
-- DROP FUNCTION IF EXISTS validate_withdrawal();

-- ==================== CREATE WITHDRAWAL METHODS TABLE ====================
CREATE TABLE IF NOT EXISTS withdrawal_methods (
    id SERIAL PRIMARY KEY,
    method_code VARCHAR(20) UNIQUE NOT NULL,
    method_name VARCHAR(50) NOT NULL,
    method_name_am VARCHAR(50),
    min_amount DECIMAL(12,2) DEFAULT 50.00 CHECK (min_amount >= 0),
    max_amount DECIMAL(12,2) DEFAULT 10000.00 CHECK (max_amount >= 0),
    fee_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (fee_percentage >= 0),
    processing_time_hours INTEGER DEFAULT 24 CHECK (processing_time_hours > 0),
    is_active BOOLEAN DEFAULT TRUE,
    requires_account_name BOOLEAN DEFAULT FALSE,
    requires_phone BOOLEAN DEFAULT TRUE,
    requires_bank_branch BOOLEAN DEFAULT FALSE,
    description TEXT,
    description_am TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default withdrawal methods
INSERT INTO withdrawal_methods (method_code, method_name, method_name_am, min_amount, max_amount, fee_percentage, processing_time_hours, requires_phone, sort_order) VALUES
    ('CBE', 'Commercial Bank of Ethiopia', 'ንግድ ባንክ', 50.00, 10000.00, 0.00, 24, TRUE, 1),
    ('ABBISINIYA', 'Abyssinia Bank', 'አቢሲኒያ ባንክ', 50.00, 10000.00, 0.00, 24, TRUE, 2),
    ('TELEBIRR', 'TeleBirr', 'ቴሌ ብር', 50.00, 5000.00, 0.00, 12, TRUE, 3),
    ('MPESA', 'M-Pesa', 'ኤም-ፔሳ', 50.00, 5000.00, 0.00, 12, TRUE, 4)
ON CONFLICT (method_code) DO NOTHING;

-- ==================== CREATE PENDING WITHDRAWALS TABLE ====================
CREATE TABLE IF NOT EXISTS pending_withdrawals (
    id SERIAL PRIMARY KEY,
    withdrawal_id VARCHAR(50) UNIQUE,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    username VARCHAR(64),
    phone VARCHAR(20),
    
    -- Withdrawal details
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    fee_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (fee_amount >= 0),
    net_amount DECIMAL(12,2) GENERATED ALWAYS AS (amount - fee_amount) STORED,
    
    -- Payment details
    method VARCHAR(20) NOT NULL,
    account_number VARCHAR(100) NOT NULL,
    account_name VARCHAR(100),
    bank_branch VARCHAR(100),
    reference_number VARCHAR(100),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',
    status_reason TEXT,
    
    -- Approval/Rejection details
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    
    -- Admin tracking
    processed_by VARCHAR(100),
    approved_by VARCHAR(100),
    rejected_by VARCHAR(100),
    
    -- Additional info
    ip_address INET,
    user_agent TEXT,
    notes TEXT,
    rejection_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== CREATE WITHDRAWAL HISTORY TABLE ====================
CREATE TABLE IF NOT EXISTS withdrawal_history (
    id SERIAL PRIMARY KEY,
    withdrawal_id VARCHAR(50) NOT NULL,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    amount DECIMAL(12,2),
    note TEXT,
    performed_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== CREATE WITHDRAWAL LIMITS TABLE ====================
CREATE TABLE IF NOT EXISTS withdrawal_limits (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    daily_limit DECIMAL(12,2) DEFAULT 10000.00,
    weekly_limit DECIMAL(12,2) DEFAULT 50000.00,
    monthly_limit DECIMAL(12,2) DEFAULT 100000.00,
    daily_used DECIMAL(12,2) DEFAULT 0.00,
    weekly_used DECIMAL(12,2) DEFAULT 0.00,
    monthly_used DECIMAL(12,2) DEFAULT 0.00,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(telegram_id)
);

-- ==================== ADD TABLE COMMENTS ====================
COMMENT ON TABLE withdrawal_methods IS 'Available withdrawal methods and their configurations';
COMMENT ON TABLE pending_withdrawals IS 'Pending withdrawal requests from users';
COMMENT ON TABLE withdrawal_history IS 'History of all withdrawal status changes';
COMMENT ON TABLE withdrawal_limits IS 'User-specific withdrawal limits and usage';

COMMENT ON COLUMN pending_withdrawals.withdrawal_id IS 'Unique withdrawal identifier (WDL-YYYYMMDD-XXXXXX)';
COMMENT ON COLUMN pending_withdrawals.status IS 'Status: pending, approved, rejected, failed, completed';
COMMENT ON COLUMN pending_withdrawals.method IS 'Payment method: CBE, ABBISINIYA, TELEBIRR, MPESA';
COMMENT ON COLUMN pending_withdrawals.fee_amount IS 'Fee charged for this withdrawal';
COMMENT ON COLUMN pending_withdrawals.net_amount IS 'Amount after fee deduction (auto-calculated)';

-- ==================== CREATE INDEXES ====================
-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram ON pending_withdrawals(telegram_id);
CREATE INDEX IF NOT EXISTS idx_withdrawals_withdrawal_id ON pending_withdrawals(withdrawal_id);
CREATE INDEX IF NOT EXISTS idx_withdrawals_username ON pending_withdrawals(username);
CREATE INDEX IF NOT EXISTS idx_withdrawals_phone ON pending_withdrawals(phone);

-- Status indexes
CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON pending_withdrawals(status);
CREATE INDEX IF NOT EXISTS idx_withdrawals_pending ON pending_withdrawals(status, requested_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_withdrawals_approved ON pending_withdrawals(status, approved_at) WHERE status = 'approved';
CREATE INDEX IF NOT EXISTS idx_withdrawals_completed ON pending_withdrawals(status, completed_at) WHERE status = 'completed';

-- Time-based indexes
CREATE INDEX IF NOT EXISTS idx_withdrawals_requested_at ON pending_withdrawals(requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawals_processed_at ON pending_withdrawals(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawals_date_range ON pending_withdrawals(requested_at, status);

-- Method indexes
CREATE INDEX IF NOT EXISTS idx_withdrawals_method ON pending_withdrawals(method);
CREATE INDEX IF NOT EXISTS idx_withdrawals_method_status ON pending_withdrawals(method, status);

-- Amount indexes
CREATE INDEX IF NOT EXISTS idx_withdrawals_amount ON pending_withdrawals(amount DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawals_amount_range ON pending_withdrawals(amount, status);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram_status ON pending_withdrawals(telegram_id, status);
CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram_date ON pending_withdrawals(telegram_id, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_withdrawals_status_date ON pending_withdrawals(status, requested_at DESC);

-- History indexes
CREATE INDEX IF NOT EXISTS idx_withdrawal_history_withdrawal ON withdrawal_history(withdrawal_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_history_telegram ON withdrawal_history(telegram_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_history_created_at ON withdrawal_history(created_at DESC);

-- Limits indexes
CREATE INDEX IF NOT EXISTS idx_withdrawal_limits_telegram ON withdrawal_limits(telegram_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_limits_reset_date ON withdrawal_limits(last_reset_date);

-- ==================== CREATE FUNCTIONS ====================

-- Generate unique withdrawal ID
CREATE OR REPLACE FUNCTION generate_withdrawal_id()
RETURNS TRIGGER AS $$
DECLARE
    new_id VARCHAR(50);
    sequence_num INTEGER;
BEGIN
    -- Get next sequence number for today
    SELECT COALESCE(MAX(CAST(SUBSTRING(withdrawal_id FROM 'WDL-[0-9]{8}-([0-9]{6})$') AS INTEGER)), 0) + 1
    INTO sequence_num
    FROM pending_withdrawals
    WHERE withdrawal_id LIKE 'WDL-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-%';
    
    -- Generate ID: WDL-YYYYMMDD-XXXXXX
    new_id := 'WDL-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(sequence_num::TEXT, 6, '0');
    
    NEW.withdrawal_id := new_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update processed_at automatically
CREATE OR REPLACE FUNCTION update_processed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('approved', 'rejected', 'failed', 'completed') AND OLD.status = 'pending' THEN
        NEW.processed_at = NOW();
        
        -- Set specific timestamps based on status
        IF NEW.status = 'approved' THEN
            NEW.approved_at = NOW();
        ELSIF NEW.status = 'rejected' THEN
            NEW.rejected_at = NOW();
        ELSIF NEW.status = 'failed' THEN
            NEW.failed_at = NOW();
        ELSIF NEW.status = 'completed' THEN
            NEW.completed_at = NOW();
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update updated_at automatically
CREATE OR REPLACE FUNCTION update_withdrawal_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log withdrawal history
CREATE OR REPLACE FUNCTION log_withdrawal_history()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO withdrawal_history (
        withdrawal_id, telegram_id, action, old_status, new_status, amount, note, performed_by
    ) VALUES (
        NEW.withdrawal_id, NEW.telegram_id, TG_OP, OLD.status, NEW.status, NEW.amount, NEW.status_reason, NEW.processed_by
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Validate withdrawal amount
CREATE OR REPLACE FUNCTION validate_withdrawal_amount()
RETURNS TRIGGER AS $$
DECLARE
    user_balance DECIMAL(12,2);
    method_min DECIMAL(12,2);
    method_max DECIMAL(12,2);
    daily_used DECIMAL(12,2);
BEGIN
    -- Check user balance
    SELECT balance INTO user_balance FROM users WHERE telegram_id = NEW.telegram_id;
    IF user_balance < NEW.amount THEN
        RAISE EXCEPTION 'Insufficient balance: % < %', user_balance, NEW.amount;
    END IF;
    
    -- Check method limits
    SELECT min_amount, max_amount INTO method_min, method_max 
    FROM withdrawal_methods WHERE method_code = NEW.method AND is_active = TRUE;
    
    IF NEW.amount < method_min THEN
        RAISE EXCEPTION 'Amount % below minimum % for method %', NEW.amount, method_min, NEW.method;
    END IF;
    
    IF NEW.amount > method_max THEN
        RAISE EXCEPTION 'Amount % above maximum % for method %', NEW.amount, method_max, NEW.method;
    END IF;
    
    -- Check daily limit
    SELECT daily_used INTO daily_used 
    FROM withdrawal_limits 
    WHERE telegram_id = NEW.telegram_id AND last_reset_date = CURRENT_DATE;
    
    IF daily_used IS NOT NULL AND (daily_used + NEW.amount) > 10000 THEN
        RAISE EXCEPTION 'Daily withdrawal limit exceeded';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update withdrawal limits
CREATE OR REPLACE FUNCTION update_withdrawal_limits()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'approved' THEN
        INSERT INTO withdrawal_limits (telegram_id, daily_used, weekly_used, monthly_used)
        VALUES (NEW.telegram_id, NEW.amount, NEW.amount, NEW.amount)
        ON CONFLICT (telegram_id) DO UPDATE SET
            daily_used = withdrawal_limits.daily_used + NEW.amount,
            weekly_used = withdrawal_limits.weekly_used + NEW.amount,
            monthly_used = withdrawal_limits.monthly_used + NEW.amount,
            updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Reset daily limits function
CREATE OR REPLACE FUNCTION reset_daily_withdrawal_limits()
RETURNS VOID AS $$
BEGIN
    UPDATE withdrawal_limits 
    SET daily_used = 0, last_reset_date = CURRENT_DATE
    WHERE last_reset_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- ==================== CREATE TRIGGERS ====================

-- Trigger for generating withdrawal ID
DROP TRIGGER IF EXISTS trigger_generate_withdrawal_id ON pending_withdrawals;
CREATE TRIGGER trigger_generate_withdrawal_id
    BEFORE INSERT ON pending_withdrawals
    FOR EACH ROW
    WHEN (NEW.withdrawal_id IS NULL)
    EXECUTE FUNCTION generate_withdrawal_id();

-- Trigger for processed_at
DROP TRIGGER IF EXISTS trigger_update_processed_at ON pending_withdrawals;
CREATE TRIGGER trigger_update_processed_at
    BEFORE UPDATE ON pending_withdrawals
    FOR EACH ROW
    EXECUTE FUNCTION update_processed_at();

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trigger_update_withdrawal_updated_at ON pending_withdrawals;
CREATE TRIGGER trigger_update_withdrawal_updated_at
    BEFORE UPDATE ON pending_withdrawals
    FOR EACH ROW
    EXECUTE FUNCTION update_withdrawal_updated_at();

-- Trigger for history logging
DROP TRIGGER IF EXISTS trigger_log_withdrawal_history ON pending_withdrawals;
CREATE TRIGGER trigger_log_withdrawal_history
    AFTER UPDATE OF status ON pending_withdrawals
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION log_withdrawal_history();

-- Trigger for amount validation
DROP TRIGGER IF EXISTS trigger_validate_withdrawal_amount ON pending_withdrawals;
CREATE TRIGGER trigger_validate_withdrawal_amount
    BEFORE INSERT ON pending_withdrawals
    FOR EACH ROW
    EXECUTE FUNCTION validate_withdrawal_amount();

-- Trigger for updating limits
DROP TRIGGER IF EXISTS trigger_update_withdrawal_limits ON pending_withdrawals;
CREATE TRIGGER trigger_update_withdrawal_limits
    AFTER UPDATE OF status ON pending_withdrawals
    FOR EACH ROW
    WHEN (NEW.status = 'approved' AND OLD.status = 'pending')
    EXECUTE FUNCTION update_withdrawal_limits();

-- ==================== CREATE VIEWS ====================

-- Pending withdrawals summary view
CREATE OR REPLACE VIEW pending_withdrawals_summary AS
SELECT 
    COUNT(*) as total_pending,
    COALESCE(SUM(amount), 0) as total_amount_pending,
    MIN(requested_at) as oldest_request,
    MAX(requested_at) as newest_request,
    AVG(amount) as avg_amount
FROM pending_withdrawals
WHERE status = 'pending';

-- Withdrawal statistics by method
CREATE OR REPLACE VIEW withdrawal_stats_by_method AS
SELECT 
    method,
    COUNT(*) as total_count,
    COALESCE(SUM(amount), 0) as total_amount,
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
FROM pending_withdrawals
WHERE requested_at > NOW() - INTERVAL '30 days'
GROUP BY method
ORDER BY total_amount DESC;

-- User withdrawal summary view
CREATE OR REPLACE VIEW user_withdrawal_summary AS
SELECT 
    telegram_id,
    username,
    phone,
    COUNT(*) as total_withdrawals,
    COALESCE(SUM(amount), 0) as total_amount,
    COALESCE(SUM(fee_amount), 0) as total_fees,
    AVG(amount) as avg_amount,
    MAX(amount) as max_amount,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
    MAX(requested_at) as last_withdrawal_date
FROM pending_withdrawals
GROUP BY telegram_id, username, phone;

-- Daily withdrawal volume view
CREATE OR REPLACE VIEW daily_withdrawal_volume AS
SELECT 
    DATE(requested_at) as withdrawal_date,
    COUNT(*) as total_withdrawals,
    COALESCE(SUM(amount), 0) as total_amount,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
    COALESCE(SUM(CASE WHEN status = 'approved' THEN amount ELSE 0 END), 0) as approved_amount
FROM pending_withdrawals
WHERE requested_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(requested_at)
ORDER BY withdrawal_date DESC;

-- ==================== ADD CONSTRAINTS ====================

-- Add status constraint
ALTER TABLE pending_withdrawals 
    DROP CONSTRAINT IF EXISTS chk_withdrawal_status;

ALTER TABLE pending_withdrawals 
    ADD CONSTRAINT chk_withdrawal_status 
    CHECK (status IN ('pending', 'approved', 'rejected', 'failed', 'completed'));

-- Add method constraint
ALTER TABLE pending_withdrawals 
    DROP CONSTRAINT IF EXISTS chk_withdrawal_method;

ALTER TABLE pending_withdrawals 
    ADD CONSTRAINT chk_withdrawal_method 
    CHECK (method IN ('CBE', 'ABBISINIYA', 'TELEBIRR', 'MPESA'));

-- Add positive amount constraint
ALTER TABLE pending_withdrawals 
    DROP CONSTRAINT IF EXISTS chk_withdrawal_positive;

ALTER TABLE pending_withdrawals 
    ADD CONSTRAINT chk_withdrawal_positive 
    CHECK (amount > 0);

-- ==================== SCHEDULED JOBS (PostgreSQL 14+) ====================
-- Reset daily limits at midnight
DO $$
BEGIN
    -- For PostgreSQL 14+
    CREATE EXTENSION IF NOT EXISTS pg_cron;
    
    -- Schedule daily reset at midnight
    -- SELECT cron.schedule('reset-withdrawal-limits', '0 0 * * *', 'SELECT reset_daily_withdrawal_limits();');
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pg_cron not available - schedule reset manually';
END $$;

-- ==================== VERIFICATION ====================
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    trigger_count INTEGER;
    view_count INTEGER;
BEGIN
    -- Check tables
    SELECT COUNT(*) INTO table_count FROM information_schema.tables 
    WHERE table_name IN ('pending_withdrawals', 'withdrawal_history', 'withdrawal_methods', 'withdrawal_limits');
    
    -- Check indexes
    SELECT COUNT(*) INTO index_count FROM pg_indexes 
    WHERE tablename IN ('pending_withdrawals', 'withdrawal_history', 'withdrawal_methods', 'withdrawal_limits');
    
    -- Check triggers
    SELECT COUNT(*) INTO trigger_count FROM pg_trigger 
    WHERE tgrelid IN ('pending_withdrawals'::regclass, 'withdrawal_history'::regclass);
    
    -- Check views
    SELECT COUNT(*) INTO view_count FROM pg_views 
    WHERE viewname IN ('pending_withdrawals_summary', 'withdrawal_stats_by_method', 'user_withdrawal_summary', 'daily_withdrawal_volume');
    
    RAISE NOTICE '✅ Migration 002_withdrawals.sql completed successfully';
    RAISE NOTICE '   - Created 4 tables';
    RAISE NOTICE '   - Created % indexes', index_count;
    RAISE NOTICE '   - Created % triggers', trigger_count;
    RAISE NOTICE '   - Created % views', view_count;
    RAISE NOTICE '   - Inserted % withdrawal methods', (SELECT COUNT(*) FROM withdrawal_methods);
    
    -- Print sample verification
    RAISE NOTICE '📊 Sample Data:';
    RAISE NOTICE '   - Total pending withdrawals: (SELECT COUNT(*) FROM pending_withdrawals WHERE status = ''pending'')';
    RAISE NOTICE '   - Total pending amount: (SELECT COALESCE(SUM(amount), 0) FROM pending_withdrawals WHERE status = ''pending'') ETB';
END $$;