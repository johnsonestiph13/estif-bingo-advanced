# telegram-bot/bot/handlers/transfer.py
# COMPLETE - With add/subtract amount functions

import logging
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from bot.db.database import Database
from bot.keyboards.menu import back_button, main_menu_inline
from bot.config import config
from bot.texts.emojis import get_emoji
from bot.utils import logger

# ==================== CONSTANTS ====================
PHONE_NUMBER, AMOUNT, CONFIRM = range(3)

# Transfer limits
MIN_TRANSFER_AMOUNT = config.MIN_TRANSFER
MAX_TRANSFER_AMOUNT = config.MAX_TRANSFER
DAILY_TRANSFER_LIMIT = config.TRANSFER_DAILY_LIMIT
TRANSFER_FEE_PERCENTAGE = config.TRANSFER_FEE_PERCENTAGE

# Cache for recently transferred users
_transfer_cooldown: Dict[int, datetime] = {}


# ==================== VALIDATOR CLASS ====================
class TransferValidator:
    @staticmethod
    def validate_phone(phone: str) -> bool:
        pattern = r'^(09|07)[0-9]{8}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_amount(amount: float) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "Amount must be greater than 0"
        if amount < MIN_TRANSFER_AMOUNT:
            return False, f"Minimum transfer amount is {MIN_TRANSFER_AMOUNT} ETB"
        if amount > MAX_TRANSFER_AMOUNT:
            return False, f"Maximum transfer amount is {MAX_TRANSFER_AMOUNT} ETB"
        return True, ""
    
    @staticmethod
    async def check_daily_limit(user_id: int, amount: float) -> Tuple[bool, float]:
        async with Database._pool.acquire() as conn:
            today = datetime.now().date()
            total_sent = await conn.fetchval("""
                SELECT COALESCE(SUM(ABS(amount)), 0)
                FROM game_transactions
                WHERE telegram_id = $1 AND type = 'transfer_out' AND DATE(timestamp) = $2
            """, user_id, today)
            total_sent = float(total_sent or 0)
            if total_sent + amount > DAILY_TRANSFER_LIMIT:
                return False, DAILY_TRANSFER_LIMIT - total_sent
            return True, DAILY_TRANSFER_LIMIT - (total_sent + amount)
    
    @staticmethod
    def check_cooldown(user_id: int) -> Tuple[bool, int]:
        now = datetime.now()
        last_transfer = _transfer_cooldown.get(user_id)
        if last_transfer:
            seconds_passed = (now - last_transfer).total_seconds()
            if seconds_passed < 30:
                return False, int(30 - seconds_passed)
        _transfer_cooldown[user_id] = now
        return True, 0


