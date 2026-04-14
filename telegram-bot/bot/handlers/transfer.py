# telegram-bot/bot/handlers/transfer.py
# ULTRA OPTIMIZED - Complete Transfer Handler with Full Features

import logging
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from bot.db.database import Database
from bot.keyboards.menu import back_button, main_menu_inline
from bot.config import config
from bot.texts.emojis import get_emoji
from bot.utils import logger, log_transfer

# ==================== CONSTANTS ====================
PHONE_NUMBER, AMOUNT, CONFIRM = range(3)

# Transfer limits
MIN_TRANSFER_AMOUNT = config.MIN_TRANSFER
MAX_TRANSFER_AMOUNT = config.MAX_TRANSFER
DAILY_TRANSFER_LIMIT = config.TRANSFER_DAILY_LIMIT
TRANSFER_FEE_PERCENTAGE = config.TRANSFER_FEE_PERCENTAGE

# Cache for recently transferred users (prevent spam)
_transfer_cooldown: Dict[int, datetime] = {}


# ==================== VALIDATOR CLASS ====================
class TransferValidator:
    """Validate transfer requests"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate Ethiopian phone number"""
        pattern = r'^(09|07)[0-9]{8}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_amount(amount: float) -> Tuple[bool, str]:
        """Validate transfer amount"""
        if amount <= 0:
            return False, "Amount must be greater than 0"
        if amount < MIN_TRANSFER_AMOUNT:
            return False, f"Minimum transfer amount is {MIN_TRANSFER_AMOUNT} ETB"
        if amount > MAX_TRANSFER_AMOUNT:
            return False, f"Maximum transfer amount is {MAX_TRANSFER_AMOUNT} ETB"
        return True, ""
    
    @staticmethod
    async def check_daily_limit(user_id: int, amount: float) -> Tuple[bool, float]:
        """Check daily transfer limit"""
        async with Database._pool.acquire() as conn:
            today = datetime.now().date()
            total_sent = await conn.fetchval("""
                SELECT COALESCE(SUM(ABS(amount)), 0)
                FROM game_transactions
                WHERE telegram_id = $1 
                AND type = 'transfer_out'
                AND DATE(timestamp) = $2
            """, user_id, today)
            
            total_sent = float(total_sent or 0)
            if total_sent + amount > DAILY_TRANSFER_LIMIT:
                remaining = DAILY_TRANSFER_LIMIT - total_sent
                return False, remaining
            return True, DAILY_TRANSFER_LIMIT - (total_sent + amount)
    
    @staticmethod
    def check_cooldown(user_id: int) -> Tuple[bool, int]:
        """Prevent spam transfers (30 second cooldown)"""
        now = datetime.now()
        last_transfer = _transfer_cooldown.get(user_id)
        
        if last_transfer:
            seconds_passed = (now - last_transfer).total_seconds()
            if seconds_passed < 30:
                return False, int(30 - seconds_passed)
        
        _transfer_cooldown[user_id] = now
        return True, 0


