# telegram-bot/bot/handlers/transfer.py
# ENHANCED VERSION - With additional features and optimizations

import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from bot.db.database import Database
from bot.keyboards.menu import back_button, main_menu
from bot.config import Config

logger = logging.getLogger(__name__)

# Conversation states
PHONE_NUMBER, AMOUNT, CONFIRM = range(3)

# Transfer limits (can be moved to config)
MIN_TRANSFER_AMOUNT = 1
MAX_TRANSFER_AMOUNT = 10000
DAILY_TRANSFER_LIMIT = 50000
TRANSFER_FEE_PERCENTAGE = 0  # 0% fee (can be changed)

# Cache for recently transferred users (prevent spam)
_transfer_cooldown = {}

class TransferValidator:
    """Validate transfer requests"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate Ethiopian phone number"""
        # Supports 09XXXXXXXX and 07XXXXXXXX formats
        pattern = r'^(09|07)[0-9]{8}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_amount(amount: float) -> tuple[bool, str]:
        """Validate transfer amount"""
        if amount <= 0:
            return False, "Amount must be greater than 0"
        if amount < MIN_TRANSFER_AMOUNT:
            return False, f"Minimum transfer amount is {MIN_TRANSFER_AMOUNT} ETB"
        if amount > MAX_TRANSFER_AMOUNT:
            return False, f"Maximum transfer amount per transaction is {MAX_TRANSFER_AMOUNT} ETB"
        return True, ""
    
    @staticmethod
    async def check_daily_limit(user_id: int, amount: float) -> tuple[bool, float]:
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
    def check_cooldown(user_id: int) -> tuple[bool, int]:
        """Prevent spam transfers (30 second cooldown)"""
        now = datetime.now()
        last_transfer = _transfer_cooldown.get(user_id)
        
        if last_transfer:
            seconds_passed = (now - last_transfer).total_seconds()
            if seconds_passed < 30:
                return False, int(30 - seconds_passed)
        
        _transfer_cooldown[user_id] = now
        return True, 0

