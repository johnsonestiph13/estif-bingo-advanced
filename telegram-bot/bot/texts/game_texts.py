# telegram-bot/bot/texts/game_texts.py
# Estif Bingo 24/7 - Game-Specific Texts

from . import EMOJIS

# ==================== GAME TEXTS ====================
GAME_TEXTS = {
    'en': {
        # Game start
        'game_welcome': f"{EMOJIS['game']} *Welcome to Bingo Game!*\n\n"
                       f"💰 Balance: `{{balance:.2f}} ETB`\n"
                       f"🎫 Cartela Price: `{{cartela_price}} ETB`\n"
                       f"📊 Max Cartelas: `{{max_cartelas}}`\n"
                       f"🎯 Win Percentage: `{{win_percentage}}%`\n\n"
                       f"Click the button below to start playing!",
        
        'game_start': f"{EMOJIS['play']} *Game Started!*\n\n"
                     f"🎫 Cartelas: `{{cartelas}}`\n"
                     f"💰 Cost: `{{cost:.2f}} ETB`\n"
                     f"💵 New Balance: `{{new_balance:.2f}} ETB`\n\n"
                     f"🍀 Good luck!",
        
        'game_win': f"{EMOJIS['win']} *CONGRATULATIONS! YOU WON!*\n\n"
                   f"💰 Winnings: `+{{amount:.2f}} ETB`\n"
                   f"💵 New Balance: `{{new_balance:.2f}} ETB`\n"
                   f"🏆 Total Wins: `{{total_wins}}`\n"
                   f"⭐ Win Rate: `{{win_rate:.1f}}%`\n\n"
                   f"🎯 Pattern: `{{pattern}}`\n"
                   f"🎫 Cartela: `{{cartela_id}}`",
        
        'game_loss': f"{EMOJIS['lose']} *Better Luck Next Time!*\n\n"
                    f"📊 Numbers Drawn: `{{numbers_drawn}}`\n"
                    f"🎯 Closest Pattern: `{{closest_pattern}}`\n\n"
                    f"💰 Balance: `{{balance:.2f}} ETB`\n"
                    f"⭐ Win Rate: `{{win_rate:.1f}}%`\n\n"
                    f"💪 Don't give up! Your win is coming!",
        
        'game_end': f"{EMOJIS['stop']} *Game Ended*\n\n"
                   f"📊 Session Summary:\n"
                   f"• Cartelas: `{{cartelas}}`\n"
                   f"• Spent: `{{spent:.2f}} ETB`\n"
                   f"• Won: `{{won:.2f}} ETB`\n"
                   f"• Net: `{{net:+.2f}} ETB`\n\n"
                   f"🔄 Play again with /play",
        
        # Game stats
        'stats_title': f"{EMOJIS['stats']} *Your Bingo Statistics*\n\n",
        'stats_games': f"🎮 *Games:*\n• Played: `{{played}}`\n• Won: `{{won}}`\n• Win Rate: `{{rate:.1f}}%`\n\n",
        'stats_financial': f"💰 *Financial:*\n• Total Bet: `{{bet:.2f}} ETB`\n• Total Win: `{{win:.2f}} ETB`\n• Net Profit: `{{net:+.2f}} ETB`\n• Best Win: `{{best:.2f}} ETB`\n\n",
        'stats_time': f"⏰ *Last Played:* `{{last_played}}`\n\n",
        'stats_rank': f"🏆 *Rank:* `#{rank}`",
        
        # Leaderboard
        'leaderboard_title': f"{EMOJIS['trophy']} *BINGO LEADERBOARD* {EMOJIS['trophy']}\n\n",
        'leaderboard_entry': "{emoji} *{username}* - {total_won:.0f} ETB won (Win Rate: {win_rate}%)\n",
        'leaderboard_empty': "🏆 *No players yet. Be the first!*\n",
        'leaderboard_updated': f"\n📅 *Updated:* `{{timestamp}}`",
        
        # Cartela messages
        'cartela_bought': f"{EMOJIS['cartela']} *Cartela Purchased!*\n\n"
                         f"🎫 Cartela ID: `{{cartela_id}}`\n"
                         f"💰 Cost: `{{cost:.2f}} ETB`\n"
                         f"💵 New Balance: `{{balance:.2f}} ETB`",
        
        'cartela_selected': f"{EMOJIS['success']} Cartela `{{cartela_id}}` selected",
        'cartela_deselected': f"{EMOJIS['warning']} Cartela `{{cartela_id}}` deselected",
        
        # Round messages
        'round_start': f"{EMOJIS['play']} *Round {{round_number}} Started!*\n\n"
                      f"🎫 Active Cartelas: `{{cartelas}}`\n"
                      f"💰 Prize Pool: `{{pool:.2f}} ETB`\n"
                      f"🎯 Win Chance: `{{win_percentage}}%`",
        
        'round_end': f"{EMOJIS['stop']} *Round {{round_number}} Ended!*\n\n"
                    f"🎯 Winning Numbers: `{{numbers}}`\n"
                    f"🏆 Winners: `{{winners}}`\n"
                    f"💰 Prize Pool: `{{pool:.2f}} ETB`",
        
        # Quick play
        'quick_play': f"{EMOJIS['lightning']} *Quick Play - {{cartelas}} Cartela{{s}}*\n\n"
                     f"💰 Cost: `{{cost:.2f}} ETB`\n"
                     f"🎯 Win Chance: `{{win_percentage}}%`\n\n"
                     f"Click below to start!",
        
        'all_in': f"{EMOJIS['fire']} *ALL IN!*\n\n"
                 f"💰 Bet Amount: `{{amount:.2f}} ETB`\n"
                 f"🎫 Cartelas: `{{cartelas}}`\n"
                 f"💵 Remaining Balance: `{{remaining:.2f}} ETB`",
        
        # Settings
        'settings_updated': f"{EMOJIS['success']} Setting updated: `{{setting}}` = `{{value}}`",
        'settings_reset': f"{EMOJIS['success']} All settings reset to default",
        
        # Help
        'help_rules': f"{EMOJIS['help']} *Game Rules*\n\n"
                     f"1️⃣ Select 1-4 cartelas per round\n"
                     f"2️⃣ Numbers (1-75) are drawn randomly\n"
                     f"3️⃣ Match patterns on your cartela to win\n"
                     f"4️⃣ Win up to {{win_percentage}}% of the pool!\n\n"
                     f"🎯 *Winning Patterns:*\n"
                     f"• Line (Horizontal/Vertical)\n"
                     f"• Diagonal\n"
                     f"• Four Corners\n"
                     f"• Full House (BINGO!)",
        
        'help_cartelas': f"{EMOJIS['cartela']} *About Cartelas*\n\n"
                        f"• Each cartela has 24 numbers + 1 free space\n"
                        f"• Numbers range from 1-75\n"
                        f"• Each cartela costs `{{price}} ETB`\n"
                        f"• Max {{max}} cartelas per round\n"
                        f"• More cartelas = higher win chance!",
        
        'help_payment': f"{EMOJIS['money']} *Payments & Prizes*\n\n"
                       f"💰 *Deposit:*\n"
                       f"• Minimum: `10 ETB`\n"
                       f"• Methods: CBE, TeleBirr, M-Pesa\n\n"
                       f"💸 *Withdrawal:*\n"
                       f"• Minimum: `50 ETB`\n"
                       f"• Maximum: `10000 ETB` per request\n"
                       f"• Processed within 24 hours\n\n"
                       f"🎁 *Prizes:*\n"
                       f"• Win up to {{win_percentage}}% of pool\n"
                       f"• Jackpot for Full House!",
    },
    
    'am': {
        # Game start (Amharic)
        'game_welcome': f"{EMOJIS['game']} *እንኳን ወደ ቢንጎ ጨዋታ በደህና መጡ!*\n\n"
                       f"💰 ቀሪ ሂሳብ: `{{balance:.2f}} ብር`\n"
                       f"🎫 የካርቴላ ዋጋ: `{{cartela_price}} ብር`\n"
                       f"📊 ከፍተኛ ካርቴላዎች: `{{max_cartelas}}`\n"
                       f"🎯 የማሸነፊያ መቶኛ: `{{win_percentage}}%`\n\n"
                       f"ጨዋታውን ለመጀመር ከታች ያለውን ቁልፍ ይጫኑ!",
        
        'game_start': f"{EMOJIS['play']} *ጨዋታ ተጀምሯል!*\n\n"
                     f"🎫 ካርቴላዎች: `{{cartelas}}`\n"
                     f"💰 ወጪ: `{{cost:.2f}} ብር`\n"
                     f"💵 አዲስ ቀሪ ሂሳብ: `{{new_balance:.2f}} ብር`\n\n"
                     f"🍀 መልካም እድል!",
        
        'game_win': f"{EMOJIS['win']} *እንኳን ደስ ያለዎት! አሸንፈዋል!*\n\n"
                   f"💰 ሽልማት: `+{{amount:.2f}} ብር`\n"
                   f"💵 አዲስ ቀሪ ሂሳብ: `{{new_balance:.2f}} ብር`\n"
                   f"🏆 አጠቃላይ ድሎች: `{{total_wins}}`\n"
                   f"⭐ የማሸነፊያ መጠን: `{{win_rate:.1f}}%`\n\n"
                   f"🎯 ቅርጽ: `{{pattern}}`\n"
                   f"🎫 ካርቴላ: `{{cartela_id}}`",
        
        'game_loss': f"{EMOJIS['lose']} *በሚቀጥለው ጊዜ እድል ይሞክሩ!*\n\n"
                    f"📊 የተወጡ ቁጥሮች: `{{numbers_drawn}}`\n"
                    f"🎯 ቅርብ ቅርጽ: `{{closest_pattern}}`\n\n"
                    f"💰 ቀሪ ሂሳብ: `{{balance:.2f}} ብር`\n"
                    f"⭐ የማሸነፊያ መጠን: `{{win_rate:.1f}}%`\n\n"
                    f"💪 አይተዉ! ድልዎ እየቀረበ ነው!",
        
        'game_end': f"{EMOJIS['stop']} *ጨዋታ አልቋል*\n\n"
                   f"📊 የክፍለ ጊዜ ማጠቃለያ:\n"
                   f"• ካርቴላዎች: `{{cartelas}}`\n"
                   f"• ወጪ: `{{spent:.2f}} ብር`\n"
                   f"• አሸንፈዋል: `{{won:.2f}} ብር`\n"
                   f"• ትርፍ: `{{net:+.2f}} ብር`\n\n"
                   f"🔄 እንደገና ለመጫወት /play ይጠቀሙ",
    }
}

