// game-server/src/game/gameState.js

const { config } = require("../config");

// ==================== GLOBAL GAME STATE ====================

// Main game state object
let gameState = {
    status: "selection",      // selection, active, ended
    round: 1,
    timer: config.SELECTION_TIME,
    drawnNumbers: [],
    winners: [],
    players: new Map(),       // socketId -> player object
    totalBet: 0,
    winnerReward: 0,
    adminCommission: 0,
    winPercentage: config.DEFAULT_WIN_PERCENTAGE,
    roundStartTime: null,
    roundEndTime: null,
    gameActive: false
};

// Cartela tracking
let globalTakenCartelas = new Map();     // cartelaNumber -> { telegramId, username, timestamp }
let globalTotalSelectedCartelas = 0;

// Session tracking
let activeSessions = new Map();          // telegramId -> Set of socketIds

// Timer references
let selectionTimer = null;
let drawTimer = null;
let nextRoundTimer = null;

// ==================== PLAYER MANAGEMENT ====================

/**
 * Add or update a player in game state
 */
function addPlayer(socketId, playerData) {
    gameState.players.set(socketId, playerData);
    return playerData;
}

/**
 * Remove a player from game state
 */
function removePlayer(socketId) {
    const player = gameState.players.get(socketId);
    if (player) {
        gameState.players.delete(socketId);
        return player;
    }
    return null;
}

/**
 * Get player by socket ID
 */
function getPlayer(socketId) {
    return gameState.players.get(socketId);
}

/**
 * Get player by Telegram ID
 */
function getPlayerByTelegramId(telegramId) {
    for (const [socketId, player] of gameState.players) {
        if (player.telegramId === telegramId) {
            return { socketId, player };
        }
    }
    return null;
}

/**
 * Get all players as array (for broadcasting)
 */
function getAllPlayers() {
    return Array.from(gameState.players.values()).map(p => ({
        socketId: p.socketId,
        username: p.username,
        telegramId: p.telegramId,
        selectedCartelas: p.selectedCartelas,
        selectedCount: p.selectedCartelas.length,
        balance: p.balance
    }));
}

/**
 * Get players with cartelas selected
 */
function getActivePlayers() {
    return Array.from(gameState.players.values()).filter(p => p.selectedCartelas.length > 0);
}

/**
 * Update player balance
 */
function updatePlayerBalance(socketId, newBalance) {
    const player = gameState.players.get(socketId);
    if (player) {
        player.balance = newBalance;
        return true;
    }
    return false;
}

/**
 * Add selected cartela to player
 */
function addPlayerCartela(socketId, cartelaNumber) {
    const player = gameState.players.get(socketId);
    if (player && !player.selectedCartelas.includes(cartelaNumber)) {
        player.selectedCartelas.push(cartelaNumber);
        return true;
    }
    return false;
}

/**
 * Remove selected cartela from player
 */
function removePlayerCartela(socketId, cartelaNumber) {
    const player = gameState.players.get(socketId);
    if (player) {
        const index = player.selectedCartelas.indexOf(cartelaNumber);
        if (index !== -1) {
            player.selectedCartelas.splice(index, 1);
            return true;
        }
    }
    return false;
}

/**
 * Clear all player cartelas (for next round)
 */
function clearAllPlayerCartelas() {
    for (const [socketId, player] of gameState.players) {
        player.selectedCartelas = [];
    }
}

/**
 * Increment player stats (wins, played)
 */
function incrementPlayerStats(socketId, winAmount = 0) {
    const player = gameState.players.get(socketId);
    if (player) {
        player.totalPlayed = (player.totalPlayed || 0) + 1;
        if (winAmount > 0) {
            player.totalWon = (player.totalWon || 0) + winAmount;
            player.gamesWon = (player.gamesWon || 0) + 1;
        }
    }
}

// ==================== CARTELA MANAGEMENT ====================

/**
 * Reserve a cartela for a player
 */
