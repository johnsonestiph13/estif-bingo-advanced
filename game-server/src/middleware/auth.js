// game-server/src/middleware/auth.js

const jwt = require("jsonwebtoken");
const { config } = require("../config");

// Store active admin tokens in memory (for production, use Redis)
const adminTokens = new Map();

// ==================== ADMIN AUTHENTICATION ====================

/**
 * Verify admin JWT token from Authorization header
 */
function verifyAdminToken(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
        return res.status(401).json({ 
            success: false, 
            message: "No authorization token provided" 
        });
    }

    const token = authHeader.split(" ")[1];
    if (!token) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid token format" 
        });
    }

    // Check if token exists in memory
    if (!adminTokens.has(token)) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid or expired token" 
        });
    }

    try {
        // Verify JWT
        const decoded = jwt.verify(token, config.JWT_SECRET);
        req.admin = decoded;
        next();
    } catch (err) {
        // If token is invalid, remove from memory
        adminTokens.delete(token);
        return res.status(401).json({ 
            success: false, 
            message: "Invalid or expired token" 
        });
    }
}

/**
 * Generate admin JWT token after successful login
 */
function generateAdminToken(email) {
    const token = jwt.sign(
        { email, role: "admin", timestamp: Date.now() },
        config.JWT_SECRET,
        { expiresIn: "24h" }
    );
    adminTokens.set(token, Date.now());
    
    // Clean up old tokens every hour
    setTimeout(() => {
        const now = Date.now();
        for (const [t, time] of adminTokens) {
            if (now - time > 24 * 60 * 60 * 1000) {
                adminTokens.delete(t);
            }
        }
    }, 60 * 60 * 1000);
    
    return token;
}

/**
 * Remove admin token (logout)
 */
function revokeAdminToken(token) {
    adminTokens.delete(token);
}

/**
 * Get all active admin tokens count (for monitoring)
 */
function getActiveAdminTokensCount() {
    return adminTokens.size;
}

// ==================== SOCKET.IO AUTHENTICATION ====================

/**
 * Verify JWT token for Socket.IO connections
 * This is called from the socket 'authenticate' event
 */
function verifySocketToken(token) {
    if (!token) {
        return { valid: false, error: "No token provided" };
    }
    
    try {
        const decoded = jwt.verify(token, config.JWT_SECRET);
        return { valid: true, decoded };
    } catch (err) {
        if (err.name === "TokenExpiredError") {
            return { valid: false, error: "Token expired" };
        }
        return { valid: false, error: "Invalid token" };
    }
}

/**
 * Generate JWT token for player (used by bot via API)
 */
function generatePlayerToken(telegramId, username, balance) {
    return jwt.sign(
        { 
            telegram_id: telegramId, 
            username: username, 
            balance: balance,
            exp: Math.floor(Date.now() / 1000) + (2 * 60 * 60) // 2 hours
        },
        config.JWT_SECRET
    );
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
            message: "API key required" 
        });
    }
    
    if (apiKey !== config.API_SECRET) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid API key" 
        });
    }
    
    next();
}

// ==================== EXPORTS ====================
module.exports = {
    verifyAdminToken,
    generateAdminToken,
    revokeAdminToken,
    getActiveAdminTokensCount,
    verifySocketToken,
    generatePlayerToken,
    verifyApiKey,
    adminTokens, // exported for monitoring/debugging
};