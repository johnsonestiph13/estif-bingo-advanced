# utils/otp.py
"""OTP (One-Time Password) generation and verification utilities"""

import secrets
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict

# ==================== OTP GENERATION ====================

def generate_numeric_otp(length: int = 6) -> str:
    """Generate numeric OTP of specified length"""
    if length < 1:
        raise ValueError("Length must be at least 1")
    max_num = 10 ** length
    otp = secrets.randbelow(max_num)
    return str(otp).zfill(length)

def generate_alphanumeric_otp(length: int = 8) -> str:
    """Generate alphanumeric OTP"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Removed similar looking chars
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)

# ==================== OTP HASHING ====================

def hash_otp(otp: str, secret: str) -> str:
    """Hash OTP with secret for secure storage"""
    combined = f"{otp}:{secret}"
    return hashlib.sha256(combined.encode()).hexdigest()

def verify_hashed_otp(otp: str, hashed: str, secret: str) -> bool:
    """Verify OTP against stored hash"""
    expected = hash_otp(otp, secret)
    return hmac.compare_digest(expected, hashed)

# ==================== TIME-BASED OTP ====================

class TOTPGenerator:
    """Time-based OTP generator (RFC 6238 compatible)"""
    
    def __init__(self, secret: bytes = None, digits: int = 6, interval: int = 30):
        self.secret = secret or secrets.token_bytes(20)
        self.digits = digits
        self.interval = interval
    
    def generate(self, time_offset: int = 0) -> str:
        """Generate TOTP for current time"""
        counter = int((time.time() + time_offset) / self.interval)
        return self._hotp(counter)
    
    def _hotp(self, counter: int) -> str:
        """Generate HOTP for given counter"""
        counter_bytes = counter.to_bytes(8, 'big')
        hmac_hash = hmac.new(self.secret, counter_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = ((hmac_hash[offset] & 0x7F) << 24 |
                (hmac_hash[offset + 1] & 0xFF) << 16 |
                (hmac_hash[offset + 2] & 0xFF) << 8 |
                (hmac_hash[offset + 3] & 0xFF))
        return str(code % (10 ** self.digits)).zfill(self.digits)
    
    def verify(self, otp: str, window: int = 1) -> bool:
        """Verify OTP within time window"""
        for i in range(-window, window + 1):
            if self.generate(time_offset=i * self.interval) == otp:
                return True
        return False

# ==================== OTP STORAGE ====================

class OTPStore:
    """In-memory OTP storage with expiration"""
    
    def __init__(self):
        self._store: Dict[str, Tuple[str, datetime]] = {}
    
    def store(self, key: str, otp: str, secret: str, expires_seconds: int = 300) -> None:
        """Store OTP with expiration"""
        expires_at = datetime.utcnow() + timedelta(seconds=expires_seconds)
        self._store[key] = (hash_otp(otp, secret), expires_at)
    
    def verify(self, key: str, otp: str, secret: str) -> bool:
        """Verify and consume OTP"""
        if key not in self._store:
            return False
        
        stored_hash, expires_at = self._store[key]
        if datetime.utcnow() > expires_at:
            del self._store[key]
            return False
        
        if verify_hashed_otp(otp, stored_hash, secret):
            del self._store[key]
            return True
        
        return False
    
    def cleanup(self) -> int:
        """Remove expired OTPs and return count"""
        now = datetime.utcnow()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(expired)
    
    def get(self, key: str) -> Optional[Tuple[str, datetime]]:
        """Get OTP data for key"""
        return self._store.get(key)

# ==================== OTP VALIDATION ====================

def is_valid_otp(otp: str, expected_length: int = 6) -> bool:
    """Validate OTP format (numeric only)"""
    if not otp or len(otp) != expected_length:
        return False
    return otp.isdigit()

# ==================== EXPORTS ====================

__all__ = [
    'generate_numeric_otp',
    'generate_alphanumeric_otp',
    'generate_secure_token',
    'hash_otp',
    'verify_hashed_otp',
    'TOTPGenerator',
    'OTPStore',
    'is_valid_otp'
]