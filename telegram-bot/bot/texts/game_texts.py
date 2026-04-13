# telegram-bot/bot/texts/game_texts.py
# Estif Bingo 24/7 - Game-Specific Texts (FULLY FIXED)

from .emojis import get_emoji

# Helper function to safely get emoji
def _e(key: str) -> str:
    """Safely get emoji character"""
    return get_emoji(key)

# ==================== GAME TEXTS ====================
GAME_TEXTS = {
    'en': {
        # Game start
        'game_welcome': f"{_e('game')} *Welcome to Bingo Game!*\n\n"
                       f"{_e('money')} Balance: `{{balance:.2f}} ETB`\n"
                       f"{_e('cartela')} Cartela Price: `{{cartela_price}} ETB`\n"
                       f"{_e('stats')} Max Cartelas: `{{max_cartelas}}`\n"
                       f"{_e('target')} Win Percentage: `{{win_percentage}}%`\n\n"
                       f"Click the button below to start playing!",
        
        'game_start': f"{_e('play')} *Game Started!*\n\n"
                     f"{_e('cartela')} Cartelas: `{{cartelas}}`\n"
                     f"{_e('money')} Cost: `{{cost:.2f}} ETB`\n"
                     f"{_e('balance')} New Balance: `{{new_balance:.2f}} ETB`\n\n"
                     f"{_e('four_leaf_clover')} Good luck!",
        
        'game_win': f"{_e('win')} *CONGRATULATIONS! YOU WON!*\n\n"
                   f"{_e('money')} Winnings: `+{{amount:.2f}} ETB`\n"
                   f"{_e('balance')} New Balance: `{{new_balance:.2f}} ETB`\n"
                   f"{_e('trophy')} Total Wins: `{{total_wins}}`\n"
                   f"{_e('star')} Win Rate: `{{win_rate:.1f}}%`\n\n"
                   f"{_e('target')} Pattern: `{{pattern}}`\n"
                   f"{_e('cartela')} Cartela: `{{cartela_id}}`",
        
        'game_loss': f"{_e('lose')} *Better Luck Next Time!*\n\n"
                    f"{_e('stats')} Numbers Drawn: `{{numbers_drawn}}`\n"
                    f"{_e('target')} Closest Pattern: `{{closest_pattern}}`\n\n"
                    f"{_e('money')} Balance: `{{balance:.2f}} ETB`\n"
                    f"{_e('star')} Win Rate: `{{win_rate:.1f}}%`\n\n"
                    f"{_e('muscle')} Don't give up! Your win is coming!",
        
        'game_end': f"{_e('stop')} *Game Ended*\n\n"
                   f"{_e('stats')} Session Summary:\n"
                   f"• {_e('cartela')} Cartelas: `{{cartelas}}`\n"
                   f"• {_e('money')} Spent: `{{spent:.2f}} ETB`\n"
                   f"• {_e('win')} Won: `{{won:.2f}} ETB`\n"
                   f"• {_e('balance')} Net: `{{net:+.2f}} ETB`\n\n"
                   f"{_e('refresh')} Play again with /play",
        
        # Game stats (FIXED: Using double braces for rank placeholder)
        'stats_title': f"{_e('stats')} *Your Bingo Statistics*\n\n",
        'stats_games': f"{_e('game')} *Games:*\n• Played: `{{played}}`\n• Won: `{{won}}`\n• Win Rate: `{{rate:.1f}}%`\n\n",
        'stats_financial': f"{_e('money')} *Financial:*\n• Total Bet: `{{bet:.2f}} ETB`\n• Total Win: `{{win:.2f}} ETB`\n• Net Profit: `{{net:+.2f}} ETB`\n• Best Win: `{{best:.2f}} ETB`\n\n",
        'stats_time': f"{_e('clock')} *Last Played:* `{{last_played}}`\n\n",
        'stats_rank': f"{_e('trophy')} *Rank:* `{{rank}}`",  # ← FIXED: Double braces for placeholder
        
        # Leaderboard
        'leaderboard_title': f"{_e('trophy')} *BINGO LEADERBOARD* {_e('trophy')}\n\n",
        'leaderboard_entry': "{emoji} *{username}* - {total_won:.0f} ETB won (Win Rate: {win_rate}%)\n",
        'leaderboard_empty': f"{_e('trophy')} *No players yet. Be the first!*\n",
        'leaderboard_updated': f"\n{_e('calendar')} *Updated:* `{{timestamp}}`",
        
        # Cartela messages
        'cartela_bought': f"{_e('cartela')} *Cartela Purchased!*\n\n"
                         f"{_e('cartela')} Cartela ID: `{{cartela_id}}`\n"
                         f"{_e('money')} Cost: `{{cost:.2f}} ETB`\n"
                         f"{_e('balance')} New Balance: `{{balance:.2f}} ETB`",
        
        'cartela_selected': f"{_e('success')} Cartela `{{cartela_id}}` selected",
        'cartela_deselected': f"{_e('warning')} Cartela `{{cartela_id}}` deselected",
        
        # Round messages
        'round_start': f"{_e('play')} *Round {{round_number}} Started!*\n\n"
                      f"{_e('cartela')} Active Cartelas: `{{cartelas}}`\n"
                      f"{_e('money')} Prize Pool: `{{pool:.2f}} ETB`\n"
                      f"{_e('target')} Win Chance: `{{win_percentage}}%`",
        
        'round_end': f"{_e('stop')} *Round {{round_number}} Ended!*\n\n"
                    f"{_e('target')} Winning Numbers: `{{numbers}}`\n"
                    f"{_e('trophy')} Winners: `{{winners}}`\n"
                    f"{_e('money')} Prize Pool: `{{pool:.2f}} ETB`",
        
        # Quick play
        'quick_play': f"{_e('lightning')} *Quick Play - {{cartelas}} Cartela{{s}}*\n\n"
                     f"{_e('money')} Cost: `{{cost:.2f}} ETB`\n"
                     f"{_e('target')} Win Chance: `{{win_percentage}}%`\n\n"
                     f"Click below to start!",
        
        'all_in': f"{_e('fire')} *ALL IN!*\n\n"
                 f"{_e('money')} Bet Amount: `{{amount:.2f}} ETB`\n"
                 f"{_e('cartela')} Cartelas: `{{cartelas}}`\n"
                 f"{_e('balance')} Remaining Balance: `{{remaining:.2f}} ETB`",
        
        # Settings
        'settings_updated': f"{_e('success')} Setting updated: `{{setting}}` = `{{value}}`",
        'settings_reset': f"{_e('success')} All settings reset to default",
        
        # Help
        'help_rules': f"{_e('help')} *Game Rules*\n\n"
                     f"1️⃣ Select 1-4 cartelas per round\n"
                     f"2️⃣ Numbers (1-75) are drawn randomly\n"
                     f"3️⃣ Match patterns on your cartela to win\n"
                     f"4️⃣ Win up to {{win_percentage}}% of the pool!\n\n"
                     f"{_e('target')} *Winning Patterns:*\n"
                     f"• Line (Horizontal/Vertical)\n"
                     f"• Diagonal\n"
                     f"• Four Corners\n"
                     f"• Full House (BINGO!)",
        
        'help_cartelas': f"{_e('cartela')} *About Cartelas*\n\n"
                        f"• Each cartela has 24 numbers + 1 free space\n"
                        f"• Numbers range from 1-75\n"
                        f"• Each cartela costs `{{price}} ETB`\n"
                        f"• Max {{max}} cartelas per round\n"
                        f"• More cartelas = higher win chance!",
        
        'help_payment': f"{_e('money')} *Payments & Prizes*\n\n"
                       f"{_e('money')} *Deposit:*\n"
                       f"• Minimum: `10 ETB`\n"
                       f"• Methods: CBE, TeleBirr, M-Pesa\n\n"
                       f"{_e('withdraw')} *Withdrawal:*\n"
                       f"• Minimum: `50 ETB`\n"
                       f"• Maximum: `10000 ETB` per request\n"
                       f"• Processed within 24 hours\n\n"
                       f"{_e('gift')} *Prizes:*\n"
                       f"• Win up to {{win_percentage}}% of pool\n"
                       f"• Jackpot for Full House!",
    },
    
    'am': {
        # Game start (Amharic)
        'game_welcome': f"{_e('game')} *እንኳን ወደ ቢንጎ ጨዋታ በደህና መጡ!*\n\n"
                       f"{_e('money')} ቀሪ ሂሳብ: `{{balance:.2f}} ብር`\n"
                       f"{_e('cartela')} የካርቴላ ዋጋ: `{{cartela_price}} ብር`\n"
                       f"{_e('stats')} ከፍተኛ ካርቴላዎች: `{{max_cartelas}}`\n"
                       f"{_e('target')} የማሸነፊያ መቶኛ: `{{win_percentage}}%`\n\n"
                       f"ጨዋታውን ለመጀመር ከታች ያለውን ቁልፍ ይጫኑ!",
        
        'game_start': f"{_e('play')} *ጨዋታ ተጀምሯል!*\n\n"
                     f"{_e('cartela')} ካርቴላዎች: `{{cartelas}}`\n"
                     f"{_e('money')} ወጪ: `{{cost:.2f}} ብር`\n"
                     f"{_e('balance')} አዲስ ቀሪ ሂሳብ: `{{new_balance:.2f}} ብር`\n\n"
                     f"{_e('four_leaf_clover')} መልካም እድል!",
        
        'game_win': f"{_e('win')} *እንኳን ደስ ያለዎት! አሸንፈዋል!*\n\n"
                   f"{_e('money')} ሽልማት: `+{{amount:.2f}} ብር`\n"
                   f"{_e('balance')} አዲስ ቀሪ ሂሳብ: `{{new_balance:.2f}} ብር`\n"
                   f"{_e('trophy')} አጠቃላይ ድሎች: `{{total_wins}}`\n"
                   f"{_e('star')} የማሸነፊያ መጠን: `{{win_rate:.1f}}%`\n\n"
                   f"{_e('target')} ቅርጽ: `{{pattern}}`\n"
                   f"{_e('cartela')} ካርቴላ: `{{cartela_id}}`",
        
        'game_loss': f"{_e('lose')} *በሚቀጥለው ጊዜ እድል ይሞክሩ!*\n\n"
                    f"{_e('stats')} የተወጡ ቁጥሮች: `{{numbers_drawn}}`\n"
                    f"{_e('target')} ቅርብ ቅርጽ: `{{closest_pattern}}`\n\n"
                    f"{_e('money')} ቀሪ ሂሳብ: `{{balance:.2f}} ብር`\n"
                    f"{_e('star')} የማሸነፊያ መጠን: `{{win_rate:.1f}}%`\n\n"
                    f"{_e('muscle')} አይተዉ! ድልዎ እየቀረበ ነው!",
        
        'game_end': f"{_e('stop')} *ጨዋታ አልቋል*\n\n"
                   f"{_e('stats')} የክፍለ ጊዜ ማጠቃለያ:\n"
                   f"• {_e('cartela')} ካርቴላዎች: `{{cartelas}}`\n"
                   f"• {_e('money')} ወጪ: `{{spent:.2f}} ብር`\n"
                   f"• {_e('win')} አሸንፈዋል: `{{won:.2f}} ብር`\n"
                   f"• {_e('balance')} ትርፍ: `{{net:+.2f}} ብር`\n\n"
                   f"{_e('refresh')} እንደገና ለመጫወት /play ይጠቀሙ",
    }
}

