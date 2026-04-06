// game-server/src/game/rewardPool.js

const { config } = require("../config");

// ==================== REWARD POOL STATE ====================

let currentWinPercentage = config.DEFAULT_WIN_PERCENTAGE;

// ==================== WIN PERCENTAGE MANAGEMENT ====================

/**
 * Set the current win percentage (called by admin)
 */
function setWinPercentage(percentage) {
    if (config.WIN_PERCENTAGES.includes(percentage)) {
        currentWinPercentage = percentage;
        console.log(`💰 Win percentage changed to ${percentage}%`);
        return true;
    }
    return false;
}

/**
 * Get the current win percentage
 */
function getWinPercentage() {
    return currentWinPercentage;
}

/**
 * Get available win percentage options
 */
function getAvailableWinPercentages() {
    return [...config.WIN_PERCENTAGES];
}

/**
 * Validate if a percentage is allowed
 */
function isValidWinPercentage(percentage) {
    return config.WIN_PERCENTAGES.includes(percentage);
}

// ==================== REWARD CALCULATIONS ====================

/**
 * Calculate reward pool based on selected cartelas
 */
function calculateRewardPool(totalCartelas, betAmount = config.BET_AMOUNT, winPercentage = currentWinPercentage) {
    const totalBetAmount = totalCartelas * betAmount;
    const winnerReward = (totalBetAmount * winPercentage) / 100;
    const adminCommission = totalBetAmount - winnerReward;
    
    return {
        totalBetAmount,
        winnerReward,
        adminCommission,
        winPercentage,
        totalCartelas
    };
}

/**
 * Calculate reward per winner
 */
function calculateRewardPerWinner(totalCartelas, winnerCount, betAmount = config.BET_AMOUNT, winPercentage = currentWinPercentage) {
    if (winnerCount === 0) return 0;
    
    const { winnerReward } = calculateRewardPool(totalCartelas, betAmount, winPercentage);
    return winnerReward / winnerCount;
}

/**
 * Calculate commission amount
 */
function calculateCommission(totalCartelas, betAmount = config.BET_AMOUNT, winPercentage = currentWinPercentage) {
    const { adminCommission } = calculateRewardPool(totalCartelas, betAmount, winPercentage);
    return adminCommission;
}

// ==================== STATISTICS ====================

/**
 * Calculate house edge (percentage)
 */
function getHouseEdge() {
    return 100 - currentWinPercentage;
}

/**
 * Calculate expected return for a player (per cartela)
 */
function getExpectedReturnPerCartela(betAmount = config.BET_AMOUNT) {
    return (betAmount * currentWinPercentage) / 100;
}

// ==================== BROADCAST HELPERS ====================

/**
 * Get reward pool update object for broadcasting
 */
function getRewardPoolUpdate(totalCartelas, betAmount = config.BET_AMOUNT) {
    const { totalBetAmount, winnerReward, adminCommission } = calculateRewardPool(totalCartelas, betAmount);
    
    return {
        totalSelectedCartelas: totalCartelas,
        totalBetAmount,
        winnerReward,
        adminCommission,
        winPercentage: currentWinPercentage,
        remainingCartelas: config.TOTAL_CARTELAS - totalCartelas
    };
}

// ==================== EXPORTS ====================
module.exports = {
    currentWinPercentage,
    setWinPercentage,
    getWinPercentage,
    getAvailableWinPercentages,
    isValidWinPercentage,
    calculateRewardPool,
    calculateRewardPerWinner,
    calculateCommission,
    getHouseEdge,
    getExpectedReturnPerCartela,
    getRewardPoolUpdate,
};