# test_db.py
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_db():
    try:
        from bot.db.database import Database
        await Database.init_pool()
        print("✅ Database connected successfully!")
        
        # Test query
        async with Database._pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Test query result: {result}")
        
        await Database.close_pool()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_db())
