# telegram-bot/bot/handlers/cashout.py
# Estif Bingo 24/7 - Cashout Request Handler with Withdrawal Method Selection

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.db.database import Database
from bot.keyboards.menu import menu, cashout_methods_keyboard
from bot.config import config
from bot.texts.emojis import get_emoji
from bot.texts.locales import TEXTS

logger = logging.getLogger(__name__)

# Conversation states
AMOUNT, ACCOUNT = range(2)


async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cashout payment methods"""
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} Please register first.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Check minimum deposit requirement
    if user.get('total_deposited', 0) < config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            TEXTS[lang]['cashout_not_allowed'].format(user.get('total_deposited', 0)),
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return ConversationHandler.END
    
    # Check sufficient balance
    if user.get('balance', 0) < config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} {TEXTS[lang]['insufficient_balance']}",
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return ConversationHandler.END
    
    # Clear any existing data
    context.user_data.clear()
    
    # Show cashout methods
    keyboard = cashout_methods_keyboard(lang)
    await update.message.reply_text(
        f"{get_emoji('withdraw')} {TEXTS[lang]['cashout_select']}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return AMOUNT


async def cashout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal method selection callback"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("cashout_"):
        method = data.split("_")[1].upper()
        
        # Map method names to keys
        method_map = {
            'CBE': 'CBE',
            'ABYSSINIA': 'ABBISINIYA',
            'ABBISINIYA': 'ABBISINIYA',
            'TELEBIRR': 'TELEBIRR',
            'MPESA': 'MPESA'
        }
        method_key = method_map.get(method, method)
        
        if method_key not in config.PAYMENT_ACCOUNTS:
            await query.edit_message_text(
                f"{get_emoji('error')} Invalid method.",
                parse_mode='Markdown'
            )
            return AMOUNT
        
        # Store method in context
        context.user_data['cashout_method'] = method_key
        
        user = await Database.get_user(query.from_user.id)
        lang = user.get('lang', 'en') if user else 'en'
        balance = user.get('balance', 0)
        
        await query.edit_message_text(
            f"{get_emoji('info')} {TEXTS[lang]['cashout_selected'].format(method_key, balance)}\n\n"
            f"{get_emoji('money')} Enter amount (Min: {config.MIN_WITHDRAWAL} ETB, Max: {config.MAX_WITHDRAWAL} ETB):\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    return AMOUNT


async def cashout_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process cashout amount entry"""
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    text = update.message.text.strip()
    nums = re.findall(r"\d+\.?\d*", text)
    
    if not nums:
        await update.message.reply_text(
            f"{get_emoji('error')} Please enter a valid number.\nType /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    amount = float(nums[0])
    
    if amount < config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} Minimum withdrawal is {config.MIN_WITHDRAWAL} ETB.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    if amount > config.MAX_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} Maximum withdrawal is {config.MAX_WITHDRAWAL} ETB.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    if amount > user.get('balance', 0):
        await update.message.reply_text(
            f"{get_emoji('error')} Insufficient balance! Your balance: {user.get('balance', 0):.2f} ETB",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Store amount
    context.user_data['cashout_amount'] = amount
    
    await update.message.reply_text(
        f"{get_emoji('success')} Amount: {amount:.2f} ETB accepted.\n\n"
        f"{get_emoji('phone')} Please enter your {context.user_data['cashout_method']} account number:\n"
        f"Type /cancel to cancel.",
        parse_mode='Markdown'
    )
    return ACCOUNT


async def cashout_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process account number entry and create withdrawal request"""
    user_id = update.effective_user.id
    user = update.effective_user
    user_data = await Database.get_user(user_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    
    account = update.message.text.strip()
    
    if len(account) < 3:
        await update.message.reply_text(
            f"{get_emoji('error')} Please enter a valid account number.",
            parse_mode='Markdown'
        )
        return ACCOUNT
    
    method = context.user_data.get('cashout_method')
    amount = context.user_data.get('cashout_amount')
    
    if not method or not amount:
        await update.message.reply_text(
            f"{get_emoji('error')} Session expired. Please start over with /cashout",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Create withdrawal request
    withdrawal_id = await Database.add_pending_withdrawal(user_id, amount, account, method)
    
    # Notify admin
    admin_msg = (
        f"{get_emoji('withdraw')} *CASHOUT REQUEST* #{withdrawal_id}\n"
        f"User: {user.first_name} (@{user.username or 'N/A'})\n"
        f"ID: `{user_id}`\n"
        f"Amount: {amount:.2f} ETB\n"
        f"Method: {method}\n"
        f"Account: {account}"
    )
    await context.bot.send_message(
        chat_id=config.ADMIN_CHAT_ID,
        text=admin_msg,
        parse_mode='Markdown'
    )
    
    # Confirm to user
    await update.message.reply_text(
        f"{get_emoji('success')} {TEXTS[lang]['cashout_sent']}\n"
        f"Request ID: #{withdrawal_id}",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    logger.info(f"Cashout request #{withdrawal_id} from {user_id}: {amount:.2f} ETB via {method}")
    
    # Clear flow data
    context.user_data.clear()
    
    return ConversationHandler.END


async def cashout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel cashout"""
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await update.message.reply_text(
        f"{get_emoji('warning')} Withdrawal cancelled.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


# For backward compatibility with older code that expects these names
handle_cashout_amount = cashout_amount
handle_cashout_account = cashout_account


# Export all
__all__ = [
    'cashout',
    'cashout_callback',
    'cashout_amount',
    'cashout_account',
    'cashout_cancel',
    'handle_cashout_amount',
    'handle_cashout_account',
    'AMOUNT',
    'ACCOUNT',
]