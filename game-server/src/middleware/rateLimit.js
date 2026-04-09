// game-server/src/middleware/rateLimit.js

const rateLimit = require("express-rate-limit");
const { config } = require("../config");

// ==================== GENERAL API RATE LIMIT ====================

/**
 * General rate limiter for all API endpoints
 * Prevents DDoS and brute force attacks
 */
const apiLimiter = rateLimit({
    windowMs: config.RATE_LIMIT_WINDOW_MS || 15 * 60 * 1000, // 15 minutes
    max: config.RATE_LIMIT_MAX || 100,
    message: { 
        success: false, 
        message: "Too many requests, please try again later.",
        code: "RATE_LIMIT_EXCEEDED"
    },
    standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
    legacyHeaders: false,  // Disable the `X-RateLimit-*` headers
    skipSuccessfulRequests: false, // Count all requests
    keyGenerator: (req) => {
        // Use IP address as key, fallback to socket ID for WebSocket
        return req.ip || req.socket?.remoteAddress || req.connection?.remoteAddress || "unknown";
    },
});

// ==================== STRICT AUTH RATE LIMIT ====================

/**
 * Stricter rate limiter for authentication endpoints (login, OTP)
 */
const authLimiter = rateLimit({
    windowMs: 10 * 60 * 1000, // 10 minutes
    max: config.AUTH_RATE_LIMIT_MAX || 5,
    message: { 
        success: false, 
        message: "Too many authentication attempts. Please try again later.",
        code: "AUTH_RATE_LIMIT_EXCEEDED"
    },
    standardHeaders: true,
    legacyHeaders: false,
    skipSuccessfulRequests: true, // Don't count successful logins
    keyGenerator: (req) => {
        // Use email or IP as key for login attempts
        const email = req.body?.email || "";
        const ip = req.ip || req.socket?.remoteAddress;
        return `${email}:${ip}`;
    },
});

// ==================== CARTELA SELECTION RATE LIMIT ====================

/**
 * Rate limiter for cartela selection (prevents rapid click spam)
 * Applied per socket connection or per IP
 */
const cartelaLimiter = rateLimit({
    windowMs: 10 * 1000, // 10 seconds
    max: 10, // Max 10 selections per 10 seconds
    message: { 
        success: false, 
        message: "Too many cartela selections. Please slow down.",
        code: "SELECTION_RATE_LIMIT"
    },
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => {
        // Use socket ID or IP address as key
        return req.socket?.id || req.ip || req.connection?.remoteAddress;
    },
});

// ==================== DEPOSIT/CASHOUT REQUEST RATE LIMIT ====================

/**
 * Rate limiter for deposit and cashout requests (via bot)
 */
const financialLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 3, // Max 3 requests per 15 minutes
    message: { 
        success: false, 
        message: "Too many financial requests. Please wait before trying again.",
        code: "FINANCIAL_RATE_LIMIT"
    },
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => {
        // Use telegram_id if available, otherwise IP
        const telegramId = req.body?.telegram_id || req.params?.telegramId;
        const ip = req.ip || req.socket?.remoteAddress;
        return telegramId ? `telegram:${telegramId}` : `ip:${ip}`;
    },
});

// ==================== WEBHOOK RATE LIMIT (for payment gateways) ====================

/**
 * Rate limiter for webhook endpoints (payment callbacks)
 * Higher limit but still protected
 */
const webhookLimiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 30, // Max 30 webhook calls per minute
    message: { 
        success: false, 
        message: "Too many webhook requests.",
        code: "WEBHOOK_RATE_LIMIT"
    },
    standardHeaders: true,
    legacyHeaders: false,
    skip: (req) => {
        // Optionally skip rate limiting for trusted IPs
        const trustedIps = process.env.TRUSTED_WEBHOOK_IPS?.split(",") || [];
        return trustedIps.includes(req.ip);
    },
    keyGenerator: (req) => {
        // Use webhook type and IP as key
        const webhookType = req.params?.type || req.body?.type || "unknown";
        const ip = req.ip || req.socket?.remoteAddress;
        return `${webhookType}:${ip}`;
    },
});

// ==================== REPORT GENERATION RATE LIMIT ====================

/**
 * Rate limiter for report generation endpoints
 */
const reportLimiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 10, // Max 10 report requests per minute
    message: { 
        success: false, 
        message: "Too many report requests. Please wait.",
        code: "REPORT_RATE_LIMIT"
    },
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => {
        const adminEmail = req.admin?.email || "unknown";
        const ip = req.ip || req.socket?.remoteAddress;
        return `${adminEmail}:${ip}`;
    },
});

// ==================== ADMIN ACTION RATE LIMIT ====================

/**
 * Rate limiter for admin actions (start/end/reset game)
 */
const adminActionLimiter = rateLimit({
    windowMs: 30 * 1000, // 30 seconds
    max: 5, // Max 5 admin actions per 30 seconds
    message: { 
        success: false, 
        message: "Too many admin actions. Please wait.",
        code: "ADMIN_ACTION_RATE_LIMIT"
    },
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => {
        const adminEmail = req.admin?.email || "unknown";
        const ip = req.ip || req.socket?.remoteAddress;
        return `${adminEmail}:${ip}`;
    },
});

