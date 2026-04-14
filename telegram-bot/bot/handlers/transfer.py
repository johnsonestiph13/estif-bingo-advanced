# telegram-bot/bot/handlers/transfer.py
# Estif Bingo 24/7 - Transfer Handler (Complete Working Version)

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu, back_button, main_menu_inline
from bot.config import config
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)

# Conversation states
PHONE_NUMBER = 1
AMOUNT = 2
CONFIRM = 3

# Transfer limits from config
MIN_TRANSFER = config.MIN_TRANSFER
MAX_TRANSFER = config.MAX_TRANSFER
DAILY_LIMIT = config.TRANSFER_DAILY_LIMIT
FEE = config.TRANSFER_FEE_PERCENTAGE


async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start transfer flow - Show transfer instructions"""
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
    
    # Clear any existing transfer data
    context.user_data.clear()
    
    await update.message.reply_text(
        f"{get_emoji('transfer')} *BALANCE TRANSFER*\n\n"
        f"Send money to another player instantly!\n\n"
        f"{get_emoji('info')} *Rules:*\n"
        f"• Minimum: {MIN_TRANSFER} ETB\n"
        f"• Maximum: {MAX_TRANSFER} ETB\n"
        f"• Daily limit: {DAILY_LIMIT} ETB\n"
        f"• Fee: {FEE}%\n\n"
        f"{get_emoji('phone')} Please enter the receiver's phone number:\n"
        f"Example: `0912345678` or `0712345678`\n\n"
        f"Type /cancel to cancel.",
        parse_mode='Markdown'
    )
    return PHONE_NUMBER


async def transfer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process receiver's phone number"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    phone = update.message.text.strip()
    
    # Check if user is trying to transfer to themselves
    if user.get('phone') == phone:
        await update.message.reply_text(
            f"{get_emoji('error')} You cannot transfer money to yourself!\n\n"
            f"Please enter a different phone number.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Validate phone format
    if not re.match(r'^(09|07)[0-9]{8}$', phone):
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid phone number format!\n\n"
            f"Please enter a valid Ethiopian phone number:\n"
            f"• Starting with 09 (e.g., 0912345678)\n"
            f"• Or starting with 07 (e.g., 0712345678)\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Find receiver
    receiver = await Database.get_user_by_phone(phone)
    if not receiver or not receiver.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} User not found!\n\n"
            f"No user registered with phone number `{phone}`.\n\n"
            f"Please check the number or ask them to register first.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return PHONE_NUMBER
    
    # Store receiver info
    context.user_data['receiver'] = {
        'telegram_id': receiver['telegram_id'],
        'username': receiver.get('username') or receiver.get('first_name', 'Unknown'),
        'phone': phone
    }
    
    # Get sender's balance
    sender_balance = await Database.get_balance(telegram_id)
    
    await update.message.reply_text(
        f"{get_emoji('success')} *Receiver Found!*\n\n"
        f"{get_emoji('user')} Name: *{context.user_data['receiver']['username']}*\n"
        f"{get_emoji('phone')} Phone: `{phone}`\n\n"
        f"{get_emoji('money')} Your Balance: `{sender_balance:.2f} ETB`\n"
        f"{get_emoji('info')} Transfer Fee: {FEE}%\n\n"
        f"Please enter the amount to transfer (Min: {MIN_TRANSFER} ETB, Max: {MAX_TRANSFER} ETB):\n\n"
        f"Type /cancel to cancel.",
        parse_mode='Markdown'
    )
    return AMOUNT


async def transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process amount input"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    text = update.message.text.strip()
    nums = re.findall(r"\d+\.?\d*", text)
    
    if not nums:
        await update.message.reply_text(
            f"{get_emoji('error')} Please enter a valid amount (e.g., 100)\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    amount = float(nums[0])
    
    # Validate amount
    if amount < MIN_TRANSFER:
        await update.message.reply_text(
            f"{get_emoji('error')} Minimum transfer amount is {MIN_TRANSFER} ETB\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    if amount > MAX_TRANSFER:
        await update.message.reply_text(
            f"{get_emoji('error')} Maximum transfer amount is {MAX_TRANSFER} ETB\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Check balance
    current_balance = user.get('balance', 0)
    fee = (amount * FEE) / 100
    total_deduction = amount + fee
    
    if current_balance < total_deduction:
        await update.message.reply_text(
            f"{get_emoji('error')} *Insufficient Balance!*\n\n"
            f"{get_emoji('money')} Your Balance: `{current_balance:.2f} ETB`\n"
            f"{get_emoji('transfer')} Transfer Amount: `{amount:.2f} ETB`\n"
            f"{get_emoji('info')} Fee: `{fee:.2f} ETB`\n"
            f"{get_emoji('money')} Total Deduction: `{total_deduction:.2f} ETB`\n\n"
            f"Please enter a smaller amount or use /deposit to add funds.\n\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    
    # Store transfer details
    context.user_data['transfer_amount'] = amount
    context.user_data['transfer_fee'] = fee
    context.user_data['total_deduction'] = total_deduction
    
    receiver = context.user_data['receiver']
    
    # Create confirmation keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{get_emoji('success')} Confirm Transfer", callback_data="transfer_confirm"),
            InlineKeyboardButton(f"{get_emoji('error')} Cancel", callback_data="transfer_cancel")
        ]
    ])
    
    await update.message.reply_text(
        f"{get_emoji('question')} *Transfer Confirmation*\n\n"
        f"{get_emoji('user')} *To:* {receiver['username']}\n"
        f"{get_emoji('phone')} *Phone:* `{receiver['phone']}`\n"
        f"{get_emoji('money')} *Amount:* `{amount:.2f} ETB`\n"
        f"{get_emoji('info')} *Fee:* `{fee:.2f} ETB`\n"
        f"{get_emoji('money')} *Total Deduction:* `{total_deduction:.2f} ETB`\n\n"
        f"{get_emoji('warning')} *This action cannot be undone!*\n\n"
        f"Please confirm the transfer.",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return CONFIRM


async def transfer_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and execute transfer"""
    query = update.callback_query
    await query.answer()
    
    sender_id = query.from_user.id
    sender = await Database.get_user(sender_id)
    lang = sender.get('lang', 'en') if sender else 'en'
    
    receiver = context.user_data.get('receiver')
    amount = context.user_data.get('transfer_amount')
    fee = context.user_data.get('transfer_fee', 0)
    total_deduction = context.user_data.get('total_deduction', amount + fee)
    
    if not receiver or not amount:
        await query.edit_message_text(
            f"{get_emoji('error')} Transfer session expired. Please start over with /transfer.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    receiver_id = receiver['telegram_id']
    
    # Double-check balance
    sender_balance = await Database.get_balance(sender_id)
    if sender_balance < total_deduction:
        await query.edit_message_text(
            f"{get_emoji('error')} *Transfer Failed - Insufficient Balance*\n\n"
            f"{get_emoji('money')} Your Balance: `{sender_balance:.2f} ETB`\n"
            f"{get_emoji('money')} Required: `{total_deduction:.2f} ETB`\n\n"
            f"Please try again with a smaller amount.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        # Deduct from sender
        await Database.deduct_balance(sender_id, total_deduction, "transfer_out")
        
        # Add to receiver
        await Database.add_balance(receiver_id, amount, "transfer_in")
        
        # Get updated balances
        new_sender_balance = await Database.get_balance(sender_id)
        new_receiver_balance = await Database.get_balance(receiver_id)
        
        # Success message to sender
        success_msg = (
            f"{get_emoji('success')} *Transfer Successful!*\n\n"
            f"{get_emoji('transfer')} Sent: `{amount:.2f} ETB`\n"
            f"{get_emoji('user')} To: *{receiver['username']}*\n"
            f"{get_emoji('phone')} Phone: `{receiver['phone']}`\n"
        )
        
        if fee > 0:
            success_msg += f"{get_emoji('info')} Fee: `{fee:.2f} ETB`\n"
        
        success_msg += (
            f"\n{get_emoji('money')} Your New Balance: `{new_sender_balance:.2f} ETB`\n\n"
            f"Thank you for using Estif Bingo!"
        )
        
        await query.edit_message_text(
            success_msg,
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        
        # Notify receiver
        try:
            receiver_user = await Database.get_user(receiver_id)
            
            await context.bot.send_message(
                chat_id=receiver_id,
                text=(
                    f"{get_emoji('win')} *You Received a Transfer!*\n\n"
                    f"{get_emoji('money')} Amount: `{amount:.2f} ETB`\n"
                    f"{get_emoji('user')} From: *{sender.get('username') or sender.get('first_name', 'User')}*\n"
                    f"{get_emoji('money')} Your New Balance: `{new_receiver_balance:.2f} ETB`\n\n"
                    f"Use /balance to check your balance."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Could not notify receiver {receiver_id}: {e}")
        
        # Log transaction
        await Database.log_game_transaction(
            sender_id, sender.get('username', 'User'), "transfer_out", -amount, None, None,
            f"Transfer to {receiver['phone']}"
        )
        await Database.log_game_transaction(
            receiver_id, receiver['username'], "transfer_in", amount, None, None,
            f"Transfer from {sender.get('username', 'User')}"
        )
        
        logger.info(f"Transfer: {amount} ETB from {sender_id} to {receiver_id}")
        
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} *Transfer Failed*\n\n"
            f"An error occurred. Please try again later.\n\n"
            f"Support: {config.SUPPORT_GROUP_LINK}",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
    
    context.user_data.clear()
    return ConversationHandler.END


async def transfer_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel transfer (callback)"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await query.edit_message_text(
        f"{get_emoji('warning')} Transfer cancelled.\n\n"
        f"You can start a new transfer anytime from the main menu.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


async def transfer_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command during transfer"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await update.message.reply_text(
        f"{get_emoji('warning')} Transfer cancelled.\n\n"
        f"Use /transfer to start a new transfer.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


# Placeholders for add/subtract (in case main.py calls them)
async def transfer_add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Use /transfer to start a new transfer.", parse_mode='Markdown')


async def transfer_subtract_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Use /transfer to start a new transfer.", parse_mode='Markdown')


# Export all
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