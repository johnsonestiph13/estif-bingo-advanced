# bot/handlers/game.py
import json
import asyncio
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from functools import lru_cache
from dataclasses import dataclass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.db.database import Database
from bot.config import config
from bot.texts.emojis import get_emoji
from bot.keyboards.menu import menu

logger = logging.getLogger(__name__)


# ==================== STATISTICS MANAGER ====================
class StatsManager:
    @staticmethod
    @lru_cache(maxsize=1000)
    async def get_player_stats(telegram_id: int):
        """Get player statistics"""
        try:
            async with Database._pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as total_bet,
                        COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END), 0) as total_win,
                        COUNT(CASE WHEN type = 'win' THEN 1 END) as games_won,
                        COUNT(CASE WHEN type = 'bet' THEN 1 END) as games_played
                    FROM game_transactions
                    WHERE telegram_id = $1
                """, telegram_id)
            
            games_played = stats['games_played'] or 0
            games_won = stats['games_won'] or 0
            win_rate = (games_won / games_played * 100) if games_played > 0 else 0
            
            return {
                'total_bet': float(stats['total_bet'] or 0),
                'total_win': float(stats['total_win'] or 0),
                'games_played': games_played,
                'games_won': games_won,
                'win_rate': round(win_rate, 1),
                'net_profit': float(stats['total_win'] or 0) - float(stats['total_bet'] or 0)
            }
        except Exception as e:
            logger.error(f"Stats error for {telegram_id}: {e}")
            return {
                'total_bet': 0, 'total_win': 0,
                'games_played': 0, 'games_won': 0,
                'win_rate': 0, 'net_profit': 0
            }


# ==================== PLAY COMMAND HANDLER ====================
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /play command - Display player status and web app button"""
    user = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name
    
    try:
        # Get user data
        user_data = await Database.get_user(telegram_id)
        
        # Check if user is registered
        if not user_data or not user_data.get('registered'):
            await update.message.reply_text(
                f"{get_emoji('error')} Please register first using /register",
                reply_markup=menu('en'),
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get balance
        balance = await Database.get_balance(telegram_id)
        
        # Check minimum balance
        if balance < config.MIN_BALANCE_FOR_PLAY:
            await update.message.reply_text(
                f"{get_emoji('error')} <b>Insufficient Balance!</b>\n\n"
                f"{get_emoji('money')} Your Balance: <code>{balance:.2f} ETB</code>\n"
                f"{get_emoji('cartela')} Need at least: <code>{config.MIN_BALANCE_FOR_PLAY} ETB</code>\n\n"
                f"{get_emoji('deposit')} Use /deposit to add funds",
                reply_markup=menu(user_data.get('lang', 'en')),
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get win percentage and player stats
        win_percentage = await Database.get_win_percentage()
        stats = await StatsManager.get_player_stats(telegram_id)
        
        # Generate one-time auth code for game server
        auth_code = await Database.create_auth_code(telegram_id)
        
        # Build web app URL with auth code and user ID
        web_app_url = f"{config.GAME_WEB_URL}?code={auth_code}&telegram_id={telegram_id}"
        
        # Create inline keyboard with Play Now button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"{get_emoji('game')} PLAY NOW {get_emoji('game')}",
                web_app=WebAppInfo(url=web_app_url)
            )],
            [
                InlineKeyboardButton(f"{get_emoji('stats')} My Stats", callback_data="game_stats"),
                InlineKeyboardButton(f"{get_emoji('trophy')} Leaderboard", callback_data="game_leaderboard")
            ]
        ])
        
        # Build status message
        status_message = (
            f"{get_emoji('game')} <b>ESTIF BINGO 24/7</b> {get_emoji('game')}\n\n"
            f"{get_emoji('money')} <b>Balance:</b> <code>{balance:.2f} ETB</code>\n"
            f"{get_emoji('cartela')} <b>Cartela Price:</b> <code>{config.CARTELA_PRICE} ETB</code>\n"
            f"{get_emoji('stats')} <b>Max Cartelas:</b> <code>{config.MAX_CARTELAS}</code>\n"
            f"{get_emoji('target')} <b>Win Rate:</b> <code>{win_percentage}%</code>\n"
            f"{get_emoji('star')} <b>Your Win Rate:</b> <code>{stats['win_rate']}%</code>\n"
            f"{get_emoji('trophy')} <b>Games Won:</b> <code>{stats['games_won']}</code>\n"
            f"{get_emoji('game')} <b>Games Played:</b> <code>{stats['games_played']}</code>\n"
            f"{get_emoji('money')} <b>Net Profit:</b> <code>{stats['net_profit']:+.2f} ETB</code>\n\n"
            f"{get_emoji('click')} <b>Click the button below to start playing!</b>"
        )
        
        await update.message.reply_text(
            status_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"Play command executed for user {telegram_id}")
        
    except Exception as e:
        logger.error(f"Play command error for {telegram_id}: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} An error occurred. Please try again later.",
            parse_mode=ParseMode.HTML
        )


