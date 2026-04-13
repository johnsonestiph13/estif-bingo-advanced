# telegram-bot/bot/config.py
# Estif Bingo 24/7 - Complete Production Configuration
# Updated with all game features, security settings, and environment variables

import os
import sys
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# Load environment variables
load_dotenv()

# ==================== PROJECT PATHS ====================
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

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

# Admin Configuration
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "johnsonestiph13@gmail.com")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", os.environ.get("ADMIN_PASSWORD"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")

# Server Configuration
FLASK_PORT = int(os.environ.get("FLASK_PORT", "10000"))
PORT = int(os.environ.get("PORT", "10000"))
NODE_ENV = os.environ.get("NODE_ENV", "production")
HOST = os.environ.get("HOST", "0.0.0.0")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Game URLs
GAME_WEB_URL = os.environ.get("GAME_WEB_URL", "https://estif-bingo-advanced-1.onrender.com/player.html")
BOT_API_URL = os.environ.get("BOT_API_URL", "https://estif-bingo-bot-1.onrender.com")
ADMIN_URL = os.environ.get("ADMIN_URL", "https://estif-bingo-advanced-1.onrender.com/admin.html")

# Game Constants
CARTELA_PRICE = int(os.environ.get("CARTELA_PRICE", "10"))
MIN_BALANCE_FOR_PLAY = int(os.environ.get("MIN_BALANCE_FOR_PLAY", "10"))
MAX_CARTELAS = int(os.environ.get("MAX_CARTELAS", "4"))
TOTAL_CARTELAS = int(os.environ.get("TOTAL_CARTELAS", "75"))
WIN_PERCENTAGES = [int(x.strip()) for x in os.environ.get("WIN_PERCENTAGES", "70,75,76,80").split(",")]
DEFAULT_WIN_PERCENTAGE = int(os.environ.get("DEFAULT_WIN_PERCENTAGE", "80"))

# Game Timing (milliseconds)
SELECTION_TIME = int(os.environ.get("SELECTION_TIME", "50000"))  # 50 seconds
DRAW_INTERVAL = int(os.environ.get("DRAW_INTERVAL", "4000"))  # 4 seconds
NEXT_ROUND_DELAY = int(os.environ.get("NEXT_ROUND_DELAY", "6000"))  # 6 seconds

# Sound & Effects
DEFAULT_SOUND_PACK = os.environ.get("DEFAULT_SOUND_PACK", "pack1")
SOUND_PACKS = [x.strip() for x in os.environ.get("SOUND_PACKS", "pack1,pack2,pack3,pack4").split(",")]

# Support Links
SUPPORT_CHANNEL_LINK = os.environ.get("SUPPORT_CHANNEL_LINK", "https://t.me/temarineh")
SUPPORT_GROUP_LINK = os.environ.get("SUPPORT_GROUP_LINK", "https://t.me/presectionA")

# Database Configuration
DB_MIN_SIZE = int(os.environ.get("DB_MIN_SIZE", "2"))
DB_MAX_SIZE = int(os.environ.get("DB_MAX_SIZE", "10"))
DB_COMMAND_TIMEOUT = int(os.environ.get("DB_COMMAND_TIMEOUT", "60"))
DB_CONNECTION_TIMEOUT = int(os.environ.get("DB_CONNECTION_TIMEOUT", "5000"))
DB_IDLE_TIMEOUT = int(os.environ.get("DB_IDLE_TIMEOUT", "30000"))
DB_POOL_MAX = int(os.environ.get("DB_POOL_MAX", "20"))
SKIP_AUTO_MIGRATIONS = os.environ.get("SKIP_AUTO_MIGRATIONS", "false").lower() == "true"
MANUAL_MIGRATION = os.environ.get("MANUAL_MIGRATION", "false").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_TO_FILE = os.environ.get("LOG_TO_FILE", "false").lower() == "true"

# Python Version
PYTHON_VERSION = os.environ.get("PYTHON_VERSION", "3.11.0")

