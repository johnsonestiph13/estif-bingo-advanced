// game-server/src/middleware/auth.js

const jwt = require("jsonwebtoken");
const { config } = require("../config");

// Store active admin tokens in memory (for production, use Redis)
const adminTokens = new Map();
const playerTokens = new Map(); // Track player tokens for additional security

// Token cleanup interval (default: 1 hour)
const TOKEN_CLEANUP_INTERVAL = 60 * 60 * 1000;
const ADMIN_TOKEN_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours
const PLAYER_TOKEN_EXPIRY = 2 * 60 * 60 * 1000; // 2 hours

// ==================== ADMIN AUTHENTICATION ====================

/**
 * Verify admin JWT token from Authorization header
 */
function verifyAdminToken(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
        return res.status(401).json({ 
            success: false, 
            message: "No authorization token provided",
            code: "MISSING_TOKEN"
        });
    }

    const token = authHeader.split(" ")[1];
    if (!token) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid token format. Use: Bearer <token>",
            code: "INVALID_FORMAT"
        });
    }

    // Check if token exists in memory
    if (!adminTokens.has(token)) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid or expired token",
            code: "TOKEN_NOT_FOUND"
        });
    }

    try {
        // Verify JWT
        const decoded = jwt.verify(token, config.JWT_SECRET);
        
        // Check if token is expired based on stored timestamp
        const tokenTimestamp = adminTokens.get(token);
        if (Date.now() - tokenTimestamp > ADMIN_TOKEN_EXPIRY) {
            adminTokens.delete(token);
            return res.status(401).json({ 
                success: false, 
                message: "Token expired",
                code: "TOKEN_EXPIRED"
            });
        }
        
        req.admin = decoded;
        next();
    } catch (err) {
        // If token is invalid, remove from memory
        adminTokens.delete(token);
        
        if (err.name === "TokenExpiredError") {
            return res.status(401).json({ 
                success: false, 
                message: "Token expired",
                code: "TOKEN_EXPIRED"
            });
        }
        
        return res.status(401).json({ 
            success: false, 
            message: "Invalid token",
            code: "INVALID_TOKEN"
        });
    }
}

/**
 * Generate admin JWT token after successful login
 */
function generateAdminToken(email) {
    const token = jwt.sign(
        { email, role: "admin", type: "admin", timestamp: Date.now() },
        config.JWT_SECRET,
        { expiresIn: "24h" }
    );
    adminTokens.set(token, Date.now());
    
    // Log admin login
    console.log(`🔐 Admin token generated for ${email} at ${new Date().toISOString()}`);
    
    return token;
}

/**
 * Remove admin token (logout)
 */
function revokeAdminToken(token) {
    if (adminTokens.has(token)) {
        adminTokens.delete(token);
        console.log(`🔐 Admin token revoked`);
        return true;
    }
    return false;
}

/**
 * Get all active admin tokens count (for monitoring)
 */
function getActiveAdminTokensCount() {
    return adminTokens.size;
}

/**
 * Get all active admin sessions (for debugging)
 */
function getActiveAdminSessions() {
    const sessions = [];
    for (const [token, timestamp] of adminTokens) {
        try {
            const decoded = jwt.decode(token);
            if (decoded) {
                sessions.push({
                    email: decoded.email,
                    issuedAt: new Date(timestamp).toISOString(),
                    expiresAt: new Date(timestamp + ADMIN_TOKEN_EXPIRY).toISOString()
                });
            }
        } catch (err) {
            // Skip invalid tokens
        }
    }
    return sessions;
}

/**
 * Clear all expired admin tokens
 */
function clearExpiredAdminTokens() {
    const now = Date.now();
    let expiredCount = 0;
    
    for (const [token, timestamp] of adminTokens) {
        if (now - timestamp > ADMIN_TOKEN_EXPIRY) {
            adminTokens.delete(token);
            expiredCount++;
        }
    }
    
    if (expiredCount > 0) {
        console.log(`🧹 Cleared ${expiredCount} expired admin tokens`);
    }
}

// ==================== PLAYER AUTHENTICATION ====================

/**
 * Verify JWT token for Socket.IO connections
 * This is called from the socket 'authenticate' event
 */