# ==================== STATS CALLBACK ====================
async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stats button callback"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    stats = await StatsManager.get_player_stats(telegram_id)
    
    stats_message = (
        f"{get_emoji('stats')} <b>YOUR BINGO STATISTICS</b>\n\n"
        f"{get_emoji('game')} <b>Games Played:</b> <code>{stats['games_played']}</code>\n"
        f"{get_emoji('trophy')} <b>Games Won:</b> <code>{stats['games_won']}</code>\n"
        f"{get_emoji('star')} <b>Win Rate:</b> <code>{stats['win_rate']}%</code>\n\n"
        f"{get_emoji('money')} <b>Total Bet:</b> <code>{stats['total_bet']:.2f} ETB</code>\n"
        f"{get_emoji('win')} <b>Total Won:</b> <code>{stats['total_win']:.2f} ETB</code>\n"
        f"{get_emoji('balance')} <b>Net Profit:</b> <code>{stats['net_profit']:+.2f} ETB</code>"
    )
    
    await query.edit_message_text(
        stats_message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{get_emoji('back')} Back to Game", callback_data="back_to_game")
        ]])
    )


# ==================== LEADERBOARD CALLBACK ====================
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard button callback"""
    query = update.callback_query
    await query.answer()
    
    try:
        async with Database._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT username, total_won, games_won, games_played
                FROM users 
                WHERE registered = TRUE AND total_won > 0
                ORDER BY total_won DESC
                LIMIT 10
            """)
        
        if not rows:
            entries = f"{get_emoji('trophy')} <i>No players yet. Be the first!</i>"
        else:
            entries_list = []
            for i, row in enumerate(rows, 1):
                win_rate = (row['games_won'] / row['games_played'] * 100) if row['games_played'] > 0 else 0
                medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f"{i}️⃣"
                entries_list.append(
                    f"{medal} <b>{row['username'] or f'Player_{i}'}</b> - {float(row['total_won']):.0f} ETB won (Win Rate: {win_rate:.0f}%)"
                )
            entries = "\n".join(entries_list)
        
        await query.edit_message_text(
            f"{get_emoji('trophy')} <b>BINGO LEADERBOARD</b> {get_emoji('trophy')}\n\n{entries}\n\n{get_emoji('calendar')} Updated: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{get_emoji('refresh')} Refresh", callback_data="game_leaderboard"),
                InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="back_to_game")
            ]])
        )
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} Failed to load leaderboard.",
            parse_mode=ParseMode.HTML
        )


# ==================== BACK TO GAME CALLBACK ====================
async def back_to_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to game button"""
    query = update.callback_query
    await query.answer()
    await play_command(update, context)


# ==================== GAME CALLBACK (Web App Data) ====================
async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data from web app game"""
    try:
        data = update.effective_message.web_app_data
        if not data:
            return
        
        game_data = json.loads(data.data)
        action = game_data.get('action')
        telegram_id = update.effective_user.id
        
        if action == 'game_result':
            won = game_data.get('won', False)
            amount = float(game_data.get('amount', 0))
            
            if won and amount > 0:
                await update.message.reply_text(
                    f"{get_emoji('win')} <b>Congratulations!</b> You won <code>{amount:.2f} ETB</code>!\n\nUse /balance to check your balance.",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"{get_emoji('lose')} <b>Better luck next time!</b>\n\nUse /deposit to add more funds.",
                    parse_mode=ParseMode.HTML
                )
    except Exception as e:
        logger.error(f"Game callback error: {e}")


# ==================== SESSION CLEANUP ====================
async def start_game_handlers():
    """Start background tasks for game handlers"""
    logger.info(f"{get_emoji('game')} Game handlers initialized")


# Export all
__all__ = [
    'play_command',
    'game_callback',
    'stats_callback',
    'leaderboard_callback',
    'back_to_game_callback',
    'start_game_handlers'
]