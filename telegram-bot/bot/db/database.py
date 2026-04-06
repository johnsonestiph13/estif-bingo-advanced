# db/database.py
"""PostgreSQL database operations for Estif Bingo Bot"""

import asyncpg
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from ..config import (
    DATABASE_URL, DB_MIN_SIZE, DB_MAX_SIZE, 
    DB_COMMAND_TIMEOUT, SKIP_AUTO_MIGRATIONS
)

logger = logging.getLogger(__name__)


class Database:
    """Database manager with connection pool and CRUD operations"""
    
    _pool: asyncpg.Pool = None

    @classmethod
    async def init_pool(cls):
        """Initialize database connection pool"""
        cls._pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=DB_MIN_SIZE,
            max_size=DB_MAX_SIZE,
            command_timeout=DB_COMMAND_TIMEOUT
        )
        await cls._init_tables()
        if not SKIP_AUTO_MIGRATIONS:
            await cls._run_migrations()
        logger.info("✅ Database pool initialized")

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
                    phone TEXT,
                    balance DECIMAL(12,2) DEFAULT 0,
                    total_deposited DECIMAL(12,2) DEFAULT 0,
                    registered BOOLEAN DEFAULT FALSE,
                    joined_group BOOLEAN DEFAULT FALSE,
                    lang TEXT DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_seen TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Pending withdrawals
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_withdrawals (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT REFERENCES users(telegram_id),
                    amount DECIMAL(12,2),
                    account TEXT,
                    method TEXT,
                    status TEXT DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT NOW(),
                    processed_at TIMESTAMP
                )
            """)
            
            # OTP codes
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS otp_codes (
                    telegram_id BIGINT PRIMARY KEY,
                    otp TEXT,
                    expires_at TIMESTAMP
                )
            """)
            
            # Auth codes for game link
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS auth_codes (
                    code TEXT PRIMARY KEY,
                    telegram_id BIGINT,
                    expires_at TIMESTAMP
                )
            """)
            
            # Settings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Insert default settings
            await conn.execute("""
                INSERT INTO settings (key, value) VALUES ('win_percentage', '75')
                ON CONFLICT (key) DO NOTHING
            """)
            
            # Indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON pending_withdrawals(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes(expires_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_expires ON auth_codes(expires_at)")
            
        logger.info("✅ Database tables ready")

    @classmethod
    async def _run_migrations(cls):
        """Run pending migrations automatically"""
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
            
            # Add migrations here as needed
            # Example:
            # if "002_add_leaderboard.sql" not in executed_set:
            #     await conn.execute("ALTER TABLE users ADD COLUMN games_won INT DEFAULT 0")
            #     await conn.execute("INSERT INTO migrations (name) VALUES ('002_add_leaderboard.sql')")
            #     logger.info("✅ Migration 002_add_leaderboard.sql applied")

    # ==================== USER OPERATIONS ====================
    
    @classmethod
    async def get_user(cls, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", 
                telegram_id
            )
            return dict(row) if row else None

    @classmethod
    async def get_user_by_phone(cls, phone: str) -> Optional[Dict]:
        """Get user by phone number"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE phone = $1", 
                phone
            )
            return dict(row) if row else None

    @classmethod
    async def create_user(cls, telegram_id: int, username: str, 
                          first_name: str, last_name: str, 
                          phone: str, lang: str = "en") -> None:
        """Create a new user"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, 
                                   phone, registered, lang)
                VALUES ($1, $2, $3, $4, $5, TRUE, $6)
            """, telegram_id, username, first_name, last_name, phone, lang)

    @classmethod
    async def update_user(cls, telegram_id: int, **kwargs) -> None:
        """Update user fields"""
        if not kwargs:
            return
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        values = [telegram_id] + list(kwargs.values())
        async with cls._pool.acquire() as conn:
            await conn.execute(
                f"UPDATE users SET {set_clause} WHERE telegram_id = $1", 
                *values
            )

    @classmethod
    async def update_last_seen(cls, telegram_id: int) -> None:
        """Update user's last seen timestamp"""
        async with cls._pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_seen = NOW() WHERE telegram_id = $1",
                telegram_id
            )

    # ==================== BALANCE OPERATIONS ====================
    
    @classmethod
    async def add_balance(cls, telegram_id: int, amount: float, 
                          reason: str = None) -> float:
        """Add balance to user with transaction lock"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow(
                    "SELECT balance, total_deposited FROM users WHERE telegram_id = $1 FOR UPDATE",
                    telegram_id
                )
                if not user:
                    raise ValueError("User not found")
                
                new_balance = user["balance"] + amount
                await conn.execute(
                    "UPDATE users SET balance = $1 WHERE telegram_id = $2",
                    new_balance, telegram_id
                )
                
                # Only count positive amounts as deposits (exclude wins/refunds)
                if amount > 0 and reason not in ("win", "refund", "deselect"):
                    await conn.execute(
                        "UPDATE users SET total_deposited = total_deposited + $1 WHERE telegram_id = $2",
                        amount, telegram_id
                    )
                
                return new_balance

    @classmethod
    async def deduct_balance(cls, telegram_id: int, amount: float,
                             reason: str = None) -> float:
        """Deduct balance from user with transaction lock"""
        async with cls._pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow(
                    "SELECT balance FROM users WHERE telegram_id = $1 FOR UPDATE",
                    telegram_id
                )
                if not user:
                    raise ValueError("User not found")
                if user["balance"] < amount:
                    raise ValueError("Insufficient balance")
                
                new_balance = user["balance"] - amount
                await conn.execute(
                    "UPDATE users SET balance = $1 WHERE telegram_id = $2",
                    new_balance, telegram_id
                )
                return new_balance

    @classmethod
    async def get_balance(cls, telegram_id: int) -> float:
        """Get user's current balance"""
        user = await cls.get_user(telegram_id)
        return user["balance"] if user else 0.0

    # ==================== OTP OPERATIONS ====================
    
    @classmethod
    async def store_otp(cls, telegram_id: int, otp: str) -> None:
        """Store OTP code for user"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO otp_codes (telegram_id, otp, expires_at)
                VALUES ($1, $2, NOW() + INTERVAL '5 minutes')
                ON CONFLICT (telegram_id) DO UPDATE
                SET otp = EXCLUDED.otp, expires_at = EXCLUDED.expires_at
            """, telegram_id, otp)

    @classmethod
    async def verify_otp(cls, telegram_id: int, otp: str) -> bool:
        """Verify OTP code (one-time use)"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT otp, expires_at FROM otp_codes WHERE telegram_id = $1",
                telegram_id
            )
            if not row or row["expires_at"] < datetime.utcnow() or row["otp"] != otp:
                return False
            await conn.execute("DELETE FROM otp_codes WHERE telegram_id = $1", telegram_id)
            return True

    # ==================== AUTH CODE OPERATIONS ====================
    
    @classmethod
    async def create_auth_code(cls, telegram_id: int) -> str:
        """Create one-time authentication code for game access"""
        import secrets
        code = secrets.token_urlsafe(16)
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO auth_codes (code, telegram_id, expires_at)
                VALUES ($1, $2, NOW() + INTERVAL '5 minutes')
            """, code, telegram_id)
        return code

    @classmethod
    async def consume_auth_code(cls, code: str) -> Optional[int]:
        """Consume auth code and return telegram_id if valid"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT telegram_id FROM auth_codes WHERE code = $1 AND expires_at > NOW()",
                code
            )
            if row:
                await conn.execute("DELETE FROM auth_codes WHERE code = $1", code)
                return row["telegram_id"]
        return None

    # ==================== WITHDRAWAL OPERATIONS ====================
    
    @classmethod
    async def add_pending_withdrawal(cls, telegram_id: int, amount: float,
                                      account: str, method: str) -> int:
        """Add pending withdrawal request"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO pending_withdrawals (telegram_id, amount, account, method)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, telegram_id, amount, account, method)
            return row["id"]

    @classmethod
    async def get_pending_withdrawals(cls, telegram_id: int = None) -> List[Dict]:
        """Get pending withdrawal requests"""
        async with cls._pool.acquire() as conn:
            if telegram_id:
                rows = await conn.fetch(
                    "SELECT * FROM pending_withdrawals WHERE telegram_id = $1 AND status = 'pending'",
                    telegram_id
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM pending_withdrawals WHERE status = 'pending' ORDER BY requested_at"
                )
            return [dict(r) for r in rows]

    @classmethod
    async def get_withdrawal_by_id(cls, withdrawal_id: int) -> Optional[Dict]:
        """Get withdrawal by ID"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM pending_withdrawals WHERE id = $1",
                withdrawal_id
            )
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
                    return None
                
                try:
                    await cls.deduct_balance(withdrawal["telegram_id"], withdrawal["amount"], "cashout")
                except ValueError:
                    return None
                
                await conn.execute(
                    "UPDATE pending_withdrawals SET status = 'approved', processed_at = NOW() WHERE id = $1",
                    withdrawal_id
                )
                return withdrawal["telegram_id"], withdrawal["amount"]

    @classmethod
    async def reject_withdrawal(cls, withdrawal_id: int) -> None:
        """Reject withdrawal request"""
        async with cls._pool.acquire() as conn:
            await conn.execute(
                "UPDATE pending_withdrawals SET status = 'rejected', processed_at = NOW() WHERE id = $1",
                withdrawal_id
            )

    # ==================== SETTINGS OPERATIONS ====================
    
    @classmethod
    async def get_setting(cls, key: str) -> Optional[str]:
        """Get setting value by key"""
        async with cls._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM settings WHERE key = $1", key)
            return row["value"] if row else None

    @classmethod
    async def set_setting(cls, key: str, value: str) -> None:
        """Set setting value"""
        async with cls._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO settings (key, value) VALUES ($1, $2)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
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