# ==================== GAME MESSAGES ====================
GAME_MESSAGES = {
    'en': {
        'select_cartelas': f"{EMOJIS['cartela']} Select your cartelas (1-{{max}}):",
        'confirm_selection': f"{EMOJIS['question']} Confirm your cartela selection?",
        'waiting_for_round': f"{EMOJIS['clock']} Waiting for next round to start...",
        'numbers_drawn': f"{EMOJIS['numbers']} Numbers drawn this round:",
        'you_have_cartelas': f"{EMOJIS['cartela']} You have {{count}} active cartela(s)",
        'no_cartelas': f"{EMOJIS['warning']} You have no active cartelas. Buy some to play!",
        'max_cartelas_reached': f"{EMOJIS['warning']} You've reached the maximum of {{max}} cartelas!",
        'insufficient_balance_play': f"{EMOJIS['error']} Need at least {{min}} ETB to play!",
        'game_already_active': f"{EMOJIS['warning']} You already have an active game session!",
        'session_expired': f"{EMOJIS['error']} Your game session has expired. Start a new game!",
    },
    'am': {
        'select_cartelas': f"{EMOJIS['cartela']} ካርቴላዎችዎን ይምረጡ (1-{{max}}):",
        'confirm_selection': f"{EMOJIS['question']} ምርጫዎን ያረጋግጡ?",
        'waiting_for_round': f"{EMOJIS['clock']} እባክዎ ቀጣዩ ዙር እስኪጀመር ይጠብቁ...",
        'numbers_drawn': f"{EMOJIS['numbers']} በዚህ ዙር የተወጡ ቁጥሮች:",
        'you_have_cartelas': f"{EMOJIS['cartela']} {{count}} ንቁ ካርቴላ(ዎች) አሉዎት",
        'no_cartelas': f"{EMOJIS['warning']} ምንም ንቁ ካርቴላዎች የሉዎትም። ለመጫወት ይግዙ!",
        'max_cartelas_reached': f"{EMOJIS['warning']} ከፍተኛው {{max}} ካርቴላዎች ላይ ደርሰዋል!",
        'insufficient_balance_play': f"{EMOJIS['error']} ለመጫወት ቢያንስ {{min}} ብር ያስፈልጋል!",
    }
}

