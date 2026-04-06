// game-server/src/services/botClient.js

const fetch = require("node-fetch");
const { config } = require("../config");

// ==================== CONFIGURATION ====================

const BOT_API_URL = config.BOT_API_URL;
const API_SECRET = config.API_SECRET;
const TIMEOUT = config.BOT_API_TIMEOUT || 5000;
const MAX_RETRIES = config.BOT_API_RETRIES || 3;
const RETRY_DELAY = 1000; // 1 second base delay

// ==================== HELPER FUNCTIONS ====================

/**
 * Delay function for retry backoff
 */
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Make a request to the bot API with retry logic
 */
async function makeRequest(endpoint, method = "POST", body = null, retries = MAX_RETRIES) {
    const url = `${BOT_API_URL}${endpoint}`;
    const headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_SECRET
    };
    
    const options = {
        method,
        headers,
        signal: AbortSignal.timeout(TIMEOUT)
    };
    
    if (body && (method === "POST" || method === "PUT")) {
        options.body = JSON.stringify(body);
    }
    
    let lastError = null;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return data;
        } catch (err) {
            lastError = err;
            console.warn(`Bot API request failed (attempt ${attempt}/${retries}): ${err.message}`);
            
            if (attempt < retries) {
                // Exponential backoff
                const backoffDelay = RETRY_DELAY * Math.pow(2, attempt - 1);
                await delay(backoffDelay);
            }
        }
    }
    
    throw new Error(`Failed after ${retries} attempts: ${lastError.message}`);
}

/**
 * Make a GET request to the bot API
 */
async function getRequest(endpoint, retries = MAX_RETRIES) {
    const url = `${BOT_API_URL}${endpoint}`;
    const headers = {
        "X-API-Key": API_SECRET
    };
    
    const options = {
        method: "GET",
        headers,
        signal: AbortSignal.timeout(TIMEOUT)
    };
    
    let lastError = null;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return data;
        } catch (err) {
            lastError = err;
            console.warn(`Bot API GET request failed (attempt ${attempt}/${retries}): ${err.message}`);
            
            if (attempt < retries) {
                const backoffDelay = RETRY_DELAY * Math.pow(2, attempt - 1);
                await delay(backoffDelay);
            }
        }
    }
    
    throw new Error(`Failed after ${retries} attempts: ${lastError.message}`);
}

// ==================== AUTHENTICATION ENDPOINTS ====================

/**
 * Verify a JWT token with the bot
 * @param {string} token - JWT token to verify
 * @returns {Promise<{valid: boolean, telegram_id?: number, username?: string, balance?: number}>}
 */
async function verifyToken(token) {
    try {
        const data = await makeRequest("/api/verify-token", "POST", { token });
        return {
            valid: data.valid,
            telegram_id: data.telegram_id,
            username: data.username,
            balance: data.balance
        };
    } catch (err) {
        console.error("Token verification failed:", err);
        return { valid: false, error: err.message };
    }
}

/**
 * Exchange a one-time code for a JWT token
 * @param {string} code - One-time code from bot
 * @returns {Promise<{success: boolean, token?: string, telegram_id?: number, username?: string, balance?: number}>}
 */
async function exchangeCode(code) {
    try {
        const data = await makeRequest("/api/exchange-code", "POST", { code });
        return {
            success: data.success,
            token: data.token,
            telegram_id: data.telegram_id,
            username: data.username,
            balance: data.balance
        };
    } catch (err) {
        console.error("Code exchange failed:", err);
        return { success: false, error: err.message };
    }
}

// ==================== BALANCE MANAGEMENT ENDPOINTS ====================

/**
 * Deduct balance from a user
 * @param {number} telegramId - User's Telegram ID
 * @param {number} amount - Amount to deduct
 * @param {string} reason - Reason for deduction
 * @returns {Promise<{success: boolean, new_balance?: number, message?: string}>}
 */
async function deductBalance(telegramId, amount, reason = "") {
    try {
        const data = await makeRequest("/api/deduct", "POST", {
            telegram_id: telegramId,
            amount,
            reason
        });
        return {
            success: data.success,
            new_balance: data.new_balance,
            message: data.message
        };
    } catch (err) {
        console.error(`Balance deduction failed for user ${telegramId}:`, err);
        return { success: false, error: err.message };
    }
}

