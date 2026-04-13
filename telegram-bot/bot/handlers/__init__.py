# telegram-bot/bot/handlers/__init__.py
# Estif Bingo 24/7 - All Handlers Exports (UPDATED with Game Handlers)

# ==================== CORE HANDLERS ====================
from .start import start, language_callback
from .register import register, handle_contact
from .balance import balance
from .invite import invite
from .contact import contact_center
from .bingo_otp import bingo_otp

# ==================== FINANCIAL HANDLERS ====================
from .deposit import (
    deposit, 
    deposit_callback, 
    handle_deposit_amount, 
    handle_deposit_screenshot
)
from .cashout import (
    cashout, 
    cashout_callback, 
    handle_cashout_amount, 
    handle_cashout_account
)

# ==================== TRANSFER HANDLER ====================
from .transfer import (
    transfer,
    transfer_phone,
    transfer_amount,
    transfer_confirm,
    transfer_cancel,
    transfer_cancel_command,
    PHONE_NUMBER,
    AMOUNT,
    CONFIRM
)

# ==================== ADMIN HANDLERS ====================
from .admin_commands import (
    approve_deposit,
    reject_deposit,
    approve_cashout,
    reject_cashout
)

# ==================== GAME HANDLERS (NEW - ULTRA OPTIMIZED) ====================
from .game import (
    play_command,           # Main /play command handler
    game_callback,          # Web app data callback handler
    quick_play_callback,    # Quick play button handler (1-4 cartelas)
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
    'balance',
    'invite',
    'contact_center',
    'bingo_otp',
    'legacy_play',  # Deprecated, use play_command instead
    
    # Financial handlers
    'deposit',
    'deposit_callback',
    'handle_deposit_amount',
    'handle_deposit_screenshot',
    'cashout',
    'cashout_callback',
    'handle_cashout_amount',
    'handle_cashout_account',
    
    # Transfer handlers
    'transfer',
    'transfer_phone',
    'transfer_amount',
    'transfer_confirm',
    'transfer_cancel',
    'transfer_cancel_command',
    'PHONE_NUMBER',
    'AMOUNT',
    'CONFIRM',
    
    # Admin handlers
    'approve_deposit',
    'reject_deposit',
    'approve_cashout',
    'reject_cashout',
    
    # Game handlers (NEW)
    'play_command',          # Main game launcher
    'game_callback',         # Web app data receiver
    'quick_play_callback',   # Quick play buttons
    'stats_callback',        # Player stats
    'leaderboard_callback',  # Leaderboard
    'back_to_game_callback', # Navigation
    'start_game_handlers',   # Background tasks
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
        'play': play_command,  # Using new play_command
        
        # Callback handlers
        'language_callback': language_callback,
        'deposit_callback': deposit_callback,
        'cashout_callback': cashout_callback,
        'quick_play_callback': quick_play_callback,
        'stats_callback': stats_callback,
        'leaderboard_callback': leaderboard_callback,
        'back_to_game_callback': back_to_game_callback,
        
        # Step handlers
        'handle_deposit_amount': handle_deposit_amount,
        'handle_deposit_screenshot': handle_deposit_screenshot,
        'handle_cashout_amount': handle_cashout_amount,
        'handle_cashout_account': handle_cashout_account,
        'transfer_phone': transfer_phone,
        'transfer_amount': transfer_amount,
        'transfer_confirm': transfer_confirm,
        'transfer_cancel': transfer_cancel,
        
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
        ('approve', 'Approve pending transactions'),
        ('reject', 'Reject pending transactions'),
        ('stats', 'View bot statistics'),
        ('setwin', 'Set win percentage'),
    ],
    'game_features': [
        'Web App Bingo Game',
        'Quick Play (1-4 cartelas)',
        'Live Statistics',
        'Leaderboard',
        'Auto-balance updates',
    ]
}