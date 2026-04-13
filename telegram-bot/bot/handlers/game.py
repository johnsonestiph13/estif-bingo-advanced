# bot/handlers/game.py - ULTRA OPTIMIZED GAME HANDLER
# Estif Bingo 24/7 - High-Performance Web App Game Integration

import json
import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
from collections import defaultdict
import logging
from dataclasses import dataclass, asdict

from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, 
    WebAppInfo, Update, User
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.db.database import database
from bot.config import Config

# ==================== OPTIMIZED LOGGING ====================
logger = logging.getLogger(__name__)

# ==================== CACHE MANAGEMENT ====================
class GameCache:
    """Ultra-fast in-memory cache for game data"""
    
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value with TTL check"""
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
        """Set cached value"""
        self._cache[key] = (value, time.time())
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            'size': len(self._cache),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }

# Global cache instance
game_cache = GameCache(ttl_seconds=120)

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
    
    def to_dict(self) -> Dict:
        return asdict(self)

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

# ==================== MESSAGE TEMPLATES ====================
class GameMessages:
    """Optimized message templates with emojis"""
    
    WELCOME = """
🎲 <b>ESTIF BINGO 24/7</b> 🎲

💰 <b>Balance:</b> <code>{balance:.2f} ETB</code>
🎫 <b>Cartela Price:</b> <code>{cartela_price} ETB</code>
📊 <b>Max Cartelas:</b> <code>{max_cartelas}</code>
🎯 <b>Win Rate:</b> <code>{win_percentage}%</code>
👥 <b>Active Players:</b> <code>{active_players}</code>

🎮 <b>How to Play:</b>
• Select 1-4 cartelas per round
• Numbers are drawn automatically
• Match patterns to win!
• Win up to {win_percentage}% of pool!

👇 <b>Click the button below to start!</b>
"""
    
    INSUFFICIENT_BALANCE = """
❌ <b>Insufficient Balance!</b>

💰 Your Balance: <code>{balance:.2f} ETB</code>
🎫 Need at least: <code>{min_needed} ETB</code>

💳 <b>Add funds via /deposit</b>
🎁 Get <b>bonus</b> on first deposit!
"""
    
    GAME_START = """
🎮 <b>Game Started!</b>

📊 <b>Session Details:</b>
• Cartelas: <code>{cartelas}</code>
• Cost: <code>{cost:.2f} ETB</code>
• New Balance: <code>{new_balance:.2f} ETB</code>

🎯 <b>Win Chance:</b> <code>{win_percentage}%</code>
⏱️ <b>Round Duration:</b> <code>{round_duration}s</code>

🍀 <b>Good luck! May the numbers be with you!</b>
"""
    
    GAME_WIN = """
🎉 <b>CONGRATULATIONS! YOU WON!</b> 🎉

💰 <b>Winnings:</b> <code>+{amount:.2f} ETB</code>
📊 <b>New Balance:</b> <code>{new_balance:.2f} ETB</code>
🏆 <b>Total Wins:</b> <code>{total_wins}</code>
⭐ <b>Win Rate:</b> <code>{win_rate:.1f}%</code>

🎯 <b>Pattern:</b> {pattern}
🎫 <b>Cartela:</b> {cartela_id}

🔄 <b>Play again?</b> Use /play
"""
    
    GAME_LOSS = """
😢 <b>Better Luck Next Time!</b>

📊 <b>Round Stats:</b>
• Numbers Drawn: <code>{numbers_drawn}</code>
• Closest Pattern: <code>{closest_pattern}</code>

💰 <b>Current Balance:</b> <code>{balance:.2f} ETB</code>
🎯 <b>Win Rate:</b> <code>{win_rate:.1f}%</code>

💪 <b>Don't give up!</b> Your win is coming!
🔄 <b>Play again:</b> /play
"""
    
    STATS = """
📊 <b>YOUR BINGO STATISTICS</b>

🎮 <b>Games:</b>
• Played: <code>{games_played}</code>
• Won: <code>{games_won}</code>
• Win Rate: <code>{win_rate:.1f}%</code>

💰 <b>Financial:</b>
• Total Bet: <code>{total_bet:.2f} ETB</code>
• Total Win: <code>{total_win:.2f} ETB</code>
• Net Profit: <code>{net_profit:+.2f} ETB</code>
• Best Win: <code>{best_win:.2f} ETB</code>

⏰ <b>Last Played:</b> {last_played}

🏆 <b>Rank:</b> #{rank}
"""
    
    LEADERBOARD = """
🏆 <b>BINGO LEADERBOARD</b> 🏆

{entries}

