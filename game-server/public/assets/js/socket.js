// assets/js/socket.js - Socket.IO Connection Manager

class SocketManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.eventHandlers = new Map();
    }
    
    /**
     * Connect to server
     */
    connect() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('🔌 Socket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.trigger('connect');
        });
        
        this.socket.on('disconnect', () => {
            console.log('🔌 Socket disconnected');
            this.connected = false;
            this.trigger('disconnect');
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.reconnectAttempts++;
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                showMessage('Connection lost. Please refresh the page.', 'error', 5000);
            }
        });
        
        // Register all game events
        this.registerGameEvents();
    }
    
    /**
     * Register event handlers
     */
    registerGameEvents() {
        const events = [
            'authenticated', 'error', 'gameState', 'timerUpdate', 'rewardPoolUpdate',
            'selectionConfirmed', 'selectionUpdated', 'cartelaTaken', 'cartelaReleased',
            'numberDrawn', 'gameStarted', 'roundEnded', 'youWon', 'nextRound',
            'nextRoundCountdown', 'playersUpdate', 'balanceUpdated', 'stateSync'
        ];
        
        events.forEach(event => {
            this.socket.on(event, (data) => {
                this.trigger(event, data);
            });
        });
    }
    
    /**
     * Authenticate with token
     */
    authenticate(token) {
        this.socket.emit('authenticate', { token });
    }
    
    /**
     * Select cartela
     */
    selectCartela(cartelaNumber, callback) {
        this.socket.emit('selectCartela', { cartelaNumber }, callback);
    }
    
    /**
     * Deselect cartela
     */
    deselectCartela(cartelaNumber) {
        this.socket.emit('deselectCartela', { cartelaNumber });
    }
    
    /**
     * Get player status
     */
    getStatus() {
        this.socket.emit('getStatus');
    }
    
    /**
     * Get cartela grid
     */
    getCartelaGrid(cartelaId, callback) {
        this.socket.emit('getCartelaGrid', { cartelaId }, callback);
    }
    
    /**
     * Set username
     */
    setUsername(username) {
        this.socket.emit('setUsername', { username });
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
            this.eventHandlers.get(event).forEach(handler => handler(data));
        }
    }
    
    /**
     * Disconnect
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Create global instance
const socketManager = new SocketManager();