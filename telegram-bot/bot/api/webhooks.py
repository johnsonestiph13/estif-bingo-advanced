# telegram-bot/bot/api/webhooks.py
# Estif Bingo 24/7 - Payment Webhook Handlers (UPDATED & COMPATIBLE)

import logging
import hmac
import hashlib
import os
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify
from bot.db.database import Database
from bot.config import config

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhooks', __name__)

# Payment webhook secret (set in environment variables)
PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", None)


# ==================== HELPER FUNCTIONS ====================

def verify_webhook_signature(data: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature for security"""
    if not signature or not secret:
        logger.warning("Missing signature or secret for webhook verification")
        return False
    
    try:
        expected = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def run_async(coro):
    """Run async coroutine in a new event loop"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"run_async error: {e}")
        raise
    finally:
        try:
            loop.close()
        except Exception:
            pass


# ==================== WEBHOOK ENDPOINTS ====================

@webhook_bp.route('/api/webhook/deposit', methods=['POST'])
def deposit_webhook():
    """Handle payment provider deposit confirmation webhook"""
    try:
        # Verify signature if secret is configured
        signature = request.headers.get('X-Webhook-Signature')
        if PAYMENT_WEBHOOK_SECRET:
            if not verify_webhook_signature(request.data, signature, PAYMENT_WEBHOOK_SECRET):
                logger.warning(f"Invalid webhook signature from {request.remote_addr}")
                return jsonify({"success": False, "message": "Invalid signature"}), 401
        
        data = request.get_json()
        if not data:
            logger.warning("Empty webhook data received")
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        transaction_id = data.get('transaction_id')
        payment_method = data.get('payment_method', 'unknown')
        reference = data.get('reference')
        
        if not telegram_id or not amount:
            logger.error(f"Missing required fields: telegram_id={telegram_id}, amount={amount}")
            return jsonify({"success": False, "message": "Missing telegram_id or amount"}), 400
        
        # Process deposit
        new_balance = run_async(Database.add_balance(telegram_id, amount, f"auto_deposit_{payment_method}"))
        
        # Log the transaction
        run_async(Database.log_game_transaction(
            telegram_id, 
            None, 
            "deposit", 
            amount, 
            None, 
            None, 
            f"Auto deposit via {payment_method}, TX: {transaction_id}"
        ))
        
        logger.info(f"✅ Auto-deposit: User {telegram_id} +{amount} ETB via {payment_method}. New balance: {new_balance:.2f}")
        
        return jsonify({
            "success": True,
            "new_balance": new_balance,
            "transaction_id": transaction_id,
            "message": f"Deposit of {amount} ETB processed successfully"
        })
        
    except ValueError as e:
        logger.error(f"Deposit webhook value error: {e}")
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        logger.exception("Deposit webhook error")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@webhook_bp.route('/api/webhook/withdrawal', methods=['POST'])
def withdrawal_webhook():
    """Handle payment provider withdrawal status webhook"""
    try:
        # Verify signature if secret is configured
        signature = request.headers.get('X-Webhook-Signature')
        if PAYMENT_WEBHOOK_SECRET:
            if not verify_webhook_signature(request.data, signature, PAYMENT_WEBHOOK_SECRET):
                logger.warning(f"Invalid webhook signature from {request.remote_addr}")
                return jsonify({"success": False, "message": "Invalid signature"}), 401
        
        data = request.get_json()
        if not data:
            logger.warning("Empty webhook data received")
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        withdrawal_id = data.get('withdrawal_id')
        status = data.get('status')
        transaction_id = data.get('transaction_id')
        failure_reason = data.get('failure_reason')
        
        if not withdrawal_id:
            logger.error("Missing withdrawal_id in webhook")
            return jsonify({"success": False, "message": "Missing withdrawal_id"}), 400
        
        # Process based on status
        if status == 'completed':
            # Mark withdrawal as completed
            run_async(_mark_withdrawal_completed(withdrawal_id, transaction_id))
            logger.info(f"✅ Withdrawal {withdrawal_id} marked as completed")
            
        elif status == 'failed':
            # Refund the amount to user
            refund_amount = run_async(_process_failed_withdrawal(withdrawal_id, failure_reason))
            if refund_amount:
                logger.info(f"🔄 Withdrawal {withdrawal_id} failed, refunded {refund_amount} ETB")
            else:
                logger.warning(f"Withdrawal {withdrawal_id} failed but no refund processed")
                
        elif status == 'pending':
            logger.info(f"Withdrawal {withdrawal_id} is still pending")
            
        else:
            logger.warning(f"Unknown withdrawal status: {status} for withdrawal {withdrawal_id}")
        
        return jsonify({"success": True, "message": f"Webhook processed for withdrawal {withdrawal_id}"})
        
    except Exception as e:
        logger.exception("Withdrawal webhook error")
        return jsonify({"success": False, "message": "Internal server error"}), 500


async def _mark_withdrawal_completed(withdrawal_id: int, transaction_id: str = None):
    """Mark withdrawal as completed in database"""
    async with Database._pool.acquire() as conn:
        await conn.execute("""
            UPDATE pending_withdrawals 
            SET status = 'completed', processed_at = NOW(), note = $2
            WHERE id = $1 AND status = 'pending'
        """, withdrawal_id, f"Completed. TX: {transaction_id}" if transaction_id else "Completed")


async def _process_failed_withdrawal(withdrawal_id: int, failure_reason: str = None):
    """Process failed withdrawal - refund the amount to user"""
    async with Database._pool.acquire() as conn:
        async with conn.transaction():
            # Get withdrawal details
            withdrawal = await conn.fetchrow(
                "SELECT telegram_id, amount FROM pending_withdrawals WHERE id=$1 AND status='pending'",
                withdrawal_id
            )
            
            if not withdrawal:
                logger.warning(f"Withdrawal {withdrawal_id} not found or already processed")
                return None
            
            telegram_id = withdrawal['telegram_id']
            amount = float(withdrawal['amount'])
            
            # Refund the amount
            await Database.add_balance(telegram_id, amount, f"withdrawal_refund: {failure_reason or 'Failed'}")
            
            # Update withdrawal status
            await conn.execute("""
                UPDATE pending_withdrawals 
                SET status = 'failed', processed_at = NOW(), note = $2
                WHERE id = $1
            """, withdrawal_id, failure_reason or "Payment provider failed")
            
            # Log the refund transaction
            await Database.log_game_transaction(
                telegram_id, 
                None, 
                "refund", 
                amount, 
                None, 
                None, 
                f"Refund for failed withdrawal #{withdrawal_id}"
            )
            
            return amount


@webhook_bp.route('/api/webhook/deposit/cbe', methods=['POST'])
def cbe_deposit_webhook():
    """Commercial Bank of Ethiopia (CBE) deposit webhook"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # CBE specific fields
        account_number = data.get('account_number')
        amount = data.get('amount')
        reference = data.get('reference')
        phone_number = data.get('phone_number')
        
        # Find user by phone number
        user = run_async(Database.get_user_by_phone(phone_number))
        if not user:
            logger.warning(f"CBE deposit: User not found for phone {phone_number}")
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Process deposit
        new_balance = run_async(Database.add_balance(user['telegram_id'], amount, "cbe_deposit"))
        
        logger.info(f"🏦 CBE Deposit: User {user['telegram_id']} +{amount} ETB. New balance: {new_balance:.2f}")
        
        return jsonify({
            "success": True,
            "telegram_id": user['telegram_id'],
            "new_balance": new_balance,
            "reference": reference
        })
        
    except Exception as e:
        logger.exception("CBE deposit webhook error")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@webhook_bp.route('/api/webhook/deposit/telebirr', methods=['POST'])
def telebirr_deposit_webhook():
    """TeleBirr deposit webhook"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # TeleBirr specific fields
        transaction_id = data.get('transactionId')
        amount = data.get('amount')
        payer_phone = data.get('payerPhone')
        status = data.get('status')
        
        if status != 'success':
            logger.info(f"TeleBirr transaction {transaction_id} status: {status}")
            return jsonify({"success": True, "message": f"Transaction status: {status}"})
        
        # Find user by phone number
        user = run_async(Database.get_user_by_phone(payer_phone))
        if not user:
            logger.warning(f"TeleBirr deposit: User not found for phone {payer_phone}")
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Process deposit
        new_balance = run_async(Database.add_balance(user['telegram_id'], amount, "telebirr_deposit"))
        
        logger.info(f"📱 TeleBirr Deposit: User {user['telegram_id']} +{amount} ETB. New balance: {new_balance:.2f}")
        
        return jsonify({
            "success": True,
            "telegram_id": user['telegram_id'],
            "new_balance": new_balance,
            "transaction_id": transaction_id
        })
        
    except Exception as e:
        logger.exception("TeleBirr deposit webhook error")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@webhook_bp.route('/api/webhook/deposit/mpesa', methods=['POST'])
def mpesa_deposit_webhook():
    """M-Pesa deposit webhook"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # M-Pesa specific fields
        transaction_id = data.get('TransactionID')
        amount = data.get('Amount')
        sender_phone = data.get('SenderPhone')
        result_code = data.get('ResultCode')
        
        if result_code != '0':
            logger.info(f"M-Pesa transaction {transaction_id} failed with code: {result_code}")
            return jsonify({"success": True, "message": f"Transaction failed: {result_code}"})
        
        # Find user by phone number
        user = run_async(Database.get_user_by_phone(sender_phone))
        if not user:
            logger.warning(f"M-Pesa deposit: User not found for phone {sender_phone}")
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Process deposit
        new_balance = run_async(Database.add_balance(user['telegram_id'], amount, "mpesa_deposit"))
        
        logger.info(f"📱 M-Pesa Deposit: User {user['telegram_id']} +{amount} ETB. New balance: {new_balance:.2f}")
        
        return jsonify({
            "success": True,
            "telegram_id": user['telegram_id'],
            "new_balance": new_balance,
            "transaction_id": transaction_id
        })
        
    except Exception as e:
        logger.exception("M-Pesa deposit webhook error")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@webhook_bp.route('/api/webhook/test', methods=['POST'])
def test_webhook():
    """Test endpoint for webhook debugging"""
    data = request.get_json()
    headers = dict(request.headers)
    
    # Remove sensitive headers from log
    safe_headers = {k: v for k, v in headers.items() if k.lower() not in ['authorization', 'x-webhook-signature']}
    
    logger.info(f"Test webhook received from {request.remote_addr}")
    logger.info(f"Headers: {safe_headers}")
    logger.info(f"Body: {data}")
    
    return jsonify({
        "success": True,
        "received": data,
        "headers": safe_headers,
        "timestamp": datetime.utcnow().isoformat()
    })


@webhook_bp.route('/api/webhook/health', methods=['GET'])
def webhook_health():
    """Health check for webhook endpoints"""
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "webhook_secret_configured": bool(PAYMENT_WEBHOOK_SECRET)
    })


# ==================== ERROR HANDLERS ====================

@webhook_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({"success": False, "message": "Unauthorized"}), 401


@webhook_bp.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@webhook_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Webhook internal error: {error}")
    return jsonify({"success": False, "message": "Internal server error"}), 500