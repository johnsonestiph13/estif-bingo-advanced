# telegram-bot/bot/handlers/game.py
# ESTIF BINGO 24/7 - ULTIMATE GAME HANDLER
# Ultra-fast, production-ready, fully optimized

import json
import asyncio
import time
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache, wraps
from dataclasses import dataclass, asdict
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update, User
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.db.database import database
from bot.config import config
from bot.utils import logger
from bot.texts.emojis import get_emoji

# ==================== ULTRA-FAST CACHE ====================
class FastCache:
    """Lightning-fast in-memory cache with TTL"""
    __slots__ = ('_cache', '_ttl')
    
    def __init__(self, ttl_seconds: int = 60):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        data = self._cache.get(key)
        if data and time.time() - data[1] < self._ttl:
            return data[0]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = (value, time.time())
    
    def delete(self, key: str):
        self._cache.pop(key, None)
    
    def clear(self):
        self._cache.clear()

# Global caches
user_cache = FastCache(ttl_seconds=30)
stats_cache = FastCache(ttl_seconds=60)
leaderboard_cache = FastCache(ttl_seconds=120)

# ==================== PERFORMANCE DECORATORS ====================
def async_cache(cache: FastCache, key_func=None):
    """Decorator for caching async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = key_func(*args, **kwargs) if key_func else f"{func.__name__}:{args[0] if args else ''}"
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

# ==================== DATA CLASSES ====================
@dataclass
class GameSession:
    telegram_id: int
    username: str
    balance: float
    auth_code: str
    created_at: float
    expires_at: float
    cartelas: int = 0
    spent: float = 0.0
    won: float = 0.0
    
    @property
    def net(self) -> float:
        return self.won - self.spent
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

# ==================== SESSION MANAGER ====================
class SessionManager:
    """Ultra-fast session manager with auto-cleanup"""
    __slots__ = ('_sessions', '_lock', '_cleanup_task')
    
    def __init__(self):
        self._sessions: Dict[int, GameSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
    
    async def start(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            await self._cleanup()
    
    async def _cleanup(self):
        async with self._lock:
            expired = [tid for tid, s in self._sessions.items() if s.is_expired]
            for tid in expired:
                del self._sessions[tid]
            if expired:
                logger.debug(f"Cleaned {len(expired)} expired sessions")
    
    async def create(self, telegram_id: int, username: str, balance: float, auth_code: str) -> GameSession:
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
    
    async def get(self, telegram_id: int) -> Optional[GameSession]:
        async with self._lock:
            session = self._sessions.get(telegram_id)
            if session and session.is_expired:
                del self._sessions[telegram_id]
                return None
            return session
    
    async def update(self, telegram_id: int, **kwargs):
        async with self._lock:
            session = self._sessions.get(telegram_id)
            if session:
                for key, val in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, val)
    
    async def delete(self, telegram_id: int):
        async with self._lock:
            self._sessions.pop(telegram_id, None)

session_manager = SessionManager()

# ==================== STATS MANAGER ====================
class StatsManager:
    """Ultra-fast statistics manager with caching"""
    
    @staticmethod
    @async_cache(stats_cache)
    async def get_stats(telegram_id: int) -> Dict[str, Any]:
        try:
            async with database._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        COUNT(CASE WHEN type = 'bet' THEN 1 END) as games,
                        COUNT(CASE WHEN type = 'win' THEN 1 END) as wins,
                        COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as total_bet,
                        COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END), 0) as total_win,
                        MAX(CASE WHEN type = 'win' THEN amount ELSE 0 END) as best_win,
                        MAX(timestamp) as last_played
                    FROM game_transactions
                    WHERE telegram_id = $1
                """, telegram_id)
                
                games = row['games'] or 0
                wins = row['wins'] or 0
                win_rate = (wins / games * 100) if games > 0 else 0
                
                return {
                    'games': games,
                    'wins': wins,
                    'losses': games - wins,
                    'win_rate': round(win_rate, 1),
                    'total_bet': float(row['total_bet'] or 0),
                    'total_win': float(row['total_win'] or 0),
                    'net_profit': float(row['total_win'] or 0) - float(row['total_bet'] or 0),
                    'best_win': float(row['best_win'] or 0),
                    'last_played': row['last_played'].strftime("%Y-%m-%d %H:%M") if row['last_played'] else "Never"
                }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                'games': 0, 'wins': 0, 'losses': 0, 'win_rate': 0,
                'total_bet': 0, 'total_win': 0, 'net_profit': 0, 'best_win': 0,
                'last_played': "Never"
            }
    
    @staticmethod
    @async_cache(leaderboard_cache)
    async def get_leaderboard(limit: int = 10) -> list:
        try:
            async with database._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT telegram_id, username, total_won, games_played, games_won, balance
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
                        'win_rate': f"{win_rate:.1f}%",
                        'balance': float(row['balance'])
                    })
                return leaderboard
        except Exception as e:
            logger.error(f"Leaderboard error: {e}")
            return []
    
    @staticmethod
    async def get_active_players() -> int:
        try:
            async with database._pool.acquire() as conn:
                return await conn.fetchval("""
                    SELECT COUNT(DISTINCT telegram_id)
                    FROM game_transactions
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                """) or 0
        except Exception:
            return 0

