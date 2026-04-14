# telegram-bot/bot/handlers/admin_commands.py
# Estif Bingo 24/7 - Complete Admin Commands Handler (UPDATED)

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from telegram.constants import ParseMode

from bot.db.database import Database
from bot.config import config
from bot.utils import logger, log_user_action
from bot.keyboards.menu import admin_keyboard, back_button
from bot.texts.emojis import get_emoji
from bot.texts.locales import TEXTS

logger = logging.getLogger(__name__)

# ==================== ADMIN VALIDATION ====================

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return str(user_id) == str(config.ADMIN_CHAT_ID)


# ==================== MAIN ADMIN COMMAND ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - Show admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(
            f"{get_emoji('error')} You are not authorized to use this command.",
            parse_mode=ParseMode.HTML
        )
        return
    
    keyboard = admin_keyboard()
    
    # Get statistics for dashboard
    total_users = await Database.get_total_users_count()
    pending_withdrawals = await Database.get_pending_withdrawals()
    win_percentage = await Database.get_win_percentage()
    
    welcome_msg = (
        f"{get_emoji('settings')} <b>ADMIN PANEL</b> {get_emoji('settings')}\n\n"
        f"{get_emoji('stats')} <b>Statistics:</b>\n"
        f"• Total Users: <code>{total_users}</code>\n"
        f"• Pending Withdrawals: <code>{len(pending_withdrawals)}</code>\n"
        f"• Current Win %: <code>{win_percentage}%</code>\n\n"
        f"{get_emoji('info')} Select an option below:"
    )
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(
            f"{get_emoji('error')} Unauthorized access.",
            parse_mode=ParseMode.HTML
        )
        return
    
    action = query.data
    
    if action == "admin_dashboard":
        await show_dashboard(query, context)
    elif action == "admin_users":
        await show_users_panel(query, context)
    elif action == "admin_deposits":
        await show_pending_deposits(query, context)
    elif action == "admin_withdrawals":
        await show_pending_withdrawals(query, context)
    elif action == "admin_reports":
        await show_reports_panel(query, context)
    elif action == "admin_settings":
        await show_settings_panel(query, context)
    elif action == "admin_back":
        await admin_panel(update, context)


