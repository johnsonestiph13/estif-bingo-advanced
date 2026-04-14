# bot/handlers/bingo_otp.py
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.keyboards.menu import menu
from bot.config import config
from bot.texts.emojis import get_emoji

async def bingo_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    if not user or not user.get('registered'):
        await update.message.reply_text(f"{get_emoji('error')} Please register first.", reply_markup=menu(lang), parse_mode='Markdown')
        return
    otp = f"{random.randint(0, 999999):06d}"
    try:
        await Database.store_otp(user_id, otp)
    except Exception as e:
        await update.message.reply_text(f"{get_emoji('error')} Failed to generate OTP. Try again later.", reply_markup=menu(lang), parse_mode='Markdown')
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"{get_emoji('copy')} Copy OTP: {otp}", callback_data=f"copy_{otp}")]])
    await update.message.reply_text(
        f"{get_emoji('lock')} *Your Bingo Code*\n\n`{otp}`\n\nValid for {config.OTP_EXPIRY_MINUTES} minutes.\nEnter on Bingo website.",
        reply_markup=keyboard, parse_mode='Markdown'
    )

async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /verify <code>")
        return
    user_id = update.effective_user.id
    if await Database.verify_otp(user_id, context.args[0]):
        await update.message.reply_text(f"{get_emoji('success')} OTP verified! You can now login.")
    else:
        await update.message.reply_text(f"{get_emoji('error')} Invalid or expired OTP.")

__all__ = ['bingo_otp','verify_otp']