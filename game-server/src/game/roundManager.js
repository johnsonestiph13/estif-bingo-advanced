// game-server/src/game/roundManager.js

const { config } = require("../config");
const gameState = require("./gameState");
const { calculateRewardPool, getWinPercentage } = require("./rewardPool");
const { checkBingoWin, getBingoLetter } = require("./cartela");

// ==================== ROUND STATE ====================

let currentNumbers = [];
let currentNumberIndex = 0;

// ==================== HELPER FUNCTIONS ====================

/**
 * Format time for display (mm:ss)
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Generate shuffled numbers 1-75 for the game
 */
function generateShuffledNumbers() {
    const numbers = Array.from({ length: 75 }, (_, i) => i + 1);
    for (let i = numbers.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
    }
    return numbers;
}

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
        winPercentage: gameState.getWinPercentage(),
        totalBet: gameState.gameState.totalBet,
        winnerReward: gameState.gameState.winnerReward
    });
}

/**
 * Broadcast timer update
 */
function broadcastTimer(io) {
    io.emit("timerUpdate", {
        seconds: gameState.gameState.timer,
        round: gameState.gameState.round,
        formatted: formatTime(gameState.gameState.timer),
        phase: gameState.gameState.status
    });
}

// ==================== ROUND PROGRESSION ====================

/**
 * Start the selection phase (players pick cartelas)
 */
function startSelectionPhase(io) {
    gameState.clearAllTimers();
    gameState.setGameStatus("selection");
    gameState.setGameTimer(config.SELECTION_TIME);
    gameState.setRoundStartTime(new Date());
    gameState.setGameActive(false);
    
    broadcastGameState(io);
    broadcastTimer(io);
    
    // Start countdown timer
    const timer = setInterval(() => {
        if (gameState.gameState.status !== "selection") {
            clearInterval(timer);
            gameState.setSelectionTimer(null);
            return;
        }
        
        const newTimer = gameState.gameState.timer - 1;
        gameState.setGameTimer(newTimer);
        broadcastTimer(io);
        
        // Warning at 10 seconds
        if (newTimer === 10) {
            io.emit("warning", { 
                message: "⚠️ Only 10 seconds left to select cartelas!", 
                type: "warning" 
            });
        }
        
        // Play countdown sound for last 3 seconds
        if (newTimer <= 3 && newTimer > 0) {
            io.emit("countdownTick", { seconds: newTimer });
        }
        
        // Time's up - start active game
        if (newTimer <= 0) {
            clearInterval(timer);
            gameState.setSelectionTimer(null);
            startActiveGame(io);
        }
    }, 1000);
    
    gameState.setSelectionTimer(timer);
}

/**
 * Start the active game phase (drawing numbers)
 */