# ==================== GAME MESSAGES ====================
GAME_MESSAGES = {
    'en': {
        'select_cartelas': f"{_e('cartela')} Select your cartelas (1-{{max}}):",
        'confirm_selection': f"{_e('question')} Confirm your cartela selection?",
        'waiting_for_round': f"{_e('clock')} Waiting for next round to start...",
        'numbers_drawn': f"{_e('numbers')} Numbers drawn this round:",
        'you_have_cartelas': f"{_e('cartela')} You have {{count}} active cartela(s)",
        'no_cartelas': f"{_e('warning')} You have no active cartelas. Buy some to play!",
        'max_cartelas_reached': f"{_e('warning')} You've reached the maximum of {{max}} cartelas!",
        'insufficient_balance_play': f"{_e('error')} Need at least {{min}} ETB to play!",
        'game_already_active': f"{_e('warning')} You already have an active game session!",
        'session_expired': f"{_e('error')} Your game session has expired. Start a new game!",
    },
    'am': {
        'select_cartelas': f"{_e('cartela')} ካርቴላዎችዎን ይምረጡ (1-{{max}}):",
        'confirm_selection': f"{_e('question')} ምርጫዎን ያረጋግጡ?",
        'waiting_for_round': f"{_e('clock')} እባክዎ ቀጣዩ ዙር እስኪጀመር ይጠብቁ...",
        'numbers_drawn': f"{_e('numbers')} በዚህ ዙር የተወጡ ቁጥሮች:",
        'you_have_cartelas': f"{_e('cartela')} {{count}} ንቁ ካርቴላ(ዎች) አሉዎት",
        'no_cartelas': f"{_e('warning')} ምንም ንቁ ካርቴላዎች የሉዎትም። ለመጫወት ይግዙ!",
        'max_cartelas_reached': f"{_e('warning')} ከፍተኛው {{max}} ካርቴላዎች ላይ ደርሰዋል!",
        'insufficient_balance_play': f"{_e('error')} ለመጫወት ቢያንስ {{min}} ብር ያስፈልጋል!",
    }
}

