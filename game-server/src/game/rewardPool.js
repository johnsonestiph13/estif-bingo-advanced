// game-server/src/game/rewardPool.js

const { config } = require("../config");

// ==================== REWARD POOL STATE ====================

let currentWinPercentage = config.DEFAULT_WIN_PERCENTAGE;

// ==================== WIN PERCENTAGE MANAGEMENT ====================

/**
 * Set the current win percentage (called by admin)
 * @param {number} percentage - Win percentage (70, 75, 76, 80)
 * @returns {boolean} - Success status
 */
function setWinPercentage(percentage) {
    if (config.WIN_PERCENTAGES.includes(percentage)) {
        currentWinPercentage = percentage;
        console.log(`💰 Win percentage changed to ${percentage}%`);
        return true;
    }
    console.warn(`⚠️ Invalid win percentage: ${percentage}. Allowed: ${config.WIN_PERCENTAGES.join(", ")}`);
    return false;
}

/**
 * Get the current win percentage
 * @returns {number}
 */
function getWinPercentage() {
    return currentWinPercentage;
}

/**
 * Get available win percentage options
 * @returns {number[]}
 */
function getAvailableWinPercentages() {
    return [...config.WIN_PERCENTAGES];
}

/**
 * Validate if a percentage is allowed
 * @param {number} percentage
 * @returns {boolean}
 */
function isValidWinPercentage(percentage) {
    return config.WIN_PERCENTAGES.includes(percentage);
}

// ==================== REWARD CALCULATIONS ====================

/**
 * Calculate reward pool based on selected cartelas
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} betAmount - Bet amount per cartela (default from config)
 * @param {number} winPercentage - Win percentage (default from current)
 * @returns {object} - Reward pool details
 */
function calculateRewardPool(totalCartelas, betAmount = config.BET_AMOUNT, winPercentage = currentWinPercentage) {
    const totalBetAmount = totalCartelas * betAmount;
    const winnerReward = (totalBetAmount * winPercentage) / 100;
    const adminCommission = totalBetAmount - winnerReward;
    
    return {
        totalBetAmount: parseFloat(totalBetAmount.toFixed(2)),
        winnerReward: parseFloat(winnerReward.toFixed(2)),
        adminCommission: parseFloat(adminCommission.toFixed(2)),
        winPercentage: winPercentage,
        totalCartelas: totalCartelas,
        betAmount: betAmount,
        houseEdge: 100 - winPercentage
    };
}

/**
 * Calculate reward per winner
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} winnerCount - Number of winners
 * @param {number} betAmount - Bet amount per cartela
 * @param {number} winPercentage - Win percentage
 * @returns {number} - Reward per winner
 */
function calculateRewardPerWinner(totalCartelas, winnerCount, betAmount = config.BET_AMOUNT, winPercentage = currentWinPercentage) {
    if (winnerCount === 0) return 0;
    
    const { winnerReward } = calculateRewardPool(totalCartelas, betAmount, winPercentage);
    const perWinner = winnerReward / winnerCount;
    return parseFloat(perWinner.toFixed(2));
}

/**
 * Calculate commission amount
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} betAmount - Bet amount per cartela
 * @param {number} winPercentage - Win percentage
 * @returns {number} - Commission amount
 */
function calculateCommission(totalCartelas, betAmount = config.BET_AMOUNT, winPercentage = currentWinPercentage) {
    const { adminCommission } = calculateRewardPool(totalCartelas, betAmount, winPercentage);
    return adminCommission;
}

/**
 * Calculate total bet amount
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} betAmount - Bet amount per cartela
 * @returns {number}
 */
function calculateTotalBet(totalCartelas, betAmount = config.BET_AMOUNT) {
    return parseFloat((totalCartelas * betAmount).toFixed(2));
}

/**
 * Calculate winner reward amount
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} betAmount - Bet amount per cartela
 * @param {number} winPercentage - Win percentage
 * @returns {number}
 */
function calculateWinnerReward(totalCartelas, betAmount = config.BET_AMOUNT, winPercentage = currentWinPercentage) {
    const totalBet = calculateTotalBet(totalCartelas, betAmount);
    return parseFloat(((totalBet * winPercentage) / 100).toFixed(2));
}

// ==================== STATISTICS ====================

/**
 * Calculate house edge (percentage)
 * @returns {number}
 */
function getHouseEdge() {
    return 100 - currentWinPercentage;
}

/**
 * Calculate expected return for a player (per cartela)
 * @param {number} betAmount - Bet amount per cartela
 * @returns {number}
 */
function getExpectedReturnPerCartela(betAmount = config.BET_AMOUNT) {
    return parseFloat(((betAmount * currentWinPercentage) / 100).toFixed(2));
}

/**
 * Get the percentage of total pool that goes to winners
 * @returns {number}
 */
function getWinnerPercentage() {
    return currentWinPercentage;
}

/**
 * Get the percentage of total pool that goes to commission
 * @returns {number}
 */
function getCommissionPercentage() {
    return 100 - currentWinPercentage;
}

// ==================== BROADCAST HELPERS ====================

/**
 * Get reward pool update object for broadcasting
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} betAmount - Bet amount per cartela
 * @returns {object} - Reward pool update object
 */
function getRewardPoolUpdate(totalCartelas, betAmount = config.BET_AMOUNT) {
    const { totalBetAmount, winnerReward, adminCommission } = calculateRewardPool(totalCartelas, betAmount);
    const totalCartelasAvailable = config.TOTAL_CARTELAS || 1000;
    
    return {
        totalSelectedCartelas: totalCartelas,
        totalBetAmount: totalBetAmount,
        winnerReward: winnerReward,
        adminCommission: adminCommission,
        winPercentage: currentWinPercentage,
        remainingCartelas: totalCartelasAvailable - totalCartelas,
        totalCartelas: totalCartelasAvailable,
        houseEdge: getHouseEdge()
    };
}

/**
 * Get winner payout details for broadcasting
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} winnerCount - Number of winners
 * @param {number} betAmount - Bet amount per cartela
 * @returns {object} - Winner payout details
 */
function getWinnerPayoutDetails(totalCartelas, winnerCount, betAmount = config.BET_AMOUNT) {
    const { totalBetAmount, winnerReward, adminCommission } = calculateRewardPool(totalCartelas, betAmount);
    const perWinner = winnerCount > 0 ? winnerReward / winnerCount : 0;
    
    return {
        totalBetAmount: totalBetAmount,
        totalPrizePool: winnerReward,
        commission: adminCommission,
        winnerCount: winnerCount,
        perWinnerAmount: parseFloat(perWinner.toFixed(2)),
        winPercentage: currentWinPercentage
    };
}

// ==================== VALIDATION ====================

/**
 * Validate reward pool calculation
 * @param {number} totalCartelas - Number of selected cartelas
 * @param {number} betAmount - Bet amount per cartela
 * @returns {boolean}
 */
function validateRewardPool(totalCartelas, betAmount = config.BET_AMOUNT) {
    const { totalBetAmount, winnerReward, adminCommission } = calculateRewardPool(totalCartelas, betAmount);
    const sum = winnerReward + adminCommission;
    return Math.abs(sum - totalBetAmount) < 0.01; // Allow small floating point errors
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
    calculateTotalBet,
    calculateWinnerReward,
    getHouseEdge,
    getExpectedReturnPerCartela,
    getWinnerPercentage,
    getCommissionPercentage,
    getRewardPoolUpdate,
    getWinnerPayoutDetails,
    validateRewardPool,
};