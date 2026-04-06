# handlers/deposit.py
"""Deposit request handler with payment method selection"""

import logging
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import ADMIN_CHAT_ID, PAYMENT_ACCOUNTS, ACCOUNT_HOLDER

logger = logging.getLogger(__name__)

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show deposit payment methods"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            "❌ Please register first using /register",
            reply_markup=menu(lang)
        )
        return
    
    keyboard = [
        [InlineKeyboardButton(k, callback_data=f"dep_{k}")]
        for k in PAYMENT_ACCOUNTS.keys()
    ]
    await update.message.reply_text(
        TEXTS[lang]['deposit_select'].format(ACCOUNT_HOLDER),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def deposit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection"""
    query = update.callback_query
    await query.answer()
    
    method = query.data.split("_")[1]
    account_number = PAYMENT_ACCOUNTS[method]
    telegram_id = query.from_user.id
    
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Reset any existing flow
    context.user_data.clear()
    context.user_data['flow'] = 'deposit'
    context.user_data['step'] = 'waiting_amount'
    context.user_data['data'] = {
        'method': method,
        'account_number': account_number
    }
    
    await query.edit_message_text(
        TEXTS[lang]['deposit_selected'].format(method, ACCOUNT_HOLDER, account_number),
        parse_mode='Markdown'
    )

async def handle_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process deposit amount entry"""
    if context.user_data.get('flow') != 'deposit' or context.user_data.get('step') != 'waiting_amount':
        return False
    
    text = update.message.text
    nums = re.findall(r"\d+\.?\d*", text)
    
    if not nums:
        await update.message.reply_text("❌ Please enter a valid amount (e.g., 100)")
        return True
    
    amount = float(nums[0])
    if amount < 10:
        await update.message.reply_text("❌ Minimum deposit amount is 10 Birr")
        return True
    
    if amount > 100000:
        await update.message.reply_text("❌ Maximum deposit amount is 100,000 Birr")
        return True
    
    context.user_data['data']['amount'] = amount
    context.user_data['step'] = 'waiting_screenshot'
    
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await update.message.reply_text(
        TEXTS[lang]['deposit_amount_accepted'].format(amount),
        parse_mode='Markdown'
    )
    return True

async def handle_deposit_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process deposit screenshot"""
    if context.user_data.get('flow') != 'deposit' or context.user_data.get('step') != 'waiting_screenshot':
        return False
    
    user = update.effective_user
    telegram_id = user.id
    data = context.user_data['data']
    
    user_data = await Database.get_user(telegram_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    
    photo = update.message.photo[-1]
    request_id = random.randint(100000, 999999)
    
    # Send to admin
    copy_text = f"""
💰 *NEW DEPOSIT REQUEST* #{request_id}

👤 User: {user.first_name} (@{user.username or 'N/A'})
🆔 ID: `{telegram_id}`
💰 Amount: `{data['amount']}` Birr
🏦 Method: `{data['method']}`
📋 Account: `{data['account_number']}`

Commands:
`/approve_deposit {telegram_id} {data['amount']}`
`/reject_deposit {telegram_id}`
"""
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=copy_text,
        parse_mode='Markdown'
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo.file_id,
        caption=f"Deposit proof from {user.first_name}"
    )
    
    await update.message.reply_text(
        TEXTS[lang]['deposit_sent'],
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    # Clear flow
    context.user_data.clear()
    return True