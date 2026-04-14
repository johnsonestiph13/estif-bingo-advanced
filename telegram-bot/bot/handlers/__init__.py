# telegram-bot/bot/handlers/__init__.py
# Estif Bingo 24/7 - All Handlers Exports (UPDATED - Removed quick_play_callback)

# ==================== CORE HANDLERS ====================
from .start import start, language_callback
from .register import register, handle_contact, register_phone, register_cancel, play, PHONE
from .balance import balance
from .invite import invite
from .contact import contact_center
from .bingo_otp import bingo_otp

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
    METHOD, 
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
    AMOUNT,
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

# ==================== GAME HANDLERS (NO quick_play_callback) ====================
from .game import (
    play_command,           # Main /play command handler
    game_callback,          # Web app data callback handler
    stats_callback,         # Player statistics handler
    leaderboard_callback,   # Leaderboard display handler
    back_to_game_callback,  # Back to game navigation handler
    start_game_handlers     # Background task initializer
)

# ==================== LEGACY PLAY HANDLER (DEPRECATED) ====================
# Keeping for backward compatibility - points to new play_command
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
    'METHOD',
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
    'AMOUNT',
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
    
    # Game handlers (NO quick_play_callback)
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
        ('balance', 'Check your current balance'),
        ('deposit', 'Add funds to your account'),
        ('cashout', 'Withdraw your winnings'),
        ('transfer', 'Transfer funds to another player'),
        ('play', 'Play Bingo game 🎮'),
        ('invite', 'Get your referral link'),
        ('contact', 'Contact support'),
        ('bingo_otp', 'Get OTP for game access'),
    ],
    'admin_commands': [
        ('admin', 'Admin control panel'),
        ('approve_deposit', 'Approve deposit'),
        ('reject_deposit', 'Reject deposit'),
        ('approve_cashout', 'Approve withdrawal'),
        ('reject_cashout', 'Reject withdrawal'),
        ('stats', 'View bot statistics'),
        ('setwin', 'Set win percentage'),
    ],
    'game_features': [
        'Web App Bingo Game',
        'Live Statistics',
        'Leaderboard',
        'Auto-balance updates',
    ]
}