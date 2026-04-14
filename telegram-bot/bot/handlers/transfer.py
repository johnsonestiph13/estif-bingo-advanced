# telegram-bot/bot/handlers/transfer.py
# ULTRA OPTIMIZED - Complete Transfer Handler (Standalone, No Conflicts)

import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from decimal import Decimal, ROUND_DOWN

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from bot.db.database import Database
from bot.keyboards.menu import back_button, main_menu_inline
from bot.config import config
from bot.texts.emojis import get_emoji
from bot.utils import logger

# ==================== CONSTANTS ====================
PHONE_NUMBER, AMOUNT, CONFIRM = range(3)

# Transfer limits from config
MIN_AMOUNT = config.MIN_TRANSFER
MAX_AMOUNT = config.MAX_TRANSFER
DAILY_LIMIT = config.TRANSFER_DAILY_LIMIT
FEE_PERCENT = config.TRANSFER_FEE_PERCENTAGE

# Anti-spam cache
_cooldown_cache: Dict[int, datetime] = {}


# ==================== VALIDATION HELPERS ====================
def validate_phone(phone: str) -> bool:
    """Validate Ethiopian phone number"""
    return bool(re.match(r'^(09|07)[0-9]{8}$', phone))


def validate_amount(amount: float) -> Tuple[bool, str]:
    """Validate transfer amount"""
    if amount <= 0:
        return False, "Amount must be greater than 0"
    if amount < MIN_AMOUNT:
        return False, f"Minimum transfer amount is {MIN_AMOUNT} ETB"
    if amount > MAX_AMOUNT:
        return False, f"Maximum transfer amount is {MAX_AMOUNT} ETB"
    return True, ""


async def check_daily_limit(user_id: int, amount: float) -> Tuple[bool, float]:
    """Check daily transfer limit"""
    async with Database._pool.acquire() as conn:
        today = datetime.now().date()
        total_sent = await conn.fetchval("""
            SELECT COALESCE(SUM(ABS(amount)), 0)
            FROM game_transactions
            WHERE telegram_id = $1 AND type = 'transfer_out' AND DATE(timestamp) = $2
        """, user_id, today)
        
        total_sent = float(total_sent or 0)
        if total_sent + amount > DAILY_LIMIT:
            remaining = DAILY_LIMIT - total_sent
            return False, remaining
        return True, DAILY_LIMIT - (total_sent + amount)


def check_cooldown(user_id: int) -> Tuple[bool, int]:
    """Prevent spam (30 second cooldown)"""
    now = datetime.now()
    last = _cooldown_cache.get(user_id)
    
    if last:
        elapsed = (now - last).total_seconds()
        if elapsed < 30:
            return False, int(30 - elapsed)
    
    _cooldown_cache[user_id] = now
    return True, 0


