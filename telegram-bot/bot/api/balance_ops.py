# api/balance_ops.py
"""Balance operations API endpoints for game server
Estif Bingo 24/7 - Handles all balance-related API calls from Node.js game server
"""

import logging
from flask import Blueprint, request, jsonify
from .auth import api_key_required
from ..db.database import Database
from ..config import CARTELA_PRICE, MIN_BALANCE_FOR_PLAY

logger = logging.getLogger(__name__)

# Create blueprint
balance_bp = Blueprint('balance', __name__)


@balance_bp.route('/api/deduct', methods=['POST'])
@api_key_required
async def deduct():
    """Deduct balance from user (called by game server when player selects cartela)
    
    Expected JSON body:
    {
        "telegram_id": 123456789,
        "amount": 10,
        "cartela_id": "B1_001",
        "round": 5,
        "reason": "Cartela selection"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request body"}), 400
        
        telegram_id = data.get('telegram_id')
        amount = data.get('amount', CARTELA_PRICE)
        cartela_id = data.get('cartela_id')
        round_num = data.get('round')
        reason = data.get('reason', f'Cartela {cartela_id} selection')
        
        if not telegram_id:
            return jsonify({"success": False, "message": "telegram_id required"}), 400
        
        # Check if user has sufficient balance
        current_balance = await Database.get_balance(telegram_id)
        if current_balance < amount:
            logger.warning(f"Insufficient balance for user {telegram_id}: {current_balance} < {amount}")
            return jsonify({
                "success": False, 
                "error": f"Insufficient balance: {current_balance:.2f} ETB. Need {amount:.2f} ETB"
            }), 400
        
        # Perform deduction
        new_balance = await Database.deduct_balance(telegram_id, amount, reason)
        
        # Log the transaction
        await Database.log_game_transaction(
            telegram_id, 
            None,  # username will be fetched inside
            "bet", 
            -amount, 
            cartela_id, 
            round_num, 
            reason
        )
        
        logger.info(f"✅ Deducted {amount} ETB from user {telegram_id}. New balance: {new_balance:.2f}")
        
        return jsonify({
            "success": True, 
            "new_balance": new_balance,
            "message": f"Deducted {amount} ETB successfully"
        })
        
    except ValueError as e:
        logger.warning(f"Balance deduction failed for user {data.get('telegram_id')}: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception(f"Deduct error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@balance_bp.route('/api/add', methods=['POST'])
@api_key_required
async def add():
    """Add balance to user (called by game server for wins/refunds)
    
    Expected JSON body:
    {
        "telegram_id": 123456789,
        "amount": 250,
        "round_id": 5,
        "reason": "Round win"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request body"}), 400
        
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        round_id = data.get('round_id')
        reason = data.get('reason', 'Game winnings')
        
        if not telegram_id:
            return jsonify({"success": False, "message": "telegram_id required"}), 400
        
        if not amount or amount <= 0:
            return jsonify({"success": False, "message": "Valid amount required"}), 400
        
        # Perform addition
        new_balance = await Database.add_balance(telegram_id, amount, reason)
        
        # Log the transaction
        await Database.log_game_transaction(
            telegram_id, 
            None,  # username will be fetched inside
            "win", 
            amount, 
            None, 
            round_id, 
            reason
        )
        
        logger.info(f"✅ Added {amount} ETB to user {telegram_id}. New balance: {new_balance:.2f}")
        
        return jsonify({
            "success": True, 
            "new_balance": new_balance,
            "message": f"Added {amount} ETB successfully"
        })
        
    except Exception as e:
        logger.exception(f"Add balance error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@balance_bp.route('/api/balance', methods=['POST'])
@api_key_required
async def get_balance():
    """Get user's current balance
    
    Expected JSON body:
    {
        "telegram_id": 123456789
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request body"}), 400
        
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({"success": False, "message": "telegram_id required"}), 400
        
        balance = await Database.get_balance(telegram_id)
        
        return jsonify({
            "success": True, 
            "balance": balance,
            "can_play": balance >= MIN_BALANCE_FOR_PLAY
        })
        
    except Exception as e:
        logger.exception(f"Get balance error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@balance_bp.route('/api/balance/<int:telegram_id>', methods=['GET'])
@api_key_required
async def get_balance_by_id(telegram_id):
    """Get user's current balance by ID in URL
    
    Expected URL: /api/balance/123456789
    """
    try:
        balance = await Database.get_balance(telegram_id)
        
        return jsonify({
            "success": True, 
            "balance": balance,
            "can_play": balance >= MIN_BALANCE_FOR_PLAY
        })
        
    except Exception as e:
        logger.exception(f"Get balance error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@balance_bp.route('/api/balance/batch', methods=['POST'])
@api_key_required
async def batch_balance():
    """Get balances for multiple users at once
    
    Expected JSON body:
    {
        "telegram_ids": [123456789, 987654321, ...]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request body"}), 400
        
        telegram_ids = data.get('telegram_ids', [])
        
        if not telegram_ids:
            return jsonify({"success": False, "message": "telegram_ids required"}), 400
        
        results = {}
        for tid in telegram_ids:
            balance = await Database.get_balance(tid)
            results[str(tid)] = {
                "balance": balance,
                "can_play": balance >= MIN_BALANCE_FOR_PLAY
            }
        
        return jsonify({
            "success": True, 
            "balances": results
        })
        
    except Exception as e:
        logger.exception(f"Batch balance error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@balance_bp.route('/api/transfer', methods=['POST'])
@api_key_required
async def transfer_balance():
    """Transfer balance between users (admin or internal use)
    
    Expected JSON body:
    {
        "from_telegram_id": 123456789,
        "to_telegram_id": 987654321,
        "amount": 50,
        "reason": "Transfer"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request body"}), 400
        
        from_id = data.get('from_telegram_id')
        to_id = data.get('to_telegram_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Transfer')
        
        if not from_id or not to_id or not amount:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be positive"}), 400
        
        # Check if sender has sufficient balance
        sender_balance = await Database.get_balance(from_id)
        if sender_balance < amount:
            return jsonify({
                "success": False, 
                "error": f"Insufficient balance: {sender_balance:.2f} ETB"
            }), 400
        
        # Perform transfer
        await Database.deduct_balance(from_id, amount, f"Transfer to {to_id}: {reason}")
        await Database.add_balance(to_id, amount, f"Transfer from {from_id}: {reason}")
        
        # Log transactions
        await Database.log_game_transaction(from_id, None, "transfer_out", -amount, None, None, f"Transfer to {to_id}")
        await Database.log_game_transaction(to_id, None, "transfer_in", amount, None, None, f"Transfer from {from_id}")
        
        new_sender_balance = await Database.get_balance(from_id)
        new_receiver_balance = await Database.get_balance(to_id)
        
        logger.info(f"✅ Transferred {amount} ETB from {from_id} to {to_id}")
        
        return jsonify({
            "success": True,
            "from_user": {
                "telegram_id": from_id,
                "new_balance": new_sender_balance
            },
            "to_user": {
                "telegram_id": to_id,
                "new_balance": new_receiver_balance
            },
            "amount": amount,
            "message": f"Transferred {amount} ETB successfully"
        })
        
    except ValueError as e:
        logger.warning(f"Transfer failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception(f"Transfer error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@balance_bp.route('/api/transactions/<int:telegram_id>', methods=['GET'])
@api_key_required
async def get_transactions(telegram_id):
    """Get user's transaction history
    
    Optional query params:
    - limit: Number of transactions (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        transactions = await Database.get_user_transactions(telegram_id, limit, offset)
        
        # Convert Decimal to float for JSON serialization
        for tx in transactions:
            if 'amount' in tx:
                tx['amount'] = float(tx['amount'])
        
        return jsonify({
            "success": True,
            "transactions": transactions,
            "count": len(transactions)
        })
        
    except Exception as e:
        logger.exception(f"Get transactions error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@balance_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({"success": False, "message": "Unauthorized"}), 401


@balance_bp.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@balance_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"success": False, "message": "Internal server error"}), 500