# ==================== ERROR MESSAGES ====================
ERROR_MESSAGES = {
    'en': {
        'default': f"{_e('error')} An error occurred. Please try again later.",
        'database': f"{_e('error')} Database error. Please contact support.",
        'network': f"{_e('error')} Network error. Please check your connection.",
        'timeout': f"{_e('error')} Request timed out. Please try again.",
        'invalid_input': f"{_e('error')} Invalid input. Please check and try again.",
        'unauthorized': f"{_e('error')} Unauthorized access.",
        'not_found': f"{_e('error')} Requested resource not found.",
        'rate_limit': f"{_e('warning')} Too many requests. Please wait {{seconds}} seconds.",
        'maintenance': f"{_e('warning')} System under maintenance. Please try again later.",
    },
    'am': {
        'default': f"{_e('error')} ስህተት ተከስቷል። እባክዎ ቆይተው ይሞክሩ።",
        'database': f"{_e('error')} የውሂብ ጎታ ስህተት። እባክዎ ድጋፍ ያግኙ።",
        'invalid_input': f"{_e('error')} የማይሰራ ግቤት። እባክዎ ይፈትሹ እና እንደገና ይሞክሩ።",
        'rate_limit': f"{_e('warning')} በጣም ብዙ ጥያቄዎች። እባክዎ {{seconds}} ሰከንድ ይጠብቁ።",
    }
}

