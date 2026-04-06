// game-server/src/utils/helpers.js

const crypto = require("crypto");

// ==================== TIME FORMATTING ====================

/**
 * Format seconds to MM:SS format
 * @param {number} seconds - Time in seconds
 * @returns {string} - Formatted time (MM:SS)
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Format milliseconds to readable duration
 * @param {number} ms - Milliseconds
 * @returns {string} - Human readable duration
 */
function formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
}

/**
 * Format date to ISO string with timezone
 * @param {Date} date - Date object (defaults to now)
 * @returns {string} - Formatted date string
 */
function formatDate(date = new Date()) {
    return date.toISOString().replace("T", " ").substring(0, 19);
}

// ==================== RANDOM GENERATION ====================

/**
 * Generate random number between min and max (inclusive)
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} - Random number
 */
function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Generate random string of specified length
 * @param {number} length - Length of string
 * @returns {string} - Random string
 */
function randomString(length = 16) {
    return crypto.randomBytes(length).toString("hex").slice(0, length);
}

/**
 * Generate random OTP (6 digits)
 * @returns {string} - 6-digit OTP
 */
function generateOTP() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

/**
 * Shuffle array (Fisher-Yates)
 * @param {Array} array - Array to shuffle
 * @returns {Array} - Shuffled array (new array)
 */
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

// ==================== VALIDATION ====================

/**
 * Validate phone number format
 * @param {string} phone - Phone number
 * @returns {boolean} - Whether valid
 */
function isValidPhone(phone) {
    const phoneRegex = /^[0-9+\-\s()]{8,15}$/;
    return phoneRegex.test(phone);
}

/**
 * Validate email format
 * @param {string} email - Email address
 * @returns {boolean} - Whether valid
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate amount (positive number, max limit)
 * @param {number} amount - Amount to validate
 * @param {number} max - Maximum allowed (default: 1000000)
 * @returns {boolean} - Whether valid
 */
function isValidAmount(amount, max = 1000000) {
    const num = parseFloat(amount);
    return !isNaN(num) && num > 0 && num <= max;
}

/**
 * Validate cartela number
 * @param {number} cartelaId - Cartela ID
 * @param {number} totalCartelas - Total available cartelas (default: 400)
 * @returns {boolean} - Whether valid
 */
function isValidCartelaId(cartelaId, totalCartelas = 400) {
    const id = parseInt(cartelaId);
    return !isNaN(id) && id >= 1 && id <= totalCartelas;
}

/**
 * Validate win percentage
 * @param {number} percentage - Win percentage
 * @returns {boolean} - Whether valid
 */
function isValidWinPercentage(percentage) {
    return [70, 75, 76, 80].includes(percentage);
}

// ==================== SAFE PARSING ====================

/**
 * Safely parse JSON without throwing
 * @param {string} jsonString - JSON string to parse
 * @param {any} defaultValue - Default value if parsing fails
 * @returns {any} - Parsed object or default
 */
function safeJSONParse(jsonString, defaultValue = null) {
    try {
        return JSON.parse(jsonString);
    } catch {
        return defaultValue;
    }
}

/**
 * Safely convert to integer
 * @param {any} value - Value to convert
 * @param {number} defaultValue - Default value if conversion fails
 * @returns {number} - Integer value
 */
function toInt(value, defaultValue = 0) {
    const num = parseInt(value);
    return isNaN(num) ? defaultValue : num;
}

/**
 * Safely convert to float
 * @param {any} value - Value to convert
 * @param {number} defaultValue - Default value if conversion fails
 * @returns {number} - Float value
 */
function toFloat(value, defaultValue = 0) {
    const num = parseFloat(value);
    return isNaN(num) ? defaultValue : num;
}

// ==================== OBJECT HELPERS ====================

/**
 * Deep clone an object
 * @param {object} obj - Object to clone
 * @returns {object} - Cloned object
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Remove undefined and null values from object
 * @param {object} obj - Object to clean
 * @returns {object} - Cleaned object
 */