function startActiveGame(io) {
    gameState.setGameStatus("active");
    gameState.clearDrawnNumbers();
    gameState.clearWinners();
    gameState.setGameActive(true);
    
    const totalCartelas = gameState.getTotalSelectedCartelasCount();
    const activePlayersCount = gameState.getActivePlayersCount();
    const { totalBetAmount, winnerReward, adminCommission } = calculateRewardPool(
        totalCartelas,
        config.BET_AMOUNT,
        getWinPercentage()
    );
    
    gameState.setRewardPool(totalBetAmount, winnerReward, adminCommission);
    
    broadcastGameState(io);
    
    // Announce game start
    io.emit("gameStarted", {
        round: gameState.gameState.round,
        totalPlayers: activePlayersCount,
        totalCartelas: totalCartelas,
        totalBet: totalBetAmount,
        winnerReward: winnerReward,
        winPercentage: getWinPercentage(),
        message: `🎲 Game started! ${totalCartelas} cartelas selected. Prize Pool: ${winnerReward} ETB`
    });
    
    io.emit("finalRewardPool", {
        totalSelectedCartelas: totalCartelas,
        totalBetAmount: totalBetAmount,
        winnerReward: winnerReward,
        winPercentage: getWinPercentage(),
        message: `🎯 ${totalCartelas} cartelas selected! Total pool: ${totalBetAmount} ETB. Winner takes ${winnerReward} ETB!`
    });
    
    // Prepare and start number drawing
    currentNumbers = generateShuffledNumbers();
    currentNumberIndex = 0;
    
    const drawTimer = setInterval(() => {
        // Stop if game not active or winners exist
        if (gameState.gameState.status !== "active" || 
            !gameState.gameState.gameActive || 
            gameState.gameState.winners.length > 0) {
            clearInterval(drawTimer);
            gameState.setDrawTimer(null);
            return;
        }
        
        // No more numbers? End round with no winners
        if (currentNumberIndex >= currentNumbers.length) {
            clearInterval(drawTimer);
            gameState.setDrawTimer(null);
            endRound(io, []);
            return;
        }
        
        // Draw next number
        const number = currentNumbers[currentNumberIndex++];
        gameState.addDrawnNumber(number);
        
        io.emit("numberDrawn", {
            number: number,
            letter: getBingoLetter(number),
            drawnCount: gameState.gameState.drawnNumbers.length,
            remaining: 75 - gameState.gameState.drawnNumbers.length,
            numbers: gameState.gameState.drawnNumbers
        });
        
        broadcastGameState(io);
        
        // Check for winners
        const winners = checkForWinners();
        if (winners.length > 0 && gameState.gameState.winners.length === 0) {
            clearInterval(drawTimer);
            gameState.setDrawTimer(null);
            endRound(io, winners);
        }
    }, config.DRAW_INTERVAL);
    
    gameState.setDrawTimer(drawTimer);
}

/**
 * Check for winners among all players
 * Returns array of winner objects with their winning cartela details
 */
function checkForWinners() {
    const winners = [];
    const drawnNumbers = gameState.gameState.drawnNumbers;
    
    for (const [socketId, player] of gameState.gameState.players) {
        if (player.selectedCartelas.length === 0) continue;
        if (gameState.gameState.winners.includes(socketId)) continue;
        
        for (const cartelaId of player.selectedCartelas) {
            const { won, winningLines, pattern } = checkBingoWin(cartelaId, drawnNumbers);
            if (won) {
                winners.push({
                    socketId,
                    cartelaId,
                    winningLines,
                    pattern: pattern || winningLines[0],
                    username: player.username,
                    telegramId: player.telegramId,
                    balance: player.balance
                });
                break; // One winning cartela is enough
            }
        }
    }
    
    return winners;
}

/**
 * End the current round and distribute rewards
 */
async function endRound(io, winnerDetails) {
    if (gameState.gameState.status !== "active") return;
    
    gameState.clearDrawTimer();
    gameState.setGameStatus("ended");
    gameState.setWinners(winnerDetails.map(w => w.socketId));
    gameState.setRoundEndTime(new Date());
    
    const winnerCount = winnerDetails.length;
    const perWinner = winnerCount > 0 ? gameState.gameState.winnerReward / winnerCount : 0;
    
    const winnerNames = [];
    const winnerCartelas = [];
    
    // Process winners
    for (const winner of winnerDetails) {
        const player = gameState.getPlayer(winner.socketId);
        if (!player) continue;
        
        winnerNames.push(player.username);
        winnerCartelas.push({
            username: player.username,
            cartelaId: winner.cartelaId,
            winningLines: winner.winningLines,
            pattern: winner.pattern
        });
        
        // Notify winner
        io.to(winner.socketId).emit("youWon", {
            amount: perWinner,
            cartelaId: winner.cartelaId,
            winningLines: winner.winningLines,
            pattern: winner.pattern,
            newBalance: player.balance + perWinner,
            message: `🎉 You won ${perWinner.toFixed(2)} ETB!`
        });
        
        // Update player stats (balance will be updated via bot API)
        player.totalWon = (player.totalWon || 0) + perWinner;
        player.gamesWon = (player.gamesWon || 0) + 1;
    }
    
    // Update total played for all players who had cartelas
    for (const [socketId, player] of gameState.gameState.players) {
        if (player.selectedCartelas.length > 0) {
            player.totalPlayed = (player.totalPlayed || 0) + 1;
        }
    }
    
    // Announce round end
    io.emit("roundEnded", {
        winners: winnerNames,
        winnerCartelas: winnerCartelas,
        winnerCount: winnerCount,
        prizePerWinner: perWinner,
        totalPrize: gameState.gameState.winnerReward,
        totalPool: gameState.gameState.totalBet,
        commission: gameState.gameState.adminCommission,
        winPercentage: gameState.getWinPercentage(),
        round: gameState.gameState.round,
        message: winnerCount > 0 
            ? `🎉 BINGO! Winners: ${winnerNames.join(", ")}. Each wins ${perWinner.toFixed(2)} ETB!`
            : "No winners this round!"
    });
    
    broadcastGameState(io);
    
    // Schedule next round
    scheduleNextRound(io);
}