async def transfer(update: Update, context: CallbackContext):
    """Handle transfer button click - Enhanced version"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Clear any existing transfer data
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    
    message_text = (
        "💸 *Balance Transfer*\n\n"
        "Transfer funds to another player instantly!\n\n"
        f"📋 *Rules:*\n"
        f"• Minimum: {MIN_TRANSFER_AMOUNT} ETB\n"
        f"• Maximum: {MAX_TRANSFER_AMOUNT} ETB per transfer\n"
        f"• Daily limit: {DAILY_TRANSFER_LIMIT} ETB\n"
        f"• Fee: {TRANSFER_FEE_PERCENTAGE}%\n\n"
        "Please enter the **phone number** of the receiver:\n"
        "Example: `0912345678` or `0712345678`\n\n"
        "Type /cancel to cancel."
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
    """Get receiver's phone number - Enhanced with better validation"""
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Check if user is trying to transfer to themselves
    sender = await Database.get_user(user_id)
    if sender and sender.get('phone') == phone:
        await update.message.reply_text(
            "❌ You cannot transfer funds to yourself!\n\n"
            "Please enter a different phone number or type /cancel to cancel.",
            reply_markup=back_button("transfer")
        )
        return PHONE_NUMBER
    
    # Validate phone number format
    if not TransferValidator.validate_phone(phone):
        await update.message.reply_text(
            "❌ Invalid phone number format.\n\n"
            "Please enter a valid Ethiopian phone number:\n"
            "• Starting with 09 (e.g., 0912345678)\n"
            "• Or starting with 07 (e.g., 0712345678)\n\n"
            "Type /cancel to cancel.",
            reply_markup=back_button("transfer")
        )
        return PHONE_NUMBER
    
    # Check if receiver exists
    receiver = await Database.get_user_by_phone(phone)
    if not receiver:
        await update.message.reply_text(
            "❌ User with this phone number not found.\n\n"
            "Make sure the user has registered with their phone number.\n\n"
            "Possible reasons:\n"
            "• User hasn't registered yet\n"
            "• Phone number is incorrect\n"
            "• User account is inactive\n\n"
            "Please try another number or type /cancel to cancel.",
            reply_markup=back_button("transfer")
        )
        return PHONE_NUMBER
    
    # Check if receiver is active/registered
    if not receiver.get('registered', False):
        await update.message.reply_text(
            "❌ This user has not completed registration.\n\n"
            "They need to register first before receiving transfers.\n\n"
            "Please try another number or type /cancel to cancel.",
            reply_markup=back_button("transfer")
        )
        return PHONE_NUMBER
    
    # Store receiver info in context
    context.user_data['transfer_receiver'] = {
        'telegram_id': receiver['telegram_id'],
        'username': receiver.get('username') or receiver.get('first_name') or 'Unknown',
        'phone': phone,
        'registered_at': receiver.get('created_at')
    }
    
    # Get sender's balance
    sender_balance = await Database.get_balance(user_id)
    
    # Calculate max possible with fee
    fee = (sender_balance * TRANSFER_FEE_PERCENTAGE / 100) if TRANSFER_FEE_PERCENTAGE > 0 else 0
    max_send = sender_balance - fee
    
    await update.message.reply_text(
        f"✅ *Receiver Found!*\n\n"
        f"👤 Name: *{receiver['username'] or receiver['first_name'] or 'Unknown'}*\n"
        f"📱 Phone: `{phone}`\n"
        f"🆔 ID: `{receiver['telegram_id']}`\n\n"
        f"💰 *Your Balance:* `{sender_balance:.2f} ETB`\n"
        f"💸 *Transfer Fee:* `{TRANSFER_FEE_PERCENTAGE}%`\n"
        f"📊 *Max you can send:* `{max_send:.2f} ETB`\n\n"
        f"Please enter the amount to transfer (minimum {MIN_TRANSFER_AMOUNT} ETB):\n\n"
        f"💡 *Quick amounts:*\n"
        f"• 10 ETB • 50 ETB • 100 ETB • 500 ETB • 1000 ETB\n\n"
        f"Type /cancel to cancel.",
        parse_mode="Markdown",
        reply_markup=back_button("transfer")
    )
    return AMOUNT

