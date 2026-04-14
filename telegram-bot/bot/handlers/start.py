# bot/handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu
from bot.texts.emojis import get_emoji

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    if user and user.get('lang'):
        lang = user['lang']
        await update.message.reply_text(TEXTS[lang]['welcome'], reply_markup=menu(lang), parse_mode='Markdown')
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")]
    ])
    await update.message.reply_text(f"{get_emoji('language')} Select your language / ቋንቋ ይምረጡ:", reply_markup=keyboard)

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_id = query.from_user.id
    user = await Database.get_user(user_id)
    if not user:
        await Database.create_user(user_id, query.from_user.username or "", query.from_user.first_name or "", query.from_user.last_name or "", "", lang)
    else:
        await Database.update_user(user_id, lang=lang)
    await query.edit_message_text(TEXTS[lang]['welcome'], parse_mode='Markdown')
    await query.message.reply_text(f"{get_emoji('click')} Choose an option:", reply_markup=menu(lang), parse_mode='Markdown')

__all__ = ['start','language_callback']