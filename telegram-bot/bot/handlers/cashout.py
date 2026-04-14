# telegram-bot/bot/handlers/cashout.py
# ULTRA OPTIMIZED - Complete Cashout Handler (Standalone, No Conflicts)

import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.db.database import Database
from bot.keyboards.menu import menu, cashout_methods_keyboard
from bot.config import config
from bot.texts.emojis import get_emoji
from bot.texts.locales import TEXTS
from bot.utils import logger

# ==================== CONSTANTS ====================
METHOD, AMOUNT, ACCOUNT = range(3)

# Withdrawal limits from config
MIN_WITHDRAWAL = config.MIN_WITHDRAWAL
MAX_WITHDRAWAL = config.MAX_WITHDRAWAL
WITHDRAWAL_FEE = config.WITHDRAWAL_FEE_PERCENTAGE
ENABLE_FEE = config.ENABLE_WITHDRAWAL_FEE

# Anti-spam cache
_cashout_cooldown: Dict[int, datetime] = {}


# ==================== VALIDATION HELPERS ====================
def validate_account(account: str) -> bool:
    """Validate account number (minimum 3 characters)"""
    return len(account.strip()) >= 3


def validate_amount(amount: float) -> Tuple[bool, str]:
    """Validate withdrawal amount"""
    if amount <= 0:
        return False, "Amount must be greater than 0"
    if amount < MIN_WITHDRAWAL:
        return False, f"Minimum withdrawal amount is {MIN_WITHDRAWAL} ETB"
    if amount > MAX_WITHDRAWAL:
        return False, f"Maximum withdrawal amount is {MAX_WITHDRAWAL} ETB"
    return True, ""


def check_cooldown(user_id: int) -> Tuple[bool, int]:
    """Prevent spam (30 second cooldown between cashout requests)"""
    now = datetime.now()
    last = _cashout_cooldown.get(user_id)
    
    if last:
        elapsed = (now - last).total_seconds()
        if elapsed < 30:
            return False, int(30 - elapsed)
    
    _cashout_cooldown[user_id] = now
    return True, 0


def calculate_fee(amount: float) -> float:
    """Calculate withdrawal fee if enabled"""
    if ENABLE_FEE and WITHDRAWAL_FEE > 0:
        return amount * WITHDRAWAL_FEE / 100
    return 0.0


