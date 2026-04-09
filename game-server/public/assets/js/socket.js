// assets/js/socket.js - Complete Socket.IO Connection Manager
// Estif Bingo 24/7 - Real-time Multiplayer Socket Management

class SocketManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.eventHandlers = new Map();
        this.pendingRequests = new Map();
        this.requestId = 0;
        this.isAuthenticated = false;
        this.userData = null;
        this.heartbeatInterval = null;
        this.reconnectTimer = null;
    }
    
    /**
     * Connect to server with auth token
     */
    connect(token = null) {
        if (this.socket && this.socket.connected) {
            console.log('Socket already connected');
            return;
        }
        
        // Close existing connection
        if (this.socket) {
            this.socket.close();
        }
        
        // Create new connection with options
        this.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: false, // We'll handle reconnection manually
            timeout: 20000,
            pingTimeout: 60000,
            pingInterval: 25000
        });
        
        // Connection events
        this.socket.on('connect', () => {
            console.log('🔌 Socket connected successfully');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.trigger('connect');
            
            // Start heartbeat
            this.startHeartbeat();
            
            // Authenticate if token provided
            if (token) {
                this.authenticate(token);
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.connected = false;
            this.trigger('connect_error', error);
            this.handleReconnect();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('Socket disconnected:', reason);
            this.connected = false;
            this.isAuthenticated = false;
            this.stopHeartbeat();
            this.trigger('disconnect', { reason });
            
            // Handle unexpected disconnect
            if (reason === 'io server disconnect' || reason === 'transport close') {
                this.handleReconnect();
            }
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.trigger('error', error);
        });
        
        this.socket.on('reconnect_attempt', (attempt) => {
            console.log(`Reconnect attempt ${attempt}`);
            this.trigger('reconnect_attempt', attempt);
        });
        
        // Register all game events
        this.registerGameEvents();
    }
    
    /**
     * Handle reconnection with exponential backoff
     */
    handleReconnect() {
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
            
            this.reconnectTimer = setTimeout(() => {
                this.reconnectAttempts++;
                this.connect();
            }, delay);
        } else {
            this.trigger('reconnect_failed', { 
                message: 'Unable to reconnect. Please refresh the page.' 
            });
            this.showReconnectModal();
        }
    }
    
    /**
     * Show reconnect modal to user
     */
    showReconnectModal() {
        const modal = document.createElement('div');
        modal.className = 'reconnect-modal';
        modal.innerHTML = `
            <div class="reconnect-content">
                <h3>⚠️ Connection Lost</h3>
                <p>Unable to reconnect to game server.</p>
                <button onclick="location.reload()">Refresh Page</button>
                <button onclick="socketManager.forceReconnect()">Try Again</button>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    /**
     * Force reconnect attempt
     */
    forceReconnect() {
        this.reconnectAttempts = 0;
        this.connect();
        const modal = document.querySelector('.reconnect-modal');
        if (modal) modal.remove();
    }
    
    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            if (this.connected && this.isAuthenticated) {
                this.sendHeartbeat();
            }
        }, 30000);
    }
    
    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    /**
     * Send heartbeat ping
     */
    sendHeartbeat() {
        this.emitWithAck('ping', { timestamp: Date.now() }, 5000)
            .then(response => {
                if (response && response.serverTime) {
                    const latency = Date.now() - response.serverTime;
                    this.trigger('latency', latency);
                }
            })
            .catch(() => {
                console.log('Heartbeat failed');
            });
    }
    
    /**
     * Register all game event handlers
     */
    registerGameEvents() {
        // Authentication events
        this.socket.on('authenticated', (data) => {
            console.log('✅ Authenticated successfully');
            this.isAuthenticated = true;
            this.userData = data.user;
            this.trigger('authenticated', data);
        });
        
        this.socket.on('auth_error', (data) => {
            console.error('Authentication error:', data);
            this.isAuthenticated = false;
            this.trigger('auth_error', data);
        });
        
        // Game state events
        this.socket.on('gameState', (data) => {
            this.trigger('gameState', data);
        });
        
        this.socket.on('stateSync', (data) => {
            console.log('State sync received');
            this.trigger('stateSync', data);
        });
        
        // Timer events
        this.socket.on('timerUpdate', (data) => {
            this.trigger('timerUpdate', data);
        });
        
        // Round events
        this.socket.on('newRound', (data) => {
            console.log(`New round started: ${data.round}`);
            this.trigger('newRound', data);
        });
        
        this.socket.on('gameActive', (data) => {
            console.log('Game active, starting draws');
            this.trigger('gameActive', data);
        });
        
        this.socket.on('roundEnded', (data) => {
            console.log(`Round ended with ${data.winners?.length || 0} winners`);
            this.trigger('roundEnded', data);
        });
        
        this.socket.on('nextRoundCountdown', (data) => {
            this.trigger('nextRoundCountdown', data);
        });
        
        // Number drawing events
        this.socket.on('numberDrawn', (data) => {
            this.trigger('numberDrawn', data);
        });
        
        // Cartela events
        this.socket.on('cartelaTaken', (data) => {
            console.log(`Cartela ${data.cartelaId} taken by ${data.username}`);
            this.trigger('cartelaTaken', data);
        });
        
        this.socket.on('cartelaReleased', (data) => {
            console.log(`Cartela ${data.cartelaId} released`);
            this.trigger('cartelaReleased', data);
        });
        
        this.socket.on('selectionConfirmed', (data) => {
            console.log(`Selection confirmed: ${data.cartelaId}`);
            this.trigger('selectionConfirmed', data);
        });
        
        this.socket.on('selectionFailed', (data) => {
            console.error('Selection failed:', data.reason);
            this.trigger('selectionFailed', data);
        });
        
        this.socket.on('selectionUpdated', (data) => {
            this.trigger('selectionUpdated', data);
        });
        
        // Balance events
        this.socket.on('balanceUpdated', (data) => {
            console.log(`Balance updated: ${data.newBalance} ETB`);
            this.trigger('balanceUpdated', data);
        });
        
        // Winner events
        this.socket.on('youWon', (data) => {
            console.log(`🎉 You won ${data.amount} ETB! Pattern: ${data.pattern}`);
            this.trigger('youWon', data);
        });
        
        // Pool events
        this.socket.on('rewardPoolUpdate', (data) => {
            this.trigger('rewardPoolUpdate', data);
        });
        
        // Player events
        this.socket.on('playersUpdate', (data) => {
            this.trigger('playersUpdate', data);
        });
        
        // Error events
        this.socket.on('error', (data) => {
            console.error('Server error:', data.message);
            this.trigger('error', data);
        });
        
        this.socket.on('warning', (data) => {
            console.warn('Server warning:', data.message);
            this.trigger('warning', data);
        });
    }
    
    /**
     * Authenticate with JWT token
     */
    authenticate(token) {
        if (!this.socket || !this.connected) {
            console.warn('Cannot authenticate: socket not connected');
            return;
        }
        this.socket.emit('authenticate', { token });
    }
    
    /**
     * Select a cartela
     */
    async selectCartela(cartelaId, price = 10) {
        if (!this.isAuthenticated) {
            throw new Error('Not authenticated');
        }
        
        if (!this.connected) {
            throw new Error('Not connected to server');
        }
        
        return this.emitWithAck('selectCartela', { 
            cartelaId, 
            price 
        }, 10000);
    }
    
    /**
     * Deselect a cartela
     */
    async deselectCartela(cartelaId) {
        if (!this.isAuthenticated) return;
        
        return this.emitWithAck('deselectCartela', { 
            cartelaId 
        }, 5000);
    }
    
    /**
     * Get current game status
     */
    async getGameStatus() {
        return this.emitWithAck('getGameStatus', {}, 5000);
    }
    
    /**
     * Get player status
     */
    async getPlayerStatus() {
        return this.emitWithAck('getPlayerStatus', {}, 5000);
    }
    
    /**
     * Request balance check
     */
    async checkBalance() {
        if (!this.isAuthenticated) return null;
        
        return this.emitWithAck('checkBalance', {}, 5000);
    }
    
    /**
     * Get cartela grid
     */
    async getCartelaGrid(cartelaId) {
        return this.emitWithAck('getCartelaGrid', { cartelaId }, 10000);
    }
    
    /**
     * Get all selected cartelas for current round
     */
    async getSelectedCartelas() {
        return this.emitWithAck('getSelectedCartelas', {}, 5000);
    }
    
    /**
     * Request state sync (for recovery after disconnect)
     */
    async requestStateSync() {
        if (!this.isAuthenticated) return;
        
        return this.emitWithAck('requestStateSync', {}, 5000);
    }
    
    /**
     * Send chat message (if implemented)
     */
    sendChatMessage(message) {
        if (!this.isAuthenticated) return;
        
        this.socket.emit('chatMessage', { message });
    }
    
    /**
     * Emit with acknowledgement (promise-based)
     */
    emitWithAck(event, data, timeout = 10000) {
        return new Promise((resolve, reject) => {
            if (!this.socket) {
                reject(new Error('Socket not initialized'));
                return;
            }
            
            const requestId = ++this.requestId;
            const ackEvent = `${event}_ack_${requestId}`;
            
            // Set timeout
            const timer = setTimeout(() => {
                this.socket.off(ackEvent);
                this.pendingRequests.delete(requestId);
                reject(new Error(`Request timeout: ${event}`));
            }, timeout);
            
            // Handle acknowledgement
            this.socket.once(ackEvent, (response) => {
                clearTimeout(timer);
                this.pendingRequests.delete(requestId);
                
                if (response && response.error) {
                    reject(new Error(response.error));
                } else {
                    resolve(response);
                }
            });
            
            // Store for cleanup if needed
            this.pendingRequests.set(requestId, { event, timer });
            
            // Emit with acknowledgement flag
            this.socket.emit(event, data, (response) => {
                clearTimeout(timer);
                this.pendingRequests.delete(requestId);
                
                if (response && response.error) {
                    reject(new Error(response.error));
                } else {
                    resolve(response);
                }
            });
        });
    }
    
    /**
     * Register event listener
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }
    
    /**
     * Register one-time event listener
     */
    once(event, handler) {
        const wrapper = (data) => {
            handler(data);
            this.off(event, wrapper);
        };
        this.on(event, wrapper);
    }
    
    /**
     * Remove event listener
     */
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index !== -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    /**
     * Trigger event
     */
    trigger(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Check if connected and authenticated
     */
    isReady() {
        return this.connected && this.isAuthenticated;
    }
    
    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.connected,
            authenticated: this.isAuthenticated,
            reconnectAttempts: this.reconnectAttempts,
            userId: this.userData?.telegram_id || null
        };
    }
    
    /**
     * Disconnect from server
     */
    disconnect() {
        this.stopHeartbeat();
        
        // Clear pending requests
        for (const [id, { timer }] of this.pendingRequests) {
            clearTimeout(timer);
        }
        this.pendingRequests.clear();
        
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.connected = false;
        this.isAuthenticated = false;
        this.userData = null;
    }
    
    /**
     * Reconnect manually
     */
    reconnect() {
        this.disconnect();
        this.reconnectAttempts = 0;
        this.connect();
    }
}

// Create global instance
const socketManager = new SocketManager();

// Auto-connect when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Get token from URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token') || localStorage.getItem('authToken');
    
    if (token) {
        socketManager.connect(token);
    } else {
        // Wait for authentication from parent window (Telegram WebApp)
        if (window.Telegram && window.Telegram.WebApp) {
            const initData = window.Telegram.WebApp.initData;
            if (initData) {
                socketManager.connect(initData);
            }
        }
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = socketManager;
}