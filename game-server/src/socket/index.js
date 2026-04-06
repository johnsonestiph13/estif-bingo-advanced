// game-server/src/socket/index.js

const { config } = require("../config");
const { verifySocketToken } = require("../middleware/auth");
const { selectCartelaRateLimiter, deselectCartelaRateLimiter } = require("../middleware/rateLimit");
const gameState = require("../game/gameState");
const cartela = require("../game/cartela");
const roundManager = require("../game/roundManager");
const rewardPool = require("../game/rewardPool");
const db = require("../db/pool");

// ==================== HELPER FUNCTIONS ====================

/**
 * Broadcast game state to all connected clients
 */
function broadcastGameState(io) {
    const playersList = gameState.getAllPlayers();
    io.emit("gameState", {
        status: gameState.gameState.status,
        round: gameState.gameState.round,
        timer: gameState.gameState.timer,
        drawnNumbers: gameState.gameState.drawnNumbers,
        playersCount: gameState.getTotalPlayersCount(),
        players: playersList,
        winPercentage: rewardPool.getWinPercentage(),
        totalBet: gameState.gameState.totalBet,
        winnerReward: gameState.gameState.winnerReward
    });
}

/**
 * Broadcast timer update to all connected clients
 */
function broadcastTimer(io) {
    io.emit("timerUpdate", {
        seconds: gameState.gameState.timer,
        round: gameState.gameState.round,
        formatted: roundManager.formatTime(gameState.gameState.timer)
    });
}

/**
 * Broadcast reward pool update to all connected clients
 */
function broadcastRewardPool(io) {
    const totalCartelas = gameState.getTotalSelectedCartelasCount();
    const update = rewardPool.getRewardPoolUpdate(totalCartelas, config.BET_AMOUNT);
    io.emit("rewardPoolUpdate", update);
}

/**
 * Broadcast players update to all connected clients
 */
function broadcastPlayersUpdate(io) {
    const players = gameState.getAllPlayers();
    io.emit("playersUpdate", {
        count: players.length,
        players: players.map(p => ({
            socketId: p.socketId,
            username: p.username,
            selectedCount: p.selectedCartelas.length,
            selectedCartelas: p.selectedCartelas,
            balance: p.balance
        }))
    });
}

/**
 * Broadcast to all devices of a specific user
 */
function broadcastToUserDevices(telegramId, event, data, excludeSocketId = null) {
    const sessions = gameState.getUserSessions(telegramId);
    for (const socketId of sessions) {
        if (socketId !== excludeSocketId) {
            const io = require("socket.io").sockets;
            io.to(socketId).emit(event, data);
        }
    }
}

/**
 * Sync player state across all user devices
 */
async function syncPlayerState(telegramId, excludeSocketId = null) {
    // Find player in game state
    let playerData = null;
    for (const [socketId, player] of gameState.gameState.players) {
        if (player.telegramId === telegramId) {
            playerData = {
                balance: player.balance,
                selectedCartelas: player.selectedCartelas,
                username: player.username,
                telegramId: player.telegramId
            };
            break;
        }
    }
    
    if (playerData) {
        broadcastToUserDevices(telegramId, "stateSync", playerData, excludeSocketId);
    }
}

// ==================== SOCKET.IO CONNECTION HANDLER ====================

/**
 * Initialize Socket.IO event handlers
 */
