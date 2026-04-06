# handlers/cashout.py
"""Cashout request handler with withdrawal method selection"""

import logging
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import ADMIN_CHAT_ID, PAYMENT_ACCOUNTS

logger = logging.getLogger(__name__)

async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cashout payment methods"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            "❌ Please register first using /register",
            reply_markup=menu(lang)
        )
        return
    
    # Check minimum deposit requirement
    if user.get('total_deposited', 0) < 100:
        await update.message.reply_text(
            TEXTS[lang]['cashout_not_allowed'].format(user.get('total_deposited', 0)),
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return
    
    # Check sufficient balance
    if user.get('balance', 0) < 50:
        await update.message.reply_text(
            TEXTS[lang]['insufficient_balance'],
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return
    
    keyboard = [
        [InlineKeyboardButton(k, callback_data=f"cash_{k}")]
        for k in PAYMENT_ACCOUNTS.keys()
    ]
    await update.message.reply_text(
        TEXTS[lang]['cashout_select'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def cashout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal method selection"""
    query = update.callback_query
    await query.answer()
    
    method = query.data.split("_")[1]
    telegram_id = query.from_user.id
    
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    balance = user.get('balance', 0)
    
    context.user_data.clear()
    context.user_data['flow'] = 'cashout'
    context.user_data['step'] = 'waiting_amount'
    context.user_data['data'] = {'method': method}
    
    await query.edit_message_text(
        TEXTS[lang]['cashout_selected'].format(method, balance),
        parse_mode='Markdown'
    )

async def handle_cashout_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process cashout amount entry"""
    if context.user_data.get('flow') != 'cashout' or context.user_data.get('step') != 'waiting_amount':
        return False
    
    text = update.message.text
    nums = re.findall(r"\d+\.?\d*", text)
    
    if not nums:
        await update.message.reply_text("❌ Please enter a valid amount (e.g., 500)")
        return True
    
    amount = float(nums[0])
    telegram_id = update.effective_user.id
    user_data = await Database.get_user(telegram_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    
    if amount < 50:
        await update.message.reply_text("❌ Minimum withdrawal is 50 Birr")
        return True
    
    if amount > 10000:
        await update.message.reply_text("❌ Maximum withdrawal is 10,000 Birr")
        return True
    
    if amount > user_data.get('balance', 0):
        await update.message.reply_text(
            f"❌ Insufficient balance! Your balance: {user_data.get('balance', 0)} Birr"
        )
        return True
    
    context.user_data['data']['amount'] = amount
    context.user_data['step'] = 'waiting_account'
    
    await update.message.reply_text(
        TEXTS[lang]['cashout_amount_accepted'].format(amount),
        parse_mode='Markdown'
    )
    return True

async def handle_cashout_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process account number entry and create withdrawal request"""
    if context.user_data.get('flow') != 'cashout' or context.user_data.get('step') != 'waiting_account':
        return False
    
    account = update.message.text.strip()
    if not account or len(account) < 3:
        await update.message.reply_text("❌ Please enter a valid account number")
        return True
    
    data = context.user_data['data']
    telegram_id = update.effective_user.id
    
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    withdrawal_id = await Database.add_pending_withdrawal(
        telegram_id,
        data['amount'],
        account,
        data['method']
    )
    
    # Notify admin
    copy_text = f"""
💰 *CASHOUT REQUEST* #{withdrawal_id}

👤 User ID: `{telegram_id}`
💰 Amount: `{data['amount']}` Birr
💳 Method: `{data['method']}`
📱 Account: `{account}`

Commands:
`/approve_cashout {withdrawal_id}`
`/reject_cashout {withdrawal_id}`
"""
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=copy_text,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        TEXTS[lang]['cashout_sent'],
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    context.user_data.clear()
    return True