async def transfer_amount(update: Update, context: CallbackContext):
    """Get amount to transfer - Enhanced with validation"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Check for quick amount buttons
    quick_amounts = {'10': 10, '50': 50, '100': 100, '500': 500, '1000': 1000}
    if text in quick_amounts:
        amount = quick_amounts[text]
    else:
        try:
            amount = float(text)
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a valid number.\n\n"
                "Examples: `10`, `50.50`, `100`\n\n"
                "Or use quick amounts: 10, 50, 100, 500, 1000\n\n"
                "Type /cancel to cancel.",
                parse_mode="Markdown",
                reply_markup=back_button("transfer")
            )
            return AMOUNT
    
    # Validate amount
    is_valid, error_msg = TransferValidator.validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {error_msg}\n\n"
            f"Minimum: {MIN_TRANSFER_AMOUNT} ETB\n"
            f"Maximum: {MAX_TRANSFER_AMOUNT} ETB per transfer\n\n"
            f"Please enter a valid amount or type /cancel to cancel.",
            reply_markup=back_button("transfer")
        )
        return AMOUNT
    
    # Check sender's balance
    sender_balance = await Database.get_balance(user_id)
    
    # Calculate fee
    fee = (amount * TRANSFER_FEE_PERCENTAGE / 100) if TRANSFER_FEE_PERCENTAGE > 0 else 0
    total_deduction = amount + fee
    
    if sender_balance < total_deduction:
        await update.message.reply_text(
            f"❌ *Insufficient Balance*\n\n"
            f"💰 Your balance: `{sender_balance:.2f} ETB`\n"
            f"💸 Transfer amount: `{amount:.2f} ETB`\n"
            f"📊 Fee ({TRANSFER_FEE_PERCENTAGE}%): `{fee:.2f} ETB`\n"
            f"💳 Total deduction: `{total_deduction:.2f} ETB`\n"
            f"📉 Shortfall: `{total_deduction - sender_balance:.2f} ETB`\n\n"
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
            f"❌ *Daily Transfer Limit Reached*\n\n"
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
            f"⏰ *Please wait before another transfer*\n\n"
            f"You can make another transfer in {wait_seconds} seconds.\n\n"
            f"This helps prevent spam and errors.\n\n"
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
    
    # Create confirmation keyboard with quick actions
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm Transfer", callback_data="transfer_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="transfer_cancel")
        ],
        [
            InlineKeyboardButton("➕ Add 10 ETB", callback_data="transfer_add_10"),
            InlineKeyboardButton("➖ Subtract 10 ETB", callback_data="transfer_sub_10")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Calculate what receiver gets (after fee if any)
    receiver_gets = amount  # No fee deduction from receiver side
    
    await update.message.reply_text(
        f"📋 *Transfer Confirmation*\n\n"
        f"👤 *From:* {sender.get('username') or sender.get('first_name') or 'You'}\n"
        f"👤 *To:* {receiver['username'] or 'Unknown'}\n"
        f"📱 *Receiver Phone:* `{receiver['phone']}`\n"
        f"💰 *Amount:* `{amount:.2f} ETB`\n"
        f"💸 *Fee ({TRANSFER_FEE_PERCENTAGE}%):* `{fee:.2f} ETB`\n"
        f"💳 *Total Deduction:* `{total_deduction:.2f} ETB`\n"
        f"🎯 *Receiver Gets:* `{receiver_gets:.2f} ETB`\n\n"
        f"📊 *Your Balance After:* `{sender_balance - total_deduction:.2f} ETB`\n\n"
        f"⚠️ *This action cannot be undone!*\n\n"
        f"Please confirm the transfer.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return CONFIRM

async def transfer_confirm(update: Update, context: CallbackContext):
    """Confirm and process the transfer - Enhanced with better logging"""
    query = update.callback_query
    await query.answer()
    
    sender_id = query.from_user.id
    receiver = context.user_data.get('transfer_receiver')
    amount = context.user_data.get('transfer_amount')
    fee = context.user_data.get('transfer_fee', 0)
    
    if not receiver or not amount:
        await query.edit_message_text(
            "❌ Transfer session expired. Please start over.\n\n"
            "Use /start and click the Transfer button.",
            reply_markup=main_menu(await Database.get_user(sender_id))
        )
        return ConversationHandler.END
    
    receiver_id = receiver['telegram_id']
    
    # Double-check balance before processing
    sender_balance = await Database.get_balance(sender_id)
    total_deduction = amount + fee
    
    if sender_balance < total_deduction:
        await query.edit_message_text(
            f"❌ *Transfer Failed - Insufficient Balance*\n\n"
            f"Your balance changed. Current balance: `{sender_balance:.2f} ETB`\n"
            f"Required: `{total_deduction:.2f} ETB`\n\n"
            f"Please try again with a smaller amount.",
            parse_mode="Markdown",
            reply_markup=main_menu(await Database.get_user(sender_id))
        )
        return ConversationHandler.END
    
    # Process the transfer with transaction safety
    try:
        async with Database._pool.acquire() as conn:
            async with conn.transaction():
                # Deduct from sender
                await Database.deduct_balance(sender_id, total_deduction, "transfer_out")
                
                # Add to receiver (full amount, fee is kept by system if any)
                await Database.add_balance(receiver_id, amount, "transfer_in")
                
                # If there's a fee, log it as system revenue
                if fee > 0:
                    await Database.log_game_transaction(
                        sender_id,
                        query.from_user.username or "User",
                        "transfer_fee",
                        -fee,
                        None,
                        None,
                        f"Transfer fee for {amount} ETB to {receiver['phone']}"
                    )
        
        # Get updated balances
        new_sender_balance = await Database.get_balance(sender_id)
        new_receiver_balance = await Database.get_balance(receiver_id)
        
        # Send success message to sender
        success_message = (
            f"✅ *Transfer Successful!*\n\n"
            f"💸 Sent: `{amount:.2f} ETB` to *{receiver['username'] or 'Unknown'}*\n"
            f"📱 Receiver Phone: `{receiver['phone']}`\n"
        )
        
        if fee > 0:
            success_message += f"💸 Fee ({TRANSFER_FEE_PERCENTAGE}%): `{fee:.2f} ETB`\n"
        
        success_message += (
            f"💰 Your new balance: `{new_sender_balance:.2f} ETB`\n"
            f"📅 Transaction ID: `{int(datetime.now().timestamp())}`\n\n"
            f"Thank you for using Estif Bingo! 🎰"
        )
        
        await query.edit_message_text(
            success_message,
            parse_mode="Markdown",
            reply_markup=main_menu(await Database.get_user(sender_id))
        )
        
        # Notify receiver with fancy message
        try:
            receiver_message = (
                f"🎉 *You received a transfer!* 🎉\n\n"
                f"💰 Amount: `{amount:.2f} ETB`\n"
                f"👤 From: *{query.from_user.username or query.from_user.first_name or 'User'}*\n"
                f"💳 Your new balance: `{new_receiver_balance:.2f} ETB`\n\n"
                f"Use /balance to check your balance.\n"
                f"Use /play to start playing! 🎮"
            )
            
            # Try to get sender's username for nicer display
            sender_user = await Database.get_user(sender_id)
            if sender_user and sender_user.get('username'):
                receiver_message = receiver_message.replace(
                    'From: *User*', 
                    f'From: *@{sender_user["username"]}*'
                )
            
            await context.bot.send_message(
                chat_id=receiver_id,
                text=receiver_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify receiver {receiver_id}: {e}")
        
        # Log transactions with detailed info
        await Database.log_game_transaction(
            sender_id, 
            query.from_user.username or "User", 
            "transfer_out", 
            -amount, 
            None, 
            None, 
            f"Transfer to {receiver['phone']} (User: {receiver_id})"
        )
        await Database.log_game_transaction(
            receiver_id, 
            receiver.get('username', 'User'), 
            "transfer_in", 
            amount, 
            None, 
            None, 
            f"Transfer from {query.from_user.username or 'User'} (ID: {sender_id})"
        )
        
        logger.info(f"Transfer: {amount} ETB from {sender_id} to {receiver_id}")
        
    except ValueError as e:
        await query.edit_message_text(
            f"❌ *Transfer Failed*\n\n{str(e)}\n\n"
            f"Please check your balance and try again.",
            parse_mode="Markdown",
            reply_markup=main_menu(await Database.get_user(sender_id))
        )
        logger.error(f"Transfer value error: {e}")
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        await query.edit_message_text(
            "❌ *An error occurred during transfer.*\n\n"
            "Please try again later. If the problem persists, contact support.\n\n"
            f"Support: {Config.SUPPORT_GROUP_LINK}",
            parse_mode="Markdown",
            reply_markup=main_menu(await Database.get_user(sender_id))
        )
    
    # Clear context data
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    
    return ConversationHandler.END

async def transfer_cancel(update: Update, context: CallbackContext):
    """Cancel the transfer - Enhanced"""
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    
    if query:
        await query.answer()
        await query.edit_message_text(
            "❌ *Transfer Cancelled*\n\n"
            "You can start a new transfer anytime from the main menu.\n\n"
            "Need help? Contact our support team.",
            parse_mode="Markdown",
            reply_markup=main_menu(await Database.get_user(user_id))
        )
    else:
        await update.message.reply_text(
            "❌ *Transfer Cancelled*\n\n"
            "You can start a new transfer anytime from the main menu.",
            parse_mode="Markdown",
            reply_markup=main_menu(await Database.get_user(user_id))
        )
    
    # Clear context data
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    
    return ConversationHandler.END

async def transfer_cancel_command(update: Update, context: CallbackContext):
    """Handle /cancel command during transfer"""
    await update.message.reply_text(
        "❌ *Transfer Cancelled*\n\n"
        "You can start a new transfer anytime from the main menu.\n\n"
        "Use /transfer to start a new transfer.",
        parse_mode="Markdown",
        reply_markup=main_menu(await Database.get_user(update.effective_user.id))
    )
    context.user_data.pop('transfer_receiver', None)
    context.user_data.pop('transfer_amount', None)
    context.user_data.pop('transfer_fee', None)
    return ConversationHandler.END

async def transfer_add_amount(update: Update, context: CallbackContext):
    """Add to amount (callback for +10 button)"""
    query = update.callback_query
    await query.answer()
    
    current_amount = context.user_data.get('transfer_amount', 0)
    new_amount = current_amount + 10
    
    if new_amount > MAX_TRANSFER_AMOUNT:
        await query.answer(f"Maximum is {MAX_TRANSFER_AMOUNT} ETB!", show_alert=True)
        return
    
    context.user_data['transfer_amount'] = new_amount
    
    # Update the confirmation message
    await update_transfer_confirmation(query, context)

async def transfer_subtract_amount(update: Update, context: CallbackContext):
    """Subtract from amount (callback for -10 button)"""
    query = update.callback_query
    await query.answer()
    
    current_amount = context.user_data.get('transfer_amount', 0)
    new_amount = current_amount - 10
    
    if new_amount < MIN_TRANSFER_AMOUNT:
        await query.answer(f"Minimum is {MIN_TRANSFER_AMOUNT} ETB!", show_alert=True)
        return
    
    context.user_data['transfer_amount'] = new_amount
    
    # Update the confirmation message
    await update_transfer_confirmation(query, context)

async def update_transfer_confirmation(query, context):
    """Update the confirmation message with new amount"""
    sender_id = query.from_user.id
    receiver = context.user_data.get('transfer_receiver')
    amount = context.user_data.get('transfer_amount', 0)
    fee = (amount * TRANSFER_FEE_PERCENTAGE / 100) if TRANSFER_FEE_PERCENTAGE > 0 else 0
    
    sender_balance = await Database.get_balance(sender_id)
    total_deduction = amount + fee
    
    sender = await Database.get_user(sender_id)
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm Transfer", callback_data="transfer_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="transfer_cancel")
        ],
        [
            InlineKeyboardButton("➕ Add 10 ETB", callback_data="transfer_add_10"),
            InlineKeyboardButton("➖ Subtract 10 ETB", callback_data="transfer_sub_10")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📋 *Transfer Confirmation*\n\n"
        f"👤 *From:* {sender.get('username') or sender.get('first_name') or 'You'}\n"
        f"👤 *To:* {receiver['username'] or 'Unknown'}\n"
        f"📱 *Receiver Phone:* `{receiver['phone']}`\n"
        f"💰 *Amount:* `{amount:.2f} ETB`\n"
        f"💸 *Fee ({TRANSFER_FEE_PERCENTAGE}%):* `{fee:.2f} ETB`\n"
        f"💳 *Total Deduction:* `{total_deduction:.2f} ETB`\n"
        f"🎯 *Receiver Gets:* `{amount:.2f} ETB`\n\n"
        f"📊 *Your Balance After:* `{sender_balance - total_deduction:.2f} ETB`\n\n"
        f"⚠️ *This action cannot be undone!*\n\n"
        f"Please confirm the transfer.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )