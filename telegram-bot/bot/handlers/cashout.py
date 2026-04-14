# telegram-bot/bot/handlers/cashout.py
# Estif Bingo 24/7 - Complete Cashout Handler (FULLY FIXED)

import logging
import random
import re
from typing import Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu, cashout_methods_keyboard
from bot.config import config
from bot.utils import logger
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)

# ==================== CONVERSATION STATES ====================
METHOD = 1   # Waiting for method selection
AMOUNT = 2   # Waiting for amount input  
ACCOUNT = 3  # Waiting for account number


# ==================== MAIN CASHOUT HANDLER ====================
async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cashout payment methods - Entry point"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} Please register first using /register",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Check minimum deposit requirement
    total_deposited = user.get('total_deposited', 0)
    if total_deposited < config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            TEXTS[lang]['cashout_not_allowed'].format(total_deposited),
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return ConversationHandler.END
    
    # Check sufficient balance
    balance = user.get('balance', 0)
    if balance < config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} {TEXTS[lang]['insufficient_balance']}",
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return ConversationHandler.END
    
    # Clear any existing cashout data
    context.user_data.pop('cashout_method', None)
    context.user_data.pop('cashout_amount', None)
    
    # Show cashout methods
    keyboard = cashout_methods_keyboard(lang)
    await update.message.reply_text(
        f"{get_emoji('withdraw')} {TEXTS[lang]['cashout_select']}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return METHOD


async def cashout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal method selection callback"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Handle method selection (cashout_cbe, cashout_telebirr, etc.)
    if callback_data.startswith("cashout_"):
        method = callback_data.split("_")[1].upper()
        
        # Map method names to keys
        method_map = {
            'CBE': 'CBE',
            'ABYSSINIA': 'ABBISINIYA',
            'ABBISINIYA': 'ABBISINIYA',
            'TELEBIRR': 'TELEBIRR',
            'MPESA': 'MPESA'
        }
        
        method_key = method_map.get(method.upper(), method.upper())
        
        if method_key not in config.PAYMENT_ACCOUNTS:
            await query.edit_message_text(
                f"{get_emoji('error')} Invalid withdrawal method selected.",
                parse_mode='Markdown'
            )
            return METHOD
        
        telegram_id = query.from_user.id
        user = await Database.get_user(telegram_id)
        lang = user.get('lang', 'en') if user else 'en'
        balance = user.get('balance', 0)
        
        # Store method in context
        context.user_data['cashout_method'] = method_key
        
        await query.edit_message_text(
            f"{get_emoji('info')} {TEXTS[lang]['cashout_selected'].format(method_key, balance)}\n\n"
            f"{get_emoji('money')} Enter amount to withdraw (Min: {config.MIN_WITHDRAWAL} ETB, Max: {config.MAX_WITHDRAWAL} ETB):\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    return METHOD


async def cashout_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process cashout amount entry"""
    telegram_id = update.effective_user.id
    user_data = await Database.get_user(telegram_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    
    text = update.message.text.strip()
    
    # Extract numbers from text
    nums = re.findall(r"\d+\.?\d*", text)
    if not nums:
        await update.message.reply_text(
            f"{get_emoji('error')} Please enter a valid amount (e.g., 500)\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    try:
        amount = float(nums[0])
    except ValueError:
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid amount. Please enter a number.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    method = context.user_data.get('cashout_method')
    if not method:
        await update.message.reply_text(
            f"{get_emoji('error')} Session expired. Please start cashout again with /cashout\n\n"
            f"Type /cancel to cancel.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Validate amount
    if amount < config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} Minimum withdrawal is {config.MIN_WITHDRAWAL} ETB\n\n"
            f"Please enter a larger amount or type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    if amount > config.MAX_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} Maximum withdrawal is {config.MAX_WITHDRAWAL} ETB\n\n"
            f"Please enter a smaller amount or type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    current_balance = user_data.get('balance', 0)
    if amount > current_balance:
        await update.message.reply_text(
            f"{get_emoji('error')} Insufficient balance!\n\n"
            f"Your balance: {current_balance:.2f} ETB\n"
            f"Requested: {amount:.2f} ETB\n\n"
            f"Please enter a smaller amount or type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Store amount
    context.user_data['cashout_amount'] = amount
    
    await update.message.reply_text(
        f"{get_emoji('success')} Amount: {amount:.2f} ETB accepted.\n\n"
        f"{get_emoji('phone')} Please enter your {method} account number:\n\n"
        f"Type /cancel to cancel.",
        parse_mode='Markdown'
    )
    return ACCOUNT


async def cashout_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process account number entry and create withdrawal request"""
    telegram_id = update.effective_user.id
    user = update.effective_user
    user_data = await Database.get_user(telegram_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    
    account = update.message.text.strip()
    
    if not account or len(account) < 3:
        await update.message.reply_text(
            f"{get_emoji('error')} Please enter a valid account number (at least 3 characters)\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return ACCOUNT
    
    method = context.user_data.get('cashout_method')
    amount = context.user_data.get('cashout_amount')
    
    if not method or not amount:
        await update.message.reply_text(
            f"{get_emoji('error')} Session expired. Please start cashout again with /cashout",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Create withdrawal request
    withdrawal_id = await Database.add_pending_withdrawal(
        telegram_id,
        amount,
        account,
        method
    )
    
    # Notify admin
    admin_msg = (
        f"{get_emoji('withdraw')} *CASHOUT REQUEST* #{withdrawal_id}\n\n"
        f"{get_emoji('user')} User: {user.first_name} (@{user.username or 'N/A'})\n"
        f"{get_emoji('id')} ID: `{telegram_id}`\n"
        f"{get_emoji('money')} Amount: `{amount:.2f}` ETB\n"
        f"{get_emoji('bank')} Method: `{method}`\n"
        f"{get_emoji('phone')} Account: `{account}`\n\n"
        f"{get_emoji('info')} Commands:\n"
        f"`/approve_cashout {withdrawal_id}`\n"
        f"`/reject_cashout {withdrawal_id}`"
    )
    
    await context.bot.send_message(
        chat_id=config.ADMIN_CHAT_ID,
        text=admin_msg,
        parse_mode='Markdown'
    )
    
    # Confirm to user
    await update.message.reply_text(
        f"{get_emoji('success')} {TEXTS[lang]['cashout_sent']}\n\n"
        f"{get_emoji('clock')} Request ID: #{withdrawal_id}\n"
        f"{get_emoji('info')} You will be notified once processed.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    logger.info(f"Cashout request #{withdrawal_id} from {telegram_id}: {amount:.2f} ETB via {method}")
    
    # Clear flow data
    context.user_data.clear()
    
    return ConversationHandler.END


async def cashout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel cashout"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await update.message.reply_text(
        f"{get_emoji('warning')} Withdrawal cancelled.\n\n"
        f"You can start a new withdrawal anytime from the main menu.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==================== BACKWARD COMPATIBILITY ALIASES ====================
handle_cashout_amount = cashout_amount
handle_cashout_account = cashout_account
cashout_method = cashout_callback


# ==================== EXPORTS ====================
__all__ = [
    'cashout',
    'cashout_callback',
    'cashout_method',
    'cashout_amount',
    'cashout_account',
    'cashout_cancel',
    'handle_cashout_amount',
    'handle_cashout_account',
    'METHOD',
    'AMOUNT',
    'ACCOUNT',
]