# Rate Limiting
MAX_OTP_REQUESTS = int(os.environ.get("MAX_OTP_REQUESTS", "3"))
MAX_DEPOSIT_REQUESTS = int(os.environ.get("MAX_DEPOSIT_REQUESTS", "5"))
MAX_CASHOUT_REQUESTS = int(os.environ.get("MAX_CASHOUT_REQUESTS", "3"))
MAX_TRANSFER_REQUESTS = int(os.environ.get("MAX_TRANSFER_REQUESTS", "5"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "300"))
GAME_RATE_LIMIT_MAX = int(os.environ.get("GAME_RATE_LIMIT_MAX", "30"))
AUTH_RATE_LIMIT_MAX = int(os.environ.get("AUTH_RATE_LIMIT_MAX", "5"))

# Payment Configuration
PAYMENT_ACCOUNTS = {
    "CBE": os.environ.get("CBE_ACCOUNT", "1000179576997"),
    "ABBISINIYA": os.environ.get("ABBISINIYA_ACCOUNT", "35241051"),
    "TELEBIRR": os.environ.get("TELEBIRR_ACCOUNT", "0987713787"),
    "MPESA": os.environ.get("MPESA_ACCOUNT", "0722345146")
}
ACCOUNT_HOLDER = os.environ.get("ACCOUNT_HOLDER", "Estifanos Yhannis")
PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", "")

# OTP Configuration
OTP_EXPIRY_MINUTES = int(os.environ.get("OTP_EXPIRY_MINUTES", "5"))
OTP_LENGTH = int(os.environ.get("OTP_LENGTH", "6"))
OTP_MAX_ATTEMPTS = int(os.environ.get("OTP_MAX_ATTEMPTS", "3"))

# Cache Configuration
CARTELA_CACHE_EXPIRY = int(os.environ.get("CARTELA_CACHE_EXPIRY", "1800000"))  # 30 minutes
PLAYER_SESSION_TIMEOUT = int(os.environ.get("PLAYER_SESSION_TIMEOUT", "1800000"))  # 30 minutes

# API Configuration
BOT_API_TIMEOUT = int(os.environ.get("BOT_API_TIMEOUT", "10000"))  # 10 seconds
BOT_API_RETRIES = int(os.environ.get("BOT_API_RETRIES", "3"))
BOT_API_RETRY_DELAY = int(os.environ.get("BOT_API_RETRY_DELAY", "1000"))  # 1 second

# CORS Configuration
CORS_ORIGINS = [x.strip() for x in os.environ.get("CORS_ORIGINS", GAME_WEB_URL).split(",")]

# Feature Flags
ENABLE_REFERRAL = os.environ.get("ENABLE_REFERRAL", "false").lower() == "true"
ENABLE_TOURNAMENT = os.environ.get("ENABLE_TOURNAMENT", "false").lower() == "true"
ENABLE_DAILY_BONUS = os.environ.get("ENABLE_DAILY_BONUS", "false").lower() == "true"
ENABLE_WITHDRAWAL_FEE = os.environ.get("ENABLE_WITHDRAWAL_FEE", "false").lower() == "true"

# Withdrawal Settings
MIN_WITHDRAWAL = float(os.environ.get("MIN_WITHDRAWAL", "50"))
MAX_WITHDRAWAL = float(os.environ.get("MAX_WITHDRAWAL", "10000"))
WITHDRAWAL_FEE_PERCENTAGE = float(os.environ.get("WITHDRAWAL_FEE_PERCENTAGE", "0"))
WITHDRAWAL_PROCESSING_TIME = int(os.environ.get("WITHDRAWAL_PROCESSING_TIME", "24"))  # hours

# Deposit Settings
MIN_DEPOSIT = float(os.environ.get("MIN_DEPOSIT", "10"))
MAX_DEPOSIT = float(os.environ.get("MAX_DEPOSIT", "100000"))
DEPOSIT_BONUS_PERCENTAGE = float(os.environ.get("DEPOSIT_BONUS_PERCENTAGE", "0"))

# Transfer Settings
MIN_TRANSFER = float(os.environ.get("MIN_TRANSFER", "1"))
MAX_TRANSFER = float(os.environ.get("MAX_TRANSFER", "10000"))
TRANSFER_DAILY_LIMIT = float(os.environ.get("TRANSFER_DAILY_LIMIT", "50000"))
TRANSFER_FEE_PERCENTAGE = float(os.environ.get("TRANSFER_FEE_PERCENTAGE", "0"))