function cleanObject(obj) {
    const cleaned = {};
    for (const [key, value] of Object.entries(obj)) {
        if (value !== undefined && value !== null) {
            cleaned[key] = value;
        }
    }
    return cleaned;
}

/**
 * Pick specific keys from an object
 * @param {object} obj - Source object
 * @param {string[]} keys - Keys to pick
 * @returns {object} - Object with picked keys
 */
function pick(obj, keys) {
    const result = {};
    for (const key of keys) {
        if (obj.hasOwnProperty(key)) {
            result[key] = obj[key];
        }
    }
    return result;
}

/**
 * Omit specific keys from an object
 * @param {object} obj - Source object
 * @param {string[]} keys - Keys to omit
 * @returns {object} - Object without omitted keys
 */
function omit(obj, keys) {
    const result = { ...obj };
    for (const key of keys) {
        delete result[key];
    }
    return result;
}

// ==================== ARRAY HELPERS ====================

/**
 * Chunk array into smaller arrays
 * @param {Array} array - Array to chunk
 * @param {number} size - Chunk size
 * @returns {Array[]} - Chunked array
 */
function chunkArray(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
        chunks.push(array.slice(i, i + size));
    }
    return chunks;
}

/**
 * Remove duplicates from array
 * @param {Array} array - Array with possible duplicates
 * @returns {Array} - Array with unique values
 */
function uniqueArray(array) {
    return [...new Set(array)];
}

// ==================== PROMISE HELPERS ====================

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry an async function with exponential backoff
 * @param {Function} fn - Async function to retry
 * @param {number} maxRetries - Maximum retry attempts
 * @param {number} baseDelay - Base delay in ms
 * @returns {Promise<any>} - Result of the function
 */
async function retry(fn, maxRetries = 3, baseDelay = 1000) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await fn();
        } catch (err) {
            lastError = err;
            if (attempt < maxRetries) {
                const delay = baseDelay * Math.pow(2, attempt - 1);
                await sleep(delay);
            }
        }
    }
    
    throw lastError;
}

/**
 * Timeout wrapper for promises
 * @param {Promise} promise - Promise to wrap
 * @param {number} timeoutMs - Timeout in milliseconds
 * @returns {Promise<any>} - Promise with timeout
 */
function timeout(promise, timeoutMs) {
    return Promise.race([
        promise,
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error(`Operation timed out after ${timeoutMs}ms`)), timeoutMs)
        )
    ]);
}

// ==================== SECURITY HELPERS ====================

/**
 * Sanitize input to prevent XSS
 * @param {string} input - Input string
 * @returns {string} - Sanitized string
 */
function sanitizeInput(input) {
    if (!input || typeof input !== "string") return "";
    return input
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#x27;")
        .replace(/\//g, "&#x2F;");
}

/**
 * Truncate string to maximum length
 * @param {string} str - Input string
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated string
 */
function truncate(str, maxLength = 100) {
    if (!str || str.length <= maxLength) return str;
    return str.substring(0, maxLength - 3) + "...";
}

// ==================== EXPORTS ====================

module.exports = {
    // Time formatting
    formatTime,
    formatDuration,
    formatDate,
    
    // Random generation
    randomInt,
    randomString,
    generateOTP,
    shuffleArray,
    
    // Validation
    isValidPhone,
    isValidEmail,
    isValidAmount,
    isValidCartelaId,
    isValidWinPercentage,
    
    // Safe parsing
    safeJSONParse,
    toInt,
    toFloat,
    
    // Object helpers
    deepClone,
    cleanObject,
    pick,
    omit,
    
    // Array helpers
    chunkArray,
    uniqueArray,
    
    // Promise helpers
    sleep,
    retry,
    timeout,
    
    // Security helpers
    sanitizeInput,
    truncate
};