/**
 * Add balance to a user
 * @param {number} telegramId - User's Telegram ID
 * @param {number} amount - Amount to add
 * @param {string} reason - Reason for addition
 * @returns {Promise<{success: boolean, new_balance?: number, message?: string}>}
 */
async function addBalance(telegramId, amount, reason = "") {
    try {
        const data = await makeRequest("/api/add", "POST", {
            telegram_id: telegramId,
            amount,
            reason
        });
        return {
            success: data.success,
            new_balance: data.new_balance,
            message: data.message
        };
    } catch (err) {
        console.error(`Balance addition failed for user ${telegramId}:`, err);
        return { success: false, error: err.message };
    }
}

/**
 * Get user's current balance
 * @param {number} telegramId - User's Telegram ID
 * @returns {Promise<{success: boolean, balance?: number, message?: string}>}
 */
async function getUserBalance(telegramId) {
    try {
        const data = await makeRequest("/api/get-balance", "POST", {
            telegram_id: telegramId
        });
        return {
            success: data.success,
            balance: data.balance,
            message: data.message
        };
    } catch (err) {
        console.error(`Get balance failed for user ${telegramId}:`, err);
        return { success: false, error: err.message };
    }
}

// ==================== COMMISSION / WIN PERCENTAGE ENDPOINTS ====================

/**
 * Get current win percentage from bot
 * @returns {Promise<{success: boolean, percentage?: number, message?: string}>}
 */
async function getWinPercentage() {
    try {
        const data = await getRequest("/api/commission");
        return {
            success: true,
            percentage: data.percentage
        };
    } catch (err) {
        console.error("Get win percentage failed:", err);
        return { success: false, error: err.message };
    }
}

/**
 * Set win percentage in bot
 * @param {number} percentage - Win percentage (70, 75, 76, or 80)
 * @returns {Promise<{success: boolean, message?: string}>}
 */
async function setWinPercentage(percentage) {
    try {
        const data = await makeRequest("/api/commission", "POST", { percentage });
        return {
            success: data.success,
            message: data.message
        };
    } catch (err) {
        console.error(`Set win percentage to ${percentage}% failed:`, err);
        return { success: false, error: err.message };
    }
}

// ==================== USER INFO ENDPOINTS ====================

/**
 * Get user information from bot
 * @param {number} telegramId - User's Telegram ID
 * @returns {Promise<{success: boolean, user?: object, message?: string}>}
 */
async function getUserInfo(telegramId) {
    try {
        const data = await makeRequest("/api/get-user", "POST", {
            telegram_id: telegramId
        });
        return {
            success: data.success,
            user: data.user,
            message: data.message
        };
    } catch (err) {
        console.error(`Get user info failed for user ${telegramId}:`, err);
        return { success: false, error: err.message };
    }
}

// ==================== HEALTH CHECK ====================

/**
 * Check if bot API is healthy
 * @returns {Promise<boolean>}
 */
async function healthCheck() {
    try {
        const response = await fetch(`${BOT_API_URL}/health`, {
            method: "GET",
            signal: AbortSignal.timeout(3000)
        });
        return response.ok;
    } catch (err) {
        console.error("Bot health check failed:", err);
        return false;
    }
}

/**
 * Get bot API status with details
 * @returns {Promise<{healthy: boolean, status?: string, uptime?: number, timestamp?: string}>}
 */
async function getBotStatus() {
    try {
        const response = await fetch(`${BOT_API_URL}/health`, {
            method: "GET",
            signal: AbortSignal.timeout(3000)
        });
        
        if (response.ok) {
            const data = await response.json();
            return {
                healthy: true,
                status: data.status || "ok",
                uptime: data.uptime,
                timestamp: data.timestamp
            };
        }
        
        return { healthy: false, status: "unhealthy" };
    } catch (err) {
        return { healthy: false, status: "unreachable", error: err.message };
    }
}

// ==================== BULK OPERATIONS ====================

/**
 * Process multiple balance operations in parallel
 * @param {Array<{telegramId: number, amount: number, reason: string, type: 'add'|'deduct'}>} operations
 * @returns {Promise<Array<{success: boolean, telegramId: number, new_balance?: number, error?: string}>>}
 */
