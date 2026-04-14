# bot/handlers/game.py - ULTRA OPTIMIZED GAME HANDLER (NO QUICK-PLAY BUTTONS)

import json
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any
from functools import lru_cache
import logging
from dataclasses import dataclass, asdict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update, User
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.db.database import database
from bot.config import config
from bot.utils import logger
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)

# ==================== CACHE & DATA CLASSES (unchanged) ====================
class GameCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0
    def get(self, key: str):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                self._hits += 1
                return value
            else:
                del self._cache[key]
        self._misses += 1
        return None
    def set(self, key: str, value: Any):
        self._cache[key] = (value, time.time())
    def clear(self):
        self._cache.clear()
    def stats(self) -> Dict:
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {'size': len(self._cache), 'hits': self._hits, 'misses': self._misses, 'hit_rate': f"{hit_rate:.1f}%"}

game_cache = GameCache(ttl_seconds=120)

@dataclass
class GameSession:
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
    games_played: int = 0
    games_won: int = 0
    total_bet: float = 0
    total_win: float = 0
    best_win: float = 0
    last_played: Optional[datetime] = None
    @property
    def win_rate(self) -> float:
        return (self.games_won / self.games_played * 100) if self.games_played else 0
    @property
    def net_profit(self) -> float:
        return self.total_win - self.total_bet