# WebSocket Settings
WS_PING_INTERVAL = int(os.environ.get("WS_PING_INTERVAL", "25000"))
WS_PING_TIMEOUT = int(os.environ.get("WS_PING_TIMEOUT", "60000"))
WS_RECONNECT_DELAY = int(os.environ.get("WS_RECONNECT_DELAY", "1000"))
WS_MAX_RECONNECT_ATTEMPTS = int(os.environ.get("WS_MAX_RECONNECT_ATTEMPTS", "10"))

# JWT Settings
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "2"))
JWT_REFRESH_EXPIRY_DAYS = int(os.environ.get("JWT_REFRESH_EXPIRY_DAYS", "7"))
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

# Session Settings
ADMIN_SESSION_EXPIRY = os.environ.get("ADMIN_SESSION_EXPIRY", "24h")
PLAYER_SESSION_EXPIRY = os.environ.get("PLAYER_SESSION_EXPIRY", "30m")

# ==================== DERIVED CONFIGURATIONS ====================

PAYMENT_METHODS = list(PAYMENT_ACCOUNTS.keys())
ALLOWED_WIN_PERCENTAGES = WIN_PERCENTAGES
SUPPORT_LINKS = {
    "channel": SUPPORT_CHANNEL_LINK,
    "group": SUPPORT_GROUP_LINK
}

# ==================== CONFIG DATACLASS ====================

