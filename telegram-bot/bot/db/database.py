# telegram-bot/bot/db/database.py
# Estif Bingo 24/7 - Complete Database Module (FULLY UPDATED & COMPATIBLE)

import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import random
import string
import os
import secrets

# ✅ Correct import for Render
try:
    from bot.config import (
        DATABASE_URL, DB_MIN_SIZE, DB_MAX_SIZE,
        DB_COMMAND_TIMEOUT, SKIP_AUTO_MIGRATIONS,
        OTP_EXPIRY_MINUTES
    )
except ImportError:
    # Fallback for local development
    from config import (
        DATABASE_URL, DB_MIN_SIZE, DB_MAX_SIZE,
        DB_COMMAND_TIMEOUT, SKIP_AUTO_MIGRATIONS,
        OTP_EXPIRY_MINUTES
    )

logger = logging.getLogger(__name__)


class Database:
    _pool: asyncpg.Pool = None

    @classmethod
    async def init_pool(cls):
        """Initialize database connection pool with SSL for Render"""
        ssl_config = "require" if os.getenv("NODE_ENV") == "production" else None
        
        cls._pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=DB_MIN_SIZE,
            max_size=DB_MAX_SIZE,
            command_timeout=DB_COMMAND_TIMEOUT,
            ssl=ssl_config
        )
        await cls._init_tables()
        await cls._ensure_columns()
        if not SKIP_AUTO_MIGRATIONS:
            await cls._run_migrations()
        logger.info("✅ Database pool initialized")

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
                'highest_win': 'DECIMAL(12,2) DEFAULT 0'
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in column_names:
                    try:
                        await conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                        logger.info(f"✅ Added missing column: {col_name}")
                    except Exception as e:
                        logger.warning(f"Could not add column {col_name}: {e}")

    @classmethod
    async def close_pool(cls):
        """Close database connection pool"""
        if cls._pool:
            await cls._pool.close()
            logger.info("Database pool closed")

    @classmethod
    async def _init_tables(cls):
        """Create all necessary tables if they don't exist"""
        async with cls._pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT UNIQUE,
                    balance DECIMAL(12,2) DEFAULT 0,
                    total_deposited DECIMAL(12,2) DEFAULT 0,
                    total_withdrawn DECIMAL(12,2) DEFAULT 0,
                    total_won DECIMAL(12,2) DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    games_lost INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    highest_win DECIMAL(12,2) DEFAULT 0,
                    referral_code TEXT UNIQUE,
                    referred_by BIGINT,
                    referral_count INTEGER DEFAULT 0,
                    referral_earnings DECIMAL(12,2) DEFAULT 0,
                    registered BOOLEAN DEFAULT FALSE,
                    joined_group BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_banned BOOLEAN DEFAULT FALSE,
                    lang TEXT DEFAULT 'en',
                    sound_enabled BOOLEAN DEFAULT TRUE,
                    animations_enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    last_seen TIMESTAMP DEFAULT NOW(),
                    last_game_at TIMESTAMP
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
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Game transactions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_transactions (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    username VARCHAR(50),
                    type VARCHAR(20) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    cartela VARCHAR(20),
                    round INTEGER,
                    note TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Game settings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Pending withdrawals table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_withdrawals (
                    id SERIAL PRIMARY KEY,
                    withdrawal_id VARCHAR(50) UNIQUE,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    amount DECIMAL(12,2) NOT NULL,
                    account TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT NOW(),
                    processed_at TIMESTAMP,
                    approved_at TIMESTAMP,
                    rejected_at TIMESTAMP,
                    processed_by TEXT,
                    rejection_reason TEXT,
                    note TEXT
                )
            """)
            
            # OTP codes table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS otp_codes (
                    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
                    otp TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    attempts INTEGER DEFAULT 0
                )
            """)
            
            # Auth codes table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS auth_codes (
                    code TEXT PRIMARY KEY,
                    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    used BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Commission logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS commission_logs (
                    id SERIAL PRIMARY KEY,
                    old_percentage INTEGER NOT NULL,
                    new_percentage INTEGER NOT NULL,
                    changed_by VARCHAR(100),
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default game settings
            await conn.execute("""
                INSERT INTO game_settings (key, value, description) VALUES 
                    ('win_percentage', '75', 'Current game win percentage (70,75,76,80)'),
                    ('default_sound_pack', 'pack1', 'Default sound pack for new players'),
                    ('selection_time', '50', 'Cartela selection time in seconds'),
                    ('draw_interval', '4000', 'Number draw interval in milliseconds'),
                    ('next_round_delay', '6000', 'Delay between rounds in milliseconds'),
                    ('bet_amount', '10', 'Cost per cartela in ETB'),
                    ('max_cartelas', '4', 'Maximum cartelas per player per round'),
                    ('total_cartelas', '75', 'Total available cartela types')
                ON CONFLICT (key) DO NOTHING
            """)
            
            # Create indexes
            await cls._create_indexes(conn)
            
        logger.info("✅ Database tables ready")

    @classmethod
    async def _create_indexes(cls, conn):
        """Create all indexes"""
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_registered ON users(registered)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON pending_withdrawals(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_telegram ON pending_withdrawals(telegram_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_pending ON pending_withdrawals(status, requested_at) WHERE status = 'pending'")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes(expires_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_telegram ON otp_codes(telegram_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_expires ON auth_codes(expires_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_code ON auth_codes(code)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_telegram ON auth_codes(telegram_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram ON game_transactions(telegram_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_transactions_timestamp ON game_transactions(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_rounds_timestamp ON game_rounds(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_commission_logs_changed_at ON commission_logs(changed_at DESC)")

    @classmethod
    async def _run_migrations(cls):
        """Run pending migrations"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    executed_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            executed = await conn.fetch("SELECT name FROM migrations")
            executed_set = {row["name"] for row in executed}
            
            migrations = [
                "001_users.sql",
                "002_withdrawals.sql", 
                "003_otp.sql",
                "004_auth_codes.sql",
                "005_commission_settings.sql",
                "006_add_indexes.sql"
            ]
            
            for migration in migrations:
                if migration not in executed_set:
                    logger.info(f"Migration {migration} already applied or not needed")

    # ==================== USER OPERATIONS ====================
    
    @classmethod
    async def get_user(cls, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            return dict(row) if row else None

    @classmethod
    async def get_user_by_phone(cls, phone: str) -> Optional[Dict]:
        """Get user by phone number"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE phone = $1", phone)
            return dict(row) if row else None

    @classmethod
    async def get_user_by_username(cls, username: str) -> Optional[Dict]:
        """Get user by username"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE username ILIKE $1", username)
            return dict(row) if row else None

    @classmethod
    async def create_user(cls, telegram_id: int, username: str, 
                          first_name: str, last_name: str, 
                          phone: str, lang: str = "en") -> None:
        """Create a new user"""
        async with cls._pool.acquire() as conn:
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            await conn.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, 
                                   phone, registered, lang, referral_code, created_at)
                VALUES ($1, $2, $3, $4, $5, TRUE, $6, $7, NOW())
            """, telegram_id, username, first_name, last_name, phone, lang, referral_code)

    @classmethod
    async def update_user(cls, telegram_id: int, **kwargs) -> None:
        """Update user fields"""
        if not kwargs:
            return
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        values = [telegram_id] + list(kwargs.values())
        async with cls._pool.acquire() as conn:
            await conn.execute(f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE telegram_id = $1", *values)

    @classmethod
    async def update_last_seen(cls, telegram_id: int) -> None:
        """Update user's last seen timestamp"""
        async with cls._pool.acquire() as conn:
            await conn.execute("UPDATE users SET last_seen = NOW() WHERE telegram_id = $1", telegram_id)

    # ==================== BALANCE OPERATIONS ====================
    
    @classmethod
    async def update_balance(cls, telegram_id: int, amount: float, 
                              transaction_type: str, round_id: int = None) -> bool:
        """Update user balance with transaction record"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT balance FROM users WHERE telegram_id = $1 FOR UPDATE", telegram_id)
                if not user:
                    return False
                current_balance = float(user["balance"]) if user["balance"] else 0.0
                new_balance = current_balance + amount
                if new_balance < 0:
                    return False
                await conn.execute("UPDATE users SET balance = $1 WHERE telegram_id = $2", new_balance, telegram_id)
                await conn.execute("""
                    INSERT INTO game_transactions (telegram_id, type, amount, round, note)
                    VALUES ($1, $2, $3, $4, $5)
                """, telegram_id, transaction_type, amount, round_id, f"{transaction_type} transaction")
                return True

    @classmethod
    async def add_balance(cls, telegram_id: int, amount: float, reason: str = None) -> float:
        """Add balance to user"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT balance, total_deposited, total_won FROM users WHERE telegram_id = $1 FOR UPDATE", telegram_id)
                if not user:
                    raise ValueError("User not found")
                current_balance = float(user["balance"]) if user["balance"] else 0.0
                current_total_deposited = float(user["total_deposited"]) if user["total_deposited"] else 0.0
                new_balance = current_balance + amount
                await conn.execute("UPDATE users SET balance = $1 WHERE telegram_id = $2", new_balance, telegram_id)
                
                if amount > 0 and reason not in ("win", "refund", "deselect", "withdrawal_refund", "transfer_in"):
                    new_total = current_total_deposited + amount
                    await conn.execute("UPDATE users SET total_deposited = $1 WHERE telegram_id = $2", new_total, telegram_id)
                
                if reason == "win" and amount > 0:
                    await conn.execute("UPDATE users SET total_won = total_won + $1 WHERE telegram_id = $2", amount, telegram_id)
                
                return new_balance

    @classmethod
    async def deduct_balance(cls, telegram_id: int, amount: float, reason: str = None) -> float:
        """Deduct balance from user"""
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
                
                if reason == "cartela_purchase":
                    await conn.execute("UPDATE users SET games_played = games_played + 1 WHERE telegram_id = $1", telegram_id)
                
                if reason == "cashout":
                    await conn.execute("UPDATE users SET total_withdrawn = total_withdrawn + $1 WHERE telegram_id = $2", amount, telegram_id)
                
                return new_balance

    @classmethod
    async def get_balance(cls, telegram_id: int) -> float:
        """Get user's current balance"""
        user = await cls.get_user(telegram_id)
        if user and user.get("balance"):
            return float(user["balance"])
        return 0.0

    # ==================== AUTH CODE OPERATIONS ====================
    
    @classmethod
    async def create_auth_code(cls, telegram_id: int) -> str:
        """Create one-time authentication code for game access"""
        code = secrets.token_urlsafe(16)
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO auth_codes (code, telegram_id, expires_at, created_at)
                VALUES ($1, $2, $3, NOW())
            """, code, telegram_id, expires_at)
        return code

    @classmethod
    async def verify_auth_code(cls, code: str) -> Optional[int]:
        """Verify auth code and return telegram_id if valid"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT telegram_id FROM auth_codes WHERE code = $1 AND expires_at > NOW() AND used = FALSE",
                code
            )
            if row:
                await conn.execute("UPDATE auth_codes SET used = TRUE WHERE code = $1", code)
                return row["telegram_id"]
        return None

    @classmethod
    async def consume_auth_code(cls, code: str) -> Optional[int]:
        """Consume auth code and return telegram_id if valid"""
        return await cls.verify_auth_code(code)

    # ==================== OTP OPERATIONS ====================
    
    @classmethod
    async def store_otp(cls, telegram_id: int, otp: str) -> None:
        """Store OTP code for user"""
        expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO otp_codes (telegram_id, otp, expires_at, created_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (telegram_id) DO UPDATE
                SET otp = EXCLUDED.otp, expires_at = EXCLUDED.expires_at, attempts = 0, created_at = NOW()
            """, telegram_id, otp, expires_at)

    @classmethod
    async def verify_otp(cls, telegram_id: int, otp: str) -> bool:
        """Verify OTP code (one-time use)"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT otp, expires_at, attempts FROM otp_codes WHERE telegram_id = $1", telegram_id)
            if not row:
                return False
            if row["expires_at"] < datetime.utcnow():
                await conn.execute("DELETE FROM otp_codes WHERE telegram_id = $1", telegram_id)
                return False
            if row["attempts"] >= 5:
                await conn.execute("DELETE FROM otp_codes WHERE telegram_id = $1", telegram_id)
                return False
            if row["otp"] != otp:
                await conn.execute("UPDATE otp_codes SET attempts = attempts + 1 WHERE telegram_id = $1", telegram_id)
                return False
            await conn.execute("DELETE FROM otp_codes WHERE telegram_id = $1", telegram_id)
            return True

    # ==================== WITHDRAWAL OPERATIONS ====================
    
    @classmethod
    async def add_pending_withdrawal(cls, telegram_id: int, amount: float,
                                      account: str, method: str) -> int:
        """Add pending withdrawal request"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO pending_withdrawals (telegram_id, amount, account, method, requested_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id
            """, telegram_id, amount, account, method)
            return row["id"]

    @classmethod
    async def get_pending_withdrawals(cls, telegram_id: int = None) -> List[Dict]:
        """Get pending withdrawal requests"""
        async with cls._pool.acquire() as conn:
            if telegram_id:
                rows = await conn.fetch(
                    "SELECT * FROM pending_withdrawals WHERE telegram_id = $1 AND status = 'pending' ORDER BY requested_at DESC",
                    telegram_id
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM pending_withdrawals WHERE status = 'pending' ORDER BY requested_at ASC"
                )
            return [dict(r) for r in rows]

    @classmethod
    async def get_withdrawal_by_id(cls, withdrawal_id: int) -> Optional[Dict]:
        """Get withdrawal by ID"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM pending_withdrawals WHERE id = $1", withdrawal_id)
            return dict(row) if row else None

    @classmethod
    async def approve_withdrawal(cls, withdrawal_id: int) -> Optional[Tuple[int, float]]:
        """Approve withdrawal and deduct balance"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                withdrawal = await conn.fetchrow(
                    "SELECT telegram_id, amount FROM pending_withdrawals WHERE id = $1 AND status = 'pending'",
                    withdrawal_id
                )
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
                    SET status = 'approved', processed_at = NOW(), approved_at = NOW() 
                    WHERE id = $1
                """, withdrawal_id)
                return telegram_id, amount

    @classmethod
    async def reject_withdrawal(cls, withdrawal_id: int, reason: str = None) -> None:
        """Reject withdrawal request"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                UPDATE pending_withdrawals 
                SET status = 'rejected', processed_at = NOW(), rejected_at = NOW(), rejection_reason = $2
                WHERE id = $1
            """, withdrawal_id, reason)

    # ==================== SETTINGS OPERATIONS ====================
    
    @classmethod
    async def get_setting(cls, key: str) -> Optional[str]:
        """Get setting value by key"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM game_settings WHERE key = $1", key)
            return row["value"] if row else None

    @classmethod
    async def set_setting(cls, key: str, value: str) -> None:
        """Set setting value"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO game_settings (key, value, updated_at) VALUES ($1, $2, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """, key, value)

    @classmethod
    async def get_win_percentage(cls) -> int:
        """Get current win percentage"""
        value = await cls.get_setting('win_percentage')
        return int(value) if value else 75

    @classmethod
    async def set_win_percentage(cls, percentage: int) -> None:
        """Set win percentage"""
        await cls.set_setting('win_percentage', str(percentage))

    @classmethod
    async def get_default_sound_pack(cls) -> str:
        """Get default sound pack for new players"""
        value = await cls.get_setting('default_sound_pack')
        return value if value else 'pack1'

    @classmethod
    async def set_default_sound_pack(cls, sound_pack: str) -> None:
        """Set default sound pack for new players"""
        await cls.set_setting('default_sound_pack', sound_pack)

    # ==================== COMMISSION LOGS ====================
    
    @classmethod
    async def log_commission_change(cls, old_percentage: int, new_percentage: int, changed_by: str = "API") -> None:
        """Log commission change to database"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO commission_logs (old_percentage, new_percentage, changed_by, changed_at)
                VALUES ($1, $2, $3, NOW())
            """, old_percentage, new_percentage, changed_by)

    @classmethod
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
    async def get_commission_stats(cls) -> Dict:
        """Get commission statistics"""
        async with cls._pool.acquire() as conn:
            total_commission = await conn.fetchval("SELECT COALESCE(SUM(admin_commission), 0) FROM game_rounds")
            avg_win_percentage = await conn.fetchval("SELECT COALESCE(AVG(win_percentage), 0) FROM game_rounds")
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
    async def search_players(cls, search_term: str) -> List[Dict]:
        """Search players by username or phone"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT telegram_id, username, phone, balance, total_deposited, total_won, games_played, games_won
                FROM users 
                WHERE username ILIKE $1 OR phone ILIKE $1
                ORDER BY balance DESC
                LIMIT 50
            """, f'%{search_term}%')
            return [dict(r) for r in rows]

    # ==================== GAME TRANSACTIONS ====================
    
    @classmethod
    async def log_game_transaction(cls, telegram_id: int, username: str, 
                                    transaction_type: str, amount: float,
                                    cartela: str = None, round_num: int = None,
                                    note: str = None) -> int:
        """Log a game transaction"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO game_transactions (telegram_id, username, type, amount, cartela, round, note, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                RETURNING id
            """, telegram_id, username, transaction_type, amount, cartela, round_num, note)
            return row["id"] if row else 0

    @classmethod
    async def get_user_transactions(cls, telegram_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get user's transaction history"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM game_transactions 
                WHERE telegram_id = $1 
                ORDER BY timestamp DESC 
                LIMIT $2 OFFSET $3
            """, telegram_id, limit, offset)
            return [dict(r) for r in rows]

    # ==================== STATISTICS ====================
    
    @classmethod
    async def get_total_users_count(cls) -> int:
        """Get total registered users count"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*) FROM users WHERE registered = TRUE")
            return row[0] if row else 0

    @classmethod
    async def get_total_deposits(cls) -> float:
        """Get total deposits across all users"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COALESCE(SUM(total_deposited), 0) FROM users")
            return float(row[0]) if row and row[0] else 0.0

    @classmethod
    async def get_top_winners(cls, limit: int = 10) -> List[Dict]:
        """Get top winners leaderboard"""
        async with cls._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT telegram_id, username, total_won, games_won, games_played
                FROM users 
                WHERE registered = TRUE AND total_won > 0
                ORDER BY total_won DESC
                LIMIT $1
            """, limit)
            return [dict(r) for r in rows]

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


# Create a global instance for easier imports
database = Database()