📅 <b>Updated:</b> {timestamp}
🎯 <b>Win to climb the ranks!</b>
"""
    
    QUICK_PLAY = """
⚡ <b>QUICK PLAY</b> ⚡

💰 <b>Balance:</b> {balance:.2f} ETB

<b>Choose cartelas:</b>
• 1 Cartela: {price1} ETB
• 2 Cartelas: {price2} ETB
• 3 Cartelas: {price3} ETB
• 4 Cartelas: {price4} ETB

🎯 <b>Auto-play available!</b> Set and forget!
"""

# ==================== GAME SESSION MANAGER ====================
class GameSessionManager:
    """Manages active game sessions with auto-cleanup"""
    
    def __init__(self, cleanup_interval: int = 60):
        self._sessions: Dict[int, GameSession] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start session cleanup daemon"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Periodically clean expired sessions"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.cleanup_expired()
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    async def cleanup_expired(self):
        """Remove expired sessions"""
        async with self._lock:
            expired = [
                tid for tid, session in self._sessions.items()
                if session.is_expired()
            ]
            for tid in expired:
                del self._sessions[tid]
            if expired:
                logger.debug(f"Cleaned {len(expired)} expired sessions")
    
    async def create_session(self, telegram_id: int, username: str, 
                             balance: float, auth_code: str) -> GameSession:
        """Create new game session"""
        async with self._lock:
            session = GameSession(
                telegram_id=telegram_id,
                username=username,
                balance=balance,
                auth_code=auth_code,
                created_at=time.time(),
                expires_at=time.time() + 300  # 5 minutes
            )
            self._sessions[telegram_id] = session
            return session
    
    async def get_session(self, telegram_id: int) -> Optional[GameSession]:
        """Get active session"""
        async with self._lock:
            session = self._sessions.get(telegram_id)
            if session and session.is_expired():
                del self._sessions[telegram_id]
                return None
            return session
    
    async def update_session(self, telegram_id: int, **kwargs):
        """Update session data"""
        async with self._lock:
            session = self._sessions.get(telegram_id)
            if session:
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
    
    async def end_session(self, telegram_id: int):
        """End and remove session"""
        async with self._lock:
            if telegram_id in self._sessions:
                del self._sessions[telegram_id]
    
    def get_active_count(self) -> int:
        """Get number of active sessions"""
        return len(self._sessions)

# Global session manager
session_manager = GameSessionManager()

# ==================== STATISTICS MANAGER ====================
class StatsManager:
    """Manages player statistics with caching"""
    
    @staticmethod
    @lru_cache(maxsize=1000)
    async def get_player_stats(telegram_id: int) -> GameStats:
        """Get cached player statistics"""
        try:
            # Get from database
            user = await database.get_user(telegram_id)
            if not user:
                return GameStats()
            
            # Get transaction stats
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
            logger.error(f"Stats error for {telegram_id}: {e}")
            return GameStats()
    
    @staticmethod
    async def get_leaderboard(limit: int = 10) -> list:
        """Get top players leaderboard"""
        cache_key = f"leaderboard_{limit}"
        cached = game_cache.get(cache_key)
        if cached:
            return cached
        
        try:
            async with database._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        telegram_id,
                        username,
                        total_won,
                        games_played,
                        games_won,
                        balance
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
        """Get count of active players (last 24h)"""
        cache_key = "active_players_count"
        cached = game_cache.get(cache_key)
        if cached:
            return cached
        
        try:
            async with database._pool.acquire() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(DISTINCT telegram_id)
                    FROM game_transactions
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                """)
            game_cache.set(cache_key, count or 0)
            return count or 0
        except Exception as e:
            logger.error(f"Active players count error: {e}")
            return 0

