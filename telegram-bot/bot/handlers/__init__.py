# telegram-bot/bot/handlers/__init__.py
# Estif Bingo 24/7 - Complete Handlers Exports (FULLY UPDATED & FIXED)

# ==================== CORE HANDLERS ====================
from .start import start, language_callback
from .register import register, handle_contact, register_phone, register_cancel, play, PHONE
from .balance import balance
from .invite import invite
from .contact import contact_center
from .bingo_otp import bingo_otp, verify_otp

# ==================== FINANCIAL HANDLERS ====================
from .deposit import (
    deposit, 
    deposit_callback, 
    deposit_amount, 
    deposit_screenshot, 
    deposit_cancel,
    AMOUNT as DEPOSIT_AMOUNT, 
    SCREENSHOT
)
from .cashout import (
    cashout, 
    cashout_callback, 
    cashout_amount, 
    cashout_account, 
    cashout_cancel,
    AMOUNT as CASHOUT_AMOUNT, 
    ACCOUNT
)

# ==================== TRANSFER HANDLER ====================
from .transfer import (
    transfer,
    transfer_phone,
    transfer_amount,
    transfer_confirm,
    transfer_cancel,
    transfer_cancel_command,
    transfer_add_amount,
    transfer_subtract_amount,
    PHONE_NUMBER,
    AMOUNT as TRANSFER_AMOUNT,
    CONFIRM
)

# ==================== ADMIN HANDLERS ====================
from .admin_commands import (
    approve_deposit,
    reject_deposit,
    approve_cashout,
    reject_cashout,
    admin_panel,
    admin_callback,
    set_win_percentage,
    stats_command
)

# ==================== GAME HANDLERS ====================
from .game import (
    play_command,
    game_callback,
    stats_callback,
    leaderboard_callback,
    back_to_game_callback,
    start_game_handlers
)

# ==================== LEGACY PLAY HANDLER (DEPRECATED) ====================
from .register import play as legacy_play

# ==================== EXPORTS ====================
__all__ = [
    # Core handlers
    'start',
    'language_callback',
    'register',
    'handle_contact',
    'register_phone',
    'register_cancel',
    'PHONE',
    'balance',
    'invite',
    'contact_center',
    'bingo_otp',
    'verify_otp',
    'legacy_play',
    'play',
    
    # Financial handlers
    'deposit',
    'deposit_callback',
    'deposit_amount',
    'deposit_screenshot',
    'deposit_cancel',
    'DEPOSIT_AMOUNT',
    'SCREENSHOT',
    'cashout',
    'cashout_callback',
    'cashout_amount',
    'cashout_account',
    'cashout_cancel',
    'CASHOUT_AMOUNT',
    'ACCOUNT',
    
    # Transfer handlers
    'transfer',
    'transfer_phone',
    'transfer_amount',
    'transfer_confirm',
    'transfer_cancel',
    'transfer_cancel_command',
    'transfer_add_amount',
    'transfer_subtract_amount',
    'PHONE_NUMBER',
    'TRANSFER_AMOUNT',
    'CONFIRM',
    
    # Admin handlers
    'approve_deposit',
    'reject_deposit',
    'approve_cashout',
    'reject_cashout',
    'admin_panel',
    'admin_callback',
    'set_win_percentage',
    'stats_command',
    
    # Game handlers
    'play_command',
    'game_callback',
    'stats_callback',
    'leaderboard_callback',
    'back_to_game_callback',
    'start_game_handlers',
]

# ==================== HELPER FOR QUICK IMPORT ====================
def get_all_handlers():
    """Return all handler functions for easy registration"""
    return {
        # Command handlers
        'start': start,
        'register': register,
        'balance': balance,
        'invite': invite,
        'contact_center': contact_center,
        'bingo_otp': bingo_otp,
        'verify_otp': verify_otp,
        'deposit': deposit,
        'cashout': cashout,
        'transfer': transfer,
        'play': play_command,
        'admin': admin_panel,
        'setwin': set_win_percentage,
        'stats': stats_command,
        
        # Callback handlers
        'language_callback': language_callback,
        'deposit_callback': deposit_callback,
        'cashout_callback': cashout_callback,
        'stats_callback': stats_callback,
        'leaderboard_callback': leaderboard_callback,
        'back_to_game_callback': back_to_game_callback,
        'admin_callback': admin_callback,
        
        # Step handlers
        'deposit_amount': deposit_amount,
        'deposit_screenshot': deposit_screenshot,
        'deposit_cancel': deposit_cancel,
        'cashout_amount': cashout_amount,
        'cashout_account': cashout_account,
        'cashout_cancel': cashout_cancel,
        'transfer_phone': transfer_phone,
        'transfer_amount': transfer_amount,
        'transfer_confirm': transfer_confirm,
        'transfer_cancel': transfer_cancel,
        'transfer_add_amount': transfer_add_amount,
        'transfer_subtract_amount': transfer_subtract_amount,
        
        # Admin handlers
        'approve_deposit': approve_deposit,
        'reject_deposit': reject_deposit,
        'approve_cashout': approve_cashout,
        'reject_cashout': reject_cashout,
    }

# ==================== HANDLER REGISTRATION INFO ====================
HANDLERS_INFO = {
    'commands': [
        ('start', 'Start the bot and see welcome message'),
        ('register', 'Register with your phone number'),
        ('balance', 'Check your current balance and game statistics'),
        ('deposit', 'Add funds to your account'),
        ('cashout', 'Withdraw your winnings'),
        ('transfer', 'Transfer funds to another player'),
        ('play', 'Play Bingo game 🎮'),
        ('invite', 'Get your referral link'),
        ('contact', 'Contact support'),
        ('bingo_otp', 'Get OTP for game access'),
        ('verify', 'Verify OTP code'),
    ],
    'admin_commands': [
        ('admin', 'Admin control panel'),
        ('approve_deposit', 'Approve deposit request'),
        ('reject_deposit', 'Reject deposit request'),
        ('approve_cashout', 'Approve withdrawal request'),
        ('reject_cashout', 'Reject withdrawal request'),
        ('stats', 'View bot statistics'),
        ('setwin', 'Set win percentage (70,75,76,80)'),
    ],
    'game_features': [
        'Web App Bingo Game',
        'Live Statistics',
        'Leaderboard',
        'Auto-balance updates',
        'Multi-device sync',
    ],
    'conversation_flows': [
        ('Deposit', 'Method → Amount → Screenshot'),
        ('Cashout', 'Method → Amount → Account'),
        ('Transfer', 'Phone → Amount → Confirm'),
        ('Register', 'Phone number entry'),
    ],
}

# ==================== VERSION INFO ====================
HANDLERS_VERSION = "3.0.0"
HANDLERS_AUTHOR = "Estif Bingo Team"