async def show_dashboard(query, context: ContextTypes.DEFAULT_TYPE):
    """Show admin dashboard"""
    total_users = await Database.get_total_users_count()
    active_today = await get_active_users_today()
    total_deposits = await Database.get_total_deposits()
    total_withdrawals = await get_total_withdrawals()
    pending_withdrawals = await Database.get_pending_withdrawals()
    win_percentage = await Database.get_win_percentage()
    
    dashboard_msg = (
        f"{get_emoji('stats')} <b>DASHBOARD</b> {get_emoji('stats')}\n\n"
        f"<b>📊 User Statistics:</b>\n"
        f"• Total Registered: <code>{total_users}</code>\n"
        f"• Active Today: <code>{active_today}</code>\n\n"
        f"<b>💰 Financial:</b>\n"
        f"• Total Deposits: <code>{total_deposits:.2f} ETB</code>\n"
        f"• Total Withdrawals: <code>{total_withdrawals:.2f} ETB</code>\n"
        f"• Pending Withdrawals: <code>{len(pending_withdrawals)}</code>\n\n"
        f"<b>🎮 Game Settings:</b>\n"
        f"• Win Percentage: <code>{win_percentage}%</code>\n"
        f"• Cartela Price: <code>{config.CARTELA_PRICE} ETB</code>\n"
        f"• Max Cartelas: <code>{config.MAX_CARTELAS}</code>\n\n"
        f"<i>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{get_emoji('refresh')} Refresh", callback_data="admin_dashboard"),
        InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="admin_back")
    ]])
    
    await query.edit_message_text(
        dashboard_msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_users_panel(query, context: ContextTypes.DEFAULT_TYPE):
    """Show users management panel"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('search')} Search Users", callback_data="admin_search_users")],
        [InlineKeyboardButton(f"{get_emoji('trophy')} Top Players", callback_data="admin_top_players")],
        [InlineKeyboardButton(f"{get_emoji('stats')} User Stats", callback_data="admin_user_stats")],
        [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="admin_back")]
    ])
    
    await query.edit_message_text(
        f"{get_emoji('users')} <b>USER MANAGEMENT</b>\n\n"
        f"Select an option to manage users:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_pending_deposits(query, context: ContextTypes.DEFAULT_TYPE):
    """Show pending deposits"""
    await query.edit_message_text(
        f"{get_emoji('pending')} <b>PENDING DEPOSITS</b>\n\n"
        f"Deposit approval is handled via /approve_deposit command.\n\n"
        f"Usage: <code>/approve_deposit USER_ID AMOUNT</code>\n"
        f"Example: <code>/approve_deposit 123456789 100</code>\n\n"
        f"{get_emoji('info')} To reject: <code>/reject_deposit USER_ID [reason]</code>\n\n"
        f"{get_emoji('back')} Use /admin to return.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="admin_back")
        ]])
    )


async def show_pending_withdrawals(query, context: ContextTypes.DEFAULT_TYPE):
    """Show pending withdrawals"""
    pending = await Database.get_pending_withdrawals()
    
    if not pending:
        msg = f"{get_emoji('success')} <b>No pending withdrawals!</b>\n\nAll withdrawal requests have been processed."
    else:
        msg = f"{get_emoji('pending')} <b>PENDING WITHDRAWALS ({len(pending)})</b>\n\n"
        for w in pending[:10]:
            amount = float(w['amount']) if w['amount'] else 0
            requested_at = w['requested_at']
            if isinstance(requested_at, datetime):
                requested_str = requested_at.strftime('%Y-%m-%d %H:%M')
            else:
                requested_str = str(requested_at)
            
            msg += (
                f"• ID: <code>{w['id']}</code> | User: <code>{w['telegram_id']}</code>\n"
                f"  Amount: <code>{amount:.2f} ETB</code> | Method: {w['method']}\n"
                f"  Requested: {requested_str}\n\n"
            )
        
        if len(pending) > 10:
            msg += f"\n<i>... and {len(pending) - 10} more</i>"
    
    msg += f"\n{get_emoji('info')} To approve: <code>/approve_cashout WITHDRAWAL_ID</code>\n"
    msg += f"To reject: <code>/reject_cashout WITHDRAWAL_ID [reason]</code>"
    
    await query.edit_message_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{get_emoji('refresh')} Refresh", callback_data="admin_withdrawals"),
            InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="admin_back")
        ]])
    )


async def show_reports_panel(query, context: ContextTypes.DEFAULT_TYPE):
    """Show reports panel"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('calendar')} Today", callback_data="report_today")],
        [InlineKeyboardButton(f"{get_emoji('calendar')} This Week", callback_data="report_week")],
        [InlineKeyboardButton(f"{get_emoji('calendar')} This Month", callback_data="report_month")],
        [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="admin_back")]
    ])
    
    await query.edit_message_text(
        f"{get_emoji('stats')} <b>REPORTS</b>\n\n"
        f"Select a time period to generate report:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_settings_panel(query, context: ContextTypes.DEFAULT_TYPE):
    """Show settings panel"""
    current_win = await Database.get_win_percentage()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('target')} Set Win % (70)", callback_data="set_win_70")],
        [InlineKeyboardButton(f"{get_emoji('target')} Set Win % (75)", callback_data="set_win_75")],
        [InlineKeyboardButton(f"{get_emoji('target')} Set Win % (76)", callback_data="set_win_76")],
        [InlineKeyboardButton(f"{get_emoji('target')} Set Win % (80)", callback_data="set_win_80")],
        [InlineKeyboardButton(f"{get_emoji('refresh')} Refresh Stats", callback_data="admin_dashboard")],
        [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="admin_back")]
    ])
    
    await query.edit_message_text(
        f"{get_emoji('settings')} <b>GAME SETTINGS</b>\n\n"
        f"Current Win Percentage: <code>{current_win}%</code>\n\n"
        f"Select a new win percentage:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


# ==================== WIN PERCENTAGE COMMANDS ====================

async def set_win_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setwin command - Set win percentage"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(f"{get_emoji('error')} Admin only command.", parse_mode=ParseMode.HTML)
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            f"{get_emoji('info')} <b>Set Win Percentage</b>\n\n"
            f"Usage: <code>/setwin PERCENTAGE</code>\n"
            f"Available: 70, 75, 76, 80\n\n"
            f"Example: <code>/setwin 75</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        percentage = int(context.args[0])
        
        if percentage not in config.WIN_PERCENTAGES:
            await update.message.reply_text(
                f"{get_emoji('error')} Invalid percentage. Available: {', '.join(map(str, config.WIN_PERCENTAGES))}",
                parse_mode=ParseMode.HTML
            )
            return
        
        old_percentage = await Database.get_win_percentage()
        await Database.set_win_percentage(percentage)
        
        await update.message.reply_text(
            f"{get_emoji('success')} <b>Win Percentage Updated!</b>\n\n"
            f"Changed from <code>{old_percentage}%</code> → <code>{percentage}%</code>\n\n"
            f"New games will use {percentage}% win rate.",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"Win percentage changed by admin {user_id}: {old_percentage}% → {percentage}%")
        
    except ValueError:
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid percentage format. Use a number.",
            parse_mode=ParseMode.HTML
        )