# ==================== MAIN HANDLER ====================
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ultra-optimized /play command handler"""
    user: User = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name
    
    start_time = time.time()
    
    try:
        # Parallel data fetching
        user_data_task = database.get_user(telegram_id)
        balance_task = database.get_balance(telegram_id)
        win_percentage_task = database.get_win_percentage()
        active_players_task = StatsManager.get_active_players_count()
        
        user_data, balance, win_percentage, active_players = await asyncio.gather(
            user_data_task, balance_task, win_percentage_task, active_players_task
        )
        
        # Validate user
        if not user_data or not user_data.get('registered'):
            await update.message.reply_text(
                "❌ Please register first using /register",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Check balance
        min_needed = Config.MIN_BALANCE_FOR_PLAY
        if balance < min_needed:
            await update.message.reply_text(
                GameMessages.INSUFFICIENT_BALANCE.format(
                    balance=balance,
                    min_needed=min_needed
                ),
                parse_mode=ParseMode.HTML
            )
            return
        
        # Generate auth code
        auth_code = await database.create_auth_code(telegram_id)
        
        # Create game session
        await session_manager.create_session(telegram_id, username, balance, auth_code)
        
        # Build web app URL
        web_app_url = f"{Config.GAME_WEB_URL}?code={auth_code}&telegram_id={telegram_id}&v={int(time.time())}"
        
        # Create quick play buttons
        keyboard = [
            [InlineKeyboardButton(
                "🎮 PLAY BINGO NOW 🎮", 
                web_app=WebAppInfo(url=web_app_url)
            )],
            [
                InlineKeyboardButton("⚡ 1 Cartela", callback_data="quick_play_1"),
                InlineKeyboardButton("⚡ 2 Cartelas", callback_data="quick_play_2"),
                InlineKeyboardButton("⚡ 3 Cartelas", callback_data="quick_play_3"),
                InlineKeyboardButton("⚡ 4 Cartelas", callback_data="quick_play_4")
            ],
            [
                InlineKeyboardButton("📊 My Stats", callback_data="game_stats"),
                InlineKeyboardButton("🏆 Leaderboard", callback_data="game_leaderboard")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send welcome message
        response_time = (time.time() - start_time) * 1000
        logger.info(f"Play command for {telegram_id} in {response_time:.2f}ms")
        
        await update.message.reply_text(
            GameMessages.WELCOME.format(
                balance=balance,
                cartela_price=Config.CARTELA_PRICE,
                max_cartelas=Config.MAX_CARTELAS,
                win_percentage=win_percentage,
                active_players=active_players
            ),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Play command error for {telegram_id}: {e}")
        await update.message.reply_text(
            "⚠️ An error occurred. Please try again later.",
            parse_mode=ParseMode.HTML
        )

# ==================== GAME CALLBACK HANDLER ====================
async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle web app game data with ultra-fast processing"""
    user: User = update.effective_user
    telegram_id = user.id
    
    try:
        data = update.effective_message.web_app_data
        if not data:
            return
        
        game_data = json.loads(data.data)
        action = game_data.get('action')
        
        # Route to appropriate handler
        if action == 'game_start':
            await handle_game_start(update, game_data, telegram_id)
        elif action == 'game_result':
            await handle_game_result(update, game_data, telegram_id)
        elif action == 'game_end':
            await handle_game_end(update, telegram_id)
        elif action == 'game_error':
            await handle_game_error(update, game_data, telegram_id)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
    except Exception as e:
        logger.error(f"Game callback error for {telegram_id}: {e}")

# ==================== ACTION HANDLERS ====================
async def handle_game_start(update: Update, game_data: Dict, telegram_id: int):
    """Handle game start event"""
    cartelas = game_data.get('cartelas', 1)
    cost = cartelas * Config.CARTELA_PRICE
    
    # Get current balance
    balance = await database.get_balance(telegram_id)
    win_percentage = await database.get_win_percentage()
    
    # Update session
    await session_manager.update_session(
        telegram_id,
        cartelas_purchased=cartelas,
        total_spent=cost
    )
    
    await update.message.reply_text(
        GameMessages.GAME_START.format(
            cartelas=cartelas,
            cost=cost,
            new_balance=balance - cost,
            win_percentage=win_percentage,
            round_duration=Config.SELECTION_TIME
        ),
        parse_mode=ParseMode.HTML
    )

async def handle_game_result(update: Update, game_data: Dict, telegram_id: int):
    """Handle game result with statistics update"""
    won = game_data.get('won', False)
    amount = float(game_data.get('amount', 0))
    pattern = game_data.get('pattern', 'Unknown')
    cartela_id = game_data.get('cartela_id', 'N/A')
    numbers_drawn = game_data.get('numbers_drawn', 0)
    closest_pattern = game_data.get('closest_pattern', 'None')
    
    # Get fresh balance
    new_balance = await database.get_balance(telegram_id)
    stats = await StatsManager.get_player_stats(telegram_id)
    
    if won and amount > 0:
        # Update session
        await session_manager.update_session(
            telegram_id,
            total_won=amount
        )
        
        # Clear leaderboard cache
        game_cache.clear()
        
        await update.message.reply_text(
            GameMessages.GAME_WIN.format(
                amount=amount,
                new_balance=new_balance,
                total_wins=stats.games_won + 1,
                win_rate=stats.win_rate,
                pattern=pattern,
                cartela_id=cartela_id
            ),
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            GameMessages.GAME_LOSS.format(
                numbers_drawn=numbers_drawn,
                closest_pattern=closest_pattern,
                balance=new_balance,
                win_rate=stats.win_rate
            ),
            parse_mode=ParseMode.HTML
        )

