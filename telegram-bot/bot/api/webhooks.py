# api/webhooks.py - SIMPLIFIED VERSION

import logging
import hmac
import hashlib
import os
from flask import Blueprint, request, jsonify
from ..db.database import Database

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhooks', __name__)

PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", None)


def verify_webhook_signature(data: bytes, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@webhook_bp.route('/api/webhook/deposit', methods=['POST'])
def deposit_webhook():
    data = request.get_json()
    signature = request.headers.get('X-Webhook-Signature')

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
            return jsonify({"success": False, "message": "Missing fields"}), 400

        # Run async operation
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        new_balance = loop.run_until_complete(
            Database.add_balance(telegram_id, amount, "auto_deposit")
        )
        loop.close()

        logger.info(f"Auto-deposit: {telegram_id} +{amount} Birr, new balance: {new_balance}")

        return jsonify({
            "success": True,
            "new_balance": new_balance,
            "transaction_id": transaction_id
        })

    except Exception as e:
        logger.exception("Deposit webhook error")
        return jsonify({"success": False, "message": str(e)}), 500


@webhook_bp.route('/api/webhook/withdrawal', methods=['POST'])
def withdrawal_webhook():
    data = request.get_json()
    signature = request.headers.get('X-Webhook-Signature')

    if PAYMENT_WEBHOOK_SECRET:
        if not verify_webhook_signature(request.data, signature, PAYMENT_WEBHOOK_SECRET):
            return jsonify({"success": False, "message": "Invalid signature"}), 401

    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    try:
        withdrawal_id = data.get('withdrawal_id')
        status = data.get('status')

        if not withdrawal_id:
            return jsonify({"success": False, "message": "Missing withdrawal_id"}), 400

        if status == 'failed':
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def process_refund():
                async with Database._pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT telegram_id, amount FROM pending_withdrawals WHERE id=$1 AND status='pending'",
                        withdrawal_id
                    )
                    if row:
                        await Database.add_balance(
                            row["telegram_id"],
                            row["amount"],
                            "withdrawal_refund"
                        )
                        await conn.execute(
                            "UPDATE pending_withdrawals SET status='failed' WHERE id=$1",
                            withdrawal_id
                        )
                        return row["amount"]
                return None
            
            refund_amount = loop.run_until_complete(process_refund())
            loop.close()
            
            if refund_amount:
                logger.info(f"Withdrawal {withdrawal_id} failed, refunded {refund_amount} Birr")

        return jsonify({"success": True})

    except Exception as e:
        logger.exception("Withdrawal webhook error")
        return jsonify({"success": False, "message": str(e)}), 500


@webhook_bp.route('/api/webhook/test', methods=['POST'])
def test_webhook():
    data = request.get_json()
    logger.info(f"Test webhook received: {data}")
    return jsonify({
        "success": True,
        "received": data,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    })