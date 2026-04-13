# telegram-bot/bot/handlers/deposit.py
# Estif Bingo 24/7 - Deposit Request Handler with Payment Method Selection

import logging
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu, deposit_methods_keyboard
from bot.config import config
from bot.utils import logger
from bot.texts.emojis import get_emoji

# Conversation states
AMOUNT = 1
SCREENSHOT = 2

logger = logging.getLogger(__name__)


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show deposit payment methods"""
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
    
    # Show deposit methods using keyboard from menu.py
    keyboard = deposit_methods_keyboard(lang)
    await update.message.reply_text(
        f"{get_emoji('deposit')} {TEXTS[lang]['deposit_select'].format(config.ACCOUNT_HOLDER)}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return AMOUNT


async def deposit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection callback"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Handle method selection (deposit_cbe, deposit_telebirr, etc.)
    if callback_data.startswith("deposit_"):
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
                f"{get_emoji('error')} Invalid payment method selected.",
                parse_mode='Markdown'
            )
            return AMOUNT
        
        account_number = config.PAYMENT_ACCOUNTS[method_key]
        telegram_id = query.from_user.id
        
        user = await Database.get_user(telegram_id)
        lang = user.get('lang', 'en') if user else 'en'
        
        # Store deposit info in context
        context.user_data['deposit_method'] = method_key
        context.user_data['deposit_account'] = account_number
        
        await query.edit_message_text(
            f"{get_emoji('info')} {TEXTS[lang]['deposit_selected'].format(method_key, config.ACCOUNT_HOLDER, account_number)}\n\n"
            f"{get_emoji('money')} Please enter the amount you want to deposit (Min: {config.MIN_DEPOSIT} ETB, Max: {config.MAX_DEPOSIT} ETB):",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    return AMOUNT


async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process deposit amount entry"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    text = update.message.text.strip()
    nums = re.findall(r"\d+\.?\d*", text)
    
    if not nums:
        await update.message.reply_text(
            f"{get_emoji('error')} Please enter a valid amount (e.g., 100)",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    amount = float(nums[0])
    
    if amount < config.MIN_DEPOSIT:
        await update.message.reply_text(
            f"{get_emoji('error')} Minimum deposit amount is {config.MIN_DEPOSIT} ETB",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    if amount > config.MAX_DEPOSIT:
        await update.message.reply_text(
            f"{get_emoji('error')} Maximum deposit amount is {config.MAX_DEPOSIT} ETB",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Store amount
    context.user_data['deposit_amount'] = amount
    
    await update.message.reply_text(
        f"{get_emoji('success')} Amount: {amount} ETB accepted.\n\n"
        f"{get_emoji('camera')} Please send a screenshot of your payment confirmation.\n\n"
        f"📋 Send to: {context.user_data['deposit_account']}\n"
        f"👤 Account Holder: {config.ACCOUNT_HOLDER}\n\n"
        f"⚠️ Make sure the transaction ID is visible in the screenshot.",
        parse_mode='Markdown'
    )
    return SCREENSHOT


async def deposit_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process deposit screenshot"""
    telegram_id = update.effective_user.id
    user = update.effective_user
    user_data = await Database.get_user(telegram_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    
    # Check if we have a photo
    if not update.message.photo:
        await update.message.reply_text(
            f"{get_emoji('error')} Please send a screenshot of your payment confirmation.",
            parse_mode='Markdown'
        )
        return SCREENSHOT
    
    method = context.user_data.get('deposit_method')
    amount = context.user_data.get('deposit_amount')
    account = context.user_data.get('deposit_account')
    
    if not method or not amount:
        await update.message.reply_text(
            f"{get_emoji('error')} Session expired. Please start deposit again with /deposit",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    photo = update.message.photo[-1]
    request_id = random.randint(100000, 999999)
    
    # Send to admin
    admin_msg = (
        f"{get_emoji('deposit')} *NEW DEPOSIT REQUEST* #{request_id}\n\n"
        f"{get_emoji('user')} User: {user.first_name} (@{user.username or 'N/A'})\n"
        f"{get_emoji('id')} ID: `{telegram_id}`\n"
        f"{get_emoji('money')} Amount: `{amount}` ETB\n"
        f"{get_emoji('bank')} Method: `{method}`\n"
        f"{get_emoji('phone')} Account: `{account}`\n\n"
        f"{get_emoji('info')} Commands:\n"
        f"`/approve_deposit {telegram_id} {amount}`\n"
        f"`/reject_deposit {telegram_id}`"
    )
    
    await context.bot.send_message(
        chat_id=config.ADMIN_CHAT_ID,
        text=admin_msg,
        parse_mode='Markdown'
    )
    
    await context.bot.send_photo(
        chat_id=config.ADMIN_CHAT_ID,
        photo=photo.file_id,
        caption=f"📸 Deposit proof from {user.first_name} (@{user.username or 'N/A'})"
    )
    
    # Confirm to user
    await update.message.reply_text(
        f"{get_emoji('success')} {TEXTS[lang]['deposit_sent']}\n\n"
        f"{get_emoji('clock')} Request ID: #{request_id}\n"
        f"{get_emoji('info')} You will be notified once approved.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    logger.info(f"Deposit request #{request_id} from {telegram_id}: {amount} ETB via {method}")
    
    # Clear flow data
    context.user_data.clear()
    
    return ConversationHandler.END


async def deposit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel deposit"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await update.message.reply_text(
        f"{get_emoji('warning')} Deposit cancelled.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


# For backward compatibility with older code that expects these names
handle_deposit_amount = deposit_amount
handle_deposit_screenshot = deposit_screenshot


# Export all
__all__ = [
    'deposit',
    'deposit_callback',
    'deposit_amount',
    'deposit_screenshot',
    'deposit_cancel',
    'handle_deposit_amount',  # Alias for backward compatibility
    'handle_deposit_screenshot',  # Alias for backward compatibility
    'AMOUNT',
    'SCREENSHOT',
]