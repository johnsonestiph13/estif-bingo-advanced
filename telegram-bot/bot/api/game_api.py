"""
Estif Bingo 24/7 - Game API Endpoints for Telegram Bot
Handles all game-related API calls from the Node.js game server
Updated: Fixed database pool reference, added error handling, and enhanced features
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import hashlib
import random
import string
import os
import asyncio
from functools import wraps

# Import database and config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.db.database import Database
from bot.config import config

# Create blueprint
game_api_bp = Blueprint('game_api', __name__)


# ==================== HELPER: Run async functions in Flask ====================

def run_async(async_func, *args, **kwargs):
    """Helper to run async functions in Flask's synchronous context"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_func(*args, **kwargs))
    except Exception as e:
        print(f"run_async error: {e}")
        raise
    finally:
        try:
            loop.close()
        except Exception:
            pass


# ==================== AUTHENTICATION DECORATOR ====================

def verify_api_key(f):
    """Decorator to verify API key for bot-to-server calls"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        if api_key != config.API_SECRET:
            print(f"Invalid API key attempt: {api_key[:20]}...")
            return jsonify({'error': 'Unauthorized: Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== AUTHENTICATION ENDPOINTS ====================

@game_api_bp.route('/api/verify-code', methods=['POST'])
@verify_api_key
def verify_code():
    """Verify one-time code and return user data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        code = data.get('code')
        if not code:
            return jsonify({'success': False, 'error': 'Code required'}), 400
        
        telegram_id = run_async(Database.verify_auth_code, code)
        
        if telegram_id:
            user = run_async(Database.get_user, telegram_id)
            if user:
                return jsonify({
                    'success': True,
                    'telegram_id': telegram_id,
                    'username': user.get('username', 'Player'),
                    'balance': float(user.get('balance', 0))
                })
        
        return jsonify({'success': False, 'error': 'Invalid or expired code'}), 401
    except Exception as e:
        print(f"Verify code error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/exchange-code', methods=['POST'])
@verify_api_key
def exchange_code():
    """Exchange one-time code for JWT token (called by game server)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        code = data.get('code')
        if not code:
            return jsonify({'success': False, 'error': 'Code required'}), 400
        
        telegram_id = run_async(Database.verify_auth_code, code)
        
        if telegram_id:
            user = run_async(Database.get_user, telegram_id)
            if user:
                # Generate JWT token for game server
                token = jwt.encode({
                    'telegram_id': telegram_id,
                    'username': user.get('username', 'Player'),
                    'balance': float(user.get('balance', 0)),
                    'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS),
                    'iat': datetime.utcnow()
                }, config.JWT_SECRET, algorithm='HS256')
                
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'telegram_id': telegram_id,
                        'username': user.get('username', 'Player'),
                        'balance': float(user.get('balance', 0))
                    }
                })
        
        return jsonify({'success': False, 'error': 'Invalid or expired code'}), 401
    except jwt.PyJWTError as e:
        print(f"JWT error: {e}")
        return jsonify({'success': False, 'error': 'Token generation failed'}), 500
    except Exception as e:
        print(f"Exchange code error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/verify-token', methods=['POST'])
@verify_api_key
def verify_token():
    """Verify JWT token (called by game server WebSocket)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'valid': False, 'message': 'Invalid request body'}), 400
        
        token = data.get('token')
        if not token:
            return jsonify({'valid': False, 'message': 'Token required'}), 400
        
        decoded = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
        
        # Verify user still exists and is registered
        user = run_async(Database.get_user, decoded['telegram_id'])
        if not user or not user.get('registered'):
            return jsonify({'valid': False, 'message': 'User not found or not registered'}), 401
        
        return jsonify({
            'valid': True,
            'telegram_id': decoded['telegram_id'],
            'username': decoded.get('username', 'Player'),
            'balance': float(user.get('balance', 0))
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        print(f"Verify token error: {e}")
        return jsonify({'valid': False, 'message': 'Internal server error'}), 500


# ==================== BALANCE OPERATIONS ====================

@game_api_bp.route('/api/deduct', methods=['POST'])
@verify_api_key
def deduct_balance():
    """Deduct balance for cartela purchase"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        telegram_id = data.get('telegram_id')
        amount = data.get('amount', config.CARTELA_PRICE)
        cartela_id = data.get('cartela_id')
        round_num = data.get('round')
        reason = data.get('reason', f'Cartela {cartela_id} selection')
        
        if not telegram_id:
            return jsonify({'success': False, 'error': 'telegram_id required'}), 400
        
        # Check current balance
        current_balance = run_async(Database.get_balance, telegram_id)
        if current_balance < amount:
            return jsonify({
                'success': False,
                'error': f'Insufficient balance: {current_balance:.2f} ETB. Need {amount:.2f} ETB'
            }), 400
        
        success = run_async(Database.update_balance, telegram_id, -amount, 'cartela_purchase', round_num)
        
        if success:
            user = run_async(Database.get_user, telegram_id)
            new_balance = float(user['balance']) if user else 0
            return jsonify({
                'success': True,
                'new_balance': new_balance,
                'message': f'Deducted {amount} ETB for cartela {cartela_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to deduct balance'
            }), 400
    except Exception as e:
        print(f"Deduct balance error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/add', methods=['POST'])
@verify_api_key
def add_balance():
    """Add winnings to user balance"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        round_id = data.get('round_id')
        reason = data.get('reason', f'Round {round_id} win')
        
        if not telegram_id:
            return jsonify({'success': False, 'error': 'telegram_id required'}), 400
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'error': 'Valid amount required'}), 400
        
        success = run_async(Database.update_balance, telegram_id, amount, 'winning', round_id)
        
        if success:
            user = run_async(Database.get_user, telegram_id)
            new_balance = float(user['balance']) if user else 0
            return jsonify({
                'success': True,
                'new_balance': new_balance,
                'message': f'Added {amount} ETB for round {round_id} win'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to add balance'}), 400
    except Exception as e:
        print(f"Add balance error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/balance/<int:telegram_id>', methods=['GET'])
@verify_api_key
def get_balance(telegram_id):
    """Get user balance"""
    try:
        user = run_async(Database.get_user, telegram_id)
        if user:
            balance = float(user.get('balance', 0))
            return jsonify({
                'success': True,
                'balance': balance,
                'can_play': balance >= config.MIN_BALANCE_FOR_PLAY
            })
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        print(f"Get balance error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/balance', methods=['POST'])
@verify_api_key
def get_balance_post():
    """Get user balance (POST method)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        telegram_id = data.get('telegram_id')
        if not telegram_id:
            return jsonify({'success': False, 'error': 'telegram_id required'}), 400
        
        user = run_async(Database.get_user, telegram_id)
        if user:
            balance = float(user.get('balance', 0))
            return jsonify({
                'success': True,
                'balance': balance,
                'can_play': balance >= config.MIN_BALANCE_FOR_PLAY
            })
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        print(f"Get balance error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/adjust-balance', methods=['POST'])
@verify_api_key
def adjust_balance():
    """Adjust user balance (admin action)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Admin adjustment')
        
        if not telegram_id or amount is None:
            return jsonify({'success': False, 'error': 'telegram_id and amount required'}), 400
        
        success = run_async(Database.update_balance, telegram_id, amount, 'admin_adjustment', None)
        
        if success:
            user = run_async(Database.get_user, telegram_id)
            new_balance = float(user['balance']) if user else 0
            return jsonify({
                'success': True,
                'new_balance': new_balance,
                'message': f'Balance adjusted by {amount} ETB'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to adjust balance'}), 400
    except Exception as e:
        print(f"Adjust balance error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==================== TRANSFER OPERATIONS ====================

@game_api_bp.route('/api/transfer', methods=['POST'])
@verify_api_key
def transfer_balance():
    """Transfer balance between users"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        from_id = data.get('from_telegram_id')
        to_id = data.get('to_telegram_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Transfer')
        
        if not from_id or not to_id or not amount:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        
        # Check sender balance
        sender_balance = run_async(Database.get_balance, from_id)
        if sender_balance < amount:
            return jsonify({
                'success': False,
                'error': f'Insufficient balance: {sender_balance:.2f} ETB'
            }), 400
        
        # Perform transfer
        run_async(Database.deduct_balance, from_id, amount, f"Transfer to {to_id}: {reason}")
        run_async(Database.add_balance, to_id, amount, f"Transfer from {from_id}: {reason}")
        
        # Get updated balances
        new_sender_balance = run_async(Database.get_balance, from_id)
        new_receiver_balance = run_async(Database.get_balance, to_id)
        
        # Log transactions
        run_async(Database.log_game_transaction, from_id, None, "transfer_out", -amount, None, None, f"Transfer to {to_id}")
        run_async(Database.log_game_transaction, to_id, None, "transfer_in", amount, None, None, f"Transfer from {from_id}")
        
        return jsonify({
            'success': True,
            'from_user': {
                'telegram_id': from_id,
                'new_balance': new_sender_balance
            },
            'to_user': {
                'telegram_id': to_id,
                'new_balance': new_receiver_balance
            },
            'amount': amount,
            'message': f'Transferred {amount} ETB successfully'
        })
    except Exception as e:
        print(f"Transfer error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==================== COMMISSION / WIN PERCENTAGE ====================

@game_api_bp.route('/api/commission', methods=['GET'])
@verify_api_key
def get_commission():
    """Get current win percentage"""
    try:
        percentage = run_async(Database.get_win_percentage)
        return jsonify({
            'success': True,
            'percentage': percentage,
            'available': config.WIN_PERCENTAGES,
            'default': config.DEFAULT_WIN_PERCENTAGE
        })
    except Exception as e:
        print(f"Get commission error: {e}")
        return jsonify({
            'success': True,
            'percentage': config.DEFAULT_WIN_PERCENTAGE,
            'available': config.WIN_PERCENTAGES
        }), 500


@game_api_bp.route('/api/commission', methods=['POST'])
@verify_api_key
def set_commission():
    """Set win percentage"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        percentage = data.get('percentage')
        
        if percentage not in config.WIN_PERCENTAGES:
            return jsonify({
                'success': False,
                'error': f'Invalid percentage. Allowed: {config.WIN_PERCENTAGES}'
            }), 400
        
        previous = run_async(Database.get_win_percentage)
        run_async(Database.set_win_percentage, percentage)
        
        return jsonify({
            'success': True,
            'message': f'Win percentage updated from {previous}% to {percentage}%',
            'percentage': percentage,
            'previous': previous
        })
    except Exception as e:
        print(f"Set commission error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==================== USER MANAGEMENT ====================

@game_api_bp.route('/api/get-user/<int:telegram_id>', methods=['GET'])
@verify_api_key
def get_user(telegram_id):
    """Get user details by Telegram ID"""
    try:
        user = run_async(Database.get_user, telegram_id)
        
        if user:
            user_dict = dict(user)
            if 'balance' in user_dict:
                user_dict['balance'] = float(user_dict['balance'])
            if 'total_deposited' in user_dict:
                user_dict['total_deposited'] = float(user_dict['total_deposited'])
            
            return jsonify({
                'success': True,
                'user': user_dict
            })
        
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/get-user', methods=['POST'])
@verify_api_key
def get_user_post():
    """Get user details by Telegram ID (POST method)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        telegram_id = data.get('telegram_id')
        if not telegram_id:
            return jsonify({'success': False, 'error': 'telegram_id required'}), 400
        
        user = run_async(Database.get_user, telegram_id)
        
        if user:
            user_dict = dict(user)
            if 'balance' in user_dict:
                user_dict['balance'] = float(user_dict['balance'])
            if 'total_deposited' in user_dict:
                user_dict['total_deposited'] = float(user_dict['total_deposited'])
            
            return jsonify({
                'success': True,
                'user': user_dict
            })
        
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/search-players', methods=['POST'])
@verify_api_key
def search_players():
    """Search players by username or phone"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        search_term = data.get('search', '')
        
        if len(search_term) < 2:
            return jsonify({
                'success': False,
                'error': 'Search term must be at least 2 characters'
            }), 400
        
        players = run_async(Database.search_players, search_term)
        
        players_list = []
        for player in players:
            player_dict = dict(player)
            if 'balance' in player_dict:
                player_dict['balance'] = float(player_dict['balance'])
            if 'total_deposited' in player_dict:
                player_dict['total_deposited'] = float(player_dict['total_deposited'])
            players_list.append(player_dict)
        
        return jsonify({
            'success': True,
            'players': players_list,
            'count': len(players_list)
        })
    except Exception as e:
        print(f"Search players error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@game_api_bp.route('/api/player-stats/<int:telegram_id>', methods=['GET'])
@verify_api_key
def get_player_stats(telegram_id):
    """Get player statistics"""
    try:
        user = run_async(Database.get_user, telegram_id)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        async def get_stats():
            async with Database._pool.acquire() as conn:
                total_bets = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM game_transactions 
                    WHERE telegram_id = $1 AND type = 'bet'
                """, telegram_id)
                
                total_wins = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM game_transactions 
                    WHERE telegram_id = $1 AND type = 'win'
                """, telegram_id)
                
                games_played = await conn.fetchval("""
                    SELECT COUNT(*) FROM game_transactions 
                    WHERE telegram_id = $1 AND type = 'bet'
                """, telegram_id)
                
                games_won = await conn.fetchval("""
                    SELECT COUNT(*) FROM game_transactions 
                    WHERE telegram_id = $1 AND type = 'win'
                """, telegram_id)
                
                return {
                    'total_bets': float(total_bets) if total_bets else 0,
                    'total_wins': float(total_wins) if total_wins else 0,
                    'games_played': games_played or 0,
                    'games_won': games_won or 0
                }
        
        stats = run_async(get_stats)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_bets': stats['total_bets'],
                'total_wins': stats['total_wins'],
                'games_played': stats['games_played'],
                'games_won': stats['games_won'],
                'net_result': stats['total_wins'] - stats['total_bets'],
                'win_rate': round((stats['games_won'] / (stats['games_played'] or 1)) * 100, 2)
            }
        })
    except Exception as e:
        print(f"Get player stats error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==================== ROUND MANAGEMENT ====================

@game_api_bp.route('/api/save-round', methods=['POST'])
@verify_api_key
def save_round():
    """Save round result to database"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request body'}), 400
        
        required_fields = ['round_id', 'pool_amount', 'win_percentage', 'winners', 'commission', 'total_payout']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        async def save():
            async with Database._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO game_rounds (round_number, total_pool, winner_reward, admin_commission, winners, win_percentage)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, data['round_id'], data['pool_amount'], data['total_payout'], 
                    data['commission'], data['winners'], data['win_percentage'])
        
        run_async(save)
        
        return jsonify({'success': True, 'message': 'Round saved successfully'})
    except Exception as e:
        print(f"Save round error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==================== HEALTH CHECK ====================

@game_api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    try:
        db_connected = run_async(Database.health_check)
        
        return jsonify({
            'status': 'alive',
            'database': 'connected' if db_connected else 'disconnected',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'telegram-bot-api'
        })
    except Exception as e:
        print(f"Health check error: {e}")
        return jsonify({
            'status': 'alive',
            'database': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'telegram-bot-api'
        }), 500


@game_api_bp.route('/api/bridge-health', methods=['GET'])
@verify_api_key
def bridge_health():
    """Health check for bot bridge"""
    try:
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'telegram-bot-api'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ERROR HANDLERS ====================

@game_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'success': False, 'error': 'Unauthorized'}), 401


@game_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@game_api_bp.errorhandler(500)
def internal_error(error):
    print(f"Internal server error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500