# ==================== ERROR MESSAGES ====================
ERROR_MESSAGES = {
    'en': {
        'default': f"{EMOJIS['error']} An error occurred. Please try again later.",
        'database': f"{EMOJIS['error']} Database error. Please contact support.",
        'network': f"{EMOJIS['error']} Network error. Please check your connection.",
        'timeout': f"{EMOJIS['error']} Request timed out. Please try again.",
        'invalid_input': f"{EMOJIS['error']} Invalid input. Please check and try again.",
        'unauthorized': f"{EMOJIS['error']} Unauthorized access.",
        'not_found': f"{EMOJIS['error']} Requested resource not found.",
        'rate_limit': f"{EMOJIS['warning']} Too many requests. Please wait {{seconds}} seconds.",
        'maintenance': f"{EMOJIS['warning']} System under maintenance. Please try again later.",
    },
    'am': {
        'default': f"{EMOJIS['error']} ስህተት ተከስቷል። እባክዎ ቆይተው ይሞክሩ።",
        'database': f"{EMOJIS['error']} የውሂብ ጎታ ስህተት። እባክዎ ድጋፍ ያግኙ።",
        'invalid_input': f"{EMOJIS['error']} የማይሰራ ግቤት። እባክዎ ይፈትሹ እና እንደገና ይሞክሩ።",
        'rate_limit': f"{EMOJIS['warning']} በጣም ብዙ ጥያቄዎች። እባክዎ {{seconds}} ሰከንድ ይጠብቁ።",
    }
}