function verifySocketToken(token) {
    if (!token) {
        return { valid: false, error: "No token provided", code: "MISSING_TOKEN" };
    }
    
    try {
        const decoded = jwt.verify(token, config.JWT_SECRET);
        
        // Check token type
        if (decoded.type !== "player" && !decoded.telegram_id) {
            return { valid: false, error: "Invalid token type", code: "INVALID_TYPE" };
        }
        
        // Check if token is in active player tokens (optional additional security)
        if (playerTokens.has(token)) {
            const tokenData = playerTokens.get(token);
            if (Date.now() - tokenData.timestamp > PLAYER_TOKEN_EXPIRY) {
                playerTokens.delete(token);
                return { valid: false, error: "Token expired", code: "TOKEN_EXPIRED" };
            }
        }
        
        return { valid: true, decoded };
    } catch (err) {
        if (err.name === "TokenExpiredError") {
            return { valid: false, error: "Token expired", code: "TOKEN_EXPIRED" };
        }
        if (err.name === "JsonWebTokenError") {
            return { valid: false, error: "Invalid token", code: "INVALID_TOKEN" };
        }
        return { valid: false, error: "Token verification failed", code: "VERIFICATION_FAILED" };
    }
}

/**
 * Generate JWT token for player (used by bot via API)
 */
function generatePlayerToken(telegramId, username, balance) {
    const token = jwt.sign(
        { 
            telegram_id: telegramId, 
            username: username, 
            balance: balance,
            type: "player",
            iat: Math.floor(Date.now() / 1000),
            exp: Math.floor(Date.now() / 1000) + (2 * 60 * 60) // 2 hours
        },
        config.JWT_SECRET
    );
    
    // Store in player tokens for tracking (optional)
    playerTokens.set(token, {
        telegramId,
        username,
        timestamp: Date.now()
    });
    
    // Clean up old player tokens periodically
    setTimeout(() => {
        cleanupExpiredPlayerTokens();
    }, 60 * 60 * 1000);
    
    return token;
}

/**
 * Revoke player token (logout)
 */
function revokePlayerToken(token) {
    if (playerTokens.has(token)) {
        playerTokens.delete(token);
        return true;
    }
    return false;
}

/**
 * Clean up expired player tokens
 */
function cleanupExpiredPlayerTokens() {
    const now = Date.now();
    let expiredCount = 0;
    
    for (const [token, data] of playerTokens) {
        if (now - data.timestamp > PLAYER_TOKEN_EXPIRY) {
            playerTokens.delete(token);
            expiredCount++;
        }
    }
    
    if (expiredCount > 0) {
        console.log(`🧹 Cleared ${expiredCount} expired player tokens`);
    }
}

/**
 * Get player info from token without verification (for debugging)
 */
function decodePlayerToken(token) {
    try {
        return jwt.decode(token);
    } catch (err) {
        return null;
    }
}

// ==================== API KEY AUTHENTICATION (for bot-to-server calls) ====================

/**
 * Verify API key for internal service-to-service calls
 */
function verifyApiKey(req, res, next) {
    const apiKey = req.headers["x-api-key"];
    
    if (!apiKey) {
        return res.status(401).json({ 
            success: false, 
            message: "API key required",
            code: "MISSING_API_KEY"
        });
    }
    
    if (apiKey !== config.API_SECRET) {
        // Log failed attempts for security monitoring
        console.warn(`⚠️ Invalid API key attempt from ${req.ip} at ${new Date().toISOString()}`);
        return res.status(401).json({ 
            success: false, 
            message: "Invalid API key",
            code: "INVALID_API_KEY"
        });
    }
    
    next();
}

/**
 * Optional API key verification (doesn't block if missing, but validates if present)
 */
function optionalVerifyApiKey(req, res, next) {
    const apiKey = req.headers["x-api-key"];
    
    if (apiKey && apiKey !== config.API_SECRET) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid API key",
            code: "INVALID_API_KEY"
        });
    }
    
    next();
}

// ==================== RATE LIMITING HELPERS ====================

/**
 * Generate a unique key for rate limiting based on IP and endpoint
 */
function getRateLimitKey(req) {
    const ip = req.ip || req.connection.remoteAddress;
    const endpoint = req.path;
    return `${ip}:${endpoint}`;
}

// ==================== TOKEN CLEANUP SCHEDULER ====================

// Start automatic cleanup of expired tokens
setInterval(() => {
    clearExpiredAdminTokens();
    cleanupExpiredPlayerTokens();
}, TOKEN_CLEANUP_INTERVAL);

// ==================== EXPORTS ====================
module.exports = {
    // Admin auth
    verifyAdminToken,
    generateAdminToken,
    revokeAdminToken,
    getActiveAdminTokensCount,
    getActiveAdminSessions,
    clearExpiredAdminTokens,
    
    // Player auth
    verifySocketToken,
    generatePlayerToken,
    revokePlayerToken,
    decodePlayerToken,
    cleanupExpiredPlayerTokens,
    
    // API key auth
    verifyApiKey,
    optionalVerifyApiKey,
    
    // Helpers
    getRateLimitKey,
    
    // Exports for monitoring/debugging
    adminTokens,
    playerTokens,
};