function initSocketIO(io) {
    io.on("connection", (socket) => {
        console.log(`🟢 New socket connection: ${socket.id}`);
        
        // ========== AUTHENTICATION ==========
        
        /**
         * Authenticate player with JWT token
         */
        socket.on("authenticate", async (data) => {
            const { token } = data;
            
            if (!token) {
                socket.emit("error", { message: "Authentication token required" });
                return;
            }
            
            // Verify JWT token
            const verification = verifySocketToken(token);
            if (!verification.valid) {
                socket.emit("error", { message: verification.error || "Invalid token" });
                return;
            }
            
            const { telegram_id, username, balance } = verification.decoded;
            
            // Check if user is registered in bot (optional validation)
            // Store user session
            gameState.addUserSession(telegram_id, socket.id);
            
            // Check if player already exists in game state
            let existingPlayer = null;
            for (const [sid, player] of gameState.gameState.players) {
                if (player.telegramId === telegram_id) {
                    existingPlayer = player;
                    break;
                }
            }
            
            let playerData;
            if (existingPlayer) {
                // Use existing player data (preserve cartela selections)
                playerData = {
                    socketId: socket.id,
                    telegramId: telegram_id,
                    username: username || existingPlayer.username,
                    selectedCartelas: existingPlayer.selectedCartelas,
                    balance: existingPlayer.balance,
                    totalWon: existingPlayer.totalWon || 0,
                    totalPlayed: existingPlayer.totalPlayed || 0,
                    gamesWon: existingPlayer.gamesWon || 0,
                    joinedAt: Date.now()
                };
                gameState.addPlayer(socket.id, playerData);
            } else {
                // Check for saved selections from crash recovery
                let savedSelections = [];
                for (const [cartelaNum, reservation] of gameState.globalTakenCartelas) {
                    if (reservation.telegramId === telegram_id) {
                        savedSelections.push(cartelaNum);
                    }
                }
                
                playerData = {
                    socketId: socket.id,
                    telegramId: telegram_id,
                    username: username || `Player_${telegram_id.toString().slice(-4)}`,
                    selectedCartelas: savedSelections,
                    balance: balance || 0,
                    totalWon: 0,
                    totalPlayed: 0,
                    gamesWon: 0,
                    joinedAt: Date.now()
                };
                gameState.addPlayer(socket.id, playerData);
            }
            
            // Send initial data to client
            socket.emit("authenticated", {
                success: true,
                username: playerData.username,
                balance: playerData.balance,
                selectedCartelas: playerData.selectedCartelas,
                telegramId: telegram_id
            });
            
            // Send current game state
            socket.emit("gameState", {
                status: gameState.gameState.status,
                round: gameState.gameState.round,
                timer: gameState.gameState.timer,
                drawnNumbers: gameState.gameState.drawnNumbers,
                playersCount: gameState.getTotalPlayersCount(),
                winPercentage: rewardPool.getWinPercentage(),
                totalBet: gameState.gameState.totalBet,
                winnerReward: gameState.gameState.winnerReward
            });
            
            socket.emit("timerUpdate", {
                seconds: gameState.gameState.timer,
                round: gameState.gameState.round,
                formatted: roundManager.formatTime(gameState.gameState.timer)
            });
            
            // Send reward pool update
            const totalCartelas = gameState.getTotalSelectedCartelasCount();
            const rewardUpdate = rewardPool.getRewardPoolUpdate(totalCartelas, config.BET_AMOUNT);
            socket.emit("rewardPoolUpdate", rewardUpdate);
            
            // Send player data
            socket.emit("playerData", {
                selectedCartelas: playerData.selectedCartelas,
                balance: playerData.balance,
                username: playerData.username
            });
            
            // Update all clients with new player list
            broadcastPlayersUpdate(io);
            
            // Sync state to other devices of same user
            await syncPlayerState(telegram_id, socket.id);
            
            console.log(`✅ Player authenticated: ${playerData.username} (${telegram_id})`);
        });
        
        // ========== PLAYER ACTIONS ==========
        
        /**
         * Change username
         */
        socket.on("setUsername", (data) => {
            const player = gameState.getPlayer(socket.id);
            if (player && data.username?.trim()) {
                const newUsername = data.username.trim().substring(0, 20);
                player.username = newUsername;
                
                socket.emit("usernameChanged", { username: newUsername });
                broadcastGameState(io);
                broadcastToUserDevices(player.telegramId, "usernameChanged", { username: newUsername }, socket.id);
            }
        });
        
        /**
         * Select a cartela
         */
        socket.on("selectCartela", async (data, callback) => {
            // Rate limiting
            if (!selectCartelaRateLimiter.isAllowed(socket.id)) {
                if (callback) {
                    callback({ success: false, error: "Too many attempts. Please slow down." });
                } else {
                    socket.emit("error", { message: "Too many attempts. Please slow down." });
                }
                return;
            }
            
            try {
                const player = gameState.getPlayer(socket.id);
                if (!player) {
                    throw new Error("Not authenticated");
                }
                
                // Validate game state
                if (gameState.gameState.status !== "selection") {
                    throw new Error(`Cannot select now. Current status: ${gameState.gameState.status}`);
                }
                
                // Validate cartela limits
                if (player.selectedCartelas.length >= config.MAX_CARTELAS) {
                    throw new Error(`Maximum ${config.MAX_CARTELAS} cartelas per round`);
                }
                
                if (player.selectedCartelas.includes(data.cartelaNumber)) {
                    throw new Error("Cartela already selected");
                }
                
                // Validate balance
                if (player.balance < config.BET_AMOUNT) {
                    throw new Error(`Insufficient balance: ${player.balance} ETB. Need ${config.BET_AMOUNT} ETB`);
                }
                
                // Validate cartela availability
                if (!gameState.isCartelaAvailable(data.cartelaNumber)) {
                    const owner = gameState.getCartelaOwner(data.cartelaNumber);
                    throw new Error(`Cartela ${data.cartelaNumber} already taken by ${owner.username}`);
                }
                
                // Reserve cartela
                const reserved = gameState.reserveCartela(data.cartelaNumber, player.telegramId, player.username);
                if (!reserved) {
                    throw new Error("Cartela was just taken by someone else");
                }
                
                // Deduct balance (will be handled by bot via API call)
                // The actual deduction happens in the main server.js via bot API
                
                // Add cartela to player
                gameState.addPlayerCartela(socket.id, data.cartelaNumber);
                
                // Generate cartela grid (caches it)
                cartela.getCartelaGrid(data.cartelaNumber);
                
                // Log transaction
                await db.logGameTransaction(
                    player.telegramId,
                    player.username,
                    "bet",
                    config.BET_AMOUNT,
                    data.cartelaNumber,
                    gameState.gameState.round,
                    "Cartela selection"
                );
                
                // Prepare response data
                const selectionData = {
                    cartela: data.cartelaNumber,
                    selectedCount: player.selectedCartelas.length,
                    selectedCartelas: player.selectedCartelas,
                    balance: player.balance - config.BET_AMOUNT,
                    remainingSlots: config.MAX_CARTELAS - player.selectedCartelas.length
                };
                
                // Send confirmation to client
                socket.emit("selectionConfirmed", selectionData);
                
                // Sync to other devices of same user
                broadcastToUserDevices(player.telegramId, "selectionConfirmed", selectionData, socket.id);
                
                // Broadcast updates to all clients
                broadcastRewardPool(io);
                io.emit("cartelaTaken", {
                    cartelaNumber: data.cartelaNumber,
                    takenBy: player.username,
                    remainingCartelas: config.TOTAL_CARTELAS - gameState.getTotalSelectedCartelasCount(),
                    totalSelected: gameState.getTotalSelectedCartelasCount()
                });
                
                broadcastGameState(io);
                broadcastPlayersUpdate(io);
                
                if (callback) {
                    callback({ 
                        success: true, 
                        newBalance: player.balance - config.BET_AMOUNT,
                        selectedCartelas: player.selectedCartelas
                    });
                }
                
            } catch (err) {
                console.error("Select cartela error:", err.message);
                if (callback) {
                    callback({ success: false, error: err.message });
                } else {
                    socket.emit("error", { message: err.message });
                }
            }
        });
        
        /**
         * Deselect a cartela (refund)
         */
        socket.on("deselectCartela", async (data) => {
            // Rate limiting
            if (!deselectCartelaRateLimiter.isAllowed(socket.id)) {
                socket.emit("error", { message: "Too many attempts. Please slow down." });
                return;
            }
            
            try {
                const player = gameState.getPlayer(socket.id);
                if (!player) return;
                
                if (gameState.gameState.status !== "selection") {
                    socket.emit("error", { message: "Cannot deselect now" });
                    return;
                }
                
                const index = player.selectedCartelas.indexOf(data.cartelaNumber);
                if (index !== -1) {
                    // Release cartela reservation
                    const released = gameState.releaseCartela(data.cartelaNumber, player.telegramId);
                    
                    if (released) {
                        // Remove from player
                        gameState.removePlayerCartela(socket.id, data.cartelaNumber);
                        
                        // Refund will be handled by bot API
                        
                        // Log transaction
                        await db.logGameTransaction(
                            player.telegramId,
                            player.username,
                            "refund",
                            config.BET_AMOUNT,
                            data.cartelaNumber,
                            gameState.gameState.round,
                            "Cartela deselected"
                        );
                        
                        const updateData = {
                            selectedCartelas: player.selectedCartelas,
                            balance: player.balance + config.BET_AMOUNT
                        };
                        
                        socket.emit("selectionUpdated", updateData);
                        broadcastToUserDevices(player.telegramId, "selectionUpdated", updateData, socket.id);
                        
                        broadcastRewardPool(io);
                        io.emit("cartelaReleased", {
                            cartelaNumber: data.cartelaNumber,
                            releasedBy: player.username,
                            availableCartelas: config.TOTAL_CARTELAS - gameState.getTotalSelectedCartelasCount(),
                            totalSelected: gameState.getTotalSelectedCartelasCount()
                        });
                        
                        broadcastGameState(io);
                    }
                }
            } catch (err) {
                console.error("Deselect cartela error:", err);
                socket.emit("error", { message: err.message });
            }
        });
        
        /**
         * Get player status
         */
        socket.on("getStatus", () => {
            const player = gameState.getPlayer(socket.id);
            if (player) {
                socket.emit("playerStatus", {
                    balance: player.balance,
                    selectedCartelas: player.selectedCartelas,
                    gameStatus: gameState.gameState.status,
                    timer: gameState.gameState.timer,
                    round: gameState.gameState.round,
                    drawnNumbers: gameState.gameState.drawnNumbers,
                    totalWon: player.totalWon,
                    totalPlayed: player.totalPlayed,
                    gamesWon: player.gamesWon,
                    winPercentage: rewardPool.getWinPercentage()
                });
            }
        });
        
        /**
         * Get cartela grid
         */
        socket.on("getCartelaGrid", async (data, callback) => {
            const { cartelaId } = data;
            
            if (!cartela.isValidCartelaId(cartelaId)) {
                if (callback) {
                    callback({ success: false, error: "Invalid cartela ID" });
                }
                return;
            }
            
            const grid = cartela.getCartelaGrid(cartelaId);
            
            if (callback) {
                callback({ success: true, cartelaId: cartelaId, grid: grid });
            } else {
                socket.emit("cartelaGrid", { cartelaId: cartelaId, grid: grid });
            }
        });
        
        /**
         * Ping/pong for latency check
         */
        socket.on("ping", (callback) => {
            if (callback) {
                callback({ pong: Date.now() });
            }
        });
        
        // ========== DISCONNECTION ==========
        
        /**
         * Handle disconnection
         */
        socket.on("disconnect", () => {
            console.log(`🔴 Socket disconnected: ${socket.id}`);
            
            // Find which user this socket belonged to
            let telegramId = null;
            for (const [tid, sessions] of gameState.activeSessions) {
                if (sessions.has(socket.id)) {
                    telegramId = tid;
                    break;
                }
            }
            
            // Remove from active sessions
            if (telegramId) {
                const noMoreSessions = gameState.removeUserSession(telegramId, socket.id);
                
                // If no more sessions, clean up player from game state
                if (noMoreSessions) {
                    const player = gameState.getPlayer(socket.id);
                    if (player) {
                        // Release all cartelas held by this player
                        for (const [cartelaNum, reservation] of gameState.globalTakenCartelas) {
                            if (reservation.telegramId === player.telegramId) {
                                gameState.globalTakenCartelas.delete(cartelaNum);
                            }
                        }
                        gameState.globalTotalSelectedCartelas = gameState.globalTakenCartelas.size;
                        
                        // Remove player from game state
                        gameState.removePlayer(socket.id);
                    }
                }
            } else {
                // Fallback: just remove player
                const player = gameState.getPlayer(socket.id);
                if (player) {
                    const hasOtherSessions = gameState.hasOtherSessions(player.telegramId, socket.id);
                    if (!hasOtherSessions) {
                        for (const [cartelaNum, reservation] of gameState.globalTakenCartelas) {
                            if (reservation.telegramId === player.telegramId) {
                                gameState.globalTakenCartelas.delete(cartelaNum);
                            }
                        }
                        gameState.globalTotalSelectedCartelas = gameState.globalTakenCartelas.size;
                        gameState.removePlayer(socket.id);
                    }
                }
            }
            
            // Broadcast updates
            broadcastRewardPool(io);
            broadcastPlayersUpdate(io);
            broadcastGameState(io);
        });
    });
    
    // ==================== RETURN FUNCTIONS FOR USE IN SERVER.JS ====================
    
    return {
        broadcastGameState: () => broadcastGameState(io),
        broadcastTimer: () => broadcastTimer(io),
        broadcastRewardPool: () => broadcastRewardPool(io),
        broadcastPlayersUpdate: () => broadcastPlayersUpdate(io),
        broadcastToUserDevices,
        syncPlayerState
    };
}

// ==================== EXPORTS ====================
module.exports = {
    initSocketIO,
    broadcastGameState,
    broadcastTimer,
    broadcastRewardPool,
    broadcastPlayersUpdate,
    broadcastToUserDevices,
    syncPlayerState
};