function reserveCartela(cartelaNumber, telegramId, username) {
    if (globalTakenCartelas.has(cartelaNumber)) {
        return false;
    }
    globalTakenCartelas.set(cartelaNumber, {
        telegramId,
        username,
        timestamp: Date.now()
    });
    globalTotalSelectedCartelas = globalTakenCartelas.size;
    return true;
}

/**
 * Release a cartela reservation
 */
function releaseCartela(cartelaNumber, telegramId) {
    const cartela = globalTakenCartelas.get(cartelaNumber);
    if (cartela && cartela.telegramId === telegramId) {
        globalTakenCartelas.delete(cartelaNumber);
        globalTotalSelectedCartelas = globalTakenCartelas.size;
        return true;
    }
    return false;
}

/**
 * Check if cartela is available
 */
function isCartelaAvailable(cartelaNumber) {
    return !globalTakenCartelas.has(cartelaNumber);
}

/**
 * Get cartela owner info
 */
function getCartelaOwner(cartelaNumber) {
    return globalTakenCartelas.get(cartelaNumber);
}

/**
 * Get all reserved cartelas
 */
function getAllReservedCartelas() {
    return Array.from(globalTakenCartelas.entries()).map(([number, data]) => ({
        cartelaNumber: number,
        telegramId: data.telegramId,
        username: data.username
    }));
}

/**
 * Clear all cartela reservations (for next round)
 */
function clearAllCartelas() {
    globalTakenCartelas.clear();
    globalTotalSelectedCartelas = 0;
}

// ==================== SESSION MANAGEMENT (Multi-device) ====================

/**
 * Add socket to user's active sessions
 */
function addUserSession(telegramId, socketId) {
    if (!activeSessions.has(telegramId)) {
        activeSessions.set(telegramId, new Set());
    }
    activeSessions.get(telegramId).add(socketId);
}

/**
 * Remove socket from user's active sessions
 */
function removeUserSession(telegramId, socketId) {
    const sessions = activeSessions.get(telegramId);
    if (sessions) {
        sessions.delete(socketId);
        if (sessions.size === 0) {
            activeSessions.delete(telegramId);
            return true; // No more sessions for this user
        }
    }
    return false;
}

/**
 * Check if user has other active sessions
 */
function hasOtherSessions(telegramId, currentSocketId) {
    const sessions = activeSessions.get(telegramId);
    if (!sessions) return false;
    for (const socketId of sessions) {
        if (socketId !== currentSocketId) {
            return true;
        }
    }
    return false;
}

/**
 * Get all active socket IDs for a user
 */
function getUserSessions(telegramId) {
    const sessions = activeSessions.get(telegramId);
    return sessions ? Array.from(sessions) : [];
}

// ==================== GAME STATE SETTERS/GETTERS ====================

function getGameState() {
    return { ...gameState, players: getAllPlayers() };
}

function setGameStatus(status) {
    gameState.status = status;
}

function setGameRound(round) {
    gameState.round = round;
}

function setGameTimer(timer) {
    gameState.timer = timer;
}

function addDrawnNumber(number) {
    gameState.drawnNumbers.push(number);
}

function clearDrawnNumbers() {
    gameState.drawnNumbers = [];
}

function setWinners(winners) {
    gameState.winners = winners;
}

function clearWinners() {
    gameState.winners = [];
}

function setRewardPool(totalBet, winnerReward, adminCommission) {
    gameState.totalBet = totalBet;
    gameState.winnerReward = winnerReward;
    gameState.adminCommission = adminCommission;
}

function setWinPercentage(percentage) {
    gameState.winPercentage = percentage;
}

function setGameActive(active) {
    gameState.gameActive = active;
}

function setRoundStartTime(time) {
    gameState.roundStartTime = time;
}

function setRoundEndTime(time) {
    gameState.roundEndTime = time;
}

// ==================== TIMER MANAGEMENT ====================

function setSelectionTimer(timer) {
    selectionTimer = timer;
}

function getSelectionTimer() {
    return selectionTimer;
}

function clearSelectionTimer() {
    if (selectionTimer) {
        clearInterval(selectionTimer);
        selectionTimer = null;
    }
}

