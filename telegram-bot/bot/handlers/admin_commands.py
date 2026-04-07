# handlers/admin_commands.py
"""Admin-only commands for deposit/cashout approval"""

import logging
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import ADMIN_CHAT_ID

logger = logging.getLogger(__name__)


async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to approve deposit"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "📝 Usage: `/approve_deposit USER_ID AMOUNT`\n"
            "Example: `/approve_deposit 123456789 100`",
            parse_mode='Markdown'
        )
        return
    
    try:
        telegram_id = int(context.args[0])
        amount = float(context.args[1])
        
        user = await Database.get_user(telegram_id)
        if not user:
            await update.message.reply_text(f"❌ User {telegram_id} not found")
            return
        
        # Get current balance (may be Decimal from DB)
        current_balance = float(user["balance"]) if user["balance"] else 0.0
        new_balance = current_balance + amount
        
        # Perform the balance update using the database method
        await Database.add_balance(telegram_id, amount, "deposit_approval")
        
        lang = user.get('lang', 'en')
        
        # Notify the user
        await context.bot.send_message(
            chat_id=telegram_id,
            text=TEXTS[lang]['approved_deposit'].format(amount, new_balance),
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        
        await update.message.reply_text(
            f"✅ Deposit of {amount} Birr approved for user {telegram_id}\n"
            f"💰 New balance: {new_balance} Birr"
        )
        
        logger.info(f"Deposit approved: {telegram_id} - {amount} Birr")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid USER_ID or AMOUNT format")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def reject_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reject deposit"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "📝 Usage: `/reject_deposit USER_ID [reason]`\n"
            "Example: `/reject_deposit 123456789 Invalid screenshot`",
            parse_mode='Markdown'
        )
        return
    
    try:
        telegram_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Not specified"
        
        user = await Database.get_user(telegram_id)
        if user:
            lang = user.get('lang', 'en')
            await context.bot.send_message(
                chat_id=telegram_id,
                text=TEXTS[lang]['rejected'].format(reason),
                parse_mode='Markdown',
                reply_markup=menu(lang)
            )
        
        await update.message.reply_text(f"✅ Deposit rejected for user {telegram_id}")
        logger.info(f"Deposit rejected: {telegram_id} - Reason: {reason}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid USER_ID format")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def approve_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to approve cashout"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "📝 Usage: `/approve_cashout WITHDRAWAL_ID`\n"
            "Example: `/approve_cashout 12345`",
            parse_mode='Markdown'
        )
        return
    
    try:
        withdrawal_id = int(context.args[0])
        result = await Database.approve_withdrawal(withdrawal_id)
        
        if not result:
            await update.message.reply_text("❌ Withdrawal not found or already processed")
            return
        
        telegram_id, amount = result
        user = await Database.get_user(telegram_id)
        
        if user:
            lang = user.get('lang', 'en')
            # Get updated balance (after deduction)
            new_balance = float(user['balance']) - amount
            await context.bot.send_message(
                chat_id=telegram_id,
                text=TEXTS[lang]['approved_cashout'].format(amount, new_balance),
                parse_mode='Markdown',
                reply_markup=menu(lang)
            )
        
        await update.message.reply_text(
            f"✅ Cashout of {amount} Birr approved for withdrawal #{withdrawal_id}"
        )
        logger.info(f"Cashout approved: {withdrawal_id} - {amount} Birr")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid WITHDRAWAL_ID format")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def reject_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reject cashout"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "📝 Usage: `/reject_cashout WITHDRAWAL_ID [reason]`\n"
            "Example: `/reject_cashout 12345 Invalid account`",
            parse_mode='Markdown'
        )
        return
    
    try:
        withdrawal_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Not specified"
        
        # Get withdrawal details before rejecting
        withdrawal = await Database.get_withdrawal_by_id(withdrawal_id)
        
        if withdrawal:
            await Database.reject_withdrawal(withdrawal_id)
            
            # Notify the user
            user = await Database.get_user(withdrawal["telegram_id"])
            if user:
                lang = user.get('lang', 'en')
                await context.bot.send_message(
                    chat_id=withdrawal["telegram_id"],
                    text=TEXTS[lang]['rejected'].format(reason),
                    parse_mode='Markdown',
                    reply_markup=menu(lang)
                )
            
            await update.message.reply_text(f"✅ Cashout rejected for withdrawal #{withdrawal_id}")
            logger.info(f"Cashout rejected: {withdrawal_id} - Reason: {reason}")
        else:
            await update.message.reply_text(f"❌ Withdrawal #{withdrawal_id} not found")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid WITHDRAWAL_ID format")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")