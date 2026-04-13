# bot/texts/emojis.py
# Estif Bingo 24/7 - Complete Emoji Mappings

EMOJIS = {
    # ==================== GAME EMOJIS ====================
    'game': '🎮',
    'bingo': '🎰',
    'win': '🎉',
    'lose': '😢',
    'jackpot': '💰',
    'cartela': '🎫',
    'numbers': '🔢',
    'dice': '🎲',
    'trophy': '🏆',
    'medal': '🥇',
    'star': '⭐',
    'lightning': '⚡',
    'fire': '🔥',
    'crown': '👑',
    'gift': '🎁',
    'bonus': '🎯',
    'target': '🎯',
    'users': '👥',
    'click': '👇',
    'four_leaf_clover': '🍀',
    'muscle': '💪',
    
    # ==================== ACTION EMOJIS ====================
    'play': '▶️',
    'pause': '⏸️',
    'stop': '⏹️',
    'next': '⏭️',
    'back': '🔙',
    'refresh': '🔄',
    'settings': '⚙️',
    'help': '❓',
    'info': 'ℹ️',
    'warning': '⚠️',
    'error': '❌',
    'success': '✅',
    'question': '❓',
    'idea': '💡',
    
    # ==================== FINANCIAL EMOJIS ====================
    'money': '💰',
    'deposit': '💳',
    'withdraw': '💸',
    'balance': '📊',
    'transaction': '📝',
    'bank': '🏦',
    'phone': '📱',
    'transfer': '🔄',
    
    # ==================== STATUS EMOJIS ====================
    'pending': '⏳',
    'approved': '✅',
    'rejected': '❌',
    'active': '🟢',
    'inactive': '🔴',
    'loading': '🔄',
    'processing': '⚙️',
    'complete': '✅',
    'failed': '❌',
    'locked': '🔒',
    'unlocked': '🔓',
    'verified': '✓',
    'unverified': '✗',
    
    # ==================== TIME EMOJIS ====================
    'clock': '⏰',
    'calendar': '📅',
    'hourglass': '⌛',
    'waiting': '⏰',
    
    # ==================== COMMUNICATION EMOJIS ====================
    'chat': '💬',
    'support': '📞',
    'email': '📧',
    'link': '🔗',
    'notification': '🔔',
    
    # ==================== STATISTICS & DATA ====================
    'stats': '📊',
    'statistics': '📈',
    'leaderboard': '🏆',
    'rank': '🎖️',
    'score': '⭐',
    'level': '🔰',
    
    # ==================== GAME SPECIFIC ====================
    'selection': '🎯',
    'draw': '🎲',
    'round': '🔄',
    'winner': '🏆',
    'loser': '😢',
    
    # ==================== ACTIONS ====================
    'select': '✅',
    'deselect': '❌',
    'confirm': '✓',
    'cancel': '✗',
    'submit': '📤',
    'reset': '🔄',
    
    # ==================== NAVIGATION ====================
    'menu': '📋',
    'home': '🏠',
    'exit': '🚪',
    
    # ==================== ALERTS & STATUS ====================
    'alert': '⚠️',
    'critical': '🔴',
    
    # ==================== SEARCH & FILTERS ====================
    'search': '🔍',
    'filter': '🔽',
    'export': '📎',
    'import': '📥',
    
    # ==================== MESSAGING ====================
    'checking': '🔍',
    'updating': '🔄',
    'waiting': '⏰',
    'complete': '✅',
    'failed': '❌',
    
    # ==================== ADDITIONAL COMMON EMOJIS ====================
    'check': '✅',
    'cross': '❌',
    'plus': '➕',
    'minus': '➖',
    'arrow_up': '⬆️',
    'arrow_down': '⬇️',
    'arrow_left': '⬅️',
    'arrow_right': '➡️',
}

# ==================== HELPER FUNCTIONS ====================

def get_emoji(key: str, fallback: str = '📌') -> str:
    """
    Safely get emoji by key with fallback.
    
    Args:
        key: The emoji key to look up
        fallback: Default emoji if key not found
    
    Returns:
        The emoji character or fallback
    """
    return EMOJIS.get(key, fallback)


def get_game_emoji() -> str:
    """Get game emoji"""
    return get_emoji('game')


def get_win_emoji() -> str:
    """Get win celebration emoji"""
    return get_emoji('win')


def get_lose_emoji() -> str:
    """Get lose emoji"""
    return get_emoji('lose')


def get_money_emoji() -> str:
    """Get money emoji"""
    return get_emoji('money')


def get_cartela_emoji() -> str:
    """Get cartela emoji"""
    return get_emoji('cartela')


def get_trophy_emoji() -> str:
    """Get trophy emoji"""
    return get_emoji('trophy')


def get_warning_emoji() -> str:
    """Get warning emoji"""
    return get_emoji('warning')


def get_error_emoji() -> str:
    """Get error emoji"""
    return get_emoji('error')


def get_success_emoji() -> str:
    """Get success emoji"""
    return get_emoji('success')


def get_clock_emoji() -> str:
    """Get clock emoji"""
    return get_emoji('clock')


