# telegram-bot/bot/handlers/game.py
# ULTRA OPTIMIZED - Complete Game Handler with Web App Launch

import json
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from functools import lru_cache
from dataclasses import dataclass, asdict

from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, 
    WebAppInfo, Update, User
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.db.database import Database
from bot.config import config
from bot.utils import logger
from bot.texts.emojis import get_emoji

# ==================== DATA CLASSES ====================
@dataclass
class GameSession:
    """Game session data"""
    telegram_id: int
    username: str
    balance: float
    auth_code: str
    created_at: float
    expires_at: float
    cartelas_purchased: int = 0
    total_spent: float = 0
    total_won: float = 0
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


@dataclass
class GameStats:
    """Player game statistics"""
    games_played: int = 0
    games_won: int = 0
    total_bet: float = 0
    total_win: float = 0
    best_win: float = 0
    last_played: Optional[datetime] = None
    
    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0
        return (self.games_won / self.games_played) * 100
    
    @property
    def net_profit(self) -> float:
        return self.total_win - self.total_bet


# ==================== CACHE MANAGEMENT ====================
class GameCache:
    """Ultra-fast in-memory cache"""
    
    def __init__(self, ttl_seconds: int = 120):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = (value, time.time())
    
    def clear(self):
        self._cache.clear()


game_cache = GameCache()


# ==================== SESSION MANAGER ====================
class GameSessionManager:
    """Manages active game sessions"""
    
    def __init__(self):
        self._sessions: Dict[int, GameSession] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(self, telegram_id: int, username: str, 
                             balance: float, auth_code: str) -> GameSession:
        async with self._lock:
            session = GameSession(
                telegram_id=telegram_id,
                username=username,
                balance=balance,
                auth_code=auth_code,
                created_at=time.time(),
                expires_at=time.time() + 300
            )
            self._sessions[telegram_id] = session
            return session
    
    async def get_session(self, telegram_id: int) -> Optional[GameSession]:
        async with self._lock:
            session = self._sessions.get(telegram_id)
            if session and session.is_expired():
                del self._sessions[telegram_id]
                return None
            return session
    
    async def end_session(self, telegram_id: int):
        async with self._lock:
            if telegram_id in self._sessions:
                del self._sessions[telegram_id]


session_manager = GameSessionManager()


# ==================== STATISTICS MANAGER ====================
class StatsManager:
    """Manages player statistics"""
    
    @staticmethod
    @lru_cache(maxsize=1000)
    async def get_player_stats(telegram_id: int) -> GameStats:
        try:
            async with Database._pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(CASE WHEN type = 'bet' THEN 1 END) as games_played,
                        COUNT(CASE WHEN type = 'win' THEN 1 END) as games_won,
                        COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as total_bet,
                        COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END), 0) as total_win,
                        MAX(CASE WHEN type = 'win' THEN amount ELSE 0 END) as best_win,
                        MAX(timestamp) as last_played
                    FROM game_transactions
                    WHERE telegram_id = $1
                """, telegram_id)
            
            return GameStats(
                games_played=stats['games_played'] or 0,
                games_won=stats['games_won'] or 0,
                total_bet=float(stats['total_bet'] or 0),
                total_win=float(stats['total_win'] or 0),
                best_win=float(stats['best_win'] or 0),
                last_played=stats['last_played']
            )
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return GameStats()
    
    @staticmethod
    async def get_leaderboard(limit: int = 10) -> List[Dict]:
        cache_key = f"leaderboard_{limit}"
        cached = game_cache.get(cache_key)
        if cached:
            return cached
        
        try:
            async with Database._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT telegram_id, username, total_won, games_played, games_won
                    FROM users 
                    WHERE registered = TRUE AND total_won > 0
                    ORDER BY total_won DESC
                    LIMIT $1
                """, limit)
                
                leaderboard = []
                for i, row in enumerate(rows, 1):
                    win_rate = (row['games_won'] / row['games_played'] * 100) if row['games_played'] > 0 else 0
                    leaderboard.append({
                        'rank': i,
                        'username': row['username'] or f"Player_{row['telegram_id']}",
                        'total_won': float(row['total_won']),
                        'win_rate': f"{win_rate:.1f}%"
                    })
            
            game_cache.set(cache_key, leaderboard)
            return leaderboard
        except Exception as e:
            logger.error(f"Leaderboard error: {e}")
            return []