@dataclass
class Config:
    """Centralized configuration class for easy access"""
    
    # Required
    BOT_TOKEN: str = BOT_TOKEN
    ADMIN_CHAT_ID: str = ADMIN_CHAT_ID
    DATABASE_URL: str = DATABASE_URL
    JWT_SECRET: str = JWT_SECRET
    API_SECRET: str = API_SECRET
    
    # Admin
    ADMIN_EMAIL: str = ADMIN_EMAIL
    ADMIN_PASSWORD_HASH: Optional[str] = ADMIN_PASSWORD_HASH
    ADMIN_USERNAME: str = ADMIN_USERNAME
    
    # Server
    FLASK_PORT: int = FLASK_PORT
    PORT: int = PORT
    NODE_ENV: str = NODE_ENV
    HOST: str = HOST
    DEBUG: bool = DEBUG
    
    # URLs
    GAME_WEB_URL: str = GAME_WEB_URL
    BOT_API_URL: str = BOT_API_URL
    ADMIN_URL: str = ADMIN_URL
    
    # Game Constants
    CARTELA_PRICE: int = CARTELA_PRICE
    MIN_BALANCE_FOR_PLAY: int = MIN_BALANCE_FOR_PLAY
    MAX_CARTELAS: int = MAX_CARTELAS
    TOTAL_CARTELAS: int = TOTAL_CARTELAS
    WIN_PERCENTAGES: List[int] = field(default_factory=lambda: WIN_PERCENTAGES)
    DEFAULT_WIN_PERCENTAGE: int = DEFAULT_WIN_PERCENTAGE
    
    # Game Timing
    SELECTION_TIME: int = SELECTION_TIME
    DRAW_INTERVAL: int = DRAW_INTERVAL
    NEXT_ROUND_DELAY: int = NEXT_ROUND_DELAY
    
    # Sound
    DEFAULT_SOUND_PACK: str = DEFAULT_SOUND_PACK
    SOUND_PACKS: List[str] = field(default_factory=lambda: SOUND_PACKS)
    
    # Support
    SUPPORT_CHANNEL_LINK: str = SUPPORT_CHANNEL_LINK
    SUPPORT_GROUP_LINK: str = SUPPORT_GROUP_LINK
    
    # Database
    DB_MIN_SIZE: int = DB_MIN_SIZE
    DB_MAX_SIZE: int = DB_MAX_SIZE
    DB_COMMAND_TIMEOUT: int = DB_COMMAND_TIMEOUT
    DB_CONNECTION_TIMEOUT: int = DB_CONNECTION_TIMEOUT
    DB_IDLE_TIMEOUT: int = DB_IDLE_TIMEOUT
    DB_POOL_MAX: int = DB_POOL_MAX
    SKIP_AUTO_MIGRATIONS: bool = SKIP_AUTO_MIGRATIONS
    MANUAL_MIGRATION: bool = MANUAL_MIGRATION
    
    # Logging
    LOG_LEVEL: str = LOG_LEVEL
    LOG_FORMAT: str = LOG_FORMAT
    LOG_TO_FILE: bool = LOG_TO_FILE
    
    # Python
    PYTHON_VERSION: str = PYTHON_VERSION
    
    # Rate Limiting
    MAX_OTP_REQUESTS: int = MAX_OTP_REQUESTS
    MAX_DEPOSIT_REQUESTS: int = MAX_DEPOSIT_REQUESTS
    MAX_CASHOUT_REQUESTS: int = MAX_CASHOUT_REQUESTS
    MAX_TRANSFER_REQUESTS: int = MAX_TRANSFER_REQUESTS
    RATE_LIMIT_WINDOW: int = RATE_LIMIT_WINDOW
    GAME_RATE_LIMIT_MAX: int = GAME_RATE_LIMIT_MAX
    AUTH_RATE_LIMIT_MAX: int = AUTH_RATE_LIMIT_MAX
    
    # Payment
    PAYMENT_ACCOUNTS: Dict[str, str] = field(default_factory=lambda: PAYMENT_ACCOUNTS)
    ACCOUNT_HOLDER: str = ACCOUNT_HOLDER
    PAYMENT_METHODS: List[str] = field(default_factory=lambda: PAYMENT_METHODS)
    PAYMENT_WEBHOOK_SECRET: str = PAYMENT_WEBHOOK_SECRET
    
    # OTP
    OTP_EXPIRY_MINUTES: int = OTP_EXPIRY_MINUTES
    OTP_LENGTH: int = OTP_LENGTH
    OTP_MAX_ATTEMPTS: int = OTP_MAX_ATTEMPTS
    
    # Cache
    CARTELA_CACHE_EXPIRY: int = CARTELA_CACHE_EXPIRY
    PLAYER_SESSION_TIMEOUT: int = PLAYER_SESSION_TIMEOUT
    
    # API
    BOT_API_TIMEOUT: int = BOT_API_TIMEOUT
    BOT_API_RETRIES: int = BOT_API_RETRIES
    BOT_API_RETRY_DELAY: int = BOT_API_RETRY_DELAY
    
    # CORS
    CORS_ORIGINS: List[str] = field(default_factory=lambda: CORS_ORIGINS)
    
    # Features
    ENABLE_REFERRAL: bool = ENABLE_REFERRAL
    ENABLE_TOURNAMENT: bool = ENABLE_TOURNAMENT
    ENABLE_DAILY_BONUS: bool = ENABLE_DAILY_BONUS
    ENABLE_WITHDRAWAL_FEE: bool = ENABLE_WITHDRAWAL_FEE
    
    # Withdrawal
    MIN_WITHDRAWAL: float = MIN_WITHDRAWAL
    MAX_WITHDRAWAL: float = MAX_WITHDRAWAL
    WITHDRAWAL_FEE_PERCENTAGE: float = WITHDRAWAL_FEE_PERCENTAGE
    WITHDRAWAL_PROCESSING_TIME: int = WITHDRAWAL_PROCESSING_TIME
    
    # Deposit
    MIN_DEPOSIT: float = MIN_DEPOSIT
    MAX_DEPOSIT: float = MAX_DEPOSIT
    DEPOSIT_BONUS_PERCENTAGE: float = DEPOSIT_BONUS_PERCENTAGE
    
    # Transfer
    MIN_TRANSFER: float = MIN_TRANSFER
    MAX_TRANSFER: float = MAX_TRANSFER
    TRANSFER_DAILY_LIMIT: float = TRANSFER_DAILY_LIMIT
    TRANSFER_FEE_PERCENTAGE: float = TRANSFER_FEE_PERCENTAGE
    
    # WebSocket
    WS_PING_INTERVAL: int = WS_PING_INTERVAL
    WS_PING_TIMEOUT: int = WS_PING_TIMEOUT
    WS_RECONNECT_DELAY: int = WS_RECONNECT_DELAY
    WS_MAX_RECONNECT_ATTEMPTS: int = WS_MAX_RECONNECT_ATTEMPTS
    
    # JWT
    JWT_EXPIRY_HOURS: int = JWT_EXPIRY_HOURS
    JWT_REFRESH_EXPIRY_DAYS: int = JWT_REFRESH_EXPIRY_DAYS
    JWT_ALGORITHM: str = JWT_ALGORITHM
    
    # Session
    ADMIN_SESSION_EXPIRY: str = ADMIN_SESSION_EXPIRY
    PLAYER_SESSION_EXPIRY: str = PLAYER_SESSION_EXPIRY


