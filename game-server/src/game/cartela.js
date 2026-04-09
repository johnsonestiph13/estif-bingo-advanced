// game-server/src/game/cartela.js

const fs = require("fs");
const path = require("path");
const { config } = require("../config");

// ==================== CARTELA DATA CACHE ====================

let cartelasData = {};
let cartelaMetadata = new Map();
const CARTELA_DATA_FILE = config.CARTELA_DATA_FILE || path.join(__dirname, "../../data/cartelas.json");

// Ensure data directory exists
const dataDir = path.dirname(CARTELA_DATA_FILE);
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

// Load cartelas from JSON file
function loadCartelasFromFile() {
    try {
        if (fs.existsSync(CARTELA_DATA_FILE)) {
            const rawData = fs.readFileSync(CARTELA_DATA_FILE, "utf8");
            cartelasData = JSON.parse(rawData);
            
            // Build metadata map for quick lookups
            for (const [id, data] of Object.entries(cartelasData)) {
                cartelaMetadata.set(id, {
                    id: id,
                    letter: id.charAt(0),
                    number: parseInt(id.match(/\d+/)?.[0] || 0),
                    variation: parseInt(id.split('_')[1]) || 0
                });
            }
            
            console.log(`✅ Loaded ${Object.keys(cartelasData).length} cartelas from ${CARTELA_DATA_FILE}`);
            return true;
        } else {
            console.warn(`⚠️ Cartela file not found at: ${CARTELA_DATA_FILE}`);
            return false;
        }
    } catch (err) {
        console.error("❌ Error loading cartelas:", err.message);
        return false;
    }
}

// Load on module initialization
loadCartelasFromFile();

// ==================== BINGO CARD GENERATION (Fallback) ====================

/**
 * Generate a random Bingo card (5x5 grid) - used as fallback
 */
function generateRandomBingoCard() {
    const getRandomNumbers = (min, max, count) => {
        const nums = [];
        const available = [];
        for (let i = min; i <= max; i++) available.push(i);
        
        for (let i = 0; i < count; i++) {
            const idx = Math.floor(Math.random() * available.length);
            nums.push(available[idx]);
            available.splice(idx, 1);
        }
        return nums;
    };
    
    const b = getRandomNumbers(1, 15, 5);
    const i = getRandomNumbers(16, 30, 5);
    const n = getRandomNumbers(31, 45, 5);
    const g = getRandomNumbers(46, 60, 5);
    const o = getRandomNumbers(61, 75, 5);
    
    // Set center as FREE (0 in your JSON format)
    n[2] = 0;
    
    return [
        [b[0], i[0], n[0], g[0], o[0]],
        [b[1], i[1], n[1], g[1], o[1]],
        [b[2], i[2], n[2], g[2], o[2]],
        [b[3], i[3], n[3], g[3], o[3]],
        [b[4], i[4], n[4], g[4], o[4]]
    ];
}

// ==================== CARTELA GRID RETRIEVAL ====================

/**
 * Get cartela grid by ID (e.g., "B1_001", "O15_188")
 */
function getCartelaGrid(cartelaId) {
    // First, try exact match
    if (cartelasData[cartelaId]) {
        return cartelasData[cartelaId].grid;
    }
    
    // Try to find by prefix (e.g., "B1" instead of "B1_001")
    const matchingKey = Object.keys(cartelasData).find(key => key.startsWith(cartelaId));
    if (matchingKey) {
        return cartelasData[matchingKey].grid;
    }
    
    // Fallback: generate random grid
    console.warn(`Cartela ${cartelaId} not found, generating random grid`);
    return generateRandomBingoCard();
}

/**
 * Get full cartela data object
 */
function getCartela(cartelaId) {
    if (cartelasData[cartelaId]) {
        return cartelasData[cartelaId];
    }
    
    const matchingKey = Object.keys(cartelasData).find(key => key.startsWith(cartelaId));
    if (matchingKey) {
        return cartelasData[matchingKey];
    }
    
    return null;
}

/**
 * Get cartela metadata (without full grid)
 */
function getCartelaMetadataById(cartelaId) {
    if (cartelaMetadata.has(cartelaId)) {
        return cartelaMetadata.get(cartelaId);
    }
    
    // Try prefix match
    const matchingKey = Object.keys(cartelasData).find(key => key.startsWith(cartelaId));
    if (matchingKey && cartelaMetadata.has(matchingKey)) {
        return cartelaMetadata.get(matchingKey);
    }
    
    return null;
}

// ==================== BINGO WIN DETECTION ====================

/**
 * Check if a cartela has Bingo with the given drawn numbers
 * Returns winning lines (rows, columns, diagonals)
 */