# ==================== MESSAGE BUILDER ====================
class MessageBuilder:
    """Ultra-fast message builder with templates"""
    
    @staticmethod
    def welcome(balance: float, win_percentage: int, active_players: int) -> str:
        return (
            f"{get_emoji('game')} <b>ESTIF BINGO 24/7</b> {get_emoji('game')}\n\n"
            f"{get_emoji('money')} <b>Balance:</b> <code>{balance:.2f} ETB</code>\n"
            f"{get_emoji('cartela')} <b>Cartela Price:</b> <code>{config.CARTELA_PRICE} ETB</code>\n"
            f"{get_emoji('stats')} <b>Max Cartelas:</b> <code>{config.MAX_CARTELAS}</code>\n"
            f"{get_emoji('target')} <b>Win Rate:</b> <code>{win_percentage}%</code>\n"
            f"{get_emoji('users')} <b>Active Players:</b> <code>{active_players}</code>\n\n"
            f"{get_emoji('play')} <b>How to Play:</b>\n"
            f"• Select 1–4 cartelas per round\n"
            f"• Numbers are drawn automatically\n"
            f"• Match patterns to win!\n"
            f"• Win up to {win_percentage}% of pool!\n\n"
            f"{get_emoji('click')} <b>Click the button below to start!</b>"
        )
    
    @staticmethod
    def insufficient_balance(balance: float, needed: float) -> str:
        return (
            f"{get_emoji('error')} <b>Insufficient Balance!</b>\n\n"
            f"{get_emoji('money')} Your Balance: <code>{balance:.2f} ETB</code>\n"
            f"{get_emoji('cartela')} Need at least: <code>{needed} ETB</code>\n\n"
            f"{get_emoji('deposit')} <b>Add funds via /deposit</b>"
        )
    
    @staticmethod
    def stats(stats: Dict[str, Any], rank: Optional[int]) -> str:
        rank_text = f"#{rank}" if rank else "Unranked"
        return (
            f"{get_emoji('stats')} <b>YOUR STATISTICS</b>\n\n"
            f"{get_emoji('game')} <b>Games:</b>\n"
            f"• Played: <code>{stats['games']}</code>\n"
            f"• Won: <code>{stats['wins']}</code>\n"
            f"• Lost: <code>{stats['losses']}</code>\n"
            f"• Win Rate: <code>{stats['win_rate']}%</code>\n\n"
            f"{get_emoji('money')} <b>Financial:</b>\n"
            f"• Total Bet: <code>{stats['total_bet']:.2f} ETB</code>\n"
            f"• Total Win: <code>{stats['total_win']:.2f} ETB</code>\n"
            f"• Net Profit: <code>{stats['net_profit']:+.2f} ETB</code>\n"
            f"• Best Win: <code>{stats['best_win']:.2f} ETB</code>\n\n"
            f"{get_emoji('clock')} <b>Last Played:</b> {stats['last_played']}\n\n"
            f"{get_emoji('trophy')} <b>Rank:</b> {rank_text}"
        )
    
    @staticmethod
    def leaderboard(entries: list) -> str:
        if not entries:
            return f"{get_emoji('trophy')} <b>No players yet. Be the first!</b>"
        
        lines = []
        for p in entries:
            if p['rank'] == 1:
                emoji = '🥇'
            elif p['rank'] == 2:
                emoji = '🥈'
            elif p['rank'] == 3:
                emoji = '🥉'
            else:
                emoji = f"{p['rank']}️⃣"
            lines.append(f"{emoji} <b>{p['username'][:15]}</b> - {p['total_won']:.0f} ETB won ({p['win_rate']})")
        
        return (
            f"{get_emoji('trophy')} <b>LEADERBOARD</b> {get_emoji('trophy')}\n\n"
            f"{chr(10).join(lines)}\n\n"
            f"{get_emoji('calendar')} Updated: {datetime.now().strftime('%H:%M:%S')}"
        )