// ==================== SOCKET.IO RATE LIMITING ====================

/**
 * Enhanced in-memory rate limiter for Socket.IO events
 * Supports multiple event types and custom limits
 */
class SocketRateLimiter {
    constructor(options = {}) {
        this.windowMs = options.windowMs || 10000; // Default: 10 seconds
        this.maxRequests = options.maxRequests || 10; // Default: 10 requests
        this.eventType = options.eventType || "default";
        this.requests = new Map(); // key -> [{ timestamp, count }]
    }
    
    /**
     * Check if a request is allowed
     * @param {string} key - Unique identifier (socketId, telegramId, or IP)
     * @returns {object} - { allowed: boolean, remaining: number, resetTime: number }
     */
    isAllowed(key) {
        const now = Date.now();
        const windowStart = now - this.windowMs;
        
        if (!this.requests.has(key)) {
            this.requests.set(key, []);
        }
        
        const userRequests = this.requests.get(key);
        // Clean old requests
        const recentRequests = userRequests.filter(t => t > windowStart);
        
        const remaining = this.maxRequests - recentRequests.length;
        const resetTime = recentRequests.length > 0 
            ? recentRequests[0] + this.windowMs 
            : now + this.windowMs;
        
        if (recentRequests.length >= this.maxRequests) {
            return {
                allowed: false,
                remaining: 0,
                resetTime: resetTime,
                limit: this.maxRequests,
                windowMs: this.windowMs
            };
        }
        
        recentRequests.push(now);
        this.requests.set(key, recentRequests);
        
        return {
            allowed: true,
            remaining: remaining - 1,
            resetTime: resetTime,
            limit: this.maxRequests,
            windowMs: this.windowMs
        };
    }
    
    /**
     * Reset rate limit for a specific key
     */
    reset(key) {
        this.requests.delete(key);
    }
    
    /**
     * Clear all rate limit data
     */
    clear() {
        this.requests.clear();
    }
    
    /**
     * Get current stats for a key
     */
    getStats(key) {
        if (!this.requests.has(key)) {
            return { count: 0, remaining: this.maxRequests };
        }
        
        const now = Date.now();
        const windowStart = now - this.windowMs;
        const userRequests = this.requests.get(key);
        const recentCount = userRequests.filter(t => t > windowStart).length;
        
        return {
            count: recentCount,
            remaining: this.maxRequests - recentCount,
            limit: this.maxRequests,
            windowMs: this.windowMs
        };
    }
}

// Create instances for different event types with appropriate limits
const selectCartelaRateLimiter = new SocketRateLimiter({
    windowMs: 5000,  // 5 seconds
    maxRequests: 5,   // 5 selections per 5 seconds
    eventType: "select_cartela"
});

const deselectCartelaRateLimiter = new SocketRateLimiter({
    windowMs: 5000,  // 5 seconds
    maxRequests: 5,   // 5 deselects per 5 seconds
    eventType: "deselect_cartela"
});

const chatRateLimiter = new SocketRateLimiter({
    windowMs: 3000,  // 3 seconds
    maxRequests: 3,   // 3 messages per 3 seconds
    eventType: "chat"
});

const gameActionRateLimiter = new SocketRateLimiter({
    windowMs: 1000,  // 1 second
    maxRequests: 2,   // 2 actions per second
    eventType: "game_action"
});

const balanceCheckRateLimiter = new SocketRateLimiter({
    windowMs: 3000,  // 3 seconds
    maxRequests: 1,   // 1 balance check per 3 seconds
    eventType: "balance_check"
});

// ==================== UTILITY FUNCTIONS ====================

/**
 * Create a custom rate limiter with specific options
 * @param {object} options - Rate limiter options
 * @returns {object} - Express rate limiter middleware
 */
function createCustomLimiter(options) {
    return rateLimit({
        windowMs: options.windowMs || 60 * 1000,
        max: options.max || 100,
        message: options.message || { 
            success: false, 
            message: "Too many requests",
            code: "CUSTOM_RATE_LIMIT"
        },
        standardHeaders: true,
        legacyHeaders: false,
        keyGenerator: options.keyGenerator || ((req) => req.ip),
        skip: options.skip || (() => false),
    });
}

/**
 * Get rate limit headers for Socket.IO responses
 * @param {object} result - Result from SocketRateLimiter.isAllowed()
 * @returns {object} - Headers object
 */
function getRateLimitHeaders(result) {
    if (!result) return {};
    
    return {
        'X-RateLimit-Limit': result.limit,
        'X-RateLimit-Remaining': result.remaining,
        'X-RateLimit-Reset': Math.ceil(result.resetTime / 1000),
        'X-RateLimit-Window': Math.ceil(result.windowMs / 1000)
    };
}

// ==================== EXPORTS ====================
module.exports = {
    // Express rate limiters
    apiLimiter,
    authLimiter,
    cartelaLimiter,
    financialLimiter,
    webhookLimiter,
    reportLimiter,
    adminActionLimiter,
    
    // Socket.IO rate limiters
    SocketRateLimiter,
    selectCartelaRateLimiter,
    deselectCartelaRateLimiter,
    chatRateLimiter,
    gameActionRateLimiter,
    balanceCheckRateLimiter,
    
    // Utility functions
    createCustomLimiter,
    getRateLimitHeaders,
};