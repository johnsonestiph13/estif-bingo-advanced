# telegram-bot/bot/db/database.py
# Estif Bingo 24/7 - ULTIMATE DATABASE MODULE
# Complete Database Management System with all features
# Version: 4.0.0 - Production Ready

import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
import random
import string
import os
import secrets
import json
from decimal import Decimal
from functools import wraps
import hashlib
import hmac

# ✅ Correct import for Render
try:
    from bot.config import (
        DATABASE_URL, DB_MIN_SIZE, DB_MAX_SIZE,
        DB_COMMAND_TIMEOUT, SKIP_AUTO_MIGRATIONS,
        OTP_EXPIRY_MINUTES, JWT_SECRET, API_SECRET
    )
except ImportError:
    # Fallback for local development
    from config import (
        DATABASE_URL, DB_MIN_SIZE, DB_MAX_SIZE,
        DB_COMMAND_TIMEOUT, SKIP_AUTO_MIGRATIONS,
        OTP_EXPIRY_MINUTES, JWT_SECRET, API_SECRET
    )

logger = logging.getLogger(__name__)

# ==================== DECORATORS ====================

def log_query(func):
    """Decorator to log database queries"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Query {func.__name__} completed in {duration:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"Query {func.__name__} failed: {e}")
            raise
    return wrapper

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry failed queries"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


class Database:
    _pool: asyncpg.Pool = None
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ==================== INITIALIZATION ====================
    
    @classmethod
    async def init_pool(cls):
        """Initialize database connection pool with SSL for Render"""
        ssl_config = "require" if os.getenv("NODE_ENV") == "production" else None
        
        cls._pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=DB_MIN_SIZE,
            max_size=DB_MAX_SIZE,
            command_timeout=DB_COMMAND_TIMEOUT,
            ssl=ssl_config,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        await cls._init_tables()
        await cls._ensure_columns()
        await cls._create_all_indexes()
        await cls._create_all_views()
        await cls._create_all_functions()
        await cls._create_all_triggers()
        if not SKIP_AUTO_MIGRATIONS:
            await cls._run_migrations()
        logger.info("✅ Database pool initialized")

    @classmethod
    async def close_pool(cls):
        """Close database connection pool"""
        if cls._pool:
            await cls._pool.close()
            logger.info("Database pool closed")

    # ==================== TABLE INITIALIZATION ====================
    
    @classmethod
    async def _init_tables(cls):
        """Create all necessary tables if they don't exist"""
        async with cls._pool.acquire() as conn:
            # Users table (enhanced)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    -- Primary identifiers
                    telegram_id BIGINT PRIMARY KEY,
                    username VARCHAR(64),
                    first_name VARCHAR(64),
                    last_name VARCHAR(64),
                    phone VARCHAR(20) UNIQUE,
                    email VARCHAR(255),
                    
                    -- Balance & Financial
                    balance DECIMAL(12,2) DEFAULT 0 CHECK (balance >= 0),
                    total_deposited DECIMAL(12,2) DEFAULT 0 CHECK (total_deposited >= 0),
                    total_withdrawn DECIMAL(12,2) DEFAULT 0 CHECK (total_withdrawn >= 0),
                    total_won DECIMAL(12,2) DEFAULT 0 CHECK (total_won >= 0),
                    total_bet DECIMAL(12,2) DEFAULT 0 CHECK (total_bet >= 0),
                    total_refund DECIMAL(12,2) DEFAULT 0 CHECK (total_refund >= 0),
                    total_bonus DECIMAL(12,2) DEFAULT 0 CHECK (total_bonus >= 0),
                    
                    -- Game Statistics
                    games_played INTEGER DEFAULT 0 CHECK (games_played >= 0),
                    games_won INTEGER DEFAULT 0 CHECK (games_won >= 0),
                    games_lost INTEGER DEFAULT 0 CHECK (games_lost >= 0),
                    games_drawn INTEGER DEFAULT 0 CHECK (games_drawn >= 0),
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    worst_streak INTEGER DEFAULT 0,
                    highest_win DECIMAL(12,2) DEFAULT 0 CHECK (highest_win >= 0),
                    total_cartelas_bought INTEGER DEFAULT 0,
                    
                    -- Referral System
                    referral_code VARCHAR(8) UNIQUE,
                    referred_by BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
                    referral_count INTEGER DEFAULT 0 CHECK (referral_count >= 0),
                    referral_earnings DECIMAL(12,2) DEFAULT 0 CHECK (referral_earnings >= 0),
                    
                    -- Registration & Status
                    registered BOOLEAN DEFAULT FALSE,
                    joined_group BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT,
                    banned_at TIMESTAMP,
                    is_verified BOOLEAN DEFAULT FALSE,
                    verified_at TIMESTAMP,
                    
                    -- Preferences
                    lang VARCHAR(2) DEFAULT 'en' CHECK (lang IN ('en', 'am')),
                    sound_pack VARCHAR(20) DEFAULT 'pack1',
                    sound_enabled BOOLEAN DEFAULT TRUE,
                    animations_enabled BOOLEAN DEFAULT TRUE,
                    auto_select_cartelas BOOLEAN DEFAULT FALSE,
                    notifications_enabled BOOLEAN DEFAULT TRUE,
                    theme VARCHAR(20) DEFAULT 'dark',
                    notification_preferences JSONB DEFAULT '{}',
                    
                    -- Game Session
                    current_game_session UUID,
                    cartelas_selected INTEGER DEFAULT 0,
                    last_round_played INTEGER,
                    
                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_game_at TIMESTAMP WITH TIME ZONE,
                    last_deposit_at TIMESTAMP WITH TIME ZONE,
                    last_withdrawal_at TIMESTAMP WITH TIME ZONE,
                    last_bonus_at TIMESTAMP WITH TIME ZONE,
                    
                    -- Security
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP WITH TIME ZONE,
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    two_factor_secret TEXT,
                    
                    -- Metadata
                    device_info JSONB DEFAULT '{}',
                    ip_address INET,
                    user_agent TEXT,
                    notes TEXT,
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            # Game rounds table
            await conn.execute("""
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
                    win_percentage INTEGER DEFAULT 80,
                    drawn_numbers INTEGER[] DEFAULT '{}',
                    duration_ms INTEGER,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Game transactions table (enhanced)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_transactions (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(50) UNIQUE,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    username VARCHAR(50),
                    type VARCHAR(20) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    balance_before DECIMAL(10,2),
                    balance_after DECIMAL(10,2),
                    cartela VARCHAR(20),
                    round INTEGER,
                    note TEXT,
                    metadata JSONB DEFAULT '{}',
                    ip_address INET,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Game settings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT NOT NULL,
                    value_type VARCHAR(20) DEFAULT 'string',
                    description TEXT,
                    description_am TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100)
                )
            """)
            
            # Pending withdrawals table (enhanced)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_withdrawals (
                    id SERIAL PRIMARY KEY,
                    withdrawal_id VARCHAR(50) UNIQUE,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    amount DECIMAL(12,2) NOT NULL,
                    fee_amount DECIMAL(12,2) DEFAULT 0,
                    net_amount DECIMAL(12,2) GENERATED ALWAYS AS (amount - fee_amount) STORED,
                    account TEXT NOT NULL,
                    account_name VARCHAR(100),
                    method TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT NOW(),
                    processed_at TIMESTAMP,
                    approved_at TIMESTAMP,
                    rejected_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    processed_by VARCHAR(100),
                    rejection_reason TEXT,
                    note TEXT,
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            # OTP codes table (enhanced)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS otp_codes (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    otp TEXT NOT NULL,
                    otp_hash VARCHAR(255),
                    purpose VARCHAR(50) DEFAULT 'login',
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    used_at TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    ip_address INET,
                    user_agent TEXT,
                    is_used BOOLEAN DEFAULT FALSE,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    blocked_until TIMESTAMP
                )
            """)
            
            # Auth codes table (enhanced)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS auth_codes (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    purpose VARCHAR(50) DEFAULT 'game_access',
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    used_at TIMESTAMP,
                    used BOOLEAN DEFAULT FALSE,
                    max_uses INTEGER DEFAULT 1,
                    use_count INTEGER DEFAULT 0,
                    ip_address INET,
                    user_agent TEXT,
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            # Commission logs table (enhanced)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS commission_logs (
                    id SERIAL PRIMARY KEY,
                    old_percentage INTEGER NOT NULL,
                    new_percentage INTEGER NOT NULL,
                    changed_by VARCHAR(100),
                    changed_by_id BIGINT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET,
                    reason TEXT,
                    round_number INTEGER,
                    total_pool DECIMAL(10,2),
                    total_payout DECIMAL(10,2),
                    admin_commission DECIMAL(10,2)
                )
            """)
            
            # Bonus logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bonus_logs (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    bonus_type VARCHAR(50) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    balance_before DECIMAL(10,2),
                    balance_after DECIMAL(10,2),
                    reason TEXT,
                    expires_at TIMESTAMP,
                    claimed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Daily bonuses table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_bonuses (
                    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
                    last_claimed_date DATE,
                    streak_count INTEGER DEFAULT 1,
                    total_claimed DECIMAL(10,2) DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tournament table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    prize_pool DECIMAL(10,2) DEFAULT 0,
                    entry_fee DECIMAL(10,2) DEFAULT 0,
                    max_participants INTEGER,
                    current_participants INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'upcoming',
                    winners JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tournament participants table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tournament_participants (
                    id SERIAL PRIMARY KEY,
                    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    score INTEGER DEFAULT 0,
                    rank INTEGER,
                    joined_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(tournament_id, telegram_id)
                )
            """)
            
            # Notifications table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50) DEFAULT 'info',
                    is_read BOOLEAN DEFAULT FALSE,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    read_at TIMESTAMP
                )
            """)
            
            # Audit logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT,
                    action VARCHAR(100) NOT NULL,
                    entity_type VARCHAR(50),
                    entity_id VARCHAR(100),
                    old_value JSONB,
                    new_value JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Insert default game settings
            await conn.execute("""
                INSERT INTO game_settings (key, value, value_type, description, is_public) VALUES 
                    ('win_percentage', '75', 'integer', 'Current game win percentage (70,75,76,80)', TRUE),
                    ('default_sound_pack', 'pack1', 'string', 'Default sound pack for new players', TRUE),
                    ('selection_time', '50', 'integer', 'Cartela selection time in seconds', FALSE),
                    ('draw_interval', '4000', 'integer', 'Number draw interval in milliseconds', FALSE),
                    ('next_round_delay', '6000', 'integer', 'Delay between rounds in milliseconds', FALSE),
                    ('bet_amount', '10', 'integer', 'Cost per cartela in ETB', TRUE),
                    ('max_cartelas', '4', 'integer', 'Maximum cartelas per player per round', TRUE),
                    ('total_cartelas', '75', 'integer', 'Total available cartela types', FALSE),
                    ('min_deposit', '10', 'integer', 'Minimum deposit amount', TRUE),
                    ('max_deposit', '100000', 'integer', 'Maximum deposit amount', TRUE),
                    ('min_withdrawal', '50', 'integer', 'Minimum withdrawal amount', TRUE),
                    ('max_withdrawal', '10000', 'integer', 'Maximum withdrawal amount', TRUE),
                    ('welcome_bonus', '30', 'integer', 'Welcome bonus amount', TRUE),
                    ('referral_bonus', '10', 'integer', 'Referral bonus amount', TRUE),
                    ('daily_bonus', '5', 'integer', 'Daily login bonus', TRUE),
                    ('maintenance_mode', 'false', 'boolean', 'Maintenance mode status', TRUE),
                    ('game_enabled', 'true', 'boolean', 'Game enabled status', TRUE)
                ON CONFLICT (key) DO NOTHING
            """)
            
        logger.info("✅ Database tables ready")

    @classmethod
    async def _ensure_columns(cls):
        """Ensure all required columns exist in users table"""
        async with cls._pool.acquire() as conn:
            columns = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """)
            column_names = [col['column_name'] for col in columns]
            
            required_columns = {
                'referral_code': 'TEXT UNIQUE',
                'referred_by': 'BIGINT',
                'total_withdrawn': 'DECIMAL(12,2) DEFAULT 0',
                'total_won': 'DECIMAL(12,2) DEFAULT 0',
                'games_played': 'INTEGER DEFAULT 0',
                'games_won': 'INTEGER DEFAULT 0',
                'games_lost': 'INTEGER DEFAULT 0',
                'current_streak': 'INTEGER DEFAULT 0',
                'best_streak': 'INTEGER DEFAULT 0',
                'highest_win': 'DECIMAL(12,2) DEFAULT 0',
                'total_bet': 'DECIMAL(12,2) DEFAULT 0',
                'total_refund': 'DECIMAL(12,2) DEFAULT 0',
                'total_bonus': 'DECIMAL(12,2) DEFAULT 0',
                'games_drawn': 'INTEGER DEFAULT 0',
                'worst_streak': 'INTEGER DEFAULT 0',
                'total_cartelas_bought': 'INTEGER DEFAULT 0',
                'email': 'VARCHAR(255)',
                'is_verified': 'BOOLEAN DEFAULT FALSE',
                'verified_at': 'TIMESTAMP',
                'login_attempts': 'INTEGER DEFAULT 0',
                'locked_until': 'TIMESTAMP',
                'two_factor_enabled': 'BOOLEAN DEFAULT FALSE',
                'two_factor_secret': 'TEXT',
                'last_bonus_at': 'TIMESTAMP',
                'notification_preferences': 'JSONB DEFAULT \'{}\'',
                'metadata': 'JSONB DEFAULT \'{}\''
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in column_names:
                    try:
                        await conn.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                        logger.info(f"✅ Added missing column: {col_name}")
                    except Exception as e:
                        logger.warning(f"Could not add column {col_name}: {e}")

    @classmethod
    async def _create_all_indexes(cls):
        """Create all database indexes for performance"""
        async with cls._pool.acquire() as conn:
            # Users table indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_registered ON users(registered)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_lang ON users(lang)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_total_won ON users(total_won DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_games_played ON users(games_played DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)")
            
            # Composite indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_registered_balance ON users(registered, balance DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_active_balance ON users(is_active, balance DESC) WHERE is_active = TRUE")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen_active ON users(last_seen DESC) WHERE is_active = TRUE")
            
            # Withdrawals indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON pending_withdrawals(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram ON pending_withdrawals(telegram_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_pending ON pending_withdrawals(status, requested_at) WHERE status = 'pending'")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_method ON pending_withdrawals(method)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_requested_at ON pending_withdrawals(requested_at DESC)")
            
            # OTP indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes(expires_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_telegram ON otp_codes(telegram_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_purpose ON otp_codes(purpose)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_telegram_purpose ON otp_codes(telegram_id, purpose)")
            
            # Auth codes indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_expires ON auth_codes(expires_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_code ON auth_codes(code)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_telegram ON auth_codes(telegram_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_used ON auth_codes(used)")
            
            # Game transactions indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram ON game_transactions(telegram_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_timestamp ON game_transactions(created_at DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_type ON game_transactions(type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram_type ON game_transactions(telegram_id, type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_round ON game_transactions(round)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_transaction_id ON game_transactions(transaction_id)")
            
            # Game rounds indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_rounds_timestamp ON game_rounds(timestamp DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_rounds_number ON game_rounds(round_number DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_rounds_win_percentage ON game_rounds(win_percentage)")
            
            # Commission logs indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_commission_logs_changed_at ON commission_logs(changed_at DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_commission_logs_changed_by ON commission_logs(changed_by)")
            
            # Bonus logs indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_bonus_logs_telegram ON bonus_logs(telegram_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_bonus_logs_created_at ON bonus_logs(created_at DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_bonus_logs_type ON bonus_logs(bonus_type)")
            
            # Notifications indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_telegram ON notifications(telegram_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC)")
            
            # Audit logs indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id)")
            
            # Full-text search indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_search_gin ON users USING gin(
                    to_tsvector('english', COALESCE(username, '') || ' ' || 
                                COALESCE(first_name, '') || ' ' || 
                                COALESCE(last_name, '') || ' ' || 
                                COALESCE(phone, ''))
                )
            """)
            
        logger.info("✅ All indexes created")

    @classmethod
    async def _create_all_views(cls):
        """Create all database views for easy querying"""
        async with cls._pool.acquire() as conn:
            # Active users view
            await conn.execute("""
                CREATE OR REPLACE VIEW active_users AS
                SELECT 
                    telegram_id, username, first_name, last_name,
                    phone, balance, total_deposited, total_won,
                    games_played, games_won,
                    CASE 
                        WHEN games_played > 0 THEN ROUND((games_won::DECIMAL / games_played) * 100, 2)
                        ELSE 0
                    END as win_rate,
                    last_seen, created_at
                FROM users
                WHERE is_active = TRUE AND is_banned = FALSE AND registered = TRUE
            """)
            
            # Leaderboard view
            await conn.execute("""
                CREATE OR REPLACE VIEW leaderboard AS
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY total_won DESC) as rank,
                    telegram_id, username, first_name, last_name,
                    total_won, games_played, games_won,
                    CASE 
                        WHEN games_played > 0 THEN ROUND((games_won::DECIMAL / games_played) * 100, 2)
                        ELSE 0
                    END as win_rate,
                    highest_win, best_streak, balance
                FROM users
                WHERE registered = TRUE AND is_active = TRUE AND total_won > 0
                ORDER BY total_won DESC
            """)
            
            # Daily stats view
            await conn.execute("""
                CREATE OR REPLACE VIEW daily_stats AS
                SELECT 
                    DATE(created_at) as date,
                    COUNT(DISTINCT telegram_id) as unique_users,
                    COUNT(*) as total_transactions,
                    SUM(CASE WHEN type = 'deposit' THEN amount ELSE 0 END) as total_deposits,
                    SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as total_withdrawals,
                    SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END) as total_wins,
                    SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END) as total_bets
                FROM game_transactions
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            # Pending withdrawals summary view
            await conn.execute("""
                CREATE OR REPLACE VIEW pending_withdrawals_summary AS
                SELECT 
                    COUNT(*) as total_pending,
                    COALESCE(SUM(amount), 0) as total_amount_pending,
                    MIN(requested_at) as oldest_request,
                    MAX(requested_at) as newest_request,
                    AVG(amount) as avg_amount
                FROM pending_withdrawals
                WHERE status = 'pending'
            """)
            
            # User financial summary view
            await conn.execute("""
                CREATE OR REPLACE VIEW user_financial_summary AS
                SELECT 
                    u.telegram_id, u.username,
                    u.balance,
                    u.total_deposited,
                    u.total_withdrawn,
                    u.total_won,
                    u.total_bet,
                    (u.total_won - u.total_bet) as net_profit,
                    COALESCE(w.pending_count, 0) as pending_withdrawals,
                    COALESCE(w.pending_amount, 0) as pending_withdrawal_amount
                FROM users u
                LEFT JOIN (
                    SELECT telegram_id, 
                           COUNT(*) as pending_count,
                           SUM(amount) as pending_amount
                    FROM pending_withdrawals
                    WHERE status = 'pending'
                    GROUP BY telegram_id
                ) w ON u.telegram_id = w.telegram_id
                WHERE u.registered = TRUE
            """)
            
        logger.info("✅ All views created")

    @classmethod
    async def _create_all_functions(cls):
        """Create all database functions"""
        async with cls._pool.acquire() as conn:
            # Update updated_at function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)
            
            # Update last_seen function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_last_seen()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.last_seen = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)
            
            # Calculate win rate function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION calculate_win_rate(user_id BIGINT)
                RETURNS DECIMAL(5,2) AS $$
                DECLARE
                    win_rate DECIMAL(5,2);
                BEGIN
                    SELECT CASE 
                        WHEN games_played > 0 THEN (games_won::DECIMAL / games_played) * 100
                        ELSE 0
                    END INTO win_rate
                    FROM users
                    WHERE telegram_id = user_id;
                    
                    RETURN COALESCE(win_rate, 0);
                END;
                $$ LANGUAGE plpgsql STABLE
            """)
            
            # Generate transaction ID function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION generate_transaction_id()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.transaction_id := 'TXN-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('transaction_id_seq')::TEXT, 8, '0');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)
            
            # Generate withdrawal ID function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION generate_withdrawal_id()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.withdrawal_id := 'WDL-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('withdrawal_id_seq')::TEXT, 6, '0');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)
            
            # Clean expired OTPs function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION clean_expired_otps()
                RETURNS INTEGER AS $$
                DECLARE
                    deleted_count INTEGER;
                BEGIN
                    DELETE FROM otp_codes 
                    WHERE expires_at < NOW() OR is_used = TRUE
                    RETURNING COUNT(*) INTO deleted_count;
                    
                    RETURN deleted_count;
                END;
                $$ LANGUAGE plpgsql
            """)
            
            # Get total commission function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION get_total_commission()
                RETURNS DECIMAL(12,2) AS $$
                DECLARE
                    total DECIMAL(12,2);
                BEGIN
                    SELECT COALESCE(SUM(admin_commission), 0) INTO total
                    FROM game_rounds;
                    
                    RETURN total;
                END;
                $$ LANGUAGE plpgsql STABLE
            """)
            
        logger.info("✅ All functions created")

    @classmethod
    async def _create_all_triggers(cls):
        """Create all database triggers"""
        async with cls._pool.acquire() as conn:
            # Users updated_at trigger
            await conn.execute("""
                DROP TRIGGER IF EXISTS trigger_users_updated_at ON users;
                CREATE TRIGGER trigger_users_updated_at
                    BEFORE UPDATE ON users
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at()
            """)
            
            # Users last_seen trigger
            await conn.execute("""
                DROP TRIGGER IF EXISTS trigger_users_last_seen ON users;
                CREATE TRIGGER trigger_users_last_seen
                    BEFORE UPDATE ON users
                    FOR EACH ROW
                    EXECUTE FUNCTION update_last_seen()
            """)
            
        logger.info("✅ All triggers created")

    @classmethod
    async def _run_migrations(cls):
        """Run pending migrations"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    executed_at TIMESTAMP DEFAULT NOW(),
                    duration_ms INTEGER,
                    checksum VARCHAR(64)
                )
            """)
            
            migrations = [
                "001_initial_schema.sql",
                "002_add_referral_system.sql",
                "003_add_tournaments.sql",
                "004_add_notifications.sql",
                "005_add_audit_logs.sql",
                "006_add_bonus_system.sql"
            ]
            
            for migration in migrations:
                # Check if migration already executed
                exists = await conn.fetchval("SELECT 1 FROM migrations WHERE name = $1", migration)
                if not exists:
                    logger.info(f"Migration {migration} would be applied if file exists")
                    
        logger.info("✅ Migrations check completed")

    # ==================== USER OPERATIONS ====================
    
    @classmethod
    @log_query
    async def get_user(cls, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            return dict(row) if row else None

    @classmethod
    @log_query
    async def get_user_by_phone(cls, phone: str) -> Optional[Dict]:
        """Get user by phone number"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE phone = $1", phone)
            return dict(row) if row else None

    @classmethod
    @log_query
    async def get_user_by_username(cls, username: str) -> Optional[Dict]:
        """Get user by username"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE username ILIKE $1", username)
            return dict(row) if row else None

    @classmethod
    @log_query
    async def get_user_by_email(cls, email: str) -> Optional[Dict]:
        """Get user by email"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            return dict(row) if row else None

    @classmethod
    @log_query
    async def get_user_by_referral_code(cls, referral_code: str) -> Optional[Dict]:
        """Get user by referral code"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE referral_code = $1", referral_code)
            return dict(row) if row else None

    @classmethod
    @log_query
    async def create_user(cls, telegram_id: int, username: str, 
                          first_name: str, last_name: str, 
                          phone: str, lang: str = "en") -> None:
        """Create a new user"""
        async with cls._pool.acquire() as conn:
            # Generate unique referral code
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            while await conn.fetchval("SELECT 1 FROM users WHERE referral_code = $1", referral_code):
                referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            await conn.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, 
                                   phone, registered, lang, referral_code, created_at)
                VALUES ($1, $2, $3, $4, $5, TRUE, $6, $7, NOW())
            """, telegram_id, username, first_name, last_name, phone, lang, referral_code)
            
            # Add welcome bonus
            welcome_bonus = await cls.get_setting_int('welcome_bonus', 30)
            if welcome_bonus > 0:
                await cls.add_balance(telegram_id, welcome_bonus, "welcome_bonus")
                
                await cls.log_bonus(
                    telegram_id=telegram_id,
                    bonus_type="welcome",
                    amount=welcome_bonus,
                    reason="Welcome bonus for new user"
                )
            
            # Log user creation
            await cls.log_audit(
                user_id=telegram_id,
                action="user_created",
                entity_type="user",
                entity_id=str(telegram_id),
                new_value={"username": username, "phone": phone}
            )

    @classmethod
    @log_query
    async def update_user(cls, telegram_id: int, **kwargs) -> None:
        """Update user fields"""
        if not kwargs:
            return
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        values = [telegram_id] + list(kwargs.values())
        async with cls._pool.acquire() as conn:
            await conn.execute(f"UPDATE users SET {set_clause} WHERE telegram_id = $1", *values)
            
            # Log significant updates
            significant_fields = ['balance', 'total_deposited', 'total_withdrawn', 'is_banned', 'is_active']
            if any(field in kwargs for field in significant_fields):
                await cls.log_audit(
                    user_id=telegram_id,
                    action="user_updated",
                    entity_type="user",
                    entity_id=str(telegram_id),
                    new_value=kwargs
                )

    @classmethod
    @log_query
    async def update_last_seen(cls, telegram_id: int) -> None:
        """Update user's last seen timestamp"""
        async with cls._pool.acquire() as conn:
            await conn.execute("UPDATE users SET last_seen = NOW() WHERE telegram_id = $1", telegram_id)

    @classmethod
    @log_query
    async def update_user_preferences(cls, telegram_id: int, preferences: Dict) -> None:
        """Update user preferences"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                UPDATE users 
                SET notification_preferences = $2, updated_at = NOW()
                WHERE telegram_id = $1
            """, telegram_id, json.dumps(preferences))

    @classmethod
    @log_query
    async def search_users(cls, search_term: str, limit: int = 20) -> List[Dict]:
        """Search users by name, username, or phone"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT telegram_id, username, first_name, last_name, phone, balance, 
                       total_deposited, total_won, games_played, games_won, created_at
                FROM users
                WHERE username ILIKE $1 
                   OR first_name ILIKE $1 
                   OR last_name ILIKE $1 
                   OR phone ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
            """, f'%{search_term}%', limit)
            return [dict(row) for row in rows]

    # ==================== BALANCE OPERATIONS ====================
    
    @classmethod
    @log_query
    @retry_on_failure(max_retries=3, delay=0.5)
    async def add_balance(cls, telegram_id: int, amount: float, reason: str = None) -> float:
        """Add balance to user with transaction logging"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("""
                    SELECT balance, total_deposited, total_won, total_bonus 
                    FROM users WHERE telegram_id = $1 FOR UPDATE
                """, telegram_id)
                if not user:
                    raise ValueError("User not found")
                
                current_balance = float(user["balance"]) if user["balance"] else 0.0
                new_balance = current_balance + amount
                
                await conn.execute("UPDATE users SET balance = $1 WHERE telegram_id = $2", new_balance, telegram_id)
                
                # Update appropriate totals based on reason
                if amount > 0:
                    if reason in ("deposit", "deposit_approval", "auto_deposit"):
                        new_total = float(user["total_deposited"] or 0) + amount
                        await conn.execute("UPDATE users SET total_deposited = $1 WHERE telegram_id = $2", new_total, telegram_id)
                    elif reason == "win":
                        new_total = float(user["total_won"] or 0) + amount
                        await conn.execute("UPDATE users SET total_won = $1 WHERE telegram_id = $2", new_total, telegram_id)
                    elif reason in ("welcome_bonus", "daily_bonus", "referral_bonus"):
                        new_total = float(user["total_bonus"] or 0) + amount
                        await conn.execute("UPDATE users SET total_bonus = $1 WHERE telegram_id = $2", new_total, telegram_id)
                
                # Log transaction
                transaction_id = await cls.log_game_transaction(
                    telegram_id=telegram_id,
                    username=None,
                    transaction_type="add_balance",
                    amount=amount,
                    note=reason,
                    metadata={"balance_before": current_balance, "balance_after": new_balance}
                )
                
                return new_balance

    @classmethod
    @log_query
    @retry_on_failure(max_retries=3, delay=0.5)
    async def deduct_balance(cls, telegram_id: int, amount: float, reason: str = None) -> float:
        """Deduct balance from user with transaction logging"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT balance FROM users WHERE telegram_id = $1 FOR UPDATE", telegram_id)
                if not user:
                    raise ValueError("User not found")
                
                current_balance = float(user["balance"]) if user["balance"] else 0.0
                if current_balance < amount:
                    raise ValueError(f"Insufficient balance: {current_balance} < {amount}")
                
                new_balance = current_balance - amount
                await conn.execute("UPDATE users SET balance = $1 WHERE telegram_id = $2", new_balance, telegram_id)
                
                # Update games_played for cartela purchases
                if reason == "cartela_purchase":
                    await conn.execute("""
                        UPDATE users SET games_played = games_played + 1, 
                                          total_bet = total_bet + $1,
                                          total_cartelas_bought = total_cartelas_bought + 1
                        WHERE telegram_id = $2
                    """, amount, telegram_id)
                
                # Update total_withdrawn for cashouts
                if reason == "cashout":
                    await conn.execute("""
                        UPDATE users SET total_withdrawn = total_withdrawn + $1 
                        WHERE telegram_id = $2
                    """, amount, telegram_id)
                
                # Update streak for losses
                if reason == "cartela_purchase":
                    await conn.execute("""
                        UPDATE users SET current_streak = -1 * (ABS(current_streak) + 1)
                        WHERE telegram_id = $1
                    """, telegram_id)
                
                # Log transaction
                await cls.log_game_transaction(
                    telegram_id=telegram_id,
                    username=None,
                    transaction_type="deduct_balance",
                    amount=-amount,
                    note=reason,
                    metadata={"balance_before": current_balance, "balance_after": new_balance}
                )
                
                return new_balance

    @classmethod
    @log_query
    async def get_balance(cls, telegram_id: int) -> float:
        """Get user's current balance"""
        user = await cls.get_user(telegram_id)
        if user and user.get("balance"):
            return float(user["balance"])
        return 0.0

    @classmethod
    @log_query
    async def transfer_balance(cls, from_id: int, to_id: int, amount: float, reason: str = "transfer") -> Tuple[bool, str]:
        """Transfer balance between users"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                # Check sender balance
                sender = await conn.fetchrow("SELECT balance FROM users WHERE telegram_id = $1 FOR UPDATE", from_id)
                if not sender:
                    return False, "Sender not found"
                
                sender_balance = float(sender["balance"]) if sender["balance"] else 0.0
                if sender_balance < amount:
                    return False, f"Insufficient balance: {sender_balance:.2f} ETB"
                
                # Check receiver exists
                receiver = await conn.fetchrow("SELECT balance FROM users WHERE telegram_id = $1 FOR UPDATE", to_id)
                if not receiver:
                    return False, "Receiver not found"
                
                # Perform transfer
                new_sender_balance = sender_balance - amount
                new_receiver_balance = float(receiver["balance"] or 0) + amount
                
                await conn.execute("UPDATE users SET balance = $1 WHERE telegram_id = $2", new_sender_balance, from_id)
                await conn.execute("UPDATE users SET balance = $1 WHERE telegram_id = $2", new_receiver_balance, to_id)
                
                # Log transactions
                await cls.log_game_transaction(from_id, None, "transfer_out", -amount, note=f"Transfer to {to_id}: {reason}")
                await cls.log_game_transaction(to_id, None, "transfer_in", amount, note=f"Transfer from {from_id}: {reason}")
                
                return True, "Transfer successful"

    # ==================== AUTH CODE OPERATIONS ====================
    
    @classmethod
    @log_query
    async def create_auth_code(cls, telegram_id: int, purpose: str = "game_access", max_uses: int = 1) -> str:
        """Create one-time authentication code for game access"""
        code = secrets.token_urlsafe(16)
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO auth_codes (code, telegram_id, purpose, expires_at, max_uses, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
            """, code, telegram_id, purpose, expires_at, max_uses)
        
        return code

    @classmethod
    @log_query
    async def verify_auth_code(cls, code: str) -> Optional[int]:
        """Verify auth code and return telegram_id if valid"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, telegram_id, max_uses, use_count 
                FROM auth_codes 
                WHERE code = $1 AND expires_at > NOW() AND used = FALSE
            """, code)
            
            if row:
                # Update usage
                new_use_count = row["use_count"] + 1
                is_used = new_use_count >= row["max_uses"]
                
                await conn.execute("""
                    UPDATE auth_codes 
                    SET use_count = $1, used = $2, used_at = NOW()
                    WHERE id = $3
                """, new_use_count, is_used, row["id"])
                
                return row["telegram_id"]
        
        return None

    @classmethod
    @log_query
    async def consume_auth_code(cls, code: str) -> Optional[int]:
        """Consume auth code and return telegram_id if valid"""
        return await cls.verify_auth_code(code)

    @classmethod
    @log_query
    async def revoke_auth_code(cls, code: str) -> bool:
        """Revoke an auth code"""
        async with cls._pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE auth_codes 
                SET used = TRUE, used_at = NOW()
                WHERE code = $1 AND used = FALSE
            """, code)
            return result == "UPDATE 1"

    # ==================== OTP OPERATIONS ====================
    
    @classmethod
    @log_query
    async def store_otp(cls, telegram_id: int, otp: str, purpose: str = "login") -> bool:
        """Store OTP code for user with rate limiting"""
        # Check rate limit (max 3 OTPs in 5 minutes)
        async with cls._pool.acquire() as conn:
            recent_count = await conn.fetchval("""
                SELECT COUNT(*) FROM otp_codes 
                WHERE telegram_id = $1 AND created_at > NOW() - INTERVAL '5 minutes'
            """, telegram_id)
            
            if recent_count >= 3:
                logger.warning(f"Rate limit exceeded for user {telegram_id}")
                return False
            
            expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
            otp_hash = hashlib.sha256(f"{otp}:{API_SECRET}".encode()).hexdigest()
            
            await conn.execute("""
                INSERT INTO otp_codes (telegram_id, otp_hash, purpose, expires_at, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (telegram_id, purpose) DO UPDATE
                SET otp_hash = EXCLUDED.otp_hash, 
                    expires_at = EXCLUDED.expires_at, 
                    attempts = 0,
                    created_at = NOW()
            """, telegram_id, otp_hash, purpose, expires_at)
            
            return True

    @classmethod
    @log_query
    async def verify_otp(cls, telegram_id: int, otp: str, purpose: str = "login") -> bool:
        """Verify OTP code (one-time use)"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, otp_hash, expires_at, attempts, max_attempts, is_blocked, blocked_until
                FROM otp_codes 
                WHERE telegram_id = $1 AND purpose = $2 AND is_used = FALSE
                ORDER BY created_at DESC LIMIT 1
            """, telegram_id, purpose)
            
            if not row:
                return False
            
            # Check if blocked
            if row["is_blocked"] and row["blocked_until"] > datetime.utcnow():
                logger.warning(f"OTP blocked for user {telegram_id} until {row['blocked_until']}")
                return False
            
            # Check expiration
            if row["expires_at"] < datetime.utcnow():
                await conn.execute("DELETE FROM otp_codes WHERE id = $1", row["id"])
                return False
            
            # Check attempts
            if row["attempts"] >= row["max_attempts"]:
                await conn.execute("""
                    UPDATE otp_codes 
                    SET is_blocked = TRUE, blocked_until = NOW() + INTERVAL '15 minutes'
                    WHERE id = $1
                """, row["id"])
                return False
            
            # Verify OTP
            expected_hash = hashlib.sha256(f"{otp}:{API_SECRET}".encode()).hexdigest()
            
            if row["otp_hash"] != expected_hash:
                await conn.execute("""
                    UPDATE otp_codes SET attempts = attempts + 1 WHERE id = $1
                """, row["id"])
                return False
            
            # Mark as used
            await conn.execute("""
                UPDATE otp_codes 
                SET is_used = TRUE, used_at = NOW()
                WHERE id = $1
            """, row["id"])
            
            return True

    # ==================== WITHDRAWAL OPERATIONS ====================
    
    @classmethod
    @log_query
    async def add_pending_withdrawal(cls, telegram_id: int, amount: float,
                                      account: str, method: str) -> int:
        """Add pending withdrawal request"""
        async with cls._pool.acquire() as conn:
            # Check for existing pending withdrawals
            existing = await conn.fetchval("""
                SELECT COUNT(*) FROM pending_withdrawals 
                WHERE telegram_id = $1 AND status = 'pending'
            """, telegram_id)
            
            if existing >= 3:
                raise ValueError("Maximum 3 pending withdrawals allowed")
            
            row = await conn.fetchrow("""
                INSERT INTO pending_withdrawals (telegram_id, amount, account, method, requested_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id
            """, telegram_id, amount, account, method)
            
            # Log the withdrawal request
            await cls.log_audit(
                user_id=telegram_id,
                action="withdrawal_requested",
                entity_type="withdrawal",
                entity_id=str(row["id"]),
                new_value={"amount": amount, "method": method, "account": account}
            )
            
            return row["id"]

    @classmethod
    @log_query
    async def get_pending_withdrawals(cls, telegram_id: int = None) -> List[Dict]:
        """Get pending withdrawal requests"""
        async with cls._pool.acquire() as conn:
            if telegram_id:
                rows = await conn.fetch("""
                    SELECT * FROM pending_withdrawals 
                    WHERE telegram_id = $1 AND status = 'pending' 
                    ORDER BY requested_at DESC
                """, telegram_id)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM pending_withdrawals 
                    WHERE status = 'pending' 
                    ORDER BY requested_at ASC
                """)
            return [dict(r) for r in rows]

    @classmethod
    @log_query
    async def get_withdrawal_by_id(cls, withdrawal_id: int) -> Optional[Dict]:
        """Get withdrawal by ID"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM pending_withdrawals WHERE id = $1", withdrawal_id)
            return dict(row) if row else None

    @classmethod
    @log_query
    async def approve_withdrawal(cls, withdrawal_id: int, processed_by: str = "admin") -> Optional[Tuple[int, float]]:
        """Approve withdrawal and deduct balance"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                withdrawal = await conn.fetchrow("""
                    SELECT telegram_id, amount FROM pending_withdrawals 
                    WHERE id = $1 AND status = 'pending'
                """, withdrawal_id)
                
                if not withdrawal:
                    logger.warning(f"Withdrawal {withdrawal_id} not found or already processed")
                    return None
                
                telegram_id = withdrawal["telegram_id"]
                amount = float(withdrawal["amount"]) if withdrawal["amount"] else 0.0
                
                try:
                    new_balance = await cls.deduct_balance(telegram_id, amount, "cashout")
                except ValueError as e:
                    logger.error(f"Balance deduction failed for withdrawal {withdrawal_id}: {e}")
                    return None
                
                await conn.execute("""
                    UPDATE pending_withdrawals 
                    SET status = 'approved', processed_at = NOW(), approved_at = NOW(), 
                        processed_by = $2
                    WHERE id = $1
                """, withdrawal_id, processed_by)
                
                # Log approval
                await cls.log_audit(
                    user_id=telegram_id,
                    action="withdrawal_approved",
                    entity_type="withdrawal",
                    entity_id=str(withdrawal_id),
                    new_value={"amount": amount, "processed_by": processed_by}
                )
                
                return telegram_id, amount

    @classmethod
    @log_query
    async def reject_withdrawal(cls, withdrawal_id: int, reason: str = None, processed_by: str = "admin") -> None:
        """Reject withdrawal request"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                UPDATE pending_withdrawals 
                SET status = 'rejected', processed_at = NOW(), rejected_at = NOW(), 
                    rejection_reason = $2, processed_by = $3
                WHERE id = $1
            """, withdrawal_id, reason, processed_by)
            
            # Get telegram_id for audit
            withdrawal = await conn.fetchrow("SELECT telegram_id FROM pending_withdrawals WHERE id = $1", withdrawal_id)
            if withdrawal:
                await cls.log_audit(
                    user_id=withdrawal["telegram_id"],
                    action="withdrawal_rejected",
                    entity_type="withdrawal",
                    entity_id=str(withdrawal_id),
                    new_value={"reason": reason, "processed_by": processed_by}
                )

    # ==================== SETTINGS OPERATIONS ====================
    
    @classmethod
    @log_query
    async def get_setting(cls, key: str) -> Optional[str]:
        """Get setting value by key"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM game_settings WHERE key = $1", key)
            return row["value"] if row else None

    @classmethod
    @log_query
    async def get_setting_int(cls, key: str, default: int = 0) -> int:
        """Get integer setting value"""
        value = await cls.get_setting(key)
        return int(value) if value else default

    @classmethod
    @log_query
    async def get_setting_bool(cls, key: str, default: bool = False) -> bool:
        """Get boolean setting value"""
        value = await cls.get_setting(key)
        return value.lower() == "true" if value else default

    @classmethod
    @log_query
    async def set_setting(cls, key: str, value: str, updated_by: str = "system") -> None:
        """Set setting value"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO game_settings (key, value, updated_at, updated_by) 
                VALUES ($1, $2, NOW(), $3)
                ON CONFLICT (key) DO UPDATE 
                SET value = EXCLUDED.value, updated_at = NOW(), updated_by = EXCLUDED.updated_by
            """, key, value, updated_by)

    @classmethod
    @log_query
    async def get_win_percentage(cls) -> int:
        """Get current win percentage"""
        value = await cls.get_setting('win_percentage')
        return int(value) if value else 75

    @classmethod
    @log_query
    async def set_win_percentage(cls, percentage: int, changed_by: str = "admin") -> None:
        """Set win percentage with logging"""
        old_percentage = await cls.get_win_percentage()
        await cls.set_setting('win_percentage', str(percentage), changed_by)
        
        # Log commission change
        await cls.log_commission_change(old_percentage, percentage, changed_by)

    @classmethod
    @log_query
    async def get_default_sound_pack(cls) -> str:
        """Get default sound pack for new players"""
        value = await cls.get_setting('default_sound_pack')
        return value if value else 'pack1'

    @classmethod
    @log_query
    async def set_default_sound_pack(cls, sound_pack: str) -> None:
        """Set default sound pack for new players"""
        await cls.set_setting('default_sound_pack', sound_pack)

    # ==================== COMMISSION LOGS ====================
    
    @classmethod
    @log_query
    async def log_commission_change(cls, old_percentage: int, new_percentage: int, 
                                     changed_by: str = "API", changed_by_id: int = None) -> None:
        """Log commission change to database"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO commission_logs (old_percentage, new_percentage, changed_by, changed_by_id, changed_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, old_percentage, new_percentage, changed_by, changed_by_id)

    @classmethod
    @log_query
    async def get_commission_history(cls, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get commission change history"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, old_percentage, new_percentage, changed_by, changed_at
                FROM commission_logs
                ORDER BY changed_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)
            return [dict(r) for r in rows]

    @classmethod
    @log_query
    async def get_commission_stats(cls) -> Dict:
        """Get commission statistics"""
        async with cls._pool.acquire() as conn:
            total_commission = await conn.fetchval("""
                SELECT COALESCE(SUM(admin_commission), 0) FROM game_rounds
            """)
            avg_win_percentage = await conn.fetchval("""
                SELECT COALESCE(AVG(win_percentage), 0) FROM game_rounds
            """)
            changes_count = await conn.fetchval("SELECT COUNT(*) FROM commission_logs")
            last_change = await conn.fetchval("SELECT MAX(changed_at) FROM commission_logs")
            
            return {
                "total_commission": float(total_commission) if total_commission else 0,
                "average_win_percentage": float(avg_win_percentage) if avg_win_percentage else 0,
                "changes_count": changes_count or 0,
                "last_change": last_change.isoformat() if last_change else None
            }

    # ==================== SEARCH OPERATIONS ====================
    
    @classmethod
    @log_query
    async def search_players(cls, search_term: str, limit: int = 50) -> List[Dict]:
        """Search players by username or phone"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT telegram_id, username, first_name, last_name, phone, 
                       balance, total_deposited, total_won, games_played, games_won,
                       created_at, last_seen
                FROM users 
                WHERE username ILIKE $1 OR phone ILIKE $1 OR first_name ILIKE $1 OR last_name ILIKE $1
                ORDER BY balance DESC
                LIMIT $2
            """, f'%{search_term}%', limit)
            return [dict(r) for r in rows]

    @classmethod
    @log_query
    async def search_players_fulltext(cls, search_term: str, limit: int = 50) -> List[Dict]:
        """Search players using full-text search"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT telegram_id, username, first_name, last_name, phone,
                       balance, total_deposited, total_won,
                       ts_rank(search_vector, plainto_tsquery('english', $1)) as relevance
                FROM users, plainto_tsquery('english', $1) as query
                WHERE search_vector @@ query
                ORDER BY relevance DESC
                LIMIT $2
            """, search_term, limit)
            return [dict(r) for r in rows]

    # ==================== GAME TRANSACTIONS ====================
    
    @classmethod
    @log_query
    async def log_game_transaction(cls, telegram_id: int, username: str = None, 
                                    transaction_type: str = None, amount: float = 0,
                                    cartela: str = None, round_num: int = None,
                                    note: str = None, metadata: Dict = None) -> int:
        """Log a game transaction"""
        async with cls._pool.acquire() as conn:
            # Get balance before
            balance_before = await cls.get_balance(telegram_id)
            
            row = await conn.fetchrow("""
                INSERT INTO game_transactions (telegram_id, username, type, amount, 
                                               balance_before, cartela, round, note, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                RETURNING id
            """, telegram_id, username, transaction_type, amount, balance_before, 
                cartela, round_num, note, json.dumps(metadata) if metadata else None)
            
            return row["id"] if row else 0

    @classmethod
    @log_query
    async def get_user_transactions(cls, telegram_id: int, limit: int = 50, 
                                     offset: int = 0, transaction_type: str = None) -> List[Dict]:
        """Get user's transaction history with optional type filter"""
        async with cls._pool.acquire() as conn:
            if transaction_type:
                rows = await conn.fetch("""
                    SELECT * FROM game_transactions 
                    WHERE telegram_id = $1 AND type = $2
                    ORDER BY created_at DESC 
                    LIMIT $3 OFFSET $4
                """, telegram_id, transaction_type, limit, offset)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM game_transactions 
                    WHERE telegram_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2 OFFSET $3
                """, telegram_id, limit, offset)
            return [dict(r) for r in rows]

    @classmethod
    @log_query
    async def get_transaction_by_id(cls, transaction_id: int) -> Optional[Dict]:
        """Get transaction by ID"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM game_transactions WHERE id = $1", transaction_id)
            return dict(row) if row else None

    # ==================== GAME ROUNDS ====================
    
    @classmethod
    @log_query
    async def save_game_round(cls, round_data: Dict) -> int:
        """Save game round result"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO game_rounds (
                    round_number, total_players, total_cartelas, total_pool,
                    winner_reward, admin_commission, winners, winner_cartelas,
                    win_percentage, drawn_numbers, duration_ms, started_at, ended_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING round_id
            """,
                round_data.get('round_number'),
                round_data.get('total_players', 0),
                round_data.get('total_cartelas', 0),
                round_data.get('total_pool', 0),
                round_data.get('winner_reward', 0),
                round_data.get('admin_commission', 0),
                json.dumps(round_data.get('winners', [])),
                json.dumps(round_data.get('winner_cartelas', [])),
                round_data.get('win_percentage', 80),
                round_data.get('drawn_numbers', []),
                round_data.get('duration_ms'),
                round_data.get('started_at'),
                round_data.get('ended_at', datetime.utcnow())
            )
            return row["round_id"]

    @classmethod
    @log_query
    async def get_game_rounds(cls, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get recent game rounds"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM game_rounds 
                ORDER BY round_id DESC 
                LIMIT $1 OFFSET $2
            """, limit, offset)
            return [dict(r) for r in rows]

    @classmethod
    @log_query
    async def get_round_stats(cls) -> Dict:
        """Get overall round statistics"""
        async with cls._pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_rounds,
                    COALESCE(SUM(total_pool), 0) as total_pool,
                    COALESCE(SUM(winner_reward), 0) as total_payout,
                    COALESCE(SUM(admin_commission), 0) as total_commission,
                    AVG(win_percentage) as avg_win_percentage,
                    AVG(total_players) as avg_players_per_round,
                    AVG(total_cartelas) as avg_cartelas_per_round,
                    MAX(total_pool) as max_pool,
                    MAX(winner_reward) as max_payout
                FROM game_rounds
            """)
            return dict(stats) if stats else {}

    # ==================== BONUS SYSTEM ====================
    
    @classmethod
    @log_query
    async def log_bonus(cls, telegram_id: int, bonus_type: str, amount: float, 
                        reason: str = None, expires_at: datetime = None) -> int:
        """Log a bonus given to user"""
        async with cls._pool.acquire() as conn:
            balance_before = await cls.get_balance(telegram_id)
            
            row = await conn.fetchrow("""
                INSERT INTO bonus_logs (telegram_id, bonus_type, amount, balance_before, 
                                        reason, expires_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING id
            """, telegram_id, bonus_type, amount, balance_before, reason, expires_at)
            
            return row["id"]

    @classmethod
    @log_query
    async def claim_daily_bonus(cls, telegram_id: int) -> Tuple[bool, float, int]:
        """Claim daily bonus for user"""
        async with cls._pool.acquire() as conn:
            today = datetime.utcnow().date()
            
            # Check if already claimed today
            existing = await conn.fetchrow("""
                SELECT last_claimed_date, streak_count 
                FROM daily_bonuses 
                WHERE telegram_id = $1
            """, telegram_id)
            
            if existing and existing["last_claimed_date"] == today:
                return False, 0, 0
            
            # Calculate streak
            streak = 1
            if existing and existing["last_claimed_date"] == today - timedelta(days=1):
                streak = existing["streak_count"] + 1
            
            # Calculate bonus amount
            base_bonus = await cls.get_setting_int('daily_bonus', 5)
            bonus_amount = base_bonus * min(streak, 7)  # Max 7x streak
            
            # Add bonus to balance
            await cls.add_balance(telegram_id, bonus_amount, "daily_bonus")
            
            # Update daily bonus record
            await conn.execute("""
                INSERT INTO daily_bonuses (telegram_id, last_claimed_date, streak_count, total_claimed, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (telegram_id) DO UPDATE
                SET last_claimed_date = EXCLUDED.last_claimed_date,
                    streak_count = EXCLUDED.streak_count,
                    total_claimed = daily_bonuses.total_claimed + EXCLUDED.bonus_amount,
                    updated_at = NOW()
            """, telegram_id, today, streak, bonus_amount)
            
            # Log bonus
            await cls.log_bonus(telegram_id, "daily", bonus_amount, f"Daily bonus - {streak} day streak")
            
            return True, bonus_amount, streak

    # ==================== NOTIFICATIONS ====================
    
    @classmethod
    @log_query
    async def add_notification(cls, telegram_id: int, title: str, message: str, 
                                notification_type: str = "info", metadata: Dict = None) -> int:
        """Add a notification for user"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO notifications (telegram_id, title, message, type, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                RETURNING id
            """, telegram_id, title, message, notification_type, json.dumps(metadata) if metadata else None)
            
            return row["id"]

    @classmethod
    @log_query
    async def get_user_notifications(cls, telegram_id: int, limit: int = 20, 
                                      unread_only: bool = False) -> List[Dict]:
        """Get user's notifications"""
        async with cls._pool.acquire() as conn:
            if unread_only:
                rows = await conn.fetch("""
                    SELECT * FROM notifications 
                    WHERE telegram_id = $1 AND is_read = FALSE
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, telegram_id, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM notifications 
                    WHERE telegram_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, telegram_id, limit)
            return [dict(r) for r in rows]

    @classmethod
    @log_query
    async def mark_notification_read(cls, notification_id: int, telegram_id: int) -> bool:
        """Mark notification as read"""
        async with cls._pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE notifications 
                SET is_read = TRUE, read_at = NOW()
                WHERE id = $1 AND telegram_id = $2 AND is_read = FALSE
            """, notification_id, telegram_id)
            return result == "UPDATE 1"

    @classmethod
    @log_query
    async def mark_all_notifications_read(cls, telegram_id: int) -> int:
        """Mark all user notifications as read"""
        async with cls._pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE notifications 
                SET is_read = TRUE, read_at = NOW()
                WHERE telegram_id = $1 AND is_read = FALSE
            """, telegram_id)
            return int(result.split()[1]) if result else 0

    # ==================== AUDIT LOGS ====================
    
    @classmethod
    @log_query
    async def log_audit(cls, user_id: int, action: str, entity_type: str = None,
                         entity_id: str = None, old_value: Dict = None, 
                         new_value: Dict = None, ip_address: str = None, 
                         user_agent: str = None) -> int:
        """Log an audit event"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, 
                                        old_value, new_value, ip_address, user_agent, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                RETURNING id
            """, user_id, action, entity_type, entity_id, 
                json.dumps(old_value) if old_value else None,
                json.dumps(new_value) if new_value else None,
                ip_address, user_agent)
            return row["id"]

    @classmethod
    @log_query
    async def get_audit_logs(cls, user_id: int = None, action: str = None, 
                              limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get audit logs with filters"""
        async with cls._pool.acquire() as conn:
            if user_id and action:
                rows = await conn.fetch("""
                    SELECT * FROM audit_logs 
                    WHERE user_id = $1 AND action = $2
                    ORDER BY created_at DESC 
                    LIMIT $3 OFFSET $4
                """, user_id, action, limit, offset)
            elif user_id:
                rows = await conn.fetch("""
                    SELECT * FROM audit_logs 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
            elif action:
                rows = await conn.fetch("""
                    SELECT * FROM audit_logs 
                    WHERE action = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2 OFFSET $3
                """, action, limit, offset)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM audit_logs 
                    ORDER BY created_at DESC 
                    LIMIT $1 OFFSET $2
                """, limit, offset)
            return [dict(r) for r in rows]

    # ==================== STATISTICS ====================
    
    @classmethod
    @log_query
    async def get_total_users_count(cls, active_only: bool = False) -> int:
        """Get total registered users count"""
        async with cls._pool.acquire() as conn:
            if active_only:
                row = await conn.fetchrow("""
                    SELECT COUNT(*) FROM users 
                    WHERE registered = TRUE AND is_active = TRUE AND is_banned = FALSE
                """)
            else:
                row = await conn.fetchrow("SELECT COUNT(*) FROM users WHERE registered = TRUE")
            return row[0] if row else 0

    @classmethod
    @log_query
    async def get_total_deposits(cls) -> float:
        """Get total deposits across all users"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COALESCE(SUM(total_deposited), 0) FROM users")
            return float(row[0]) if row and row[0] else 0.0

    @classmethod
    @log_query
    async def get_total_withdrawals(cls) -> float:
        """Get total approved withdrawals"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT COALESCE(SUM(amount), 0) FROM pending_withdrawals WHERE status = 'approved'
            """)
            return float(row[0]) if row and row[0] else 0.0

    @classmethod
    @log_query
    async def get_top_winners(cls, limit: int = 10, period: str = "all_time") -> List[Dict]:
        """Get top winners leaderboard"""
        async with cls._pool.acquire() as conn:
            if period == "daily":
                rows = await conn.fetch("""
                    SELECT u.telegram_id, u.username, u.first_name, u.last_name,
                           COALESCE(SUM(gt.amount), 0) as total_won
                    FROM users u
                    LEFT JOIN game_transactions gt ON u.telegram_id = gt.telegram_id 
                        AND gt.type = 'win' AND DATE(gt.created_at) = CURRENT_DATE
                    WHERE u.registered = TRUE
                    GROUP BY u.telegram_id
                    ORDER BY total_won DESC
                    LIMIT $1
                """, limit)
            elif period == "weekly":
                rows = await conn.fetch("""
                    SELECT u.telegram_id, u.username, u.first_name, u.last_name,
                           COALESCE(SUM(gt.amount), 0) as total_won
                    FROM users u
                    LEFT JOIN game_transactions gt ON u.telegram_id = gt.telegram_id 
                        AND gt.type = 'win' AND gt.created_at > NOW() - INTERVAL '7 days'
                    WHERE u.registered = TRUE
                    GROUP BY u.telegram_id
                    ORDER BY total_won DESC
                    LIMIT $1
                """, limit)
            else:  # all_time
                rows = await conn.fetch("""
                    SELECT u.telegram_id, u.username, u.first_name, u.last_name,
                           u.total_won, u.games_won, u.games_played,
                           CASE WHEN u.games_played > 0 
                                THEN ROUND((u.games_won::DECIMAL / u.games_played) * 100, 2)
                                ELSE 0 END as win_rate
                    FROM users u
                    WHERE u.registered = TRUE AND u.total_won > 0
                    ORDER BY u.total_won DESC
                    LIMIT $1
                """, limit)
            return [dict(r) for r in rows]

    @classmethod
    @log_query
    async def get_platform_stats(cls) -> Dict:
        """Get overall platform statistics"""
        async with cls._pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE registered = TRUE) as total_users,
                    (SELECT COUNT(*) FROM users WHERE registered = TRUE AND created_at > NOW() - INTERVAL '7 days') as new_users_week,
                    (SELECT COUNT(*) FROM users WHERE last_seen > NOW() - INTERVAL '24 hours') as active_today,
                    (SELECT COALESCE(SUM(total_deposited), 0) FROM users) as total_deposits,
                    (SELECT COALESCE(SUM(total_withdrawn), 0) FROM users) as total_withdrawals,
                    (SELECT COALESCE(SUM(total_won), 0) FROM users) as total_won,
                    (SELECT COALESCE(SUM(total_bet), 0) FROM users) as total_bet,
                    (SELECT COUNT(*) FROM game_rounds) as total_rounds,
                    (SELECT COALESCE(SUM(admin_commission), 0) FROM game_rounds) as total_commission,
                    (SELECT COUNT(*) FROM pending_withdrawals WHERE status = 'pending') as pending_withdrawals,
                    (SELECT COALESCE(SUM(amount), 0) FROM pending_withdrawals WHERE status = 'pending') as pending_amount
            """)
            return dict(stats) if stats else {}

    # ==================== REFERRAL SYSTEM ====================
    
    @classmethod
    @log_query
    async def apply_referral(cls, new_user_id: int, referral_code: str) -> bool:
        """Apply referral when a new user registers"""
        async with cls._pool.acquire() as conn:
            # Find referrer
            referrer = await conn.fetchrow("SELECT telegram_id FROM users WHERE referral_code = $1", referral_code)
            if not referrer or referrer["telegram_id"] == new_user_id:
                return False
            
            # Update referrer
            await conn.execute("""
                UPDATE users 
                SET referral_count = referral_count + 1,
                    referral_earnings = referral_earnings + $2
                WHERE telegram_id = $1
            """, referrer["telegram_id"], 10)
            
            # Update new user
            await conn.execute("UPDATE users SET referred_by = $1 WHERE telegram_id = $2", 
                              referrer["telegram_id"], new_user_id)
            
            # Add referral bonus
            await cls.add_balance(referrer["telegram_id"], 10, "referral_bonus")
            await cls.log_bonus(referrer["telegram_id"], "referral", 10, f"Referral bonus for user {new_user_id}")
            
            return True

    @classmethod
    @log_query
    async def get_referral_stats(cls, telegram_id: int) -> Dict:
        """Get referral statistics for a user"""
        async with cls._pool.acquire() as conn:
            user = await conn.fetchrow("""
                SELECT referral_code, referral_count, referral_earnings
                FROM users WHERE telegram_id = $1
            """, telegram_id)
            
            referrals = await conn.fetch("""
                SELECT telegram_id, username, first_name, last_name, created_at
                FROM users WHERE referred_by = $1
                ORDER BY created_at DESC
            """, telegram_id)
            
            return {
                "referral_code": user["referral_code"] if user else None,
                "referral_count": user["referral_count"] if user else 0,
                "referral_earnings": float(user["referral_earnings"]) if user else 0,
                "referrals": [dict(r) for r in referrals]
            }

    # ==================== TOURNAMENT SYSTEM ====================
    
    @classmethod
    @log_query
    async def create_tournament(cls, name: str, description: str, start_date: datetime,
                                 end_date: datetime, prize_pool: float, entry_fee: float = 0,
                                 max_participants: int = None) -> int:
        """Create a new tournament"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO tournaments (name, description, start_date, end_date, 
                                         prize_pool, entry_fee, max_participants, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                RETURNING id
            """, name, description, start_date, end_date, prize_pool, entry_fee, max_participants)
            return row["id"]

    @classmethod
    @log_query
    async def join_tournament(cls, tournament_id: int, telegram_id: int) -> bool:
        """Join a tournament"""
        async with cls._pool.acquire() as conn:
            # Check if tournament exists and is open
            tournament = await conn.fetchrow("""
                SELECT status, entry_fee, max_participants, current_participants
                FROM tournaments WHERE id = $1
            """, tournament_id)
            
            if not tournament or tournament["status"] != "upcoming":
                return False
            
            # Check if already joined
            exists = await conn.fetchval("""
                SELECT 1 FROM tournament_participants 
                WHERE tournament_id = $1 AND telegram_id = $2
            """, tournament_id, telegram_id)
            
            if exists:
                return False
            
            # Check capacity
            if tournament["max_participants"] and tournament["current_participants"] >= tournament["max_participants"]:
                return False
            
            # Deduct entry fee
            if tournament["entry_fee"] > 0:
                try:
                    await cls.deduct_balance(telegram_id, tournament["entry_fee"], "tournament_entry")
                except ValueError:
                    return False
            
            # Add participant
            await conn.execute("""
                INSERT INTO tournament_participants (tournament_id, telegram_id, joined_at)
                VALUES ($1, $2, NOW())
            """, tournament_id, telegram_id)
            
            # Update participant count
            await conn.execute("""
                UPDATE tournaments 
                SET current_participants = current_participants + 1
                WHERE id = $1
            """, tournament_id)
            
            return True

    @classmethod
    @log_query
    async def update_tournament_score(cls, tournament_id: int, telegram_id: int, score: int) -> None:
        """Update a player's tournament score"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                UPDATE tournament_participants 
                SET score = score + $3
                WHERE tournament_id = $1 AND telegram_id = $2
            """, tournament_id, telegram_id, score)

    # ==================== HEALTH CHECK ====================
    
    @classmethod
    async def health_check(cls) -> bool:
        """Check database connectivity"""
        try:
            async with cls._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    @classmethod
    async def get_pool_stats(cls) -> Dict:
        """Get connection pool statistics"""
        if not cls._pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "size": cls._pool.get_size(),
            "max_size": cls._pool.get_max_size(),
            "min_size": DB_MIN_SIZE,
            "command_timeout": DB_COMMAND_TIMEOUT
        }

    @classmethod
    async def vacuum_analyze(cls) -> Dict:
        """Run VACUUM ANALYZE for database maintenance"""
        async with cls._pool.acquire() as conn:
            start_time = datetime.now()
            await conn.execute("VACUUM ANALYZE")
            duration = (datetime.now() - start_time).total_seconds()
            return {"status": "completed", "duration_seconds": duration}


# Create global instance
database = Database()

# Export all
__all__ = ['Database', 'database']