# ==================== SUCCESS MESSAGES ====================
SUCCESS_MESSAGES = {
    'en': {
        'default': f"{_e('success')} Operation completed successfully!",
        'deposit': f"{_e('success')} Deposit request submitted successfully!",
        'cashout': f"{_e('success')} Withdrawal request submitted successfully!",
        'transfer': f"{_e('success')} Transfer completed successfully!",
        'register': f"{_e('success')} Registration completed successfully!",
        'update': f"{_e('success')} Update completed successfully!",
    },
    'am': {
        'default': f"{_e('success')} ስራው በሚገባ ተጠናቋል!",
        'deposit': f"{_e('success')} የተቀማጭ ገንዘብ ጥያቄ በሚገባ ተልኳል!",
        'transfer': f"{_e('success')} ገንዘብ ማስተላለፍ በሚገባ ተጠናቋል!",
    }
}

# ==================== INFO MESSAGES ====================
INFO_MESSAGES = {
    'en': {
        'loading': f"{_e('loading')} Loading... Please wait.",
        'processing': f"{_e('processing')} Processing your request...",
        'waiting': f"{_e('clock')} Please wait...",
        'checking': f"{_e('search')} Checking...",
        'updating': f"{_e('refresh')} Updating...",
    },
    'am': {
        'loading': f"{_e('loading')} በመጫን ላይ... እባክዎ ይጠብቁ።",
        'processing': f"{_e('processing')} ጥያቄዎን በማስኬድ ላይ...",
    }
}