# ==================== HELPER FUNCTIONS ====================

def get_payment_account(method: str) -> str:
    """Get payment account number for given method"""
    return PAYMENT_ACCOUNTS.get(method.upper(), "")


def is_valid_payment_method(method: str) -> bool:
    """Check if payment method is valid"""
    return method.upper() in PAYMENT_ACCOUNTS


def get_support_links() -> dict:
    """Get support channel and group links"""
    return SUPPORT_LINKS.copy()


def get_game_url(with_params: bool = False, params: dict = None) -> str:
    """Get game URL with optional query parameters"""
    url = GAME_WEB_URL
    if with_params and params:
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    return url


def get_admin_url(with_params: bool = False, params: dict = None) -> str:
    """Get admin URL with optional query parameters"""
    url = ADMIN_URL
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
        "admin_email": ADMIN_EMAIL,
        "flask_port": FLASK_PORT,
        "game_web_url": GAME_WEB_URL,
        "cartela_price": CARTELA_PRICE,
        "min_balance_for_play": MIN_BALANCE_FOR_PLAY,
        "max_cartelas": MAX_CARTELAS,
        "win_percentages": WIN_PERCENTAGES,
        "default_win_percentage": DEFAULT_WIN_PERCENTAGE,
        "payment_methods": PAYMENT_METHODS,
        "skip_auto_migrations": SKIP_AUTO_MIGRATIONS,
        "log_level": LOG_LEVEL,
        "otp_expiry_minutes": OTP_EXPIRY_MINUTES,
        "node_env": NODE_ENV,
        "python_version": PYTHON_VERSION,
        "features": {
            "referral": ENABLE_REFERRAL,
            "tournament": ENABLE_TOURNAMENT,
            "daily_bonus": ENABLE_DAILY_BONUS,
            "withdrawal_fee": ENABLE_WITHDRAWAL_FEE
        }
    }


def get_rate_limits() -> dict:
    """Get all rate limit configurations"""
    return {
        "otp": {"max": MAX_OTP_REQUESTS, "window": RATE_LIMIT_WINDOW},
        "deposit": {"max": MAX_DEPOSIT_REQUESTS, "window": RATE_LIMIT_WINDOW},
        "cashout": {"max": MAX_CASHOUT_REQUESTS, "window": RATE_LIMIT_WINDOW},
        "transfer": {"max": MAX_TRANSFER_REQUESTS, "window": RATE_LIMIT_WINDOW},
        "game": {"max": GAME_RATE_LIMIT_MAX, "window": 60},
        "auth": {"max": AUTH_RATE_LIMIT_MAX, "window": 300}
    }


def is_production() -> bool:
    """Check if running in production mode"""
    return NODE_ENV == "production"


def is_development() -> bool:
    """Check if running in development mode"""
    return NODE_ENV == "development"


# ==================== VALIDATION ====================