# ==================== MAIN HANDLER ====================
async def transfer(update: Update, context: CallbackContext):
    """Handle transfer button click - Start transfer flow"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Clear any existing transfer data
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
        await query.edit_message_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    return PHONE_NUMBER


async def transfer_phone(update: Update, context: CallbackContext):
    """Get receiver's phone number"""
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Check if user is trying to transfer to themselves
    sender = await Database.get_user(user_id)
    if sender and sender.get('phone') == phone:
        await update.message.reply_text(
            f"{get_emoji('error')} You cannot transfer funds to yourself!\n\n"
            f"Please enter a different phone number or type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Validate phone number format
    if not TransferValidator.validate_phone(phone):
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid phone number format.\n\n"
            f"Please enter a valid Ethiopian phone number:\n"
            f"• Starting with 09 (e.g., 0912345678)\n"
            f"• Or starting with 07 (e.g., 0712345678)\n\n"
            f"Type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Check if receiver exists
    receiver = await Database.get_user_by_phone(phone)
    if not receiver:
        await update.message.reply_text(
            f"{get_emoji('error')} User with this phone number not found.\n\n"
            f"Make sure the user has registered with their phone number.\n\n"
            f"Please try another number or type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Check if receiver is active/registered
    if not receiver.get('registered', False):
        await update.message.reply_text(
            f"{get_emoji('error')} This user has not completed registration.\n\n"
            f"They need to register first before receiving transfers.\n\n"
            f"Please try another number or type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Store receiver info in context
    context.user_data['transfer_receiver'] = {
        'telegram_id': receiver['telegram_id'],
        'username': receiver.get('username') or receiver.get('first_name') or 'Unknown',
        'phone': phone,
    }
    
    # Get sender's balance
    sender_balance = await Database.get_balance(user_id)
    
    await update.message.reply_text(
        f"{get_emoji('success')} *Receiver Found!*\n\n"
        f"{get_emoji('user')} Name: *{receiver['username'] or receiver['first_name'] or 'Unknown'}*\n"
        f"{get_emoji('phone')} Phone: `{phone}`\n\n"
        f"{get_emoji('money')} *Your Balance:* `{sender_balance:.2f} ETB`\n"
        f"{get_emoji('info')} *Transfer Fee:* `{TRANSFER_FEE_PERCENTAGE}%`\n\n"
        f"Please enter the amount to transfer (minimum {MIN_TRANSFER_AMOUNT} ETB):\n\n"
        f"Type /cancel to cancel.",
        parse_mode="Markdown",
        reply_markup=back_button("transfer")
    )
    return AMOUNT


async def transfer_amount(update: Update, context: CallbackContext):
    """Get amount to transfer"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Parse amount
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid amount. Please enter a valid number.\n\n"
            f"Examples: `10`, `50.50`, `100`\n\n"
            f"Type /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Validate amount
    is_valid, error_msg = TransferValidator.validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(
            f"{get_emoji('error')} {error_msg}\n\n"
            f"Minimum: {MIN_TRANSFER_AMOUNT} ETB\n"
            f"Maximum: {MAX_TRANSFER_AMOUNT} ETB\n\n"
            f"Please enter a valid amount or type /cancel to cancel.",
            reply_markup=back_button("transfer"),
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Check sender's balance
    sender_balance = await Database.get_balance(user_id)
    
    # Calculate fee
    fee = (amount * TRANSFER_FEE_PERCENTAGE / 100) if TRANSFER_FEE_PERCENTAGE > 0 else 0
    total_deduction = amount + fee
    
    if sender_balance < total_deduction:
        await update.message.reply_text(
            f"{get_emoji('error')} *Insufficient Balance*\n\n"
            f"{get_emoji('money')} Your balance: `{sender_balance:.2f} ETB`\n"
            f"{get_emoji('transfer')} Transfer amount: `{amount:.2f} ETB`\n"
            f"{get_emoji('info')} Fee: `{fee:.2f} ETB`\n"
            f"{get_emoji('money')} Total deduction: `{total_deduction:.2f} ETB`\n\n"
            f"Please enter a smaller amount or use /deposit to add funds.\n\n"
            f"Type /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Check daily limit
    within_limit, remaining = await TransferValidator.check_daily_limit(user_id, amount)
    if not within_limit:
        await update.message.reply_text(
            f"{get_emoji('error')} *Daily Transfer Limit Reached*\n\n"
            f"Daily limit: {DAILY_TRANSFER_LIMIT} ETB\n"
            f"Remaining today: {remaining:.2f} ETB\n"
            f"Requested: {amount:.2f} ETB\n\n"
            f"Please try a smaller amount or try again tomorrow.\n\n"
            f"Type /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Check cooldown
    can_transfer, wait_seconds = TransferValidator.check_cooldown(user_id)
    if not can_transfer:
        await update.message.reply_text(
            f"{get_emoji('clock')} *Please wait before another transfer*\n\n"
            f"You can make another transfer in {wait_seconds} seconds.\n\n"
            f"Type /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Store amount in context
    context.user_data['transfer_amount'] = amount
    context.user_data['transfer_fee'] = fee
    
    receiver = context.user_data['transfer_receiver']
    sender = await Database.get_user(user_id)
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton(f"{get_emoji('success')} Confirm Transfer", callback_data="transfer_confirm"),
            InlineKeyboardButton(f"{get_emoji('error')} Cancel", callback_data="transfer_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{get_emoji('question')} *Transfer Confirmation*\n\n"
        f"{get_emoji('user')} *From:* {sender.get('username') or sender.get('first_name') or 'You'}\n"
        f"{get_emoji('user')} *To:* {receiver['username'] or 'Unknown'}\n"
        f"{get_emoji('phone')} *Receiver Phone:* `{receiver['phone']}`\n"
        f"{get_emoji('money')} *Amount:* `{amount:.2f} ETB`\n"
        f"{get_emoji('info')} *Fee:* `{fee:.2f} ETB`\n"
        f"{get_emoji('money')} *Total Deduction:* `{total_deduction:.2f} ETB`\n\n"
        f"{get_emoji('warning')} *This action cannot be undone!*\n\n"
        f"Please confirm the transfer.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return CONFIRM


async def transfer_confirm(update: Update, context: CallbackContext):
    """Confirm and process the transfer"""
    query = update.callback_query
    await query.answer()
    
    sender_id = query.from_user.id
    receiver = context.user_data.get('transfer_receiver')
    amount = context.user_data.get('transfer_amount')
    fee = context.user_data.get('transfer_fee', 0)
    
    if not receiver or not amount:
        await query.edit_message_text(
            f"{get_emoji('error')} Transfer session expired. Please start over.\n\n"
            f"Use /start and click the Transfer button.",
            reply_markup=main_menu_inline(await Database.get_user(sender_id)),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    receiver_id = receiver['telegram_id']
    
    # Double-check balance before processing
    sender_balance = await Database.get_balance(sender_id)
    total_deduction = amount + fee
    
    if sender_balance < total_deduction:
        await query.edit_message_text(
            f"{get_emoji('error')} *Transfer Failed - Insufficient Balance*\n\n"
            f"Your balance: `{sender_balance:.2f} ETB`\n"
            f"Required: `{total_deduction:.2f} ETB`\n\n"
            f"Please try again with a smaller amount.",
            parse_mode="Markdown",
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
        return ConversationHandler.END
    
    # Process the transfer
    try:
        # Deduct from sender
        await Database.deduct_balance(sender_id, total_deduction, "transfer_out")
        
        # Add to receiver
        await Database.add_balance(receiver_id, amount, "transfer_in")
        
        # Get updated balances
        new_sender_balance = await Database.get_balance(sender_id)
        new_receiver_balance = await Database.get_balance(receiver_id)
        
        # Send success message to sender
        success_message = (
            f"{get_emoji('success')} *Transfer Successful!*\n\n"
            f"{get_emoji('transfer')} Sent: `{amount:.2f} ETB` to *{receiver['username'] or 'Unknown'}*\n"
            f"{get_emoji('phone')} Receiver: `{receiver['phone']}`\n"
        )
        
        if fee > 0:
            success_message += f"{get_emoji('info')} Fee: `{fee:.2f} ETB`\n"
        
        success_message += (
            f"{get_emoji('money')} Your new balance: `{new_sender_balance:.2f} ETB`\n\n"
            f"Thank you for using Estif Bingo! 🎰"
        )
        
        await query.edit_message_text(
            success_message,
            parse_mode="Markdown",
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
        
        # Notify receiver
        try:
            receiver_message = (
                f"{get_emoji('win')} *You received a transfer!* {get_emoji('win')}\n\n"
                f"{get_emoji('money')} Amount: `{amount:.2f} ETB`\n"
                f"{get_emoji('user')} From: *{query.from_user.username or query.from_user.first_name or 'User'}*\n"
                f"{get_emoji('money')} Your new balance: `{new_receiver_balance:.2f} ETB`\n\n"
                f"Use /balance to check your balance.\n"
                f"Use /play to start playing! 🎮"
            )
            
            await context.bot.send_message(
                chat_id=receiver_id,
                text=receiver_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify receiver {receiver_id}: {e}")
        
        # Log transaction
        await Database.log_game_transaction(
            sender_id, 
            query.from_user.username or "User", 
            "transfer_out", 
            -amount, 
            None, 
            None, 
            f"Transfer to {receiver['phone']}"
        )
        await Database.log_game_transaction(
            receiver_id, 
            receiver.get('username', 'User'), 
            "transfer_in", 
            amount, 
            None, 
            None, 
            f"Transfer from {query.from_user.username or 'User'}"
        )
        
        log_transfer(sender_id, receiver_id, amount, "completed")
        logger.info(f"Transfer: {amount} ETB from {sender_id} to {receiver_id}")
        
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} *An error occurred during transfer.*\n\n"
            f"Please try again later. If the problem persists, contact support.\n\n"
            f"Support: {config.SUPPORT_GROUP_LINK}",
            parse_mode="Markdown",
            reply_markup=main_menu_inline(await Database.get_user(sender_id))
        )
    
    # Clear context data
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    
    return ConversationHandler.END


async def transfer_cancel(update: Update, context: CallbackContext):
    """Cancel the transfer"""
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    
    if query:
        await query.answer()
        await query.edit_message_text(
            f"{get_emoji('warning')} *Transfer Cancelled*\n\n"
            f"You can start a new transfer anytime from the main menu.",
            parse_mode="Markdown",
            reply_markup=main_menu_inline(await Database.get_user(user_id))
        )
    else:
        await update.message.reply_text(
            f"{get_emoji('warning')} *Transfer Cancelled*\n\n"
            f"You can start a new transfer anytime from the main menu.",
            parse_mode="Markdown",
            reply_markup=main_menu_inline(await Database.get_user(user_id))
        )
    
    # Clear context data
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    
    return ConversationHandler.END


async def transfer_cancel_command(update: Update, context: CallbackContext):
    """Handle /cancel command during transfer"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"{get_emoji('warning')} *Transfer Cancelled*\n\n"
        f"You can start a new transfer anytime from the main menu.\n\n"
        f"Use /transfer to start a new transfer.",
        parse_mode="Markdown",
        reply_markup=main_menu_inline(await Database.get_user(user_id))
    )
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    return ConversationHandler.END


# ==================== EXPORTS ====================
__all__ = [
    'transfer',
    'transfer_phone',
    'transfer_amount',
    'transfer_confirm',
    'transfer_cancel',
    'transfer_cancel_command',
    'PHONE_NUMBER',
    'AMOUNT',
    'CONFIRM',
]