/**
 * Schedule the next round with countdown
 */
function scheduleNextRound(io) {
    let countdown = config.NEXT_ROUND_DELAY / 1000;
    
    const countdownInterval = setInterval(() => {
        io.emit("nextRoundCountdown", { seconds: countdown });
        countdown--;
        if (countdown < 0) {
            clearInterval(countdownInterval);
        }
    }, 1000);
    
    const timer = setTimeout(() => {
        resetForNextRound(io);
        gameState.setNextRoundTimer(null);
    }, config.NEXT_ROUND_DELAY);
    
    gameState.setNextRoundTimer(timer);
}

/**
 * Reset game state for the next round
 */
function resetForNextRound(io) {
    gameState.clearAllPlayerCartelas();
    gameState.clearAllCartelas();
    gameState.setGameRound(gameState.gameState.round + 1);
    gameState.resetForNewRound();
    
    broadcastGameState(io);
    broadcastTimer(io);
    
    io.emit("newRound", {
        round: gameState.gameState.round,
        timer: config.SELECTION_TIME,
        winPercentage: gameState.getWinPercentage(),
        message: `🎲 Round ${gameState.gameState.round} starting! Select up to ${config.MAX_CARTELAS} cartelas within ${config.SELECTION_TIME} seconds.`
    });
    
    startSelectionPhase(io);
}

/**
 * Force end current round (admin action)
 */
function forceEndRound(io) {
    if (gameState.gameState.status === "active") {
        gameState.clearDrawTimer();
        endRound(io, []);
        return true;
    }
    return false;
}

/**
 * Force start next round (admin action)
 */
function forceStartRound(io) {
    if (gameState.gameState.status === "selection") {
        gameState.clearSelectionTimer();
        startActiveGame(io);
        return true;
    }
    return false;
}

/**
 * Get current round number
 */
function getCurrentRound() {
    return gameState.gameState.round;
}

/**
 * Get current round status
 */
function getRoundStatus() {
    return {
        round: gameState.gameState.round,
        status: gameState.gameState.status,
        timer: gameState.gameState.timer,
        drawnNumbers: gameState.gameState.drawnNumbers.length,
        winners: gameState.gameState.winners.length,
        totalBet: gameState.gameState.totalBet,
        winnerReward: gameState.gameState.winnerReward
    };
}

// ==================== EXPORTS ====================
module.exports = {
    formatTime,
    generateShuffledNumbers,
    broadcastGameState,
    broadcastTimer,
    startSelectionPhase,
    startActiveGame,
    checkForWinners,
    endRound,
    scheduleNextRound,
    resetForNextRound,
    forceEndRound,
    forceStartRound,
    getCurrentRound,
    getRoundStatus,
};