# ==================== MAIN COMMANDS ====================
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ultra-fast /play command"""
    user: User = update.effective_user
    telegram_id = user.id
    
    # Check cache first
    user_data = user_cache.get(f"user_{telegram_id}")
    if not user_data:
        user_data = await database.get_user(telegram_id)
        if user_data:
            user_cache.set(f"user_{telegram_id}", user_data)
    
    if not user_data or not user_data.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} Please register first using /register",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Parallel fetch
    balance_task = database.get_balance(telegram_id)
    win_percentage_task = database.get_win_percentage()
    active_players_task = StatsManager.get_active_players()
    
    balance, win_percentage, active_players = await asyncio.gather(
        balance_task, win_percentage_task, active_players_task
    )
    
    if balance < config.MIN_BALANCE_FOR_PLAY:
        await update.message.reply_text(
            MessageBuilder.insufficient_balance(balance, config.MIN_BALANCE_FOR_PLAY),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Generate auth code
    auth_code = await database.create_auth_code(telegram_id)
    await session_manager.create(telegram_id, user.username or user.first_name, balance, auth_code)
    
    # Build web app URL
    web_app_url = f"{config.GAME_WEB_URL}?code={auth_code}&telegram_id={telegram_id}&v={int(time.time())}"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('game')} PLAY BINGO NOW {get_emoji('game')}", web_app=WebAppInfo(url=web_app_url))],
        [
            InlineKeyboardButton(f"{get_emoji('stats')} My Stats", callback_data="game_stats"),
            InlineKeyboardButton(f"{get_emoji('trophy')} Leaderboard", callback_data="game_leaderboard")
        ]
    ])
    
    await update.message.reply_text(
        MessageBuilder.welcome(balance, win_percentage, active_players),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# ==================== CALLBACK HANDLERS ====================
async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle web app callbacks"""
    try:
        data = update.effective_message.web_app_data
        if not data:
            return
        
        game_data = json.loads(data.data)
        action = game_data.get('action')
        telegram_id = update.effective_user.id
        
        if action == 'game_start':
            await _handle_game_start(update, game_data, telegram_id)
        elif action == 'game_result':
            await _handle_game_result(update, game_data, telegram_id)
        elif action == 'game_end':
            await _handle_game_end(update, telegram_id)
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in web app data")
    except Exception as e:
        logger.error(f"Game callback error: {e}")

async def _handle_game_start(update: Update, data: Dict, telegram_id: int):
    """Handle game start"""
    cartelas = data.get('cartelas', 1)
    cost = cartelas * config.CARTELA_PRICE
    
    balance = await database.get_balance(telegram_id)
    await session_manager.update(telegram_id, cartelas=cartelas, spent=cost)
    
    await update.message.reply_text(
        f"{get_emoji('play')} <b>Game Started!</b>\n\n"
        f"{get_emoji('cartela')} Cartelas: <code>{cartelas}</code>\n"
        f"{get_emoji('money')} Cost: <code>{cost:.2f} ETB</code>\n"
        f"{get_emoji('balance')} New Balance: <code>{balance - cost:.2f} ETB</code>\n\n"
        f"{get_emoji('four_leaf_clover')} Good luck!",
        parse_mode=ParseMode.HTML
    )

