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

// ==================== ROUND PROGRESSION ====================

/**
 * Start the selection phase (players pick cartelas)
 */
function startSelectionPhase(io, broadcastGameState, broadcastTimer) {
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
        
        // Time's up - start active game
        if (newTimer <= 0) {
            clearInterval(timer);
            gameState.setSelectionTimer(null);
            startActiveGame(io, broadcastGameState);
        }
    }, 1000);
    
    gameState.setSelectionTimer(timer);
}

/**
 * Start the active game phase (drawing numbers)
 */
function startActiveGame(io, broadcastGameState) {
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
            endRound(io, [], broadcastGameState);
            return;
        }
        
        // Draw next number
        const number = currentNumbers[currentNumberIndex++];
        gameState.addDrawnNumber(number);
        
        io.emit("numberDrawn", {
            number: number,
            letter: getBingoLetter(number),
            drawnCount: gameState.gameState.drawnNumbers.length,
            remaining: 75 - gameState.gameState.drawnNumbers.length
        });
        
        broadcastGameState(io);
        
        // Check for winners
        const winners = checkForWinners();
        if (winners.length > 0 && gameState.gameState.winners.length === 0) {
            clearInterval(drawTimer);
            gameState.setDrawTimer(null);
            endRound(io, winners, broadcastGameState);
        }
    }, config.DRAW_INTERVAL);
    
    gameState.setDrawTimer(drawTimer);
}

/**
 * Check for winners among all players
 * Returns array of winner socket IDs with their winning cartela details
 */
function checkForWinners() {
    const winners = [];
    const winnerDetails = [];
    const drawnNumbers = gameState.gameState.drawnNumbers;
    
    for (const [socketId, player] of gameState.gameState.players) {
        if (player.selectedCartelas.length === 0) continue;
        if (gameState.gameState.winners.includes(socketId)) continue;
        
        for (const cartelaId of player.selectedCartelas) {
            const { won, winningLines } = checkBingoWin(cartelaId, drawnNumbers);
            if (won) {
                winners.push(socketId);
                winnerDetails.push({
                    socketId,
                    cartelaId,
                    winningLines,
                    username: player.username,
                    telegramId: player.telegramId
                });
                break; // One winning cartela is enough
            }
        }
    }
    
    return winnerDetails;
}

/**
 * End the current round and distribute rewards
 */
async function endRound(io, winnerDetails, broadcastGameState, saveRoundCallback, addBalanceCallback, logTransactionCallback) {
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
            winningLines: winner.winningLines
        });
        
        // Update player stats
        player.balance += perWinner;
        player.totalWon = (player.totalWon || 0) + perWinner;
        player.gamesWon = (player.gamesWon || 0) + 1;
        
        // Notify winner
        io.to(winner.socketId).emit("youWon", {
            amount: perWinner,
            cartelaId: winner.cartelaId,
            winningLines: winner.winningLines,
            newBalance: player.balance,
            message: `🎉 You won ${perWinner.toFixed(2)} ETB!`
        });
        
        // Update balance via bot API
        if (addBalanceCallback) {
            try {
                const result = await addBalanceCallback(player.telegramId, perWinner, `won round ${gameState.gameState.round}`);
                if (result.success) {
                    player.balance = result.new_balance;
                }
            } catch (err) {
                console.error("Failed to add winnings:", err);
            }
        }
        
        // Log transaction
        if (logTransactionCallback) {
            await logTransactionCallback(player.telegramId, player.username, "win", perWinner, winner.cartelaId, gameState.gameState.round, "Round win");
        }
    }
    
    // Update total played for all players
    for (const [socketId, player] of gameState.gameState.players) {
        if (player.selectedCartelas.length > 0) {
            player.totalPlayed = (player.totalPlayed || 0) + 1;
        }
    }
    
    // Save round to database
    if (saveRoundCallback) {
        await saveRoundCallback({
            roundNumber: gameState.gameState.round,
            totalPlayers: gameState.getActivePlayersCount(),
            totalCartelas: gameState.getTotalSelectedCartelasCount(),
            totalPool: gameState.gameState.totalBet,
            winnerReward: gameState.gameState.winnerReward,
            adminCommission: gameState.gameState.adminCommission,
            winners: winnerNames,
            winnerCartelas: winnerCartelas,
            winPercentage: getWinPercentage(),
            timestamp: new Date().toISOString()
        });
    }
    
    // Announce round end
    io.emit("roundEnded", {
        winners: winnerNames,
        winnerCartelas: winnerCartelas,
        winnerCount: winnerCount,
        winnerReward: perWinner,
        totalPool: gameState.gameState.totalBet,
        adminCommission: gameState.gameState.adminCommission,
        winPercentage: getWinPercentage(),
        round: gameState.gameState.round,
        message: winnerCount > 0 
            ? `🎉 BINGO! Winners: ${winnerNames.join(", ")}. Each wins ${perWinner.toFixed(2)} ETB!`
            : "No winners this round!"
    });
    
    broadcastGameState(io);
    
    // Schedule next round
    scheduleNextRound(io, broadcastGameState, broadcastTimer);
}

/**
 * Schedule the next round with countdown
 */
function scheduleNextRound(io, broadcastGameState, broadcastTimer) {
    let countdown = config.NEXT_ROUND_DELAY / 1000;
    
    const countdownInterval = setInterval(() => {
        io.emit("nextRoundCountdown", { seconds: countdown });
        countdown--;
        if (countdown < 0) {
            clearInterval(countdownInterval);
        }
    }, 1000);
    
    const timer = setTimeout(() => {
        resetForNextRound(io, broadcastGameState, broadcastTimer);
        gameState.setNextRoundTimer(null);
    }, config.NEXT_ROUND_DELAY);
    
    gameState.setNextRoundTimer(timer);
}

/**
 * Reset game state for the next round
 */
function resetForNextRound(io, broadcastGameState, broadcastTimer) {
    gameState.clearAllPlayerCartelas();
    gameState.clearAllCartelas();
    gameState.clearActiveSelectionsForRound(gameState.gameState.round);
    gameState.setGameRound(gameState.gameState.round + 1);
    gameState.resetForNewRound();
    
    broadcastGameState(io);
    broadcastTimer(io);
    
    io.emit("nextRound", {
        round: gameState.gameState.round,
        timer: config.SELECTION_TIME,
        message: `🎲 Round ${gameState.gameState.round} starting! Select up to ${config.MAX_CARTELAS} cartelas within ${config.SELECTION_TIME} seconds.`
    });
    
    startSelectionPhase(io, broadcastGameState, broadcastTimer);
}

// ==================== EXPORTS ====================
module.exports = {
    formatTime,
    generateShuffledNumbers,
    startSelectionPhase,
    startActiveGame,
    checkForWinners,
    endRound,
    scheduleNextRound,
    resetForNextRound,
};