# ==================== ADMIN MESSAGES ====================
ADMIN_MESSAGES = {
    'en': {
        'panel': f"{_e('settings')} *Admin Panel*\n\nWelcome, Administrator!",
        'deposit_pending': f"{_e('pending')} *Pending Deposits:* {{count}}",
        'cashout_pending': f"{_e('pending')} *Pending Withdrawals:* {{count}}",
        'user_stats': f"{_e('stats')} *User Statistics*\n\n• Total Users: {{total}}\n• Active Today: {{active}}\n• Total Deposits: {{deposits:.2f}} ETB\n• Total Withdrawals: {{withdrawals:.2f}} ETB",
        'commission_set': f"{_e('success')} Win percentage set to {{percentage}}%",
    },
    'am': {
        'panel': f"{_e('settings')} *የአስተዳዳሪ ፓነል*\n\nእንኳን ደህና መጡ, አስተዳዳሪ!",
        'commission_set': f"{_e('success')} የማሸነፊያ መቶኛ ወደ {{percentage}}% ተቀይሯል",
    }
}

# ==================== TRANSFER MESSAGES ====================
TRANSFER_MESSAGES = {
    'en': {
        'start': f"{_e('transfer')} *Balance Transfer*\n\nEnter receiver's phone number:",
        'receiver_found': f"{_e('success')} Receiver found: {{username}}",
        'enter_amount': f"{_e('money')} Your balance: {{balance:.2f}} ETB\n\nEnter amount to transfer (min {{min}}, max {{max}}):",
        'confirm': f"{_e('question')} *Confirm Transfer*\n\nTo: {{receiver}}\nAmount: {{amount:.2f}} ETB\nFee: {{fee:.2f}} ETB\nTotal: {{total:.2f}} ETB\n\nConfirm?",
        'success': f"{_e('success')} *Transfer Successful!*\n\nSent: {{amount:.2f}} ETB to {{receiver}}\nNew balance: {{balance:.2f}} ETB",
        'failed': f"{_e('error')} Transfer failed: {{reason}}",
        'cancelled': f"{_e('warning')} Transfer cancelled.",
    },
    'am': {
        'start': f"{_e('transfer')} *ገንዘብ ማስተላለፍ*\n\nየተቀባዩን ስልክ ቁጥር ያስገቡ:",
        'success': f"{_e('success')} *ገንዘብ ማስተላለፍ ተሳክቷል!*\n\n{{amount:.2f}} ብር ላኩ\nአዲስ ቀሪ ሂሳብ: {{balance:.2f}} ብር",
    }
}

# Export all
__all__ = [
    'GAME_TEXTS',
    'GAME_MESSAGES',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'INFO_MESSAGES',
    'ADMIN_MESSAGES',
    'TRANSFER_MESSAGES'
]