# ==================== MAIN HANDLERS ====================
async def transfer(update: Update, context: CallbackContext):
    """Start transfer - Entry point"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Clear any existing data
    context.user_data.clear()
    
    message = (
        f"{get_emoji('transfer')} *BALANCE TRANSFER*\n\n"
        f"Send money to another player instantly!\n\n"
        f"{get_emoji('info')} *Rules:*\n"
        f"• Minimum: `{MIN_AMOUNT} ETB`\n"
        f"• Maximum: `{MAX_AMOUNT} ETB`\n"
        f"• Daily limit: `{DAILY_LIMIT} ETB`\n"
        f"• Fee: `{FEE_PERCENT}%`\n\n"
        f"{get_emoji('phone')} *Enter receiver's phone number:*\n"
        f"Example: `0912345678` or `0712345678`\n\n"
        f"Type /cancel to cancel."
    )
    
    reply_markup = back_button("main")
    
    if query:
        await query.answer()
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    
    return PHONE_NUMBER


async def transfer_phone(update: Update, context: CallbackContext):
    """Handle phone number input"""
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Check self-transfer
    sender = await Database.get_user(user_id)
    if sender and sender.get('phone') == phone:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ You cannot transfer money to yourself!\n\n"
            f"Please enter a different phone number.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Validate format
    if not validate_phone(phone):
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ Invalid phone number!\n\n"
            f"Please use format: `09XXXXXXXX` or `07XXXXXXXX`\n"
            f"Example: `0912345678`\n\n"
            f"Type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Find receiver
    receiver = await Database.get_user_by_phone(phone)
    if not receiver:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ User not found!\n\n"
            f"No registered user with phone number `{phone}`.\n"
            f"Make sure the user has registered first.\n\n"
            f"Type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    if not receiver.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ User not fully registered!\n\n"
            f"This user has not completed registration.\n\n"
            f"Type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Store receiver info
    context.user_data['receiver'] = {
        'id': receiver['telegram_id'],
        'name': receiver.get('username') or receiver.get('first_name', 'Unknown'),
        'phone': phone
    }
    
    # Get sender balance
    balance = await Database.get_balance(user_id)
    
    await update.message.reply_text(
        f"{get_emoji('success')} ✅ *Receiver Found!*\n\n"
        f"{get_emoji('user')} Name: *{context.user_data['receiver']['name']}*\n"
        f"{get_emoji('phone')} Phone: `{phone}`\n\n"
        f"{get_emoji('money')} Your balance: `{balance:.2f} ETB`\n"
        f"{get_emoji('info')} Transfer fee: `{FEE_PERCENT}%`\n\n"
        f"*Enter amount to transfer:*\n"
        f"Minimum: `{MIN_AMOUNT} ETB` | Maximum: `{MAX_AMOUNT} ETB`\n\n"
        f"Type /cancel to cancel.",
        parse_mode='Markdown',
        reply_markup=back_button("transfer")
    )
    return AMOUNT


async def transfer_amount(update: Update, context: CallbackContext):
    """Handle amount input"""
    user_id = update.effective_user.id
    
    # Parse amount
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ Invalid amount!\n\n"
            f"Please enter a valid number (e.g., `100`, `50.50`)\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown',
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Validate amount
    is_valid, error = validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ {error}\n\n"
            f"Please enter a valid amount.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown',
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Check balance with fee
    balance = await Database.get_balance(user_id)
    fee = amount * FEE_PERCENT / 100
    total = amount + fee
    
    if balance < total:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Insufficient Balance!*\n\n"
            f"{get_emoji('money')} Your balance: `{balance:.2f} ETB`\n"
            f"{get_emoji('transfer')} Transfer amount: `{amount:.2f} ETB`\n"
            f"{get_emoji('info')} Fee ({FEE_PERCENT}%): `{fee:.2f} ETB`\n"
            f"{get_emoji('money')} Total needed: `{total:.2f} ETB`\n\n"
            f"Shortfall: `{total - balance:.2f} ETB`\n\n"
            f"Please enter a smaller amount or use /deposit.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown',
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Check daily limit
    within_limit, remaining = await check_daily_limit(user_id, amount)
    if not within_limit:
        await update.message.reply_text(
            f"{get_emoji('error')} ❌ *Daily Limit Reached!*\n\n"
            f"Daily limit: `{DAILY_LIMIT} ETB`\n"
            f"Remaining today: `{remaining:.2f} ETB`\n"
            f"Requested: `{amount:.2f} ETB`\n\n"
            f"Please try a smaller amount or try again tomorrow.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown',
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Check cooldown
    can_transfer, wait = check_cooldown(user_id)
    if not can_transfer:
        await update.message.reply_text(
            f"{get_emoji('clock')} ⏰ *Please wait!*\n\n"
            f"You can make another transfer in `{wait}` seconds.\n\n"
            f"This prevents spam and errors.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown',
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Store amount
    context.user_data['amount'] = amount
    context.user_data['fee'] = fee
    context.user_data['total'] = total
    
    receiver = context.user_data['receiver']
    
    # Create confirmation keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{get_emoji('success')} ✅ CONFIRM", callback_data="transfer_confirm"),
            InlineKeyboardButton(f"{get_emoji('error')} ❌ CANCEL", callback_data="transfer_cancel")
        ]
    ])
    
    await update.message.reply_text(
        f"{get_emoji('question')} *TRANSFER CONFIRMATION*\n\n"
        f"{get_emoji('user')} *To:* {receiver['name']}\n"
        f"{get_emoji('phone')} *Phone:* `{receiver['phone']}`\n"
        f"{get_emoji('money')} *Amount:* `{amount:.2f} ETB`\n"
        f"{get_emoji('info')} *Fee ({FEE_PERCENT}%):* `{fee:.2f} ETB`\n"
        f"{get_emoji('money')} *Total deduction:* `{total:.2f} ETB`\n\n"
        f"{get_emoji('warning')} ⚠️ *This action cannot be undone!*\n\n"
        f"*Confirm transfer?*",
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    return CONFIRM


async def transfer_confirm(update: Update, context: CallbackContext):
    """Process confirmed transfer"""
    query = update.callback_query
    await query.answer()
    
    sender_id = query.from_user.id
    receiver = context.user_data.get('receiver')
    amount = context.user_data.get('amount')
    fee = context.user_data.get('fee', 0)
    total = context.user_data.get('total', amount + fee)
    
    # Validate session data
    if not receiver or not amount:
        await query.edit_message_text(
            f"{get_emoji('error')} ❌ *Session Expired!*\n\n"
            f"Please start over with /transfer",
            reply_markup=main_menu_inline(await Database.get_user(sender_id)),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    receiver_id = receiver['id']
    
    # Double-check balance
    sender_balance = await Database.get_balance(sender_id)
    if sender_balance < total:
        await query.edit_message_text(
            f"{get_emoji('error')} ❌ *Transfer Failed!*\n\n"
            f"Insufficient balance.\n"
            f"Your balance: `{sender_balance:.2f} ETB`\n"
            f"Required: `{total:.2f} ETB`\n\n"
            f"Please try again.",
            parse_mode='Markdown',
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
        return ConversationHandler.END
    
    try:
        # Execute transfer
        await Database.deduct_balance(sender_id, total, "transfer_out")
        await Database.add_balance(receiver_id, amount, "transfer_in")
        
        # Get updated balances
        new_sender_balance = await Database.get_balance(sender_id)
        new_receiver_balance = await Database.get_balance(receiver_id)
        
        # Success message to sender
        success_msg = (
            f"{get_emoji('success')} ✅ *TRANSFER SUCCESSFUL!*\n\n"
            f"{get_emoji('transfer')} Sent: `{amount:.2f} ETB`\n"
            f"{get_emoji('user')} To: *{receiver['name']}*\n"
            f"{get_emoji('phone')} Phone: `{receiver['phone']}`\n"
        )
        
        if fee > 0:
            success_msg += f"{get_emoji('info')} Fee: `{fee:.2f} ETB`\n"
        
        success_msg += (
            f"\n{get_emoji('money')} Your new balance: `{new_sender_balance:.2f} ETB`\n\n"
            f"Thank you for using Estif Bingo! 🎰"
        )
        
        await query.edit_message_text(
            success_msg,
            parse_mode='Markdown',
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
        
        # Notify receiver
        try:
            receiver_msg = (
                f"{get_emoji('win')} 🎉 *TRANSFER RECEIVED!* 🎉\n\n"
                f"{get_emoji('money')} Amount: `{amount:.2f} ETB`\n"
                f"{get_emoji('user')} From: *{query.from_user.username or query.from_user.first_name or 'User'}*\n"
                f"{get_emoji('money')} Your new balance: `{new_receiver_balance:.2f} ETB`\n\n"
                f"Use /balance to check your balance.\n"
                f"Use /play to start playing! 🎮"
            )
            await context.bot.send_message(
                chat_id=receiver_id,
                text=receiver_msg,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Could not notify receiver: {e}")
        
        # Log transaction
        await Database.log_game_transaction(
            sender_id, query.from_user.username or "User", "transfer_out", -amount,
            None, None, f"Transfer to {receiver['phone']}"
        )
        await Database.log_game_transaction(
            receiver_id, receiver.get('name', 'User'), "transfer_in", amount,
            None, None, f"Transfer from {query.from_user.username or 'User'}"
        )
        
        logger.info(f"✅ Transfer: {amount} ETB from {sender_id} to {receiver_id}")
        
    except ValueError as e:
        logger.error(f"Transfer value error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} ❌ *Transfer Failed*\n\n{str(e)}",
            parse_mode='Markdown',
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} ❌ *Transfer Failed*\n\n"
            f"An unexpected error occurred.\n"
            f"Please try again later.\n\n"
            f"Support: {config.SUPPORT_GROUP_LINK}",
            parse_mode='Markdown',
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
    
    # Clear session
    context.user_data.clear()
    return ConversationHandler.END


async def transfer_cancel(update: Update, context: CallbackContext):
    """Cancel transfer (callback query)"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    await query.edit_message_text(
        f"{get_emoji('warning')} ❌ *Transfer Cancelled*\n\n"
        f"You can start a new transfer anytime from the main menu.",
        parse_mode='Markdown',
        reply_markup=main_menu_inline(await Database.get_user(user_id))
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def transfer_cancel_command(update: Update, context: CallbackContext):
    """Handle /cancel command"""
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        f"{get_emoji('warning')} ❌ *Transfer Cancelled*\n\n"
        f"You can start a new transfer anytime from the main menu.\n\n"
        f"Use /transfer to start a new transfer.",
        parse_mode='Markdown',
        reply_markup=main_menu_inline(await Database.get_user(user_id))
    )
    
    context.user_data.clear()
    return ConversationHandler.END


# ==================== DUMMY HANDLERS FOR COMPATIBILITY ====================
# These are required by main.py but not used in simplified flow
async def transfer_add_amount(update: Update, context: CallbackContext):
    """Dummy handler for +10 button (not used)"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"{get_emoji('info')} Please use /transfer to start a new transfer.",
        parse_mode='Markdown'
    )


async def transfer_subtract_amount(update: Update, context: CallbackContext):
    """Dummy handler for -10 button (not used)"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"{get_emoji('info')} Please use /transfer to start a new transfer.",
        parse_mode='Markdown'
    )


# ==================== EXPORTS ====================
__all__ = [
    'transfer',
    'transfer_phone',
    'transfer_amount',
    'transfer_confirm',
    'transfer_cancel',
    'transfer_cancel_command',
    'transfer_add_amount',
    'transfer_subtract_amount',
    'PHONE_NUMBER',
    'AMOUNT',
    'CONFIRM',
]