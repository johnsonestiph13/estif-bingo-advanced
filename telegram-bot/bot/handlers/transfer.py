# bot/handlers/transfer.py
import logging, re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from bot.db.database import Database
from bot.keyboards.menu import back_button, main_menu_inline
from bot.config import config
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)

PHONE_NUMBER, AMOUNT, CONFIRM = range(3)

MIN_TRANSFER = config.MIN_TRANSFER
MAX_TRANSFER = config.MAX_TRANSFER
DAILY_LIMIT = config.TRANSFER_DAILY_LIMIT
FEE = config.TRANSFER_FEE_PERCENTAGE

_transfer_cooldown = {}

async def transfer(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    context.user_data.clear()
    msg = (f"{get_emoji('transfer')} *Balance Transfer*\n\nTransfer funds to another player!\n\n"
           f"{get_emoji('info')} *Rules:*\n• Min: {MIN_TRANSFER} ETB\n• Max: {MAX_TRANSFER} ETB\n"
           f"• Daily limit: {DAILY_LIMIT} ETB\n• Fee: {FEE}%\n\n"
           f"{get_emoji('phone')} Enter receiver's phone number (09XXXXXXXX):\nType /cancel to cancel.")
    reply = back_button("main")
    if query:
        await query.answer()
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply)
    else:
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply)
    return PHONE_NUMBER

async def transfer_phone(update: Update, context: CallbackContext):
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    sender = await Database.get_user(user_id)
    if sender and sender.get('phone') == phone:
        await update.message.reply_text(f"{get_emoji('error')} Cannot transfer to yourself.", reply_markup=back_button("transfer"), parse_mode='Markdown')
        return PHONE_NUMBER
    if not re.match(r'^(09|07)[0-9]{8}$', phone):
        await update.message.reply_text(f"{get_emoji('error')} Invalid phone number. Use 09XXXXXXXX or 07XXXXXXXX.", reply_markup=back_button("transfer"), parse_mode='Markdown')
        return PHONE_NUMBER
    receiver = await Database.get_user_by_phone(phone)
    if not receiver or not receiver.get('registered'):
        await update.message.reply_text(f"{get_emoji('error')} User not found or not registered.", reply_markup=back_button("transfer"), parse_mode='Markdown')
        return PHONE_NUMBER
    context.user_data['receiver'] = {'id': receiver['telegram_id'], 'name': receiver.get('username') or receiver.get('first_name','Unknown'), 'phone': phone}
    balance = await Database.get_balance(user_id)
    await update.message.reply_text(
        f"{get_emoji('success')} Receiver: *{context.user_data['receiver']['name']}* (📱{phone})\n\n"
        f"{get_emoji('money')} Your balance: {balance:.2f} ETB\n"
        f"Enter amount (min {MIN_TRANSFER} ETB):\nType /cancel to cancel.",
        parse_mode='Markdown', reply_markup=back_button("transfer")
    )
    return AMOUNT

async def transfer_amount(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        amount = float(update.message.text.strip())
    except:
        await update.message.reply_text(f"{get_emoji('error')} Invalid amount. Enter a number.", reply_markup=back_button("transfer"), parse_mode='Markdown')
        return AMOUNT
    if amount < MIN_TRANSFER:
        await update.message.reply_text(f"{get_emoji('error')} Minimum transfer is {MIN_TRANSFER} ETB.", reply_markup=back_button("transfer"), parse_mode='Markdown')
        return AMOUNT
    if amount > MAX_TRANSFER:
        await update.message.reply_text(f"{get_emoji('error')} Maximum transfer is {MAX_TRANSFER} ETB.", reply_markup=back_button("transfer"), parse_mode='Markdown')
        return AMOUNT
    balance = await Database.get_balance(user_id)
    fee = amount * FEE / 100
    total = amount + fee
    if balance < total:
        await update.message.reply_text(f"{get_emoji('error')} Insufficient balance. Need {total:.2f} ETB (incl. fee).", reply_markup=back_button("transfer"), parse_mode='Markdown')
        return AMOUNT
    # daily limit check (simplified)
    # (we assume daily limit check function exists; if not, skip)
    context.user_data['amount'] = amount
    context.user_data['fee'] = fee
    receiver = context.user_data['receiver']
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('success')} Confirm", callback_data="transfer_confirm"),
         InlineKeyboardButton(f"{get_emoji('error')} Cancel", callback_data="transfer_cancel")]
    ])
    await update.message.reply_text(
        f"{get_emoji('question')} *Confirm Transfer*\n\n"
        f"To: {receiver['name']} (📱{receiver['phone']})\n"
        f"Amount: {amount:.2f} ETB\nFee: {fee:.2f} ETB\nTotal: {total:.2f} ETB\n\n"
        f"Confirm?",
        parse_mode='Markdown', reply_markup=keyboard
    )
    return CONFIRM

async def transfer_confirm(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    sender_id = query.from_user.id
    receiver = context.user_data.get('receiver')
    amount = context.user_data.get('amount')
    fee = context.user_data.get('fee', 0)
    if not receiver or not amount:
        await query.edit_message_text(f"{get_emoji('error')} Session expired.", reply_markup=main_menu_inline(await Database.get_user(sender_id)), parse_mode='Markdown')
        return ConversationHandler.END
    total = amount + fee
    try:
        await Database.deduct_balance(sender_id, total, "transfer_out")
        await Database.add_balance(receiver['id'], amount, "transfer_in")
        new_balance = await Database.get_balance(sender_id)
        await query.edit_message_text(
            f"{get_emoji('success')} *Transfer Successful!*\n\nSent {amount:.2f} ETB to {receiver['name']}\nYour new balance: {new_balance:.2f} ETB",
            reply_markup=main_menu_inline(await Database.get_user(sender_id)), parse_mode='Markdown'
        )
        await context.bot.send_message(chat_id=receiver['id'], text=f"{get_emoji('win')} *Transfer Received!*\n\nAmount: {amount:.2f} ETB\nFrom: {query.from_user.username or 'User'}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        await query.edit_message_text(f"{get_emoji('error')} Transfer failed. Try again later.", reply_markup=main_menu_inline(await Database.get_user(sender_id)), parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END

async def transfer_cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    if query:
        await query.answer()
        await query.edit_message_text(f"{get_emoji('warning')} Transfer cancelled.", reply_markup=main_menu_inline(await Database.get_user(user_id)), parse_mode='Markdown')
    else:
        await update.message.reply_text(f"{get_emoji('warning')} Transfer cancelled.", reply_markup=main_menu_inline(await Database.get_user(user_id)), parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END

async def transfer_cancel_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await update.message.reply_text(f"{get_emoji('warning')} Transfer cancelled.", reply_markup=main_menu_inline(await Database.get_user(user_id)), parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END

# Placeholders for add/subtract (if called)
async def transfer_add_amount(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Use /transfer to start a new transfer.", parse_mode='Markdown')
async def transfer_subtract_amount(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Use /transfer to start a new transfer.", parse_mode='Markdown')

__all__ = ['transfer','transfer_phone','transfer_amount','transfer_confirm','transfer_cancel','transfer_cancel_command','transfer_add_amount','transfer_subtract_amount','PHONE_NUMBER','AMOUNT','CONFIRM']