async def handle_game_end(update: Update, telegram_id: int):
    """Handle game end event"""
    session = await session_manager.get_session(telegram_id)
    if session:
        net_result = session.total_won - session.total_spent
        await update.message.reply_text(
            f"📊 <b>Session Summary</b>\n\n"
            f"• Cartelas: {session.cartelas_purchased}\n"
            f"• Spent: {session.total_spent:.2f} ETB\n"
            f"• Won: {session.total_won:.2f} ETB\n"
            f"• Net: <code>{net_result:+.2f} ETB</code>\n\n"
            f"🔄 Play again with /play",
            parse_mode=ParseMode.HTML
        )
        await session_manager.end_session(telegram_id)

async def handle_game_error(update: Update, game_data: Dict, telegram_id: int):
    """Handle game errors gracefully"""
    error_msg = game_data.get('error', 'Unknown error')
    logger.error(f"Game error for {telegram_id}: {error_msg}")
    await update.message.reply_text(
        f"⚠️ <b>Game Error</b>\n\n{error_msg}\n\nPlease try again with /play",
        parse_mode=ParseMode.HTML
    )

# ==================== QUICK PLAY HANDLERS ====================
async def quick_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick play button callbacks"""
    query = update.callback_query
    await query.answer()
    
    cartelas = int(query.data.split('_')[-1])
    telegram_id = query.from_user.id
    
    # Generate auth code and launch game
    auth_code = await database.create_auth_code(telegram_id)
    web_app_url = f"{Config.GAME_WEB_URL}?code={auth_code}&telegram_id={telegram_id}&cartelas={cartelas}&quick=true"
    
    keyboard = [[
        InlineKeyboardButton(
            f"🎮 PLAY {cartelas} CARTELA{'S' if cartelas > 1 else ''} 🎮",
            web_app=WebAppInfo(url=web_app_url)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"⚡ <b>Quick Play - {cartelas} Cartela{'s' if cartelas > 1 else ''}</b>\n\n"
        f"💰 Cost: {cartelas * Config.CARTELA_PRICE} ETB\n"
        f"🎯 Win Chance: {await database.get_win_percentage()}%\n\n"
        f"Click below to start!",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stats button callback"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    stats = await StatsManager.get_player_stats(telegram_id)
    leaderboard = await StatsManager.get_leaderboard(50)
    
    # Find rank
    rank = next((i + 1 for i, p in enumerate(leaderboard) if p['telegram_id'] == telegram_id), None)
    
    await query.edit_message_text(
        GameMessages.STATS.format(
            games_played=stats.games_played,
            games_won=stats.games_won,
            win_rate=stats.win_rate,
            total_bet=stats.total_bet,
            total_win=stats.total_win,
            net_profit=stats.net_profit,
            best_win=stats.best_win,
            last_played=stats.last_played.strftime("%Y-%m-%d %H:%M") if stats.last_played else "Never",
            rank=rank or "Unranked"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Game", callback_data="back_to_game")
        ]])
    )

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard button callback"""
    query = update.callback_query
    await query.answer()
    
    leaderboard = await StatsManager.get_leaderboard(10)
    
    if not leaderboard:
        entries = "🏆 <i>No players yet. Be the first!</i>"
    else:
        entries = "\n".join([
            f"{'🥇' if p['rank'] == 1 else '🥈' if p['rank'] == 2 else '🥉' if p['rank'] == 3 else f'{p["rank"]}️⃣'} "
            f"<b>{p['username'][:15]}</b> - {p['total_won']:.0f} ETB won (Win Rate: {p['win_rate']})"
            for p in leaderboard
        ])
    
    await query.edit_message_text(
        GameMessages.LEADERBOARD.format(
            entries=entries,
            timestamp=datetime.now().strftime("%H:%M:%S")
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh", callback_data="game_leaderboard"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_game")
        ]])
    )

async def back_to_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to game button"""
    query = update.callback_query
    await query.answer()
    
    await play_command(update, context)

# ==================== SESSION CLEANUP ====================
async def start_game_handlers():
    """Start background tasks for game handlers"""
    await session_manager.start()
    logger.info("🎮 Game handlers initialized")

# Export handlers
__all__ = [
    'play_command',
    'game_callback',
    'quick_play_callback',
    'stats_callback',
    'leaderboard_callback',
    'back_to_game_callback',
    'start_game_handlers'
]