async function batchBalanceOperations(operations) {
    const results = [];
    
    for (const op of operations) {
        let result;
        if (op.type === "add") {
            result = await addBalance(op.telegramId, op.amount, op.reason);
        } else {
            result = await deductBalance(op.telegramId, op.amount, op.reason);
        }
        
        results.push({
            telegramId: op.telegramId,
            success: result.success,
            new_balance: result.new_balance,
            error: result.error
        });
    }
    
    return results;
}

/**
 * Get balances for multiple users
 * @param {number[]} telegramIds - Array of Telegram IDs
 * @returns {Promise<Map<number, {balance: number, success: boolean}>>}
 */
async function getBatchUserBalances(telegramIds) {
    const balances = new Map();
    
    // Process in parallel with limit to avoid overwhelming the bot
    const batchSize = 10;
    for (let i = 0; i < telegramIds.length; i += batchSize) {
        const batch = telegramIds.slice(i, i + batchSize);
        const promises = batch.map(async (id) => {
            const result = await getUserBalance(id);
            return { id, balance: result.balance, success: result.success };
        });
        
        const results = await Promise.all(promises);
        for (const result of results) {
            balances.set(result.id, {
                balance: result.balance || 0,
                success: result.success
            });
        }
    }
    
    return balances;
}

// ==================== ERROR HANDLING & RETRY UTILITIES ====================

/**
 * Wrapper for critical operations with automatic retry
 * @param {Function} operation - Async function to execute
 * @param {number} maxRetries - Maximum retry attempts
 * @returns {Promise<any>}
 */
async function withRetry(operation, maxRetries = MAX_RETRIES) {
    let lastError = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await operation();
        } catch (err) {
            lastError = err;
            console.warn(`Operation failed (attempt ${attempt}/${maxRetries}):`, err.message);
            
            if (attempt < maxRetries) {
                await delay(RETRY_DELAY * Math.pow(2, attempt - 1));
            }
        }
    }
    
    throw lastError;
}

/**
 * Circuit breaker state
 */
let circuitState = "CLOSED"; // CLOSED, OPEN, HALF_OPEN
let failureCount = 0;
let lastFailureTime = 0;
const FAILURE_THRESHOLD = 5;
const OPEN_TIMEOUT = 30000; // 30 seconds

/**
 * Circuit breaker wrapper for bot API calls
 * Prevents cascading failures when bot is down
 */
async function withCircuitBreaker(operation, operationName = "unknown") {
    // Check if circuit is open
    if (circuitState === "OPEN") {
        const now = Date.now();
        if (now - lastFailureTime > OPEN_TIMEOUT) {
            circuitState = "HALF_OPEN";
            console.log(`🔌 Circuit breaker for ${operationName} is HALF_OPEN, testing...`);
        } else {
            throw new Error(`Bot API circuit breaker is OPEN for ${operationName}`);
        }
    }
    
    try {
        const result = await operation();
        
        // Success - close circuit if half-open
        if (circuitState === "HALF_OPEN") {
            circuitState = "CLOSED";
            failureCount = 0;
            console.log(`✅ Circuit breaker for ${operationName} closed (healthy)`);
        }
        
        return result;
    } catch (err) {
        failureCount++;
        lastFailureTime = Date.now();
        
        if (failureCount >= FAILURE_THRESHOLD) {
            circuitState = "OPEN";
            console.error(`🔴 Circuit breaker for ${operationName} OPEN after ${failureCount} failures`);
        }
        
        throw err;
    }
}

// ==================== EXPORTS ====================

module.exports = {
    // Core methods
    makeRequest,
    getRequest,
    
    // Authentication
    verifyToken,
    exchangeCode,
    
    // Balance management
    deductBalance,
    addBalance,
    getUserBalance,
    
    // Commission
    getWinPercentage,
    setWinPercentage,
    
    // User info
    getUserInfo,
    
    // Health
    healthCheck,
    getBotStatus,
    
    // Bulk operations
    batchBalanceOperations,
    getBatchUserBalances,
    
    // Utilities
    withRetry,
    withCircuitBreaker,
    
    // Configuration (exposed for debugging)
    BOT_API_URL,
    TIMEOUT,
    MAX_RETRIES
};