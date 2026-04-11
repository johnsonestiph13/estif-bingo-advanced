# config.py - COMPLETE FIXED VERSION WITH GAME API SUPPORT

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
FLASK_PORT = int(os.environ.get("FLASK_PORT", "10000"))

# Game URLs
GAME_WEB_URL = os.environ.get("GAME_WEB_URL", "https://estif-bingo-advanced-1.onrender.com/player.html")

# Game Constants (for API)
CARTELA_PRICE = int(os.environ.get("CARTELA_PRICE", "10"))
MIN_BALANCE_FOR_PLAY = int(os.environ.get("MIN_BALANCE_FOR_PLAY", "10"))
WIN_PERCENTAGES = [70, 75, 76, 80]
DEFAULT_WIN_PERCENTAGE = int(os.environ.get("DEFAULT_WIN_PERCENTAGE", "80"))

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
DB_MIN_SIZE = int(os.environ.get("DB_MIN_SIZE", "2"))
DB_MAX_SIZE = int(os.environ.get("DB_MAX_SIZE", "10"))
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
ALLOWED_WIN_PERCENTAGES = WIN_PERCENTAGES

# ==================== CONFIG CLASS FOR EASY ACCESS ====================

class Config:
    """Config class for easy access to settings"""
    # Required
    BOT_TOKEN = BOT_TOKEN
    ADMIN_CHAT_ID = ADMIN_CHAT_ID
    DATABASE_URL = DATABASE_URL
    JWT_SECRET = JWT_SECRET
    API_SECRET = API_SECRET
    
    # Server
    FLASK_PORT = FLASK_PORT
    GAME_WEB_URL = GAME_WEB_URL
    
    # Game
    CARTELA_PRICE = CARTELA_PRICE
    MIN_BALANCE_FOR_PLAY = MIN_BALANCE_FOR_PLAY
    WIN_PERCENTAGES = WIN_PERCENTAGES
    DEFAULT_WIN_PERCENTAGE = DEFAULT_WIN_PERCENTAGE
    
    # Support
    SUPPORT_CHANNEL_LINK = SUPPORT_CHANNEL_LINK
    SUPPORT_GROUP_LINK = SUPPORT_GROUP_LINK
    
    # Payment
    PAYMENT_ACCOUNTS = PAYMENT_ACCOUNTS
    ACCOUNT_HOLDER = ACCOUNT_HOLDER
    
    # OTP
    OTP_EXPIRY_MINUTES = OTP_EXPIRY_MINUTES
    OTP_LENGTH = OTP_LENGTH
    
    # Database
    DB_MIN_SIZE = DB_MIN_SIZE
    DB_MAX_SIZE = DB_MAX_SIZE
    DB_COMMAND_TIMEOUT = DB_COMMAND_TIMEOUT
    
    # Migrations
    SKIP_AUTO_MIGRATIONS = SKIP_AUTO_MIGRATIONS
    
    # Logging
    LOG_LEVEL = LOG_LEVEL
    LOG_FORMAT = LOG_FORMAT
    
    # Rate Limiting
    MAX_OTP_REQUESTS = MAX_OTP_REQUESTS
    MAX_DEPOSIT_REQUESTS = MAX_DEPOSIT_REQUESTS
    MAX_CASHOUT_REQUESTS = MAX_CASHOUT_REQUESTS
    RATE_LIMIT_WINDOW = RATE_LIMIT_WINDOW

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
        "cartela_price": CARTELA_PRICE,
        "min_balance_for_play": MIN_BALANCE_FOR_PLAY,
        "win_percentages": WIN_PERCENTAGES,
        "default_win_percentage": DEFAULT_WIN_PERCENTAGE,
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