# handlers/admin_commands.py
"""Admin-only commands for deposit/cashout approval"""

import logging
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
        
        # Get user BEFORE update
        user_before = await Database.get_user(telegram_id)
        if not user_before:
            await update.message.reply_text(f"❌ User {telegram_id} not found")
            return
        
        old_balance = float(user_before["balance"]) if user_before["balance"] else 0.0
        
        # Perform the balance update
        await Database.add_balance(telegram_id, amount, "deposit_approval")
        
        # Get user AFTER update
        user_after = await Database.get_user(telegram_id)
        new_balance = float(user_after["balance"]) if user_after["balance"] else 0.0
        
        lang = user_before.get('lang', 'en')
        
        # Notify the user
        await context.bot.send_message(
            chat_id=telegram_id,
            text=TEXTS[lang]['approved_deposit'].format(amount, new_balance),
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        
        await update.message.reply_text(
            f"✅ Deposit approved for user {telegram_id}\n"
            f"💰 Amount: {amount} Birr\n"
            f"📊 Balance: {old_balance} → {new_balance} Birr"
        )
        
        logger.info(f"Deposit approved: {telegram_id} - {amount} Birr (balance: {old_balance} → {new_balance})")
        
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
        
        # Get withdrawal details BEFORE approving
        withdrawal = await Database.get_withdrawal_by_id(withdrawal_id)
        if not withdrawal:
            await update.message.reply_text("❌ Withdrawal not found")
            return
        
        if withdrawal.get("status") != "pending":
            await update.message.reply_text(f"❌ Withdrawal already {withdrawal.get('status')}")
            return
        
        telegram_id = withdrawal["telegram_id"]
        amount = float(withdrawal["amount"]) if withdrawal["amount"] else 0.0
        
        # Get user BEFORE deduction
        user_before = await Database.get_user(telegram_id)
        if not user_before:
            await update.message.reply_text(f"❌ User {telegram_id} not found")
            return
        
        old_balance = float(user_before["balance"]) if user_before["balance"] else 0.0
        
        # Check sufficient balance
        if old_balance < amount:
            await update.message.reply_text(
                f"❌ Insufficient balance! User has {old_balance} Birr, requested {amount} Birr"
            )
            return
        
        # Approve withdrawal (this deducts balance)
        result = await Database.approve_withdrawal(withdrawal_id)
        
        if not result:
            await update.message.reply_text("❌ Failed to approve withdrawal")
            return
        
        # Get user AFTER deduction
        user_after = await Database.get_user(telegram_id)
        new_balance = float(user_after["balance"]) if user_after["balance"] else 0.0
        
        lang = user_before.get('lang', 'en')
        
        # Notify the user
        await context.bot.send_message(
            chat_id=telegram_id,
            text=TEXTS[lang]['approved_cashout'].format(amount, new_balance),
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        
        await update.message.reply_text(
            f"✅ Cashout approved for withdrawal #{withdrawal_id}\n"
            f"👤 User: {telegram_id}\n"
            f"💰 Amount: {amount} Birr\n"
            f"📊 Balance: {old_balance} → {new_balance} Birr"
        )
        
        logger.info(f"Cashout approved: withdrawal #{withdrawal_id} - {amount} Birr (balance: {old_balance} → {new_balance})")
        
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
            logger.info(f"Cashout rejected: withdrawal #{withdrawal_id} - Reason: {reason}")
        else:
            await update.message.reply_text(f"❌ Withdrawal #{withdrawal_id} not found")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid WITHDRAWAL_ID format")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")