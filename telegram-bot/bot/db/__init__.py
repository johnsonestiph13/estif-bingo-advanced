# telegram-bot/bot/db/__init__.py
# Estif Bingo 24/7 - Database Module Exports (Complete)

from .database import Database, database

# ==================== EXPORTS ====================
__all__ = [
    'Database',
    'database',
    'get_db',
    'get_db_class',
    'DB_INFO',
    'check_connection',
]

# ==================== HELPER FUNCTIONS ====================
def get_db():
    """
    Get the global database instance.
    
    Returns:
        Database: The global database instance
    """
    return database


def get_db_class():
    """
    Get the Database class.
    
    Returns:
        Database: The Database class
    """
    return Database


async def check_connection() -> bool:
    """
    Check if database connection is active.
    
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        if database._pool:
            return await database.health_check()
        return False
    except Exception:
        return False


def get_db_status() -> dict:
    """
    Get database connection status.
    
    Returns:
        dict: Status information
    """
    return {
        'initialized': database._pool is not None,
        'pool_size': database._pool.get_size() if database._pool else 0,
        'max_pool_size': database._pool.get_max_size() if database._pool else 0,
    }


# ==================== DATABASE INFO ====================
DB_INFO = {
    'version': '3.0.0',
    'author': 'Estif Bingo Team',
    'tables': [
        'users',
        'game_rounds',
        'game_transactions',
        'game_settings',
        'pending_withdrawals',
        'otp_codes',
        'auth_codes',
        'commission_logs',
        'migrations'
    ],
    'indexes': [
        'idx_users_phone',
        'idx_users_balance',
        'idx_users_username',
        'idx_users_registered',
        'idx_users_last_seen',
        'idx_withdrawals_status',
        'idx_withdrawals_telegram',
        'idx_withdrawals_pending',
        'idx_otp_expires',
        'idx_otp_telegram',
        'idx_auth_expires',
        'idx_auth_code',
        'idx_auth_telegram',
        'idx_game_transactions_telegram',
        'idx_game_transactions_timestamp',
        'idx_game_rounds_timestamp',
        'idx_commission_logs_changed_at'
    ],
    'features': [
        'Connection Pooling',
        'User Management',
        'Balance Operations',
        'Auth Code Generation',
        'OTP Generation & Verification',
        'Withdrawal Management',
        'Game Transaction Logging',
        'Settings Management',
        'Commission Logging',
        'Player Search',
        'Leaderboard',
        'Health Check'
    ],
    'methods': {
        'user_operations': [
            'get_user',
            'get_user_by_phone',
            'get_user_by_username',
            'create_user',
            'update_user',
            'update_last_seen'
        ],
        'balance_operations': [
            'update_balance',
            'add_balance',
            'deduct_balance',
            'get_balance'
        ],
        'auth_operations': [
            'create_auth_code',
            'verify_auth_code',
            'consume_auth_code'
        ],
        'otp_operations': [
            'store_otp',
            'verify_otp'
        ],
        'withdrawal_operations': [
            'add_pending_withdrawal',
            'get_pending_withdrawals',
            'get_withdrawal_by_id',
            'approve_withdrawal',
            'reject_withdrawal'
        ],
        'settings_operations': [
            'get_setting',
            'set_setting',
            'get_win_percentage',
            'set_win_percentage',
            'get_default_sound_pack',
            'set_default_sound_pack'
        ],
        'statistics': [
            'get_total_users_count',
            'get_total_deposits',
            'get_top_winners',
            'get_commission_history',
            'get_commission_stats'
        ],
        'game_operations': [
            'log_game_transaction',
            'get_user_transactions'
        ],
        'search': [
            'search_players'
        ],
        'health': [
            'health_check'
        ]
    }
}


# ==================== INITIALIZATION CHECK ====================
def is_initialized() -> bool:
    """
    Check if the database has been initialized.
    
    Returns:
        bool: True if initialized, False otherwise
    """
    return database._pool is not None