def validate_config() -> bool:
    """Validate critical configuration values"""
    errors = []
    warnings = []
    
    # Validate BOT_TOKEN
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        errors.append("BOT_TOKEN appears invalid (should contain colon)")
    
    # Validate ADMIN_CHAT_ID
    if not ADMIN_CHAT_ID or not ADMIN_CHAT_ID.isdigit():
        errors.append("ADMIN_CHAT_ID should be numeric")
    
    # Validate DATABASE_URL
    if not DATABASE_URL.startswith("postgresql://"):
        errors.append("DATABASE_URL should start with postgresql://")
    
    # Validate FLASK_PORT
    if not 1 <= FLASK_PORT <= 65535:
        errors.append(f"FLASK_PORT {FLASK_PORT} is invalid")
    
    # Validate WIN_PERCENTAGES
    for p in WIN_PERCENTAGES:
        if p not in [70, 75, 76, 80]:
            warnings.append(f"WIN_PERCENTAGES contains unusual value: {p}")
    
    # Validate payment methods
    for method in PAYMENT_METHODS:
        if not PAYMENT_ACCOUNTS.get(method):
            warnings.append(f"Payment method {method} has no account number")
    
    # Validate withdrawal limits
    if MIN_WITHDRAWAL < 0:
        errors.append(f"MIN_WITHDRAWAL cannot be negative: {MIN_WITHDRAWAL}")
    
    if MAX_WITHDRAWAL < MIN_WITHDRAWAL:
        errors.append(f"MAX_WITHDRAWAL ({MAX_WITHDRAWAL}) is less than MIN_WITHDRAWAL ({MIN_WITHDRAWAL})")
    
    # Log warnings and errors
    for warning in warnings:
        print(f"⚠️ Config warning: {warning}")
    
    if errors:
        for error in errors:
            print(f"❌ Config error: {error}")
        return False
    
    return True


# ==================== INITIALIZATION ====================

# Create global config instance
config = Config()

# Validate configuration on import (unless in testing)
if __name__ != "__main__":
    try:
        if not validate_config():
            print("⚠️ Configuration has errors but continuing...")
    except Exception as e:
        print(f"⚠️ Config validation error: {e}")

# Print configuration summary in development
if not is_production():
    print("""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                         📋 BOT CONFIGURATION SUMMARY                              ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║  Bot Token:      ✅ Set                                                          ║
║  Admin Chat ID:  {:<48}║
║  Database URL:   {:<48}║
║  Flask Port:     {:<48}║
║  Game URL:       {:<48}║
║  Cartela Price:  {} ETB {:<41}║
║  Max Cartelas:   {} {:<48}║
║  Win % Options:  {} {:<48}║
║  Min Withdrawal: {} ETB {:<48}║
║  Max Withdrawal: {} ETB {:<48}║
║  Features:       Referral={}, Tournament={}, DailyBonus={} {:<23}║
╚═══════════════════════════════════════════════════════════════════════════════════╝
    """.format(
        ADMIN_CHAT_ID,
        (DATABASE_URL[:45] + "...") if len(DATABASE_URL) > 48 else DATABASE_URL,
        FLASK_PORT,
        GAME_WEB_URL[:48] if len(GAME_WEB_URL) > 48 else GAME_WEB_URL,
        CARTELA_PRICE, "",
        MAX_CARTELAS, "",
        WIN_PERCENTAGES, "",
        MIN_WITHDRAWAL, "",
        MAX_WITHDRAWAL, "",
        ENABLE_REFERRAL, ENABLE_TOURNAMENT, ENABLE_DAILY_BONUS, ""
    ))

# ==================== EXPORTS ====================

__all__ = [
    'Config',
    'config',
    'get_payment_account',
    'is_valid_payment_method',
    'get_support_links',
    'get_game_url',
    'get_admin_url',
    'get_env_info',
    'get_rate_limits',
    'is_production',
    'is_development',
    'validate_config',
    
    # Direct constants (for backward compatibility)
    'BOT_TOKEN',
    'ADMIN_CHAT_ID',
    'DATABASE_URL',
    'JWT_SECRET',
    'API_SECRET',
    'FLASK_PORT',
    'GAME_WEB_URL',
    'CARTELA_PRICE',
    'MIN_BALANCE_FOR_PLAY',
    'MAX_CARTELAS',
    'WIN_PERCENTAGES',
    'PAYMENT_ACCOUNTS',
    'SUPPORT_CHANNEL_LINK',
    'SUPPORT_GROUP_LINK',
    'LOG_LEVEL',
    'OTP_EXPIRY_MINUTES',
    'OTP_LENGTH',
]