# ==================== MAIN HANDLERS ====================
async def transfer(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    
    message_text = (
        f"{get_emoji('transfer')} *Balance Transfer*\n\n"
        f"Transfer funds to another player instantly!\n\n"
        f"{get_emoji('info')} *Rules:*\n"
        f"• Minimum: {MIN_TRANSFER_AMOUNT} ETB\n"
        f"• Maximum: {MAX_TRANSFER_AMOUNT} ETB per transfer\n"
        f"• Daily limit: {DAILY_TRANSFER_LIMIT} ETB\n"
        f"• Fee: {TRANSFER_FEE_PERCENTAGE}%\n\n"
        f"{get_emoji('phone')} Please enter the **phone number** of the receiver:\n"
        f"Example: `0912345678` or `0712345678`\n\n"
        f"Type /cancel to cancel."
    )
    
    reply_markup = back_button("main")
    
    if query:
        await query.answer()
        await query.edit_message_text(message_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, parse_mode="Markdown", reply_markup=reply_markup)
    
    return PHONE_NUMBER


async def transfer_phone(update: Update, context: CallbackContext):
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    
    sender = await Database.get_user(user_id)
    if sender and sender.get('phone') == phone:
        await update.message.reply_text(
            f"{get_emoji('error')} You cannot transfer funds to yourself!\n\n"
            f"Please enter a different phone number or type /cancel to cancel.",
            reply_markup=back_button("transfer"), parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    if not TransferValidator.validate_phone(phone):
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid phone number format.\n\n"
            f"Please enter a valid Ethiopian phone number (09XXXXXXXX or 07XXXXXXXX)\n\n"
            f"Type /cancel to cancel.",
            reply_markup=back_button("transfer"), parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    receiver = await Database.get_user_by_phone(phone)
    if not receiver:
        await update.message.reply_text(
            f"{get_emoji('error')} User with this phone number not found.\n\n"
            f"Please try another number or type /cancel to cancel.",
            reply_markup=back_button("transfer"), parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    if not receiver.get('registered', False):
        await update.message.reply_text(
            f"{get_emoji('error')} This user has not completed registration.\n\n"
            f"Please try another number or type /cancel to cancel.",
            reply_markup=back_button("transfer"), parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    context.user_data['transfer_receiver'] = {
        'telegram_id': receiver['telegram_id'],
        'username': receiver.get('username') or receiver.get('first_name') or 'Unknown',
        'phone': phone,
    }
    
    sender_balance = await Database.get_balance(user_id)
    
    await update.message.reply_text(
        f"{get_emoji('success')} *Receiver Found!*\n\n"
        f"{get_emoji('user')} Name: *{receiver['username'] or receiver['first_name'] or 'Unknown'}*\n"
        f"{get_emoji('phone')} Phone: `{phone}`\n\n"
        f"{get_emoji('money')} *Your Balance:* `{sender_balance:.2f} ETB`\n"
        f"{get_emoji('info')} *Transfer Fee:* `{TRANSFER_FEE_PERCENTAGE}%`\n\n"
        f"Please enter the amount to transfer (minimum {MIN_TRANSFER_AMOUNT} ETB):\n\n"
        f"Type /cancel to cancel.",
        parse_mode="Markdown", reply_markup=back_button("transfer")
    )
    return AMOUNT


async def transfer_amount(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid amount. Please enter a valid number.\n\n"
            f"Type /cancel to cancel.",
            parse_mode="Markdown", reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    is_valid, error_msg = TransferValidator.validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(
            f"{get_emoji('error')} {error_msg}\n\n"
            f"Please enter a valid amount or type /cancel to cancel.",
            reply_markup=back_button("transfer"), parse_mode='Markdown'
        )
        return AMOUNT
    
    sender_balance = await Database.get_balance(user_id)
    fee = (amount * TRANSFER_FEE_PERCENTAGE / 100) if TRANSFER_FEE_PERCENTAGE > 0 else 0
    total_deduction = amount + fee
    
    if sender_balance < total_deduction:
        await update.message.reply_text(
            f"{get_emoji('error')} *Insufficient Balance*\n\n"
            f"Your balance: `{sender_balance:.2f} ETB`\n"
            f"Total needed: `{total_deduction:.2f} ETB`\n\n"
            f"Please enter a smaller amount or type /cancel to cancel.",
            parse_mode="Markdown", reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    within_limit, remaining = await TransferValidator.check_daily_limit(user_id, amount)
    if not within_limit:
        await update.message.reply_text(
            f"{get_emoji('error')} *Daily Transfer Limit Reached*\n\n"
            f"Remaining today: {remaining:.2f} ETB\n"
            f"Requested: {amount:.2f} ETB\n\n"
            f"Type /cancel to cancel.",
            parse_mode="Markdown", reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    can_transfer, wait_seconds = TransferValidator.check_cooldown(user_id)
    if not can_transfer:
        await update.message.reply_text(
            f"{get_emoji('clock')} *Please wait {wait_seconds} seconds before another transfer*\n\n"
            f"Type /cancel to cancel.",
            parse_mode="Markdown", reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    context.user_data['transfer_amount'] = amount
    context.user_data['transfer_fee'] = fee
    
    receiver = context.user_data['transfer_receiver']
    sender = await Database.get_user(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton(f"{get_emoji('success')} Confirm", callback_data="transfer_confirm"),
            InlineKeyboardButton(f"{get_emoji('error')} Cancel", callback_data="transfer_cancel")
        ],
        [
            InlineKeyboardButton(f"{get_emoji('plus')} +10 ETB", callback_data="transfer_add_10"),
            InlineKeyboardButton(f"{get_emoji('minus')} -10 ETB", callback_data="transfer_sub_10")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{get_emoji('question')} *Transfer Confirmation*\n\n"
        f"{get_emoji('user')} *From:* {sender.get('username') or 'You'}\n"
        f"{get_emoji('user')} *To:* {receiver['username']}\n"
        f"{get_emoji('phone')} *Phone:* `{receiver['phone']}`\n"
        f"{get_emoji('money')} *Amount:* `{amount:.2f} ETB`\n"
        f"{get_emoji('info')} *Fee:* `{fee:.2f} ETB`\n"
        f"{get_emoji('money')} *Total:* `{total_deduction:.2f} ETB`\n\n"
        f"{get_emoji('warning')} *This action cannot be undone!*\n\n"
        f"Confirm transfer?",
        parse_mode="Markdown", reply_markup=reply_markup
    )
    return CONFIRM


async def transfer_confirm(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    sender_id = query.from_user.id
    receiver = context.user_data.get('transfer_receiver')
    amount = context.user_data.get('transfer_amount')
    fee = context.user_data.get('transfer_fee', 0)
    
    if not receiver or not amount:
        await query.edit_message_text(
            f"{get_emoji('error')} Session expired. Please start over.",
            reply_markup=main_menu_inline(await Database.get_user(sender_id)), parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    receiver_id = receiver['telegram_id']
    sender_balance = await Database.get_balance(sender_id)
    total_deduction = amount + fee
    
    if sender_balance < total_deduction:
        await query.edit_message_text(
            f"{get_emoji('error')} *Transfer Failed - Insufficient Balance*\n\n"
            f"Your balance: `{sender_balance:.2f} ETB`\n"
            f"Required: `{total_deduction:.2f} ETB`",
            parse_mode="Markdown", reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
        return ConversationHandler.END
    
    try:
        await Database.deduct_balance(sender_id, total_deduction, "transfer_out")
        await Database.add_balance(receiver_id, amount, "transfer_in")
        
        new_sender_balance = await Database.get_balance(sender_id)
        new_receiver_balance = await Database.get_balance(receiver_id)
        
        success_message = (
            f"{get_emoji('success')} *Transfer Successful!*\n\n"
            f"Sent: `{amount:.2f} ETB` to *{receiver['username']}*\n"
            f"Your new balance: `{new_sender_balance:.2f} ETB`"
        )
        
        await query.edit_message_text(
            success_message, parse_mode="Markdown",
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
        
        try:
            await context.bot.send_message(
                chat_id=receiver_id,
                text=f"{get_emoji('win')} *Transfer Received!*\n\nAmount: `{amount:.2f} ETB`\nFrom: {query.from_user.username or 'User'}\nNew balance: `{new_receiver_balance:.2f} ETB`",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify receiver: {e}")
        
        logger.info(f"Transfer: {amount} ETB from {sender_id} to {receiver_id}")
        
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} Transfer failed. Please try again later.",
            parse_mode="Markdown", reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
    
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    
    return ConversationHandler.END


async def transfer_cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    
    if query:
        await query.answer()
        await query.edit_message_text(
            f"{get_emoji('warning')} Transfer cancelled.",
            parse_mode="Markdown", reply_markup=main_menu_inline(await Database.get_user(user_id))
        )
    else:
        await update.message.reply_text(
            f"{get_emoji('warning')} Transfer cancelled.",
            parse_mode="Markdown", reply_markup=main_menu_inline(await Database.get_user(user_id))
        )
    
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    
    return ConversationHandler.END


async def transfer_cancel_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"{get_emoji('warning')} Transfer cancelled.",
        parse_mode="Markdown", reply_markup=main_menu_inline(await Database.get_user(user_id))
    )
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    return ConversationHandler.END


async def transfer_add_amount(update: Update, context: CallbackContext):
    """Add 10 ETB to amount"""
    query = update.callback_query
    await query.answer()
    
    current_amount = context.user_data.get('transfer_amount', 0)
    new_amount = current_amount + 10
    
    if new_amount > MAX_TRANSFER_AMOUNT:
        await query.answer(f"Maximum is {MAX_TRANSFER_AMOUNT} ETB!", show_alert=True)
        return
    
    context.user_data['transfer_amount'] = new_amount
    await update_transfer_confirmation(query, context)


async def transfer_subtract_amount(update: Update, context: CallbackContext):
    """Subtract 10 ETB from amount"""
    query = update.callback_query
    await query.answer()
    
    current_amount = context.user_data.get('transfer_amount', 0)
    new_amount = current_amount - 10
    
    if new_amount < MIN_TRANSFER_AMOUNT:
        await query.answer(f"Minimum is {MIN_TRANSFER_AMOUNT} ETB!", show_alert=True)
        return
    
    context.user_data['transfer_amount'] = new_amount
    await update_transfer_confirmation(query, context)


async def update_transfer_confirmation(query, context):
    """Update the confirmation message with new amount"""
    sender_id = query.from_user.id
    receiver = context.user_data.get('transfer_receiver')
    amount = context.user_data.get('transfer_amount', 0)
    fee = (amount * TRANSFER_FEE_PERCENTAGE / 100) if TRANSFER_FEE_PERCENTAGE > 0 else 0
    total_deduction = amount + fee
    sender = await Database.get_user(sender_id)
    
    keyboard = [
        [
            InlineKeyboardButton(f"{get_emoji('success')} Confirm", callback_data="transfer_confirm"),
            InlineKeyboardButton(f"{get_emoji('error')} Cancel", callback_data="transfer_cancel")
        ],
        [
            InlineKeyboardButton(f"{get_emoji('plus')} +10 ETB", callback_data="transfer_add_10"),
            InlineKeyboardButton(f"{get_emoji('minus')} -10 ETB", callback_data="transfer_sub_10")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{get_emoji('question')} *Transfer Confirmation*\n\n"
        f"{get_emoji('user')} *To:* {receiver['username']}\n"
        f"{get_emoji('money')} *Amount:* `{amount:.2f} ETB`\n"
        f"{get_emoji('info')} *Fee:* `{fee:.2f} ETB`\n"
        f"{get_emoji('money')} *Total:* `{total_deduction:.2f} ETB`\n\n"
        f"{get_emoji('warning')} Confirm transfer?",
        parse_mode="Markdown", reply_markup=reply_markup
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