# ==================== MAIN HANDLERS ====================
async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start cashout flow - Entry point"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Clear any existing session data
    context.user_data.clear()
    
    # Check registration
    if not user or not user.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Please register first!*\n\n"
            f"Use /register to complete your registration.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Check minimum deposit requirement
    total_deposited = user.get('total_deposited', 0)
    if total_deposited < MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Withdrawal Not Allowed*\n\n"
            f"You need to deposit at least `{MIN_WITHDRAWAL} ETB` before withdrawing.\n"
            f"Your total deposited: `{total_deposited:.2f} ETB`\n\n"
            f"Use /deposit to add funds.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Check sufficient balance
    balance = user.get('balance', 0)
    if balance < MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Insufficient Balance!*\n\n"
            f"Minimum withdrawal: `{MIN_WITHDRAWAL} ETB`\n"
            f"Your balance: `{balance:.2f} ETB`\n\n"
            f"Use /deposit to add funds.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Check cooldown
    can_proceed, wait_seconds = check_cooldown(telegram_id)
    if not can_proceed:
        await update.message.reply_text(
            f"{get_emoji('clock')} ⏰ *Please wait!*\n\n"
            f"You can make another withdrawal request in `{wait_seconds}` seconds.\n\n"
            f"This helps prevent spam and errors.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Show cashout methods
    keyboard = cashout_methods_keyboard(lang)
    await update.message.reply_text(
        f"{get_emoji('withdraw')} 💳 *{TEXTS[lang]['cashout_select']}*\n\n"
        f"Choose your preferred withdrawal method:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return METHOD


async def cashout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal method selection"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("cashout_"):
        method_raw = callback_data.split("_")[1].upper()
        
        # Map method names to keys
        method_map = {
            'CBE': 'CBE',
            'ABYSSINIA': 'ABBISINIYA',
            'ABBISINIYA': 'ABBISINIYA',
            'TELEBIRR': 'TELEBIRR',
            'MPESA': 'MPESA'
        }
        
        method_key = method_map.get(method_raw, method_raw)
        
        if method_key not in config.PAYMENT_ACCOUNTS:
            await query.edit_message_text(
                f"{get_emoji('error')} ❌ Invalid withdrawal method selected.",
                parse_mode='Markdown'
            )
            return METHOD
        
        telegram_id = query.from_user.id
        user = await Database.get_user(telegram_id)
        lang = user.get('lang', 'en') if user else 'en'
        balance = user.get('balance', 0)
        
        # Store method in context
        context.user_data['cashout_method'] = method_key
        
        # Calculate fee info for display
        fee = calculate_fee(0)  # Will calculate on amount
        fee_info = ""
        if ENABLE_FEE and WITHDRAWAL_FEE > 0:
            fee_info = f"\n{get_emoji('info')} Fee: {WITHDRAWAL_FEE}% (deducted from amount)"
        
        await query.edit_message_text(
            f"{get_emoji('success')} ✅ *{method_key} Selected*\n\n"
            f"{get_emoji('money')} Your balance: `{balance:.2f} ETB`\n"
            f"{get_emoji('info')} Min: `{MIN_WITHDRAWAL} ETB` | Max: `{MAX_WITHDRAWAL} ETB`{fee_info}\n\n"
            f"{get_emoji('money')} *Enter the amount you want to withdraw:*\n\n"
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
    
    # Extract numbers
    nums = re.findall(r"\d+\.?\d*", text)
    if not nums:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Invalid Amount!*\n\n"
            f"Please enter a valid number (e.g., `500`, `1000.50`)\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    try:
        amount = float(nums[0])
    except ValueError:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Invalid Amount!*\n\n"
            f"Please enter a valid number.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    method = context.user_data.get('cashout_method')
    if not method:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Session Expired!*\n\n"
            f"Please start over with /cashout",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Validate amount
    is_valid, error_msg = validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ {error_msg}\n\n"
            f"Please enter a valid amount.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Check balance
    current_balance = user_data.get('balance', 0)
    if amount > current_balance:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Insufficient Balance!*\n\n"
            f"Your balance: `{current_balance:.2f} ETB`\n"
            f"Requested: `{amount:.2f} ETB`\n\n"
            f"Please enter a smaller amount.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Calculate fee
    fee = calculate_fee(amount)
    net_amount = amount - fee
    
    # Store amount
    context.user_data['cashout_amount'] = amount
    context.user_data['cashout_fee'] = fee
    context.user_data['cashout_net'] = net_amount
    
    fee_msg = ""
    if fee > 0:
        fee_msg = f"\n{get_emoji('info')} Fee ({WITHDRAWAL_FEE}%): `{fee:.2f} ETB`\n{get_emoji('money')} You will receive: `{net_amount:.2f} ETB`"
    
    await update.message.reply_text(
        f"{get_emoji('success')} ✅ *Amount Accepted!*\n\n"
        f"Amount: `{amount:.2f} ETB`{fee_msg}\n\n"
        f"{get_emoji('phone')} *Enter your {method} account number:*\n\n"
        f"Please provide the account number where you want to receive the money.\n\n"
        f"Type /cancel to cancel.",
        parse_mode='Markdown'
    )
    return ACCOUNT


async def cashout_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process account number and create withdrawal request"""
    telegram_id = update.effective_user.id
    user = update.effective_user
    user_data = await Database.get_user(telegram_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    
    account = update.message.text.strip()
    
    # Validate account number
    if not validate_account(account):
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Invalid Account Number!*\n\n"
            f"Please enter a valid account number (at least 3 characters).\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return ACCOUNT
    
    method = context.user_data.get('cashout_method')
    amount = context.user_data.get('cashout_amount')
    fee = context.user_data.get('cashout_fee', 0)
    net_amount = context.user_data.get('cashout_net', amount)
    
    if not method or not amount:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Session Expired!*\n\n"
            f"Please start over with /cashout",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Double-check balance before creating request
    current_balance = user_data.get('balance', 0)
    if amount > current_balance:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Insufficient Balance!*\n\n"
            f"Your balance changed. Current balance: `{current_balance:.2f} ETB`\n"
            f"Requested: `{amount:.2f} ETB`\n\n"
            f"Please start over with /cashout",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Create withdrawal request
    try:
        withdrawal_id = await Database.add_pending_withdrawal(
            telegram_id,
            amount,
            account,
            method
        )
        
        # Notify admin
        admin_msg = (
            f"{get_emoji('withdraw')} *NEW CASHOUT REQUEST* #{withdrawal_id}\n\n"
            f"{get_emoji('user')} User: {user.first_name} (@{user.username or 'N/A'})\n"
            f"{get_emoji('id')} ID: `{telegram_id}`\n"
            f"{get_emoji('money')} Amount: `{amount:.2f} ETB`\n"
        )
        
        if fee > 0:
            admin_msg += f"{get_emoji('info')} Fee: `{fee:.2f} ETB`\n{get_emoji('money')} Net: `{net_amount:.2f} ETB`\n"
        
        admin_msg += (
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
        fee_msg = ""
        if fee > 0:
            fee_msg = f"\n\n{get_emoji('info')} Fee: `{fee:.2f} ETB`\n{get_emoji('money')} You'll receive: `{net_amount:.2f} ETB`"
        
        await update.message.reply_text(
            f"{get_emoji('success')} ✅ *Withdrawal Request Submitted!*\n\n"
            f"Request ID: `#{withdrawal_id}`\n"
            f"Amount: `{amount:.2f} ETB`{fee_msg}\n"
            f"Method: `{method}`\n"
            f"Account: `{account}`\n\n"
            f"{get_emoji('clock')} *Processing Time:* Within {config.WITHDRAWAL_PROCESSING_TIME} hours\n\n"
            f"{get_emoji('info')} You will be notified once your request is processed.\n\n"
            f"Thank you for using Estif Bingo! 🎰",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        
        logger.info(f"💰 Cashout request #{withdrawal_id} from {telegram_id}: {amount:.2f} ETB via {method}")
        
    except Exception as e:
        logger.error(f"Cashout request error: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Failed to Submit Request!*\n\n"
            f"An error occurred. Please try again later.\n\n"
            f"Support: {config.SUPPORT_GROUP_LINK}",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
    
    # Clear session data
    context.user_data.clear()
    return ConversationHandler.END


async def cashout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel cashout flow"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await update.message.reply_text(
        f"{get_emoji('warning')} ❌ *Withdrawal Cancelled*\n\n"
        f"You can start a new withdrawal anytime from the main menu.\n\n"
        f"Use /cashout to start again.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==================== BACKWARD COMPATIBILITY ALIASES ====================
# These aliases ensure compatibility with main.py imports
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