def get_stats_emoji() -> str:
    """Get statistics emoji"""
    return get_emoji('stats')


def get_leaderboard_emoji() -> str:
    """Get leaderboard emoji"""
    return get_emoji('leaderboard')


def get_deposit_emoji() -> str:
    """Get deposit emoji"""
    return get_emoji('deposit')


def get_withdraw_emoji() -> str:
    """Get withdraw emoji"""
    return get_emoji('withdraw')


def get_balance_emoji() -> str:
    """Get balance emoji"""
    return get_emoji('balance')


def get_transfer_emoji() -> str:
    """Get transfer emoji"""
    return get_emoji('transfer')


def get_phone_emoji() -> str:
    """Get phone emoji"""
    return get_emoji('phone')


def get_support_emoji() -> str:
    """Get support emoji"""
    return get_emoji('support')


def get_settings_emoji() -> str:
    """Get settings emoji"""
    return get_emoji('settings')


def get_help_emoji() -> str:
    """Get help emoji"""
    return get_emoji('help')


def get_info_emoji() -> str:
    """Get info emoji"""
    return get_emoji('info')


def get_refresh_emoji() -> str:
    """Get refresh emoji"""
    return get_emoji('refresh')


def get_back_emoji() -> str:
    """Get back emoji"""
    return get_emoji('back')


def get_next_emoji() -> str:
    """Get next emoji"""
    return get_emoji('next')


def get_play_emoji() -> str:
    """Get play emoji"""
    return get_emoji('play')


def get_pause_emoji() -> str:
    """Get pause emoji"""
    return get_emoji('pause')


def get_stop_emoji() -> str:
    """Get stop emoji"""
    return get_emoji('stop')


def get_calendar_emoji() -> str:
    """Get calendar emoji"""
    return get_emoji('calendar')


def get_star_emoji() -> str:
    """Get star emoji"""
    return get_emoji('star')


def get_fire_emoji() -> str:
    """Get fire emoji"""
    return get_emoji('fire')


def get_gift_emoji() -> str:
    """Get gift emoji"""
    return get_emoji('gift')


def get_bonus_emoji() -> str:
    """Get bonus emoji"""
    return get_emoji('bonus')


def get_lock_emoji() -> str:
    """Get lock emoji"""
    return get_emoji('locked')


def get_unlock_emoji() -> str:
    """Get unlock emoji"""
    return get_emoji('unlocked')


def get_search_emoji() -> str:
    """Get search emoji"""
    return get_emoji('search')


def get_filter_emoji() -> str:
    """Get filter emoji"""
    return get_emoji('filter')


def get_export_emoji() -> str:
    """Get export emoji"""
    return get_emoji('export')


def get_import_emoji() -> str:
    """Get import emoji"""
    return get_emoji('import')


# ==================== EMOJI FORMATTING HELPERS ====================

def format_with_emoji(text: str, emoji_key: str) -> str:
    """Format text with emoji prefix"""
    emoji = get_emoji(emoji_key)
    return f"{emoji} {text}"


def format_status(status: str, is_success: bool = True) -> str:
    """Format status message with appropriate emoji"""
    emoji = get_success_emoji() if is_success else get_error_emoji()
    return f"{emoji} {status}"


def format_balance(amount: float) -> str:
    """Format balance with money emoji"""
    return f"{get_money_emoji()} `{amount:.2f} ETB`"


def format_win(amount: float) -> str:
    """Format win amount with celebration emoji"""
    return f"{get_win_emoji()} `+{amount:.2f} ETB`"


def format_loss(amount: float) -> str:
    """Format loss amount with sad emoji"""
    return f"{get_lose_emoji()} `-{amount:.2f} ETB`"


# ==================== EXPORTS ====================

__all__ = [
    # Main dictionary
    'EMOJIS',
    
    # Helper functions
    'get_emoji',
    'get_game_emoji',
    'get_win_emoji',
    'get_lose_emoji',
    'get_money_emoji',
    'get_cartela_emoji',
    'get_trophy_emoji',
    'get_warning_emoji',
    'get_error_emoji',
    'get_success_emoji',
    'get_clock_emoji',
    'get_stats_emoji',
    'get_leaderboard_emoji',
    'get_deposit_emoji',
    'get_withdraw_emoji',
    'get_balance_emoji',
    'get_transfer_emoji',
    'get_phone_emoji',
    'get_support_emoji',
    'get_settings_emoji',
    'get_help_emoji',
    'get_info_emoji',
    'get_refresh_emoji',
    'get_back_emoji',
    'get_next_emoji',
    'get_play_emoji',
    'get_pause_emoji',
    'get_stop_emoji',
    'get_calendar_emoji',
    'get_star_emoji',
    'get_fire_emoji',
    'get_gift_emoji',
    'get_bonus_emoji',
    'get_lock_emoji',
    'get_unlock_emoji',
    'get_search_emoji',
    'get_filter_emoji',
    'get_export_emoji',
    'get_import_emoji',
    
    # Formatting helpers
    'format_with_emoji',
    'format_status',
    'format_balance',
    'format_win',
    'format_loss',
]