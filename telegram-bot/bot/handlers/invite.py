# handlers/invite.py
"""Invite friends handler with forwardable message"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import GAME_WEB_URL

logger = logging.getLogger(__name__)


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send forwardable invite message with game link"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Generate invite link (you can add referral parameter if needed)
    invite_link = f"{GAME_WEB_URL}?ref={telegram_id}"
    
    # Create an inline keyboard with a share button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share / Forward", url=f"https://t.me/share/url?url={invite_link}&text=🎉%20Join%20me%20in%20Estif%20Bingo!%20Play%20and%20win%20real%20prizes!")]
    ])
    
    # Send a message that can be easily forwarded
    await update.message.reply_text(
        f"🎉 *Invite Friends to Estif Bingo!* 🎉\n\n"
        f"Share this link with your friends:\n"
        f"`{invite_link}`\n\n"
        f"📢 *How to invite:*\n"
        f"1️⃣ Copy the link above\n"
        f"2️⃣ Send it to any friend, group, or channel\n"
        f"3️⃣ Or use the **Share** button below\n\n"
        f"✨ *When they register, you both get rewards!*",
        parse_mode='Markdown',
        reply_markup=keyboard
    )