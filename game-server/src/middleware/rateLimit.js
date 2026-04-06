// game-server/src/middleware/rateLimit.js

const rateLimit = require("express-rate-limit");
const { config } = require("../config");

// ==================== GENERAL API RATE LIMIT ====================

/**
 * General rate limiter for all API endpoints
 * Prevents DDoS and brute force attacks
 */
const apiLimiter = rateLimit({
    windowMs: config.RATE_LIMIT_WINDOW_MS,
    max: config.RATE_LIMIT_MAX,
    message: { 
        success: false, 
        message: "Too many requests, please try again later." 
    },
    standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
    legacyHeaders: false,  // Disable the `X-RateLimit-*` headers
    skipSuccessfulRequests: false, // Count all requests
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
        message: "Too many authentication attempts. Please try again later." 
    },
    standardHeaders: true,
    legacyHeaders: false,
    skipSuccessfulRequests: true, // Don't count successful logins
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
        message: "Too many cartela selections. Please slow down." 
    },
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => {
        // Use socket ID or IP address as key
        return req.socket?.id || req.ip;
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
        message: "Too many financial requests. Please wait before trying again." 
    },
    standardHeaders: true,
    legacyHeaders: false,
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
        message: "Too many webhook requests." 
    },
    standardHeaders: true,
    legacyHeaders: false,
    skip: (req) => {
        // Optionally skip rate limiting for trusted IPs
        const trustedIps = process.env.TRUSTED_WEBHOOK_IPS?.split(",") || [];
        return trustedIps.includes(req.ip);
    },
});

// ==================== SOCKET.IO RATE LIMITING (Helper) ====================

/**
 * Simple in-memory rate limiter for Socket.IO events
 * Returns true if allowed, false if rate limited
 */
class SocketRateLimiter {
    constructor(windowMs = 10000, maxRequests = 10) {
        this.windowMs = windowMs;
        this.maxRequests = maxRequests;
        this.requests = new Map(); // socketId -> [{ timestamp }]
    }
    
    isAllowed(socketId) {
        const now = Date.now();
        const windowStart = now - this.windowMs;
        
        if (!this.requests.has(socketId)) {
            this.requests.set(socketId, []);
        }
        
        const userRequests = this.requests.get(socketId);
        // Clean old requests
        const recentRequests = userRequests.filter(t => t > windowStart);
        
        if (recentRequests.length >= this.maxRequests) {
            return false;
        }
        
        recentRequests.push(now);
        this.requests.set(socketId, recentRequests);
        return true;
    }
    
    reset(socketId) {
        this.requests.delete(socketId);
    }
    
    clear() {
        this.requests.clear();
    }
}

// Create instances for different event types
const selectCartelaRateLimiter = new SocketRateLimiter(5000, 5);  // 5 selections per 5 seconds
const deselectCartelaRateLimiter = new SocketRateLimiter(5000, 5); // 5 deselects per 5 seconds

// ==================== EXPORTS ====================
module.exports = {
    apiLimiter,
    authLimiter,
    cartelaLimiter,
    financialLimiter,
    webhookLimiter,
    SocketRateLimiter,
    selectCartelaRateLimiter,
    deselectCartelaRateLimiter,
};