async def _handle_game_result(update: Update, data: Dict, telegram_id: int):
    """Handle game result (win/loss)"""
    won = data.get('won', False)
    amount = float(data.get('amount', 0))
    pattern = data.get('pattern', 'BINGO!')
    numbers_drawn = data.get('numbers_drawn', 0)
    
    new_balance = await database.get_balance(telegram_id)
    stats = await StatsManager.get_stats(telegram_id)
    
    if won and amount > 0:
        await session_manager.update(telegram_id, won=amount)
        stats_cache.delete(f"stats:{telegram_id}")
        leaderboard_cache.clear()
        
        await update.message.reply_text(
            f"{get_emoji('win')} <b>CONGRATULATIONS! YOU WON!</b> {get_emoji('win')}\n\n"
            f"{get_emoji('money')} Winnings: <code>+{amount:.2f} ETB</code>\n"
            f"{get_emoji('balance')} New Balance: <code>{new_balance:.2f} ETB</code>\n"
            f"{get_emoji('trophy')} Total Wins: <code>{stats['wins'] + 1}</code>\n"
            f"{get_emoji('star')} Win Rate: <code>{stats['win_rate']:.1f}%</code>\n\n"
            f"{get_emoji('target')} Pattern: {pattern}\n\n"
            f"{get_emoji('refresh')} Play again with /play",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            f"{get_emoji('lose')} <b>Better Luck Next Time!</b>\n\n"
            f"{get_emoji('stats')} Numbers Drawn: <code>{numbers_drawn}</code>\n"
            f"{get_emoji('money')} Balance: <code>{new_balance:.2f} ETB</code>\n"
            f"{get_emoji('star')} Win Rate: <code>{stats['win_rate']:.1f}%</code>\n\n"
            f"{get_emoji('muscle')} Don't give up!\n"
            f"{get_emoji('refresh')} Play again with /play",
            parse_mode=ParseMode.HTML
        )

async def _handle_game_end(update: Update, telegram_id: int):
    """Handle game end - show session summary"""
    session = await session_manager.get(telegram_id)
    if session:
        await update.message.reply_text(
            f"{get_emoji('stats')} <b>Session Summary</b>\n\n"
            f"{get_emoji('cartela')} Cartelas: {session.cartelas}\n"
            f"{get_emoji('money')} Spent: <code>{session.spent:.2f} ETB</code>\n"
            f"{get_emoji('win')} Won: <code>{session.won:.2f} ETB</code>\n"
            f"{get_emoji('balance')} Net: <code>{session.net:+.2f} ETB</code>\n\n"
            f"{get_emoji('refresh')} Play again with /play",
            parse_mode=ParseMode.HTML
        )
        await session_manager.delete(telegram_id)

# ==================== STATS & LEADERBOARD ====================
async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stats button"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    stats = await StatsManager.get_stats(telegram_id)
    leaderboard = await StatsManager.get_leaderboard(50)
    
    rank = next((i+1 for i, p in enumerate(leaderboard) if p['username'] == (await database.get_user(telegram_id)).get('username')), None)
    
    await query.edit_message_text(
        MessageBuilder.stats(stats, rank),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="back_to_game")
        ]])
    )

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard button"""
    query = update.callback_query
    await query.answer()
    
    leaderboard = await StatsManager.get_leaderboard(10)
    
    await query.edit_message_text(
        MessageBuilder.leaderboard(leaderboard),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{get_emoji('refresh')} Refresh", callback_data="game_leaderboard"),
                InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="back_to_game")
            ]
        ])
    )

async def back_to_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button"""
    query = update.callback_query
    await query.answer()
    await play_command(update, context)

# ==================== INITIALIZATION ====================
async def start_game_handlers():
    """Initialize game handlers"""
    await session_manager.start()
    logger.info(f"{get_emoji('game')} Game handlers initialized (ULTRA MODE)")

# ==================== EXPORTS ====================
__all__ = [
    'play_command',
    'game_callback',
    'stats_callback',
    'leaderboard_callback',
    'back_to_game_callback',
    'start_game_handlers',
]