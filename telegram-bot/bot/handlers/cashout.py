# bot/handlers/cashout.py
import logging, re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.db.database import Database
from bot.keyboards.menu import menu, cashout_methods_keyboard
from bot.config import config
from bot.texts.emojis import get_emoji
from bot.texts.locales import TEXTS

logger = logging.getLogger(__name__)

METHOD, AMOUNT, ACCOUNT = range(3)

async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    if not user or not user.get('registered'):
        await update.message.reply_text(f"{get_emoji('error')} Please register first.", reply_markup=menu(lang))
        return ConversationHandler.END
    if user.get('total_deposited', 0) < config.MIN_WITHDRAWAL:
        await update.message.reply_text(TEXTS[lang]['cashout_not_allowed'].format(user.get('total_deposited',0)), parse_mode='Markdown', reply_markup=menu(lang))
        return ConversationHandler.END
    if user.get('balance', 0) < config.MIN_WITHDRAWAL:
        await update.message.reply_text(f"{get_emoji('error')} {TEXTS[lang]['insufficient_balance']}", parse_mode='Markdown', reply_markup=menu(lang))
        return ConversationHandler.END
    context.user_data.clear()
    keyboard = cashout_methods_keyboard(lang)
    await update.message.reply_text(f"{get_emoji('withdraw')} {TEXTS[lang]['cashout_select']}", reply_markup=keyboard, parse_mode='Markdown')
    return METHOD

async def cashout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("cashout_"):
        method = data.split("_")[1].upper()
        method_map = {'CBE':'CBE','ABYSSINIA':'ABBISINIYA','ABBISINIYA':'ABBISINIYA','TELEBIRR':'TELEBIRR','MPESA':'MPESA'}
        method_key = method_map.get(method, method)
        if method_key not in config.PAYMENT_ACCOUNTS:
            await query.edit_message_text(f"{get_emoji('error')} Invalid method.")
            return METHOD
        context.user_data['cashout_method'] = method_key
        user = await Database.get_user(query.from_user.id)
        lang = user.get('lang', 'en') if user else 'en'
        balance = user.get('balance', 0)
        await query.edit_message_text(
            f"{get_emoji('info')} {TEXTS[lang]['cashout_selected'].format(method_key, balance)}\n\n"
            f"{get_emoji('money')} Enter amount (Min: {config.MIN_WITHDRAWAL} ETB, Max: {config.MAX_WITHDRAWAL} ETB):\nType /cancel to cancel.",
            parse_mode='Markdown'
        )
        return AMOUNT
    return METHOD

async def cashout_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    text = update.message.text.strip()
    nums = re.findall(r"\d+\.?\d*", text)
    if not nums:
        await update.message.reply_text(f"{get_emoji('error')} Please enter a valid number.\nType /cancel to cancel.", parse_mode='Markdown')
        return AMOUNT
    amount = float(nums[0])
    if amount < config.MIN_WITHDRAWAL:
        await update.message.reply_text(f"{get_emoji('error')} Minimum withdrawal is {config.MIN_WITHDRAWAL} ETB.", parse_mode='Markdown')
        return AMOUNT
    if amount > config.MAX_WITHDRAWAL:
        await update.message.reply_text(f"{get_emoji('error')} Maximum withdrawal is {config.MAX_WITHDRAWAL} ETB.", parse_mode='Markdown')
        return AMOUNT
    if amount > user.get('balance', 0):
        await update.message.reply_text(f"{get_emoji('error')} Insufficient balance! Your balance: {user.get('balance',0):.2f} ETB", parse_mode='Markdown')
        return AMOUNT
    context.user_data['cashout_amount'] = amount
    await update.message.reply_text(
        f"{get_emoji('success')} Amount: {amount:.2f} ETB accepted.\n\n{get_emoji('phone')} Please enter your {context.user_data['cashout_method']} account number:\nType /cancel to cancel.",
        parse_mode='Markdown'
    )
    return ACCOUNT

async def cashout_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    user_data = await Database.get_user(user_id)
    lang = user_data.get('lang', 'en') if user_data else 'en'
    account = update.message.text.strip()
    if len(account) < 3:
        await update.message.reply_text(f"{get_emoji('error')} Please enter a valid account number.", parse_mode='Markdown')
        return ACCOUNT
    method = context.user_data.get('cashout_method')
    amount = context.user_data.get('cashout_amount')
    if not method or not amount:
        await update.message.reply_text(f"{get_emoji('error')} Session expired. Please start over with /cashout", reply_markup=menu(lang), parse_mode='Markdown')
        return ConversationHandler.END
    w_id = await Database.add_pending_withdrawal(user_id, amount, account, method)
    # notify admin
    await context.bot.send_message(
        chat_id=config.ADMIN_CHAT_ID,
        text=f"{get_emoji('withdraw')} *CASHOUT REQUEST* #{w_id}\nUser: {user.first_name} (@{user.username or 'N/A'})\nID: `{user_id}`\nAmount: {amount:.2f} ETB\nMethod: {method}\nAccount: {account}",
        parse_mode='Markdown'
    )
    await update.message.reply_text(f"{get_emoji('success')} {TEXTS[lang]['cashout_sent']}\nRequest ID: #{w_id}", reply_markup=menu(lang), parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END

async def cashout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    await update.message.reply_text(f"{get_emoji('warning')} Withdrawal cancelled.", reply_markup=menu(lang), parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END

# Aliases for compatibility
handle_cashout_amount = cashout_amount
handle_cashout_account = cashout_account
cashout_method = cashout_callback

__all__ = ['cashout','cashout_callback','cashout_method','cashout_amount','cashout_account','cashout_cancel','handle_cashout_amount','handle_cashout_account','METHOD','AMOUNT','ACCOUNT']