function setDrawTimer(timer) {
    drawTimer = timer;
}

function getDrawTimer() {
    return drawTimer;
}

function clearDrawTimer() {
    if (drawTimer) {
        clearInterval(drawTimer);
        drawTimer = null;
    }
}

function setNextRoundTimer(timer) {
    nextRoundTimer = timer;
}

function getNextRoundTimer() {
    return nextRoundTimer;
}

function clearNextRoundTimer() {
    if (nextRoundTimer) {
        clearTimeout(nextRoundTimer);
        nextRoundTimer = null;
    }
}

function clearAllTimers() {
    clearSelectionTimer();
    clearDrawTimer();
    clearNextRoundTimer();
}

// ==================== STATISTICS ====================

function getTotalPlayersCount() {
    return gameState.players.size;
}

function getTotalSelectedCartelasCount() {
    return globalTotalSelectedCartelas;
}

function getActivePlayersCount() {
    return Array.from(gameState.players.values()).filter(p => p.selectedCartelas.length > 0).length;
}

// ==================== RESET FUNCTIONS ====================

/**
 * Reset game state for a new round (keep players)
 */
function resetForNewRound() {
    clearAllPlayerCartelas();
    clearAllCartelas();
    clearDrawnNumbers();
    clearWinners();
    gameState.status = "selection";
    gameState.timer = config.SELECTION_TIME;
    gameState.totalBet = 0;
    gameState.winnerReward = 0;
    gameState.adminCommission = 0;
    gameState.gameActive = false;
    gameState.roundStartTime = null;
    gameState.roundEndTime = null;
}

/**
 * Full game reset (round 1, keep players)
 */
function fullGameReset() {
    clearAllTimers();
    clearAllPlayerCartelas();
    clearAllCartelas();
    clearDrawnNumbers();
    clearWinners();
    gameState = {
        status: "selection",
        round: 1,
        timer: config.SELECTION_TIME,
        drawnNumbers: [],
        winners: [],
        players: gameState.players, // Preserve players
        totalBet: 0,
        winnerReward: 0,
        adminCommission: 0,
        winPercentage: config.DEFAULT_WIN_PERCENTAGE,
        roundStartTime: null,
        roundEndTime: null,
        gameActive: false
    };
}

// ==================== EXPORTS ====================
module.exports = {
    // State object (for direct access when needed)
    gameState,
    globalTakenCartelas,
    globalTotalSelectedCartelas,
    activeSessions,
    selectionTimer,
    drawTimer,
    nextRoundTimer,
    
    // Player management
    addPlayer,
    removePlayer,
    getPlayer,
    getPlayerByTelegramId,
    getAllPlayers,
    getActivePlayers,
    updatePlayerBalance,
    addPlayerCartela,
    removePlayerCartela,
    clearAllPlayerCartelas,
    incrementPlayerStats,
    
    // Cartela management
    reserveCartela,
    releaseCartela,
    isCartelaAvailable,
    getCartelaOwner,
    getAllReservedCartelas,
    clearAllCartelas,
    
    // Session management
    addUserSession,
    removeUserSession,
    hasOtherSessions,
    getUserSessions,
    
    // Game state getters/setters
    getGameState,
    setGameStatus,
    setGameRound,
    setGameTimer,
    addDrawnNumber,
    clearDrawnNumbers,
    setWinners,
    clearWinners,
    setRewardPool,
    setWinPercentage,
    setGameActive,
    setRoundStartTime,
    setRoundEndTime,
    
    // Timer management
    setSelectionTimer,
    getSelectionTimer,
    clearSelectionTimer,
    setDrawTimer,
    getDrawTimer,
    clearDrawTimer,
    setNextRoundTimer,
    getNextRoundTimer,
    clearNextRoundTimer,
    clearAllTimers,
    
    // Statistics
    getTotalPlayersCount,
    getTotalSelectedCartelasCount,
    getActivePlayersCount,
    
    // Reset
    resetForNewRound,
    fullGameReset,
};