# config.py - COMPLETE FIXED VERSION

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== REQUIRED ENVIRONMENT VARIABLES ====================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set")

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID environment variable not set")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL environment variable not set")

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("❌ JWT_SECRET environment variable not set")

API_SECRET = os.environ.get("API_SECRET")
if not API_SECRET:
    raise ValueError("❌ API_SECRET environment variable not set")

# ==================== OPTIONAL ENVIRONMENT VARIABLES ====================

# Server Configuration
FLASK_PORT = int(os.environ.get("FLASK_PORT", "8080"))

# Game URLs
GAME_WEB_URL = os.environ.get("GAME_WEB_URL", "https://estif-bingo-247.onrender.com/player.html")

# Support Links
SUPPORT_GROUP_LINK = os.environ.get("SUPPORT_GROUP_LINK", "https://t.me/presectionA")
SUPPORT_CHANNEL_LINK = os.environ.get("SUPPORT_CHANNEL_LINK", "https://t.me/temarineh")

# Payment Configuration
PAYMENT_ACCOUNTS = {
    "CBE": os.environ.get("CBE_ACCOUNT", "1000179576997"),
    "ABBISINIYA": os.environ.get("ABBISINIYA_ACCOUNT", "35241051"),
    "TELEBIRR": os.environ.get("TELEBIRR_ACCOUNT", "0987713787"),
    "MPESA": os.environ.get("MPESA_ACCOUNT", "0722345146")
}
ACCOUNT_HOLDER = os.environ.get("ACCOUNT_HOLDER", "Estifanos Yhannis")

# OTP Configuration
OTP_EXPIRY_MINUTES = int(os.environ.get("OTP_EXPIRY_MINUTES", "5"))
OTP_LENGTH = int(os.environ.get("OTP_LENGTH", "6"))

# Database Configuration
DB_MIN_SIZE = int(os.environ.get("DB_MIN_SIZE", "5"))
DB_MAX_SIZE = int(os.environ.get("DB_MAX_SIZE", "20"))
DB_COMMAND_TIMEOUT = int(os.environ.get("DB_COMMAND_TIMEOUT", "60"))

# Migration Control
SKIP_AUTO_MIGRATIONS = os.environ.get("SKIP_AUTO_MIGRATIONS", "false").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Rate Limiting
MAX_OTP_REQUESTS = int(os.environ.get("MAX_OTP_REQUESTS", "3"))
MAX_DEPOSIT_REQUESTS = int(os.environ.get("MAX_DEPOSIT_REQUESTS", "5"))
MAX_CASHOUT_REQUESTS = int(os.environ.get("MAX_CASHOUT_REQUESTS", "3"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "300"))

# ==================== DERIVED CONFIGURATIONS ====================

PAYMENT_METHODS = list(PAYMENT_ACCOUNTS.keys())
ALLOWED_WIN_PERCENTAGES = [70, 75, 76, 80]
DEFAULT_WIN_PERCENTAGE = 75

# ==================== HELPER FUNCTIONS ====================

def get_payment_account(method: str) -> str:
    """Get payment account number for given method"""
    return PAYMENT_ACCOUNTS.get(method, "")


def is_valid_payment_method(method: str) -> bool:
    """Check if payment method is valid"""
    return method in PAYMENT_ACCOUNTS


def get_support_links() -> dict:
    """Get support channel and group links"""
    return {
        "channel": SUPPORT_CHANNEL_LINK,
        "group": SUPPORT_GROUP_LINK
    }


def get_game_url(with_params: bool = False, params: dict = None) -> str:
    """Get game URL with optional query parameters"""
    url = GAME_WEB_URL
    if with_params and params:
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    return url


def get_env_info() -> dict:
    """Get environment information for debugging"""
    return {
        "bot_token_set": bool(BOT_TOKEN),
        "admin_chat_id": ADMIN_CHAT_ID,
        "database_url_set": bool(DATABASE_URL),
        "jwt_secret_set": bool(JWT_SECRET),
        "api_secret_set": bool(API_SECRET),
        "flask_port": FLASK_PORT,
        "game_web_url": GAME_WEB_URL,
        "payment_methods": PAYMENT_METHODS,
        "skip_auto_migrations": SKIP_AUTO_MIGRATIONS,
        "log_level": LOG_LEVEL,
        "otp_expiry_minutes": OTP_EXPIRY_MINUTES
    }


# ==================== VALIDATION ====================

def validate_config() -> bool:
    """Validate critical configuration values"""
    errors = []
    
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        errors.append("BOT_TOKEN appears invalid (should contain colon)")
    
    if not ADMIN_CHAT_ID.isdigit():
        errors.append("ADMIN_CHAT_ID should be numeric")
    
    if not DATABASE_URL.startswith("postgresql://"):
        errors.append("DATABASE_URL should start with postgresql://")
    
    if not 1 <= FLASK_PORT <= 65535:
        errors.append(f"FLASK_PORT {FLASK_PORT} is invalid")
    
    if not 1 <= OTP_EXPIRY_MINUTES <= 30:
        errors.append(f"OTP_EXPIRY_MINUTES {OTP_EXPIRY_MINUTES} is invalid")
    
    if errors:
        for error in errors:
            print(f"⚠️ Config warning: {error}")
        return False
    
    return True


# ==================== INITIALIZATION ====================

# Only validate if not running in a special context
if __name__ != "__main__":
    try:
        if not validate_config():
            print("⚠️ Configuration has warnings but continuing...")
    except Exception as e:
        print(f"⚠️ Config validation error: {e}")