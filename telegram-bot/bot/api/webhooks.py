# api/webhooks.py
"""Webhook endpoints for payment gateways and external services"""

import logging
import hmac
import hashlib
import asyncio
from flask import Blueprint, request, jsonify, abort, current_app
from functools import wraps
from ..db.database import Database
from ..config import API_SECRET

logger = logging.getLogger(__name__)

# Create blueprint
webhook_bp = Blueprint('webhooks', __name__)

# Optional: Payment webhook secret (set in environment if needed)
PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", None)


def verify_webhook_signature(data: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature for security"""
    if not signature or not secret:
        return False
    expected = hmac.new(
        secret.encode(),
        data,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def async_route(f):
    """Decorator to handle async Flask routes"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


@webhook_bp.route('/api/webhook/deposit', methods=['POST'])
@async_route
async def deposit_webhook():
    """
    Webhook for automatic deposit confirmation from payment gateway
    """
    data = request.get_json()
    signature = request.headers.get('X-Webhook-Signature')
    
    # Verify signature if secret is configured
    if PAYMENT_WEBHOOK_SECRET:
        if not verify_webhook_signature(request.data, signature, PAYMENT_WEBHOOK_SECRET):
            return jsonify({"success": False, "message": "Invalid signature"}), 401
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    try:
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        transaction_id = data.get('transaction_id')
        
        if not telegram_id or not amount:
            return jsonify({"success": False, "message": "Missing fields: telegram_id and amount required"}), 400
        
        # Add balance to user
        new_balance = await Database.add_balance(telegram_id, amount, "auto_deposit")
        
        logger.info(f"Auto-deposit: {telegram_id} added {amount} Birr, tx: {transaction_id}")
        
        return jsonify({
            "success": True,
            "new_balance": new_balance,
            "transaction_id": transaction_id
        })
        
    except ValueError as e:
        logger.warning(f"Deposit webhook validation error: {e}")
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        logger.exception("Deposit webhook error")
        return jsonify({"success": False, "message": "Internal error"}), 500


@webhook_bp.route('/api/webhook/withdrawal', methods=['POST'])
@async_route
async def withdrawal_webhook():
    """
    Webhook for withdrawal status updates from payment gateway
    """
    data = request.get_json()
    signature = request.headers.get('X-Webhook-Signature')
    
    # Verify signature if secret is configured
    if PAYMENT_WEBHOOK_SECRET:
        if not verify_webhook_signature(request.data, signature, PAYMENT_WEBHOOK_SECRET):
            return jsonify({"success": False, "message": "Invalid signature"}), 401
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    try:
        withdrawal_id = data.get('withdrawal_id')
        status = data.get('status')  # 'completed' or 'failed'
        transaction_id = data.get('transaction_id')
        
        if not withdrawal_id:
            return jsonify({"success": False, "message": "Missing withdrawal_id"}), 400
        
        if status == 'completed':
            logger.info(f"Withdrawal {withdrawal_id} completed via webhook, tx: {transaction_id}")
            
        elif status == 'failed':
            # Refund the user
            async with Database._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT telegram_id, amount FROM pending_withdrawals WHERE id = $1 AND status = 'pending'",
                    withdrawal_id
                )
                if row:
                    await Database.add_balance(row["telegram_id"], row["amount"], "withdrawal_refund")
                    await conn.execute(
                        "UPDATE pending_withdrawals SET status = 'failed' WHERE id = $1",
                        withdrawal_id
                    )
                    logger.info(f"Withdrawal {withdrawal_id} failed, refunded {row['amount']} Birr")
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.exception("Withdrawal webhook error")
        return jsonify({"success": False, "message": str(e)}), 500


@webhook_bp.route('/api/webhook/test', methods=['POST'])
@async_route
async def test_webhook():
    """Test webhook endpoint for debugging"""
    data = request.get_json()
    logger.info(f"Test webhook received: {data}")
    return jsonify({
        "success": True,
        "received": data,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    })


# Add missing import
import os