# ==================== GAME SESSION MANAGER ====================
class GameSessionManager:
    def __init__(self, cleanup_interval: int = 60):
        self._sessions: Dict[int, GameSession] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    async def start(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.cleanup_expired()
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    async def cleanup_expired(self):
        async with self._lock:
            expired = [tid for tid, s in self._sessions.items() if s.is_expired()]
            for tid in expired:
                del self._sessions[tid]
    async def create_session(self, telegram_id: int, username: str, balance: float, auth_code: str) -> GameSession:
        async with self._lock:
            session = GameSession(telegram_id, username, balance, auth_code, time.time(), time.time() + 300)
            self._sessions[telegram_id] = session
            return session
    async def get_session(self, telegram_id: int) -> Optional[GameSession]:
        async with self._lock:
            session = self._sessions.get(telegram_id)
            if session and session.is_expired():
                del self._sessions[telegram_id]
                return None
            return session
    async def update_session(self, telegram_id: int, **kwargs):
        async with self._lock:
            session = self._sessions.get(telegram_id)
            if session:
                for k, v in kwargs.items():
                    if hasattr(session, k):
                        setattr(session, k, v)
    async def end_session(self, telegram_id: int):
        async with self._lock:
            self._sessions.pop(telegram_id, None)

session_manager = GameSessionManager()

# ==================== STATISTICS MANAGER ====================
class StatsManager:
    @staticmethod
    @lru_cache(maxsize=1000)
    async def get_player_stats(telegram_id: int) -> GameStats:
        try:
            user = await database.get_user(telegram_id)
            if not user:
                return GameStats()
            async with database._pool.acquire() as conn:
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
    async def get_leaderboard(limit: int = 10) -> list:
        cache_key = f"leaderboard_{limit}"
        cached = game_cache.get(cache_key)
        if cached:
            return cached
        try:
            async with database._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT telegram_id, username, total_won, games_played, games_won, balance
                    FROM users WHERE registered = TRUE AND total_won > 0
                    ORDER BY total_won DESC LIMIT $1
                """, limit)
                leaderboard = []
                for i, row in enumerate(rows, 1):
                    win_rate = (row['games_won'] / row['games_played'] * 100) if row['games_played'] > 0 else 0
                    leaderboard.append({
                        'rank': i,
                        'telegram_id': row['telegram_id'],
                        'username': row['username'] or f"Player_{row['telegram_id']}",
                        'total_won': float(row['total_won']),
                        'balance': float(row['balance']),
                        'win_rate': f"{win_rate:.1f}%"
                    })
            game_cache.set(cache_key, leaderboard)
            return leaderboard
        except Exception as e:
            logger.error(f"Leaderboard error: {e}")
            return []
    
    @staticmethod
    async def get_active_players_count() -> int:
        cache_key = "active_players_count"
        cached = game_cache.get(cache_key)
        if cached:
            return cached
        try:
            async with database._pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(DISTINCT telegram_id) FROM game_transactions WHERE timestamp > NOW() - INTERVAL '24 hours'")
            game_cache.set(cache_key, count or 0)
            return count or 0
        except Exception:
            return 0

# ==================== MAIN /play COMMAND (WITHOUT QUICK-PLAY BUTTONS) ====================
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user: User = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name

    try:
        user_data, balance, win_percentage, active_players = await asyncio.gather(
            database.get_user(telegram_id),
            database.get_balance(telegram_id),
            database.get_win_percentage(),
            StatsManager.get_active_players_count()
        )
        if not user_data or not user_data.get('registered'):
            await update.message.reply_text(f"{get_emoji('error')} Please register first using /register", parse_mode=ParseMode.HTML)
            return
        if balance < config.MIN_BALANCE_FOR_PLAY:
            await update.message.reply_text(
                f"{get_emoji('error')} <b>Insufficient Balance!</b>\n\n{get_emoji('money')} Your Balance: <code>{balance:.2f} ETB</code>\n{get_emoji('cartela')} Need at least: <code>{config.MIN_BALANCE_FOR_PLAY} ETB</code>\n\n{get_emoji('deposit')} <b>Add funds via /deposit</b>",
                parse_mode=ParseMode.HTML
            )
            return

        auth_code = await database.create_auth_code(telegram_id)
        await session_manager.create_session(telegram_id, username, balance, auth_code)
        web_app_url = f"{config.GAME_WEB_URL}?code={auth_code}&telegram_id={telegram_id}&v={int(time.time())}"

        # Keyboard: only PLAY button + Stats + Leaderboard (no quick-play row)
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('game')} PLAY BINGO NOW {get_emoji('game')}", web_app=WebAppInfo(url=web_app_url))],
            [
                InlineKeyboardButton(f"{get_emoji('stats')} My Stats", callback_data="game_stats"),
                InlineKeyboardButton(f"{get_emoji('trophy')} Leaderboard", callback_data="game_leaderboard")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_msg = (
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

        await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Play command error: {e}")
        await update.message.reply_text(f"{get_emoji('error')} An error occurred. Please try again later.", parse_mode=ParseMode.HTML)

# ==================== CALLBACK HANDLERS (Stats, Leaderboard, Back) ====================
async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    stats = await StatsManager.get_player_stats(telegram_id)
    leaderboard = await StatsManager.get_leaderboard(50)
    rank = next((i+1 for i, p in enumerate(leaderboard) if p['telegram_id'] == telegram_id), None)
    msg = (
        f"{get_emoji('stats')} <b>YOUR BINGO STATISTICS</b>\n\n"
        f"{get_emoji('game')} <b>Games:</b>\n• Played: <code>{stats.games_played}</code>\n• Won: <code>{stats.games_won}</code>\n• Win Rate: <code>{stats.win_rate:.1f}%</code>\n\n"
        f"{get_emoji('money')} <b>Financial:</b>\n• Total Bet: <code>{stats.total_bet:.2f} ETB</code>\n• Total Win: <code>{stats.total_win:.2f} ETB</code>\n• Net Profit: <code>{stats.net_profit:+.2f} ETB</code>\n• Best Win: <code>{stats.best_win:.2f} ETB</code>\n\n"
        f"{get_emoji('clock')} <b>Last Played:</b> {stats.last_played.strftime('%Y-%m-%d %H:%M') if stats.last_played else 'Never'}\n\n"
        f"{get_emoji('trophy')} <b>Rank:</b> #{rank or 'Unranked'}"
    )
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{get_emoji('back')} Back to Game", callback_data="back_to_game")
    ]]))

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    leaderboard = await StatsManager.get_leaderboard(10)
    if not leaderboard:
        entries = f"{get_emoji('trophy')} <i>No players yet. Be the first!</i>"
    else:
        lines = []
        for p in leaderboard:
            emoji = '🥇' if p['rank'] == 1 else '🥈' if p['rank'] == 2 else '🥉' if p['rank'] == 3 else f"{p['rank']}️⃣"
            lines.append(f"{emoji} <b>{p['username'][:15]}</b> - {p['total_won']:.0f} ETB won (Win Rate: {p['win_rate']})")
        entries = "\n".join(lines)
    msg = f"{get_emoji('trophy')} <b>BINGO LEADERBOARD</b> {get_emoji('trophy')}\n\n{entries}\n\n{get_emoji('calendar')} <b>Updated:</b> {datetime.now().strftime('%H:%M:%S')}\n{get_emoji('target')} <b>Win to climb the ranks!</b>"
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{get_emoji('refresh')} Refresh", callback_data="game_leaderboard"),
        InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="back_to_game")
    ]]))

async def back_to_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await play_command(update, context)

# ==================== SESSION CLEANUP ====================
async def start_game_handlers():
    await session_manager.start()
    logger.info(f"{get_emoji('game')} Game handlers initialized")

# ==================== EXPORTS ====================
__all__ = [
    'play_command',
    'stats_callback',
    'leaderboard_callback',
    'back_to_game_callback',
    'start_game_handlers',
]