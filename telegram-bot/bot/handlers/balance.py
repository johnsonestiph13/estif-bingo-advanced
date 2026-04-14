# telegram-bot/bot/handlers/balance.py
# Estif Bingo 24/7 - Balance Inquiry Handler with Game Statistics

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu
from bot.texts.emojis import get_emoji
from bot.config import config

logger = logging.getLogger(__name__)


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's current balance and game statistics"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Check if user is registered
    if not user or not user.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} Please register first using /register",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    # Send typing action for better UX
    await update.message.reply_chat_action(action="typing")
    
    try:
        # Get current balance and deposit info
        balance = float(user.get('balance', 0))
        total_deposited = float(user.get('total_deposited', 0))
        total_withdrawn = float(user.get('total_withdrawn', 0))
        total_won = float(user.get('total_won', 0))
        
        # Get game statistics from database
        async with Database._pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(CASE WHEN type = 'bet' THEN 1 END) as games_played,
                    COUNT(CASE WHEN type = 'win' THEN 1 END) as games_won,
                    COALESCE(SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END), 0) as total_bet,
                    COALESCE(SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END), 0) as total_winnings,
                    MAX(CASE WHEN type = 'win' THEN amount ELSE 0 END) as biggest_win,
                    MAX(timestamp) as last_game
                FROM game_transactions
                WHERE telegram_id = $1
            """, telegram_id)
        
        games_played = stats['games_played'] or 0
        games_won = stats['games_won'] or 0
        total_bet = float(stats['total_bet'] or 0)
        total_winnings = float(stats['total_winnings'] or 0)
        biggest_win = float(stats['biggest_win'] or 0)
        last_game = stats['last_game']
        
        # Calculate win rate
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        
        # Calculate net profit/loss
        net_profit = total_winnings - total_bet
        
        # Get current win percentage from settings
        current_win_percentage = await Database.get_win_percentage()
        
        # Format last game time
        last_game_str = "Never"
        if last_game:
            last_game_str = last_game.strftime("%Y-%m-%d %H:%M")
        
        # Build the balance message
        balance_msg = (
            f"{get_emoji('money')} <b>YOUR BALANCE</b> {get_emoji('money')}\n\n"
            f"💰 <b>Current Balance:</b> <code>{balance:.2f} ETB</code>\n\n"
            f"<b>📊 Financial Summary:</b>\n"
            f"• {get_emoji('deposit')} Total Deposited: <code>{total_deposited:.2f} ETB</code>\n"
            f"• {get_emoji('withdraw')} Total Withdrawn: <code>{total_withdrawn:.2f} ETB</code>\n"
            f"• {get_emoji('win')} Total Won: <code>{total_won:.2f} ETB</code>\n\n"
            f"<b>🎮 Game Statistics:</b>\n"
            f"• {get_emoji('game')} Games Played: <code>{games_played}</code>\n"
            f"• {get_emoji('trophy')} Games Won: <code>{games_won}</code>\n"
            f"• {get_emoji('star')} Win Rate: <code>{win_rate:.1f}%</code>\n"
            f"• {get_emoji('money')} Total Bet: <code>{total_bet:.2f} ETB</code>\n"
            f"• {get_emoji('win')} Total Winnings: <code>{total_winnings:.2f} ETB</code>\n"
            f"• {get_emoji('balance')} Net Profit: <code>{net_profit:+.2f} ETB</code>\n"
            f"• {get_emoji('crown')} Biggest Win: <code>{biggest_win:.2f} ETB</code>\n\n"
            f"<b>🎯 Current Game Settings:</b>\n"
            f"• {get_emoji('cartela')} Cartela Price: <code>{config.CARTELA_PRICE} ETB</code>\n"
            f"• {get_emoji('target')} Win Percentage: <code>{current_win_percentage}%</code>\n"
            f"• {get_emoji('stats')} Max Cartelas: <code>{config.MAX_CARTELAS}</code>\n\n"
            f"<b>⏰ Last Game:</b> <code>{last_game_str}</code>\n\n"
            f"{get_emoji('info')} <i>Use /play to start playing!</i>"
        )
        
        # Add warning if balance is low
        if balance < config.MIN_BALANCE_FOR_PLAY:
            balance_msg += f"\n\n{get_emoji('warning')} <b>Low Balance Warning!</b>\n"
            balance_msg += f"Your balance is below the minimum required to play ({config.MIN_BALANCE_FOR_PLAY} ETB).\n"
            balance_msg += f"Use /deposit to add funds."
        
        # Add congratulations if win rate is high
        if win_rate > 70 and games_played > 10:
            balance_msg += f"\n\n{get_emoji('fire')} <b>Amazing Win Rate!</b> You're on fire! 🔥"
        
        await update.message.reply_text(
            balance_msg,
            parse_mode='HTML',
            reply_markup=menu(lang)
        )
        
        logger.info(f"Balance checked for user {telegram_id}: {balance:.2f} ETB")
        
    except Exception as e:
        logger.error(f"Balance error for user {telegram_id}: {e}")
        # Fallback to simple balance display
        await update.message.reply_text(
            TEXTS[lang]['balance'].format(user.get('balance', 0), user.get('total_deposited', 0)),
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )


async def balance_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple balance display (without statistics) - for quick check"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} Please register first using /register",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    balance = float(user.get('balance', 0))
    total_deposited = float(user.get('total_deposited', 0))
    
    await update.message.reply_text(
        f"{get_emoji('money')} <b>Balance</b>\n\n"
        f"💰 Current: <code>{balance:.2f} ETB</code>\n"
        f"📊 Total Deposited: <code>{total_deposited:.2f} ETB</code>\n\n"
        f"Type /balance for full statistics.",
        parse_mode='HTML',
        reply_markup=menu(lang)
    )


# Export all
__all__ = ['balance', 'balance_simple']