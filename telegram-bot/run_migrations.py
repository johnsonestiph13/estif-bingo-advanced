# run_migrations.py
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your database module
from bot.db.database import Database
from bot.config import config

# The SQL commands to create missing tables
SQL_COMMANDS = """
-- Pending withdrawals table (for cashout)
CREATE TABLE IF NOT EXISTS pending_withdrawals (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    account TEXT NOT NULL,
    method TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    rejection_reason TEXT
);

-- OTP codes table
CREATE TABLE IF NOT EXISTS otp_codes (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    otp TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    attempts INTEGER DEFAULT 0
);

-- Auth codes table (for game access, optional but safe)
CREATE TABLE IF NOT EXISTS auth_codes (
    code TEXT PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Game transactions table (for logging)
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
);
"""

async def run_migrations():
    print("Connecting to database...")
    try:
        await Database.init_pool()
        print("✅ Connected to database")
        
        async with Database._pool.acquire() as conn:
            # Split SQL commands by semicolon and execute each
            for command in SQL_COMMANDS.strip().split(';'):
                cmd = command.strip()
                if cmd:
                    print(f"Executing: {cmd[:50]}...")
                    await conn.execute(cmd)
        
        print("\n✅ All tables created/verified successfully!")
        
        # Optional: Verify tables exist
        async with Database._pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('pending_withdrawals', 'otp_codes', 'auth_codes', 'game_transactions')
            """)
            print("\n📋 Tables present:")
            for t in tables:
                print(f"   - {t['table_name']}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await Database.close_pool()

if __name__ == "__main__":
    print("🚀 Running database migrations...")
    asyncio.run(run_migrations())