# ==================== SUCCESS MESSAGES ====================
SUCCESS_MESSAGES = {
    'en': {
        'default': f"{EMOJIS['success']} Operation completed successfully!",
        'deposit': f"{EMOJIS['success']} Deposit request submitted successfully!",
        'cashout': f"{EMOJIS['success']} Withdrawal request submitted successfully!",
        'transfer': f"{EMOJIS['success']} Transfer completed successfully!",
        'register': f"{EMOJIS['success']} Registration completed successfully!",
        'update': f"{EMOJIS['success']} Update completed successfully!",
    },
    'am': {
        'default': f"{EMOJIS['success']} ስራው በሚገባ ተጠናቋል!",
        'deposit': f"{EMOJIS['success']} የተቀማጭ ገንዘብ ጥያቄ በሚገባ ተልኳል!",
        'transfer': f"{EMOJIS['success']} ገንዘብ ማስተላለፍ በሚገባ ተጠናቋል!",
    }
}

# ==================== INFO MESSAGES ====================
INFO_MESSAGES = {
    'en': {
        'loading': f"{EMOJIS['loading']} Loading... Please wait.",
        'processing': f"{EMOJIS['loading']} Processing your request...",
        'waiting': f"{EMOJIS['clock']} Please wait...",
        'checking': f"{EMOJIS['search']} Checking...",
        'updating': f"{EMOJIS['refresh']} Updating...",
    },
    'am': {
        'loading': f"{EMOJIS['loading']} በመጫን ላይ... እባክዎ ይጠብቁ።",
        'processing': f"{EMOJIS['loading']} ጥያቄዎን በማስኬድ ላይ...",
    }
}

# ==================== ADMIN MESSAGES ====================
ADMIN_MESSAGES = {
    'en': {
        'panel': f"{EMOJIS['settings']} *Admin Panel*\n\nWelcome, Administrator!",
        'deposit_pending': f"{EMOJIS['pending']} *Pending Deposits:* {{count}}",
        'cashout_pending': f"{EMOJIS['pending']} *Pending Withdrawals:* {{count}}",
        'user_stats': f"{EMOJIS['stats']} *User Statistics*\n\n• Total Users: {{total}}\n• Active Today: {{active}}\n• Total Deposits: {{deposits:.2f}} ETB\n• Total Withdrawals: {{withdrawals:.2f}} ETB",
        'commission_set': f"{EMOJIS['success']} Win percentage set to {{percentage}}%",
    },
    'am': {
        'panel': f"{EMOJIS['settings']} *የአስተዳዳሪ ፓነል*\n\nእንኳን ደህና መጡ, አስተዳዳሪ!",
        'commission_set': f"{EMOJIS['success']} የማሸነፊያ መቶኛ ወደ {{percentage}}% ተቀይሯል",
    }
}

# ==================== TRANSFER MESSAGES ====================
TRANSFER_MESSAGES = {
    'en': {
        'start': f"{EMOJIS['transfer']} *Balance Transfer*\n\nEnter receiver's phone number:",
        'receiver_found': f"{EMOJIS['success']} Receiver found: {{username}}",
        'enter_amount': f"💰 Your balance: {{balance:.2f}} ETB\n\nEnter amount to transfer (min {{min}}, max {{max}}):",
        'confirm': f"{EMOJIS['question']} *Confirm Transfer*\n\nTo: {{receiver}}\nAmount: {{amount:.2f}} ETB\nFee: {{fee:.2f}} ETB\nTotal: {{total:.2f}} ETB\n\nConfirm?",
        'success': f"{EMOJIS['success']} *Transfer Successful!*\n\nSent: {{amount:.2f}} ETB to {{receiver}}\nNew balance: {{balance:.2f}} ETB",
        'failed': f"{EMOJIS['error']} Transfer failed: {{reason}}",
        'cancelled': f"{EMOJIS['warning']} Transfer cancelled.",
    },
    'am': {
        'start': f"{EMOJIS['transfer']} *ገንዘብ ማስተላለፍ*\n\nየተቀባዩን ስልክ ቁጥር ያስገቡ:",
        'success': f"{EMOJIS['success']} *ገንዘብ ማስተላለፍ ተሳክቷል!*\n\n{{amount:.2f}} ብር ላኩ\nአዲስ ቀሪ ሂሳብ: {{balance:.2f}} ብር",
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