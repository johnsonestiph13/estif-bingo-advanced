# Add to bot/db/database.py if missing

async def store_otp(self, telegram_id: int, otp: str) -> None:
    """Store OTP code for user"""
    expires_at = datetime.utcnow() + timedelta(minutes=config.OTP_EXPIRY_MINUTES)
    async with self._pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO otp_codes (telegram_id, otp, expires_at, created_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (telegram_id) DO UPDATE
            SET otp = EXCLUDED.otp, 
                expires_at = EXCLUDED.expires_at, 
                attempts = 0,
                created_at = NOW()
        """, telegram_id, otp, expires_at)

async def verify_otp(self, telegram_id: int, otp: str) -> bool:
    """Verify OTP code (one-time use)"""
    async with self._pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT otp, expires_at, attempts 
            FROM otp_codes 
            WHERE telegram_id = $1
        """, telegram_id)
        
        if not row:
            return False
        
        if row['expires_at'] < datetime.utcnow():
            await conn.execute("DELETE FROM otp_codes WHERE telegram_id = $1", telegram_id)
            return False
        
        if row['attempts'] >= 5:
            await conn.execute("DELETE FROM otp_codes WHERE telegram_id = $1", telegram_id)
            return False
        
        if row['otp'] != otp:
            await conn.execute(
                "UPDATE otp_codes SET attempts = attempts + 1 WHERE telegram_id = $1", 
                telegram_id
            )
            return False
        
        # OTP is valid - delete it (one-time use)
        await conn.execute("DELETE FROM otp_codes WHERE telegram_id = $1", telegram_id)
        return True