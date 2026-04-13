# telegram-bot/bot/keyboards/game_keyboards.py
# Estif Bingo 24/7 - Complete Game-Specific Keyboards
# Includes: Main menu, Quick play, Cartela selection, Game controls, Settings, Stats, Leaderboard

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from typing import Optional, List, Dict, Any

# ==================== CONSTANTS ====================
BINGO_LETTERS = ['B', 'I', 'N', 'G', 'O']
CARTELA_PRICES = {
    1: 10,
    2: 20,
    3: 30,
    4: 40
}

# ==================== MAIN GAME MENU ====================
def game_menu_keyboard(lang: str = 'en', balance: float = 0):
    """Create game main menu keyboard with balance display"""
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"💰 ቀሪ ሂሳብ: {balance:.2f} ETB", callback_data="show_balance")],
            [InlineKeyboardButton("🎮 ጀምር ጨዋታ", callback_data="game_start")],
            [InlineKeyboardButton("⚡ ፈጣን ጨዋታ", callback_data="game_quick")],
            [InlineKeyboardButton("📊 የእኔ ስታቲስቲክስ", callback_data="game_stats")],
            [InlineKeyboardButton("🏆 ከፍተኛ ተጫዋቾች", callback_data="game_leaderboard")],
            [InlineKeyboardButton("🎫 ካርቴላዎቼ", callback_data="my_cartelas")],
            [InlineKeyboardButton("⚙️ ቅንብሮች", callback_data="game_settings")],
            [InlineKeyboardButton("❓ እንዴት መጫወት", callback_data="game_help")],
            [InlineKeyboardButton("🔙 ወደ መጀመሪያ ምናሌ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"💰 Balance: {balance:.2f} ETB", callback_data="show_balance")],
            [InlineKeyboardButton("🎮 Start Game", callback_data="game_start")],
            [InlineKeyboardButton("⚡ Quick Play", callback_data="game_quick")],
            [InlineKeyboardButton("📊 My Statistics", callback_data="game_stats")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="game_leaderboard")],
            [InlineKeyboardButton("🎫 My Cartelas", callback_data="my_cartelas")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="game_settings")],
            [InlineKeyboardButton("❓ How to Play", callback_data="game_help")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== QUICK PLAY KEYBOARD ====================
def quick_play_keyboard(lang: str = 'en'):
    """Create quick play keyboard with cartela options"""
    
    if lang == 'am':
        keyboard = [
            [
                InlineKeyboardButton(f"⚡ 1 ካርቴላ ({CARTELA_PRICES[1]} ETB)", callback_data="quick_play_1"),
                InlineKeyboardButton(f"⚡ 2 ካርቴላ ({CARTELA_PRICES[2]} ETB)", callback_data="quick_play_2")
            ],
            [
                InlineKeyboardButton(f"⚡ 3 ካርቴላ ({CARTELA_PRICES[3]} ETB)", callback_data="quick_play_3"),
                InlineKeyboardButton(f"⚡ 4 ካርቴላ ({CARTELA_PRICES[4]} ETB)", callback_data="quick_play_4")
            ],
            [
                InlineKeyboardButton("🎲 በዘፈቀደ", callback_data="quick_play_random"),
                InlineKeyboardButton("🎯 እድለኛ ቁጥር", callback_data="quick_play_lucky")
            ],
            [
                InlineKeyboardButton("💰 ሙሉ ሂሳብ", callback_data="quick_play_all_in"),
                InlineKeyboardButton("🎫 ከፍተኛ ካርቴላ", callback_data="quick_play_max")
            ],
            [
                InlineKeyboardButton("🔙 ወደ ጨዋታ ምናሌ", callback_data="game_menu")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(f"⚡ 1 Cartela ({CARTELA_PRICES[1]} ETB)", callback_data="quick_play_1"),
                InlineKeyboardButton(f"⚡ 2 Cartelas ({CARTELA_PRICES[2]} ETB)", callback_data="quick_play_2")
            ],
            [
                InlineKeyboardButton(f"⚡ 3 Cartelas ({CARTELA_PRICES[3]} ETB)", callback_data="quick_play_3"),
                InlineKeyboardButton(f"⚡ 4 Cartelas ({CARTELA_PRICES[4]} ETB)", callback_data="quick_play_4")
            ],
            [
                InlineKeyboardButton("🎲 Random", callback_data="quick_play_random"),
                InlineKeyboardButton("🎯 Lucky Number", callback_data="quick_play_lucky")
            ],
            [
                InlineKeyboardButton("💰 All In", callback_data="quick_play_all_in"),
                InlineKeyboardButton("🎫 Max Cartelas", callback_data="quick_play_max")
            ],
            [
                InlineKeyboardButton("🔙 Back to Game Menu", callback_data="game_menu")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== CARTELA SELECTION KEYBOARD ====================
def cartela_selection_keyboard(max_cartelas: int = 4, selected: List[int] = None, lang: str = 'en'):
    """Create cartela selection keyboard with selected tracking"""
    
    if selected is None:
        selected = []
    
    buttons = []
    row = []
    
    for i in range(1, max_cartelas + 1):
        if i in selected:
            text = f"✅ Cartela {i} (Selected)"
        else:
            text = f"🎫 Cartela {i}"
        
        row.append(InlineKeyboardButton(text, callback_data=f"select_cartela_{i}"))
        
        if len(row) == 2:  # 2 buttons per row
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    # Add selection info
    total_cost = len(selected) * CARTELA_PRICES[1]
    buttons.append([
        InlineKeyboardButton(f"💰 Total: {total_cost} ETB", callback_data="show_total")
    ])
    
    # Add control buttons
    buttons.extend([
        [
            InlineKeyboardButton("🎲 Random Selection", callback_data="select_random_cartelas"),
            InlineKeyboardButton("✨ Lucky Numbers", callback_data="select_lucky_numbers")
        ],
        [
            InlineKeyboardButton("🗑️ Clear All", callback_data="clear_cartelas"),
            InlineKeyboardButton("🎫 Select All", callback_data="select_all_cartelas")
        ],
        [
            InlineKeyboardButton("✅ Confirm & Play", callback_data="confirm_cartelas"),
            InlineKeyboardButton("🔙 Back", callback_data="game_menu")
        ]
    ])
    
    return InlineKeyboardMarkup(buttons)


# ==================== GAME CONTROL KEYBOARD ====================
def game_control_keyboard(game_state: str = 'active', lang: str = 'en'):
    """Create game control keyboard based on game state"""
    
    if lang == 'am':
        if game_state == 'active':
            keyboard = [
                [
                    InlineKeyboardButton("⏸️ ለአፍታ አቁም", callback_data="game_pause"),
                    InlineKeyboardButton("🔄 አዲስ ዙር", callback_data="game_new_round"),
                    InlineKeyboardButton("⏹️ ጨዋታውን አቁም", callback_data="game_end")
                ],
                [
                    InlineKeyboardButton("🎫 ካርቴላ ግዛ", callback_data="game_buy_cartela"),
                    InlineKeyboardButton("📊 የአሁን ስታት", callback_data="game_current_stats")
                ],
                [
                    InlineKeyboardButton("🔊 ድምጽ", callback_data="game_toggle_sound"),
                    InlineKeyboardButton("🎨 ገጽታ", callback_data="game_toggle_theme")
                ],
                [
                    InlineKeyboardButton("🎯 አውቶ ምረጥ", callback_data="game_toggle_auto"),
                    InlineKeyboardButton("⚡ ፈጣን ሁነታ", callback_data="game_toggle_fast")
                ],
                [
                    InlineKeyboardButton("🔙 ውጣ", callback_data="game_menu")
                ]
            ]
        elif game_state == 'paused':
            keyboard = [
                [
                    InlineKeyboardButton("▶️ ቀጥል", callback_data="game_resume"),
                    InlineKeyboardButton("🔄 አዲስ ዙር", callback_data="game_new_round"),
                    InlineKeyboardButton("⏹️ ጨዋታውን አቁም", callback_data="game_end")
                ],
                [
                    InlineKeyboardButton("🔙 ውጣ", callback_data="game_menu")
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("🎮 አዲስ ጨዋታ ጀምር", callback_data="game_start"),
                    InlineKeyboardButton("🔙 ወደ ጨዋታ ምናሌ", callback_data="game_menu")
                ]
            ]
    else:
        if game_state == 'active':
            keyboard = [
                [
                    InlineKeyboardButton("⏸️ Pause", callback_data="game_pause"),
                    InlineKeyboardButton("🔄 New Round", callback_data="game_new_round"),
                    InlineKeyboardButton("⏹️ End Game", callback_data="game_end")
                ],
                [
                    InlineKeyboardButton("🎫 Buy Cartela", callback_data="game_buy_cartela"),
                    InlineKeyboardButton("📊 Current Stats", callback_data="game_current_stats")
                ],
                [
                    InlineKeyboardButton("🔊 Sound", callback_data="game_toggle_sound"),
                    InlineKeyboardButton("🎨 Theme", callback_data="game_toggle_theme")
                ],
                [
                    InlineKeyboardButton("🎯 Auto-Select", callback_data="game_toggle_auto"),
                    InlineKeyboardButton("⚡ Fast Mode", callback_data="game_toggle_fast")
                ],
                [
                    InlineKeyboardButton("🔙 Exit", callback_data="game_menu")
                ]
            ]
        elif game_state == 'paused':
            keyboard = [
                [
                    InlineKeyboardButton("▶️ Resume", callback_data="game_resume"),
                    InlineKeyboardButton("🔄 New Round", callback_data="game_new_round"),
                    InlineKeyboardButton("⏹️ End Game", callback_data="game_end")
                ],
                [
                    InlineKeyboardButton("🔙 Exit", callback_data="game_menu")
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("🎮 Start New Game", callback_data="game_start"),
                    InlineKeyboardButton("🔙 Game Menu", callback_data="game_menu")
                ]
            ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== GAME SETTINGS KEYBOARD ====================
def game_settings_keyboard(current_settings: Dict[str, Any] = None, lang: str = 'en'):
    """Create game settings keyboard with toggle buttons"""
    
    if current_settings is None:
        current_settings = {}
    
    sound_status = "🔊 ON" if current_settings.get('sound', True) else "🔇 OFF"
    animation_status = "✨ ON" if current_settings.get('animation', True) else "💨 OFF"
    auto_select_status = "🤖 ON" if current_settings.get('auto_select', False) else "👆 OFF"
    fast_mode_status = "⚡ ON" if current_settings.get('fast_mode', False) else "🐢 OFF"
    notifications_status = "🔔 ON" if current_settings.get('notifications', True) else "🔕 OFF"
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"🔊 ድምጽ: {sound_status}", callback_data="toggle_sound")],
            [InlineKeyboardButton(f"🎨 እንቅስቃሴ: {animation_status}", callback_data="toggle_animation")],
            [InlineKeyboardButton(f"🤖 ራስ-ምረጥ: {auto_select_status}", callback_data="toggle_auto_select")],
            [InlineKeyboardButton(f"⚡ ፈጣን ሁነታ: {fast_mode_status}", callback_data="toggle_fast_mode")],
            [InlineKeyboardButton(f"🔔 ማሳወቂያ: {notifications_status}", callback_data="toggle_notifications")],
            [InlineKeyboardButton("🎯 ነባሪ የማሸነፊያ መቶኛ", callback_data="set_default_win_percentage")],
            [InlineKeyboardButton("🎫 ነባሪ ካርቴላዎች", callback_data="set_default_cartelas")],
            [InlineKeyboardButton("🎨 የካርቴላ ቀለም", callback_data="set_cartela_color")],
            [InlineKeyboardButton("🌐 ቋንቋ", callback_data="change_lang")],
            [InlineKeyboardButton("🔄 ነባሪ ቅንብሮችን መልስ", callback_data="reset_settings")],
            [InlineKeyboardButton("🔙 ወደ ጨዋታ ምናሌ", callback_data="game_menu")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"🔊 Sound: {sound_status}", callback_data="toggle_sound")],
            [InlineKeyboardButton(f"🎨 Animations: {animation_status}", callback_data="toggle_animation")],
            [InlineKeyboardButton(f"🤖 Auto-Select: {auto_select_status}", callback_data="toggle_auto_select")],
            [InlineKeyboardButton(f"⚡ Fast Mode: {fast_mode_status}", callback_data="toggle_fast_mode")],
            [InlineKeyboardButton(f"🔔 Notifications: {notifications_status}", callback_data="toggle_notifications")],
            [InlineKeyboardButton("🎯 Default Win %", callback_data="set_default_win_percentage")],
            [InlineKeyboardButton("🎫 Default Cartelas", callback_data="set_default_cartelas")],
            [InlineKeyboardButton("🎨 Cartela Color", callback_data="set_cartela_color")],
            [InlineKeyboardButton("🌐 Language", callback_data="change_lang")],
            [InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_settings")],
            [InlineKeyboardButton("🔙 Back to Game Menu", callback_data="game_menu")]
        ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== GAME STATS KEYBOARD ====================
def game_stats_keyboard(lang: str = 'en'):
    """Create game statistics keyboard with multiple views"""
    
    if lang == 'am':
        keyboard = [
            [
                InlineKeyboardButton("📊 አጠቃላይ ስታት", callback_data="stats_overall"),
                InlineKeyboardButton("📈 የዕለት ስታት", callback_data="stats_daily")
            ],
            [
                InlineKeyboardButton("🏆 ሳምንታዊ ስታት", callback_data="stats_weekly"),
                InlineKeyboardButton("🎯 ወርሃዊ ስታት", callback_data="stats_monthly")
            ],
            [
                InlineKeyboardButton("💰 አሸናፊነት/ሽንፈት", callback_data="stats_win_loss"),
                InlineKeyboardButton("🎫 የካርቴላ ስታት", callback_data="stats_cartelas")
            ],
            [
                InlineKeyboardButton("📅 የቅርብ ጊዜ ጨዋታዎች", callback_data="stats_recent_games"),
                InlineKeyboardButton("💵 ከፍተኛ ሽልማት", callback_data="stats_biggest_win")
            ],
            [
                InlineKeyboardButton("📤 ሪፖርት ላክ", callback_data="stats_export"),
                InlineKeyboardButton("🔄 አድስ", callback_data="stats_refresh")
            ],
            [
                InlineKeyboardButton("🔙 ተመለስ", callback_data="game_menu")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("📊 Overall Stats", callback_data="stats_overall"),
                InlineKeyboardButton("📈 Daily Stats", callback_data="stats_daily")
            ],
            [
                InlineKeyboardButton("🏆 Weekly Stats", callback_data="stats_weekly"),
                InlineKeyboardButton("🎯 Monthly Stats", callback_data="stats_monthly")
            ],
            [
                InlineKeyboardButton("💰 Win/Loss Ratio", callback_data="stats_win_loss"),
                InlineKeyboardButton("🎫 Cartela Stats", callback_data="stats_cartelas")
            ],
            [
                InlineKeyboardButton("📅 Recent Games", callback_data="stats_recent_games"),
                InlineKeyboardButton("💵 Biggest Win", callback_data="stats_biggest_win")
            ],
            [
                InlineKeyboardButton("📤 Export Report", callback_data="stats_export"),
                InlineKeyboardButton("🔄 Refresh", callback_data="stats_refresh")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="game_menu")
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== LEADERBOARD KEYBOARD ====================
def game_leaderboard_keyboard(lang: str = 'en'):
    """Create leaderboard navigation keyboard"""
    
    if lang == 'am':
        keyboard = [
            [
                InlineKeyboardButton("🏆 ከፍተኛ 10", callback_data="leaderboard_top10"),
                InlineKeyboardButton("💰 ከፍተኛ አሸናፊዎች", callback_data="leaderboard_winners")
            ],
            [
                InlineKeyboardButton("🎯 ከፍተኛ የማሸነፊያ መጠን", callback_data="leaderboard_winrate"),
                InlineKeyboardButton("🎫 ብዙ ጨዋታዎች", callback_data="leaderboard_games")
            ],
            [
                InlineKeyboardButton("💵 ከፍተኛ ገቢ", callback_data="leaderboard_earnings"),
                InlineKeyboardButton("⭐ ከፍተኛ ደረጃ", callback_data="leaderboard_rank")
            ],
            [
                InlineKeyboardButton("📅 ዛሬ", callback_data="leaderboard_today"),
                InlineKeyboardButton("📆 በዚህ ሳምንት", callback_data="leaderboard_week"),
                InlineKeyboardButton("📊 ሁሉንም ጊዜ", callback_data="leaderboard_all")
            ],
            [
                InlineKeyboardButton("🔍 የኔ ደረጃ", callback_data="leaderboard_my_rank"),
                InlineKeyboardButton("🔄 አድስ", callback_data="leaderboard_refresh")
            ],
            [
                InlineKeyboardButton("🔙 ወደ ጨዋታ ምናሌ", callback_data="game_menu")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("🏆 Top 10", callback_data="leaderboard_top10"),
                InlineKeyboardButton("💰 Top Winners", callback_data="leaderboard_winners")
            ],
            [
                InlineKeyboardButton("🎯 Top Win Rate", callback_data="leaderboard_winrate"),
                InlineKeyboardButton("🎫 Most Games", callback_data="leaderboard_games")
            ],
            [
                InlineKeyboardButton("💵 Top Earners", callback_data="leaderboard_earnings"),
                InlineKeyboardButton("⭐ Top Rank", callback_data="leaderboard_rank")
            ],
            [
                InlineKeyboardButton("📅 Today", callback_data="leaderboard_today"),
                InlineKeyboardButton("📆 This Week", callback_data="leaderboard_week"),
                InlineKeyboardButton("📊 All Time", callback_data="leaderboard_all")
            ],
            [
                InlineKeyboardButton("🔍 My Rank", callback_data="leaderboard_my_rank"),
                InlineKeyboardButton("🔄 Refresh", callback_data="leaderboard_refresh")
            ],
            [
                InlineKeyboardButton("🔙 Back to Game Menu", callback_data="game_menu")
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== IN-GAME KEYBOARDS ====================
def in_game_keyboard(lang: str = 'en'):
    """Create keyboard for active game session"""
    
    if lang == 'am':
        keyboard = [
            [
                InlineKeyboardButton("🎫 ካርቴላ ግዛ", callback_data="buy_cartela"),
                InlineKeyboardButton("🎲 ራስ-ጨዋታ", callback_data="auto_play")
            ],
            [
                InlineKeyboardButton("📊 የጨዋታ ስታት", callback_data="game_stats"),
                InlineKeyboardButton("🏆 ደረጃ", callback_data="game_leaderboard")
            ],
            [
                InlineKeyboardButton("⏸️ ለአፍታ አቁም", callback_data="pause_game"),
                InlineKeyboardButton("⏹️ ጨዋታውን አቁም", callback_data="end_game")
            ],
            [
                InlineKeyboardButton("🔊 ድምጽ", callback_data="toggle_sound"),
                InlineKeyboardButton("🎨 ገጽታ", callback_data="toggle_theme")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("🎫 Buy Cartela", callback_data="buy_cartela"),
                InlineKeyboardButton("🎲 Auto-Play", callback_data="auto_play")
            ],
            [
                InlineKeyboardButton("📊 Game Stats", callback_data="game_stats"),
                InlineKeyboardButton("🏆 Leaderboard", callback_data="game_leaderboard")
            ],
            [
                InlineKeyboardButton("⏸️ Pause", callback_data="pause_game"),
                InlineKeyboardButton("⏹️ End Game", callback_data="end_game")
            ],
            [
                InlineKeyboardButton("🔊 Sound", callback_data="toggle_sound"),
                InlineKeyboardButton("🎨 Theme", callback_data="toggle_theme")
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== BETTING KEYBOARD ====================
def betting_keyboard(min_bet: int = 10, max_bet: int = 1000, balance: float = 0, lang: str = 'en'):
    """Create betting amount keyboard with dynamic amounts"""
    
    # Calculate suggested bets based on balance
    suggested_bets = []
    if balance >= 100:
        suggested_bets = [50, 100, 200]
    elif balance >= 50:
        suggested_bets = [25, 50, 100]
    else:
        suggested_bets = [min_bet, min_bet * 2, min_bet * 5]
    
    if lang == 'am':
        keyboard = [
            [
                InlineKeyboardButton(f"{suggested_bets[0]} ETB", callback_data=f"bet_{suggested_bets[0]}"),
                InlineKeyboardButton(f"{suggested_bets[1]} ETB", callback_data=f"bet_{suggested_bets[1]}"),
                InlineKeyboardButton(f"{suggested_bets[2]} ETB", callback_data=f"bet_{suggested_bets[2]}")
            ],
            [
                InlineKeyboardButton(f"{min_bet * 10} ETB", callback_data=f"bet_{min_bet * 10}"),
                InlineKeyboardButton(f"{min_bet * 20} ETB", callback_data=f"bet_{min_bet * 20}"),
                InlineKeyboardButton(f"{max_bet} ETB", callback_data=f"bet_{max_bet}")
            ],
            [
                InlineKeyboardButton("🎲 ሙሉ ሂሳብ", callback_data="bet_all_in"),
                InlineKeyboardButton("💰 ግማሽ ሂሳብ", callback_data="bet_half")
            ],
            [
                InlineKeyboardButton("➕ ጨምር 10", callback_data="bet_add_10"),
                InlineKeyboardButton("➖ ቀንስ 10", callback_data="bet_subtract_10")
            ],
            [
                InlineKeyboardButton("✅ አረጋግጥ", callback_data="bet_confirm"),
                InlineKeyboardButton("🔙 ተመለስ", callback_data="game_menu")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(f"{suggested_bets[0]} ETB", callback_data=f"bet_{suggested_bets[0]}"),
                InlineKeyboardButton(f"{suggested_bets[1]} ETB", callback_data=f"bet_{suggested_bets[1]}"),
                InlineKeyboardButton(f"{suggested_bets[2]} ETB", callback_data=f"bet_{suggested_bets[2]}")
            ],
            [
                InlineKeyboardButton(f"{min_bet * 10} ETB", callback_data=f"bet_{min_bet * 10}"),
                InlineKeyboardButton(f"{min_bet * 20} ETB", callback_data=f"bet_{min_bet * 20}"),
                InlineKeyboardButton(f"{max_bet} ETB", callback_data=f"bet_{max_bet}")
            ],
            [
                InlineKeyboardButton("🎲 All In", callback_data="bet_all_in"),
                InlineKeyboardButton("💰 Half Balance", callback_data="bet_half")
            ],
            [
                InlineKeyboardButton("➕ Add 10", callback_data="bet_add_10"),
                InlineKeyboardButton("➖ Subtract 10", callback_data="bet_subtract_10")
            ],
            [
                InlineKeyboardButton("✅ Confirm", callback_data="bet_confirm"),
                InlineKeyboardButton("🔙 Back", callback_data="game_menu")
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== NUMBER SELECTION KEYBOARD ====================
def number_selection_keyboard(selected_numbers: List[int] = None, lang: str = 'en'):
    """Create number selection keyboard for bingo (1-75)"""
    
    if selected_numbers is None:
        selected_numbers = []
    
    keyboard = []
    row = []
    
    # Create 5x15 grid for numbers 1-75
    for i in range(1, 76):
        # Determine BINGO letter
        if i <= 15:
            letter = 'B'
        elif i <= 30:
            letter = 'I'
        elif i <= 45:
            letter = 'N'
        elif i <= 60:
            letter = 'G'
        else:
            letter = 'O'
        
        # Format button text
        if i in selected_numbers:
            text = f"✅ {letter}{i}"
        else:
            text = f"{letter}{i}"
        
        row.append(InlineKeyboardButton(text, callback_data=f"select_num_{i}"))
        
        if len(row) == 5:  # 5 columns per row (BINGO)
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Add control buttons based on language
    if lang == 'am':
        keyboard.extend([
            [
                InlineKeyboardButton("🎲 በዘፈቀደ", callback_data="random_numbers"),
                InlineKeyboardButton("✨ እድለኛ", callback_data="lucky_numbers")
            ],
            [
                InlineKeyboardButton("🎯 በቢንጎ ምረጥ", callback_data="bingo_pattern"),
                InlineKeyboardButton("🗑️ ሁሉንም አጥፋ", callback_data="clear_numbers")
            ],
            [
                InlineKeyboardButton("✅ አረጋግጥ", callback_data="confirm_numbers"),
                InlineKeyboardButton("🔙 ተመለስ", callback_data="game_menu")
            ]
        ])
    else:
        keyboard.extend([
            [
                InlineKeyboardButton("🎲 Random", callback_data="random_numbers"),
                InlineKeyboardButton("✨ Lucky", callback_data="lucky_numbers")
            ],
            [
                InlineKeyboardButton("🎯 Bingo Pattern", callback_data="bingo_pattern"),
                InlineKeyboardButton("🗑️ Clear All", callback_data="clear_numbers")
            ],
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_numbers"),
                InlineKeyboardButton("🔙 Back", callback_data="game_menu")
            ]
        ])
    
    return InlineKeyboardMarkup(keyboard)


# ==================== REPLY KEYBOARDS (Mobile-Friendly) ====================
def game_reply_keyboard(lang: str = 'en'):
    """Create reply keyboard for game (mobile-friendly)"""
    
    if lang == 'am':
        keyboard = [
            ["🎮 ጀምር", "⚡ ፈጣን", "📊 ስታት"],
            ["🏆 ደረጃ", "🎫 ካርቴላ", "⚙️ ቅንብር"],
            ["💰 ሂሳብ", "🎁 ሽልማት", "🔙 ምናሌ"]
        ]
    else:
        keyboard = [
            ["🎮 Play", "⚡ Quick", "📊 Stats"],
            ["🏆 Rank", "🎫 Cartela", "⚙️ Settings"],
            ["💰 Balance", "🎁 Bonus", "🔙 Menu"]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ==================== HELP/INFO KEYBOARD ====================
def game_help_keyboard(lang: str = 'en'):
    """Create help/info keyboard for game rules"""
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton("🎮 የጨዋታ ህጎች", callback_data="help_rules")],
            [InlineKeyboardButton("💰 እንዴት ማሸነፍ እንደሚቻል", callback_data="help_win")],
            [InlineKeyboardButton("🎫 ስለ ካርቴላዎች", callback_data="help_cartelas")],
            [InlineKeyboardButton("💵 ክፍያ እና ሽልማት", callback_data="help_payment")],
            [InlineKeyboardButton("❓ ተደጋጋሚ ጥያቄዎች", callback_data="help_faq")],
            [InlineKeyboardButton("📞 ደጋፊ", callback_data="help_support")],
            [InlineKeyboardButton("🔙 ተመለስ", callback_data="game_menu")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎮 Game Rules", callback_data="help_rules")],
            [InlineKeyboardButton("💰 How to Win", callback_data="help_win")],
            [InlineKeyboardButton("🎫 About Cartelas", callback_data="help_cartelas")],
            [InlineKeyboardButton("💵 Payments & Prizes", callback_data="help_payment")],
            [InlineKeyboardButton("❓ FAQ", callback_data="help_faq")],
            [InlineKeyboardButton("📞 Support", callback_data="help_support")],
            [InlineKeyboardButton("🔙 Back", callback_data="game_menu")]
        ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== UTILITY FUNCTIONS ====================
def get_game_keyboard(name: str, **kwargs):
    """Get game keyboard by name for dynamic loading"""
    
    keyboards = {
        'game_menu': game_menu_keyboard,
        'quick_play': quick_play_keyboard,
        'cartela_selection': cartela_selection_keyboard,
        'game_control': game_control_keyboard,
        'game_settings': game_settings_keyboard,
        'game_stats': game_stats_keyboard,
        'game_leaderboard': game_leaderboard_keyboard,
        'in_game': in_game_keyboard,
        'betting': betting_keyboard,
        'number_selection': number_selection_keyboard,
        'game_reply': game_reply_keyboard,
        'game_help': game_help_keyboard,
    }
    
    keyboard_func = keyboards.get(name)
    if keyboard_func:
        return keyboard_func(**kwargs)
    return None


# ==================== KEYBOARD PRESETS ====================
GAME_KEYBOARD_PRESETS = {
    'minimal': ['game_menu', 'quick_play', 'back'],
    'full': ['game_menu', 'quick_play', 'cartela_selection', 'game_control', 'game_settings'],
    'mobile': ['game_reply', 'quick_play'],
    'admin_game': ['game_stats', 'game_leaderboard', 'game_settings'],
}

# Export all keyboards
__all__ = [
    'game_menu_keyboard',
    'quick_play_keyboard',
    'cartela_selection_keyboard',
    'game_control_keyboard',
    'game_settings_keyboard',
    'game_stats_keyboard',
    'game_leaderboard_keyboard',
    'in_game_keyboard',
    'betting_keyboard',
    'number_selection_keyboard',
    'game_reply_keyboard',
    'game_help_keyboard',
    'get_game_keyboard',
    'GAME_KEYBOARD_PRESETS'
]