# ==================== STATS COMMAND ====================

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - Show bot statistics"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(f"{get_emoji('error')} Admin only command.", parse_mode=ParseMode.HTML)
        return
    
    total_users = await Database.get_total_users_count()
    active_today = await get_active_users_today()
    total_deposits = await Database.get_total_deposits()
    total_withdrawals = await get_total_withdrawals()
    pending_withdrawals = await Database.get_pending_withdrawals()
    win_percentage = await Database.get_win_percentage()
    
    stats_msg = (
        f"{get_emoji('stats')} <b>BOT STATISTICS</b> {get_emoji('stats')}\n\n"
        f"<b>👥 Users:</b>\n"
        f"• Total Registered: <code>{total_users}</code>\n"
        f"• Active Today: <code>{active_today}</code>\n\n"
        f"<b>💰 Financial:</b>\n"
        f"• Total Deposits: <code>{total_deposits:.2f} ETB</code>\n"
        f"• Total Withdrawals: <code>{total_withdrawals:.2f} ETB</code>\n"
        f"• Pending Withdrawals: <code>{len(pending_withdrawals)}</code>\n\n"
        f"<b>🎮 Game:</b>\n"
        f"• Win Percentage: <code>{win_percentage}%</code>\n"
        f"• Cartela Price: <code>{config.CARTELA_PRICE} ETB</code>\n"
        f"• Max Cartelas: <code>{config.MAX_CARTELAS}</code>\n\n"
        f"<b>⏰ Server Time:</b>\n"
        f"• {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await update.message.reply_text(stats_msg, parse_mode=ParseMode.HTML)


# ==================== DEPOSIT COMMANDS ====================

async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to approve deposit"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(f"{get_emoji('error')} Admin only command", parse_mode=ParseMode.HTML)
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{get_emoji('info')} <b>Approve Deposit</b>\n\n"
            f"Usage: <code>/approve_deposit USER_ID AMOUNT</code>\n"
            f"Example: <code>/approve_deposit 123456789 100</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        telegram_id = int(context.args[0])
        amount = float(context.args[1])
        
        user_before = await Database.get_user(telegram_id)
        if not user_before:
            await update.message.reply_text(f"{get_emoji('error')} User {telegram_id} not found", parse_mode=ParseMode.HTML)
            return
        
        old_balance = float(user_before.get("balance", 0))
        
        await Database.add_balance(telegram_id, amount, "deposit_approval")
        
        user_after = await Database.get_user(telegram_id)
        new_balance = float(user_after.get("balance", 0))
        
        lang = user_before.get('lang', 'en')
        
        await context.bot.send_message(
            chat_id=telegram_id,
            text=TEXTS[lang]['approved_deposit'].format(amount, new_balance),
            parse_mode=ParseMode.HTML
        )
        
        await update.message.reply_text(
            f"{get_emoji('success')} Deposit approved for user {telegram_id}\n"
            f"💰 Amount: {amount} ETB\n"
            f"📊 Balance: {old_balance:.2f} → {new_balance:.2f} ETB",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"Deposit approved: {telegram_id} - {amount} ETB")
        
    except ValueError:
        await update.message.reply_text(f"{get_emoji('error')} Invalid USER_ID or AMOUNT format", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"{get_emoji('error')} Error: {str(e)}", parse_mode=ParseMode.HTML)


async def reject_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reject deposit"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(f"{get_emoji('error')} Admin only command", parse_mode=ParseMode.HTML)
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            f"{get_emoji('info')} <b>Reject Deposit</b>\n\n"
            f"Usage: <code>/reject_deposit USER_ID [reason]</code>\n"
            f"Example: <code>/reject_deposit 123456789 Invalid screenshot</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        telegram_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Not specified"
        
        user = await Database.get_user(telegram_id)
        if user:
            lang = user.get('lang', 'en')
            await context.bot.send_message(
                chat_id=telegram_id,
                text=TEXTS[lang]['rejected'].format(reason),
                parse_mode=ParseMode.HTML
            )
        
        await update.message.reply_text(
            f"{get_emoji('success')} Deposit rejected for user {telegram_id}\nReason: {reason}",
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Deposit rejected: {telegram_id} - Reason: {reason}")
        
    except ValueError:
        await update.message.reply_text(f"{get_emoji('error')} Invalid USER_ID format", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"{get_emoji('error')} Error: {str(e)}", parse_mode=ParseMode.HTML)


# ==================== CASHOUT COMMANDS ====================

async def approve_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to approve cashout"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(f"{get_emoji('error')} Admin only command", parse_mode=ParseMode.HTML)
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            f"{get_emoji('info')} <b>Approve Cashout</b>\n\n"
            f"Usage: <code>/approve_cashout WITHDRAWAL_ID</code>\n"
            f"Example: <code>/approve_cashout 12345</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        withdrawal_id = int(context.args[0])
        
        withdrawal = await Database.get_withdrawal_by_id(withdrawal_id)
        if not withdrawal:
            await update.message.reply_text(f"{get_emoji('error')} Withdrawal not found", parse_mode=ParseMode.HTML)
            return
        
        if withdrawal.get("status") != "pending":
            await update.message.reply_text(
                f"{get_emoji('error')} Withdrawal already {withdrawal.get('status')}",
                parse_mode=ParseMode.HTML
            )
            return
        
        telegram_id = withdrawal["telegram_id"]
        amount = float(withdrawal["amount"])
        
        user_before = await Database.get_user(telegram_id)
        if not user_before:
            await update.message.reply_text(f"{get_emoji('error')} User {telegram_id} not found", parse_mode=ParseMode.HTML)
            return
        
        old_balance = float(user_before.get("balance", 0))
        
        if old_balance < amount:
            await update.message.reply_text(
                f"{get_emoji('error')} Insufficient balance! User has {old_balance:.2f} ETB, requested {amount:.2f} ETB",
                parse_mode=ParseMode.HTML
            )
            return
        
        result = await Database.approve_withdrawal(withdrawal_id)
        
        if not result:
            await update.message.reply_text(f"{get_emoji('error')} Failed to approve withdrawal", parse_mode=ParseMode.HTML)
            return
        
        user_after = await Database.get_user(telegram_id)
        new_balance = float(user_after.get("balance", 0))
        
        lang = user_before.get('lang', 'en')
        
        await context.bot.send_message(
            chat_id=telegram_id,
            text=TEXTS[lang]['approved_cashout'].format(amount, new_balance),
            parse_mode=ParseMode.HTML
        )
        
        await update.message.reply_text(
            f"{get_emoji('success')} Cashout approved for withdrawal #{withdrawal_id}\n"
            f"👤 User: {telegram_id}\n"
            f"💰 Amount: {amount:.2f} ETB\n"
            f"📊 Balance: {old_balance:.2f} → {new_balance:.2f} ETB",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"Cashout approved: withdrawal #{withdrawal_id} - {amount:.2f} ETB")
        
    except ValueError:
        await update.message.reply_text(f"{get_emoji('error')} Invalid WITHDRAWAL_ID format", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"{get_emoji('error')} Error: {str(e)}", parse_mode=ParseMode.HTML)


async def reject_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reject cashout"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(f"{get_emoji('error')} Admin only command", parse_mode=ParseMode.HTML)
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            f"{get_emoji('info')} <b>Reject Cashout</b>\n\n"
            f"Usage: <code>/reject_cashout WITHDRAWAL_ID [reason]</code>\n"
            f"Example: <code>/reject_cashout 12345 Invalid account</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        withdrawal_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Not specified"
        
        withdrawal = await Database.get_withdrawal_by_id(withdrawal_id)
        
        if withdrawal:
            await Database.reject_withdrawal(withdrawal_id)
            
            user = await Database.get_user(withdrawal["telegram_id"])
            if user:
                lang = user.get('lang', 'en')
                await context.bot.send_message(
                    chat_id=withdrawal["telegram_id"],
                    text=TEXTS[lang]['rejected'].format(reason),
                    parse_mode=ParseMode.HTML
                )
            
            await update.message.reply_text(
                f"{get_emoji('success')} Cashout rejected for withdrawal #{withdrawal_id}\nReason: {reason}",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Cashout rejected: withdrawal #{withdrawal_id} - Reason: {reason}")
        else:
            await update.message.reply_text(f"{get_emoji('error')} Withdrawal #{withdrawal_id} not found", parse_mode=ParseMode.HTML)
        
    except ValueError:
        await update.message.reply_text(f"{get_emoji('error')} Invalid WITHDRAWAL_ID format", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"{get_emoji('error')} Error: {str(e)}", parse_mode=ParseMode.HTML)


# ==================== HELPER FUNCTIONS ====================

async def get_active_users_today() -> int:
    """Get number of active users today"""
    try:
        async with Database._pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(DISTINCT telegram_id)
                FROM game_transactions
                WHERE DATE(timestamp) = CURRENT_DATE
            """)
            return count or 0
    except Exception:
        return 0


async def get_total_withdrawals() -> float:
    """Get total approved withdrawals"""
    try:
        async with Database._pool.acquire() as conn:
            total = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0)
                FROM pending_withdrawals
                WHERE status = 'approved'
            """)
            return float(total or 0)
    except Exception:
        return 0.0


# ==================== EXPORTS ====================

__all__ = [
    'admin_panel',
    'admin_callback',
    'set_win_percentage',
    'stats_command',
    'approve_deposit',
    'reject_deposit',
    'approve_cashout',
    'reject_cashout',
]