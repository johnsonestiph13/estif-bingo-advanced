// assets/js/utils.js - Shared Utility Functions

/**
 * Format seconds to MM:SS
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Show temporary message
 */
function showMessage(message, type = 'info', duration = 3000) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `round-message ${type === 'error' ? 'error-message' : type === 'warning' ? 'warning-message' : ''}`;
    msgDiv.innerText = message;
    document.getElementById('app').insertBefore(msgDiv, document.querySelector('.stats-bar').nextSibling);
    setTimeout(() => msgDiv.remove(), duration);
}

/**
 * Debounce function to limit rapid calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function to limit call rate
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Get query parameter from URL
 */
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Safe JSON parse
 */
function safeJSONParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch {
        return defaultValue;
    }
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showMessage('Copied to clipboard!', 'success', 1500);
        return true;
    } catch {
        showMessage('Failed to copy', 'error', 1500);
        return false;
    }
}

// Export for use in other files (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { formatTime, showMessage, debounce, throttle, getQueryParam, safeJSONParse, copyToClipboard };
}