function checkBingoWin(cartelaId, drawnNumbers) {
    const grid = getCartelaGrid(cartelaId);
    if (!grid) return { won: false, winningLines: [] };
    
    // Convert drawn numbers to Set for O(1) lookup
    // Also add 0 for FREE space (matching your JSON format)
    const drawnSet = new Set(drawnNumbers);
    drawnSet.add(0); // FREE space is represented as 0
    
    const winningLines = [];
    
    // Check rows
    for (let r = 0; r < 5; r++) {
        if (grid[r].every(cell => drawnSet.has(cell))) {
            winningLines.push(`Row ${r + 1}`);
        }
    }
    
    // Check columns
    for (let c = 0; c < 5; c++) {
        let win = true;
        for (let r = 0; r < 5; r++) {
            if (!drawnSet.has(grid[r][c])) {
                win = false;
                break;
            }
        }
        if (win) winningLines.push(`Column ${c + 1}`);
    }
    
    // Check main diagonal (top-left to bottom-right)
    let diag1 = true;
    for (let i = 0; i < 5; i++) {
        if (!drawnSet.has(grid[i][i])) {
            diag1 = false;
            break;
        }
    }
    if (diag1) winningLines.push("Diagonal ↘");
    
    // Check anti-diagonal (top-right to bottom-left)
    let diag2 = true;
    for (let i = 0; i < 5; i++) {
        if (!drawnSet.has(grid[i][4 - i])) {
            diag2 = false;
            break;
        }
    }
    if (diag2) winningLines.push("Diagonal ↙");
    
    return {
        won: winningLines.length > 0,
        winningLines: winningLines,
        pattern: winningLines[0] || null
    };
}

/**
 * Get the letter for a Bingo number (B, I, N, G, O)
 */
function getBingoLetter(number) {
    if (number <= 15) return "B";
    if (number <= 30) return "I";
    if (number <= 45) return "N";
    if (number <= 60) return "G";
    return "O";
}

/**
 * Format number with letter for display (e.g., "B12", "I23")
 */
function formatBingoNumber(number) {
    if (number === 0 || number === "FREE") return "FREE";
    return `${getBingoLetter(number)}${number}`;
}

// ==================== CARTELA VALIDATION ====================

/**
 * Validate cartela ID format (e.g., "B1_001" or "O15_188")
 */
function isValidCartelaId(cartelaId) {
    // Check if exists in loaded data
    if (cartelasData[cartelaId]) return true;
    
    // Check if exists by prefix
    const matchingKey = Object.keys(cartelasData).find(key => key.startsWith(cartelaId));
    if (matchingKey) return true;
    
    // Validate format: Letter + Number + _ + 3-digit variation
    const regex = /^[BINGO]\d+_\d{3}$/;
    return regex.test(cartelaId);
}

/**
 * Get all cartela IDs (all variations from loaded file)
 */
function getAllCartelaIds() {
    return Object.keys(cartelasData);
}

/**
 * Get cartela IDs by letter (B, I, N, G, O)
 */
function getCartelaIdsByLetter(letter) {
    return Object.keys(cartelasData).filter(id => id.startsWith(letter));
}

/**
 * Get total number of cartelas loaded
 */
function getTotalCartelasCount() {
    return Object.keys(cartelasData).length;
}

/**
 * Parse cartela ID into components
 */
function parseCartelaId(cartelaId) {
    const match = cartelaId.match(/^([BINGO])(\d+)_(\d{3})$/);
    if (!match) return null;
    
    return {
        fullId: cartelaId,
        letter: match[1],
        number: parseInt(match[2], 10),
        variation: parseInt(match[3], 10)
    };
}

// ==================== CACHE MANAGEMENT ====================

/**
 * Get number of cached cartelas
 */
function getCachedCartelasCount() {
    return Object.keys(cartelasData).length;
}

/**
 * Reload cartelas from file (useful for hot-reload)
 */
function reloadCartelas() {
    cartelasData = {};
    cartelaMetadata.clear();
    return loadCartelasFromFile();
}

/**
 * Clear cartela cache (useful for testing)
 */
function clearCartelaCache() {
    cartelasData = {};
    cartelaMetadata.clear();
    console.log("🗑️ Cartela cache cleared");
}

// ==================== EXPORTS ====================
module.exports = {
    generateRandomBingoCard,
    getCartelaGrid,
    getCartela,
    getCartelaMetadataById,
    checkBingoWin,
    getBingoLetter,
    formatBingoNumber,
    isValidCartelaId,
    getAllCartelaIds,
    getCartelaIdsByLetter,
    getTotalCartelasCount,
    getCachedCartelasCount,
    parseCartelaId,
    reloadCartelas,
    clearCartelaCache,
    loadCartelasFromFile,
};