# ==================== MAIN PLAY COMMAND ====================
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /play command - Show game menu with PLAY NOW button"""
    user: User = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name
    
    try:
        # Get user data
        user_data = await Database.get_user(telegram_id)
        
        if not user_data or not user_data.get('registered'):
            await update.message.reply_text(
                f"{get_emoji('error')} ❌ *Please register first!*\n\n"
                f"Use /register to complete your registration.",
                parse_mode='Markdown'
            )
            return
        
        # Get balance and win percentage
        balance = await Database.get_balance(telegram_id)
        win_percentage = await Database.get_win_percentage()
        
        # Check minimum balance
        if balance < config.MIN_BALANCE_FOR_PLAY:
            await update.message.reply_text(
                f"{get_emoji('error')} ❌ *Insufficient Balance!*\n\n"
                f"Need at least `{config.MIN_BALANCE_FOR_PLAY} ETB` to play.\n"
                f"Your balance: `{balance:.2f} ETB`\n\n"
                f"Use /deposit to add funds.",
                parse_mode='Markdown'
            )
            return
        
        # Generate auth code
        auth_code = await Database.create_auth_code(telegram_id)
        
        # Create session
        await session_manager.create_session(telegram_id, username, balance, auth_code)
        
        # Build web app URL with code parameter
        web_app_url = f"{config.GAME_WEB_URL}?code={auth_code}&telegram_id={telegram_id}&v={int(time.time())}"
        
        # Get player stats for display
        stats = await StatsManager.get_player_stats(telegram_id)
        
        # Create keyboard with PLAY NOW button (opens web app)
        keyboard = [
            [InlineKeyboardButton(
                f"{get_emoji('game')} 🎮 PLAY NOW 🎮 {get_emoji('game')}", 
                web_app=WebAppInfo(url=web_app_url)
            )],
            [InlineKeyboardButton(
                f"{get_emoji('stats')} 📊 MY STATS 📊", 
                callback_data="game_stats"
            )],
            [InlineKeyboardButton(
                f"{get_emoji('trophy')} 🏆 TOTAL WIN HISTORY 🏆", 
                callback_data="game_leaderboard"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send game menu message
        await update.message.reply_text(
            f"{get_emoji('game')} *🎲 ESTIF BINGO 24/7 🎲* {get_emoji('game')}\n\n"
            f"{get_emoji('money')} *Balance:* `{balance:.2f} ETB`\n"
            f"{get_emoji('cartela')} *Cartela Price:* `{config.CARTELA_PRICE} ETB`\n"
            f"{get_emoji('stats')} *Max Cartelas:* `{config.MAX_CARTELAS}`\n"
            f"{get_emoji('target')} *Win Percentage:* `{win_percentage}%`\n\n"
            f"{get_emoji('chart')} *Your Stats:*\n"
            f"• Games Played: `{stats.games_played}`\n"
            f"• Games Won: `{stats.games_won}`\n"
            f"• Win Rate: `{stats.win_rate:.1f}%`\n"
            f"• Total Won: `{stats.total_win:.2f} ETB`\n\n"
            f"{get_emoji('play')} *👇 Click PLAY NOW to start the game!*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Play command executed for user {telegram_id}")
        
    except Exception as e:
        logger.error(f"Play command error: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *An error occurred.*\n\n"
            f"Please try again later.\n\n"
            f"Support: {config.SUPPORT_GROUP_LINK}",
            parse_mode='Markdown'
        )


# ==================== STATS CALLBACK ====================
async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle My Stats button callback"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    stats = await StatsManager.get_player_stats(telegram_id)
    leaderboard = await StatsManager.get_leaderboard(50)
    
    # Find rank
    rank = None
    for i, p in enumerate(leaderboard):
        if p.get('username') and p['username'] in str(stats):
            rank = i + 1
            break
    
    stats_message = (
        f"{get_emoji('stats')} *📊 YOUR GAME STATISTICS* {get_emoji('stats')}\n\n"
        f"{get_emoji('game')} *Games:*\n"
        f"• Played: `{stats.games_played}`\n"
        f"• Won: `{stats.games_won}`\n"
        f"• Lost: `{stats.games_played - stats.games_won}`\n"
        f"• Win Rate: `{stats.win_rate:.1f}%`\n\n"
        f"{get_emoji('money')} *Financial:*\n"
        f"• Total Bet: `{stats.total_bet:.2f} ETB`\n"
        f"• Total Won: `{stats.total_win:.2f} ETB`\n"
        f"• Net Profit: `{stats.net_profit:+.2f} ETB`\n"
        f"• Best Win: `{stats.best_win:.2f} ETB`\n\n"
        f"{get_emoji('trophy')} *Rank:* `#{rank if rank else 'Unranked'}`\n\n"
        f"{get_emoji('refresh')} Use /play to play again!"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('back')} 🔙 Back to Game", callback_data="back_to_game")]
    ])
    
    await query.edit_message_text(
        stats_message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


# ==================== LEADERBOARD CALLBACK ====================
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Total Win History button callback"""
    query = update.callback_query
    await query.answer()
    
    leaderboard = await StatsManager.get_leaderboard(15)
    win_percentage = await Database.get_win_percentage()
    
    if not leaderboard:
        entries = f"{get_emoji('trophy')} *No winners yet. Be the first!*"
    else:
        entries_lines = []
        for p in leaderboard[:10]:
            if p['rank'] == 1:
                medal = "🥇"
            elif p['rank'] == 2:
                medal = "🥈"
            elif p['rank'] == 3:
                medal = "🥉"
            else:
                medal = f"{p['rank']}️⃣"
            entries_lines.append(
                f"{medal} *{p['username'][:15]}* - `{p['total_won']:.0f} ETB` (Win Rate: {p['win_rate']})"
            )
        entries = "\n".join(entries_lines)
    
    leaderboard_message = (
        f"{get_emoji('trophy')} *🏆 TOTAL WIN HISTORY 🏆* {get_emoji('trophy')}\n\n"
        f"{entries}\n\n"
        f"{get_emoji('calendar')} *Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"{get_emoji('target')} *Current Win Percentage:* `{win_percentage}%`\n\n"
        f"{get_emoji('info')} Top 10 players by total winnings."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('refresh')} 🔄 Refresh", callback_data="game_leaderboard")],
        [InlineKeyboardButton(f"{get_emoji('back')} 🔙 Back to Game", callback_data="back_to_game")]
    ])
    
    await query.edit_message_text(
        leaderboard_message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


# ==================== BACK TO GAME CALLBACK ====================
async def back_to_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Back to Game button callback"""
    query = update.callback_query
    await query.answer()
    
    # Create a new update with the user and call play_command
    # This effectively shows the game menu again
    await play_command(update, context)


# ==================== GAME CALLBACK (Web App Data) ====================
async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle web app game data (when game sends results)"""
    user: User = update.effective_user
    telegram_id = user.id
    
    try:
        data = update.effective_message.web_app_data
        if not data:
            return
        
        game_data = json.loads(data.data)
        action = game_data.get('action')
        
        if action == 'game_start':
            cartelas = game_data.get('cartelas', 1)
            cost = cartelas * config.CARTELA_PRICE
            
            balance = await Database.get_balance(telegram_id)
            win_percentage = await Database.get_win_percentage()
            
            await update.message.reply_text(
                f"{get_emoji('play')} 🎮 *Game Started!* 🎮\n\n"
                f"{get_emoji('cartela')} Cartelas: `{cartelas}`\n"
                f"{get_emoji('money')} Cost: `{cost:.2f} ETB`\n"
                f"{get_emoji('balance')} New Balance: `{balance - cost:.2f} ETB`\n"
                f"{get_emoji('target')} Win Chance: `{win_percentage}%`\n\n"
                f"{get_emoji('four_leaf_clover')} Good luck!",
                parse_mode='Markdown'
            )
            
        elif action == 'game_result':
            won = game_data.get('won', False)
            amount = float(game_data.get('amount', 0))
            pattern = game_data.get('pattern', 'Unknown')
            cartela_id = game_data.get('cartela_id', 'N/A')
            
            new_balance = await Database.get_balance(telegram_id)
            stats = await StatsManager.get_player_stats(telegram_id)
            
            if won and amount > 0:
                await update.message.reply_text(
                    f"{get_emoji('win')} 🎉 *CONGRATULATIONS! YOU WON!* 🎉\n\n"
                    f"{get_emoji('money')} Winnings: `+{amount:.2f} ETB`\n"
                    f"{get_emoji('balance')} New Balance: `{new_balance:.2f} ETB`\n"
                    f"{get_emoji('trophy')} Total Wins: `{stats.games_won + 1}`\n"
                    f"{get_emoji('star')} Win Rate: `{stats.win_rate:.1f}%`\n\n"
                    f"{get_emoji('target')} Pattern: `{pattern}`\n"
                    f"{get_emoji('cartela')} Cartela: `{cartela_id}`\n\n"
                    f"{get_emoji('refresh')} Use /play to play again!",
                    parse_mode='Markdown'
                )
                game_cache.clear()
            else:
                await update.message.reply_text(
                    f"{get_emoji('lose')} 😢 *Better Luck Next Time!*\n\n"
                    f"{get_emoji('money')} Current Balance: `{new_balance:.2f} ETB`\n"
                    f"{get_emoji('star')} Win Rate: `{stats.win_rate:.1f}%`\n\n"
                    f"{get_emoji('muscle')} Don't give up! Use /play to try again!",
                    parse_mode='Markdown'
                )
                
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
    except Exception as e:
        logger.error(f"Game callback error: {e}")


# ==================== START GAME HANDLERS ====================
async def start_game_handlers():
    """Initialize game handlers"""
    logger.info(f"{get_emoji('game')} Game handlers initialized")


# ==================== EXPORTS ====================
__all__ = [
    'play_command',
    'game_callback',
    'stats_callback',
    'leaderboard_callback',
    'back_to_game_callback',
    'start_game_handlers',
]