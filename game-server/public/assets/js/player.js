// Estif Bingo 24/7 - Player Module
// Updated to support string-based cartela IDs (B1_001, O15_188, etc.)

// Configuration
const CONFIG = {
    CARTELA_PRICE: 10,
    MAX_CARTELAS: 4,
    SELECTION_TIME: 50,
    DRAW_INTERVAL: 4000,
    BOT_API_URL: 'https://estif-bingo-bot-1.onrender.com',
    WS_URL: window.location.origin,
    BALANCE_CHECK_INTERVAL: 3000, // Check balance every 3 seconds
    TOTAL_CARTELAS: 75, // 75 cartela types (B1-B15, I16-I30, N31-N45, G46-G60, O61-O75)
    TOTAL_VARIATIONS: 1000 // Total cartela variations
};

// Global State
let socket = null;
let userData = null;
let selectedCartelas = new Map(); // cartelaId -> { element, grid, selectedAt }
let cartelasData = {}; // Store loaded cartela grids
let gameState = {
    status: 'selection', // selection, active, pause
    round: 1,
    timer: 50,
    numbersDrawn: [],
    winners: [],
    poolAmount: 0,
    winPercentage: 75,
    canPlay: false,
    balance: 0
};

let sounds = {};
let currentSoundPack = localStorage.getItem('soundPack') || 'pack1';
let audioContext = null;

// BINGO letter ranges
const BINGO_RANGES = {
    'B': { min: 1, max: 15, letter: 'B' },
    'I': { min: 16, max: 30, letter: 'I' },
    'N': { min: 31, max: 45, letter: 'N' },
    'G': { min: 46, max: 60, letter: 'G' },
    'O': { min: 61, max: 75, letter: 'O' }
};

// Generate all cartela IDs (75 types)
function generateAllCartelaIds() {
    const ids = [];
    // B: 1-15
    for (let i = 1; i <= 15; i++) ids.push(`B${i}`);
    // I: 16-30
    for (let i = 16; i <= 30; i++) ids.push(`I${i}`);
    // N: 31-45
    for (let i = 31; i <= 45; i++) ids.push(`N${i}`);
    // G: 46-60
    for (let i = 46; i <= 60; i++) ids.push(`G${i}`);
    // O: 61-75
    for (let i = 61; i <= 75; i++) ids.push(`O${i}`);
    return ids;
}

const ALL_CARTELA_IDS = generateAllCartelaIds();

// Initialize Game
async function initGame() {
    showLoading();
    
    // Get auth code from URL
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (!code) {
        showError('No authentication code found. Please use the Play button in Telegram.');
        return;
    }
    
    try {
        // Authenticate with game server
        const response = await fetch('/api/exchange-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Authentication failed');
        }
        
        userData = data.user;
        gameState.balance = userData.balance;
        gameState.canPlay = userData.balance >= CONFIG.CARTELA_PRICE;
        
        // Initialize sounds
        await initSounds();
        
        // Load cartelas data
        await loadCartelasData();
        
        // Connect WebSocket
        connectWebSocket(data.token);
        
        // Start balance checker
        startBalanceChecker();
        
        // Render cartelas
        renderCartelas();
        
        // Update UI
        updateUI();
        
        hideLoading();
        
    } catch (error) {
        console.error('Init error:', error);
        showError('Failed to initialize game. Please try again.');
    }
}

// Load cartelas data from server
async function loadCartelasData() {
    try {
        // Load a sample cartela to get the structure
        const response = await fetch('/api/cartela/B1');
        if (response.ok) {
            const data = await response.json();
            console.log('Cartela data loaded successfully');
        }
    } catch (error) {
        console.warn('Failed to preload cartelas:', error);
    }
}

// WebSocket Connection
function connectWebSocket(token) {
    socket = io(CONFIG.WS_URL, {
        transports: ['websocket'],
        auth: { token: token }
    });
    
    socket.on('connect', () => {
        console.log('WebSocket connected');
        socket.emit('authenticate', { token: token });
    });
    
    socket.on('authenticated', (data) => {
        console.log('Authenticated:', data);
        if (data.selectedCartelas) {
            data.selectedCartelas.forEach(cartelaId => {
                selectedCartelas.set(cartelaId, { selectedAt: Date.now() });
            });
            updateCartelaCount();
            updateCartelaSelectionsUI();
        }
        updateUI();
    });
    
    socket.on('balanceUpdate', (data) => {
        gameState.balance = data.balance;
        gameState.canPlay = data.canPlay;
        updateUI();
        updateCartelaAvailability();
    });
    
    socket.on('newRound', (data) => {
        gameState.round = data.round;
        gameState.status = 'selection';
        gameState.timer = data.timer;
        gameState.numbersDrawn = [];
        gameState.winners = [];
        gameState.winPercentage = data.winPercentage;
        
        // Clear selections
        selectedCartelas.clear();
        updateCartelaSelectionsUI();
        updateCartelaCount();
        
        updateUI();
        playSound('newRound');
        showNotification(`Round ${data.round} started! Select up to ${CONFIG.MAX_CARTELAS} cartelas.`, 'info');
    });
    
    socket.on('timerUpdate', (data) => {
        gameState.timer = data.timer;
        updateTimerDisplay(data.phase);
        
        // Play countdown tick for last 10 seconds
        if (data.phase === 'selection' && data.timer <= 10 && data.timer > 0) {
            if (data.timer === 10 || data.timer === 5 || data.timer === 3) {
                playSound('countdown');
            }
            blinkTimer();
        }
    });
    
    socket.on('cartelaTaken', (data) => {
        const cartelaElement = document.querySelector(`.cartela-card[data-id="${data.cartelaId}"]`);
        if (cartelaElement && data.telegramId !== userData?.telegram_id) {
            cartelaElement.classList.add('taken');
            const btn = cartelaElement.querySelector('.select-cartela-btn');
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Taken';
            }
        }
    });
    
    socket.on('cartelaReleased', (data) => {
        const cartelaElement = document.querySelector(`.cartela-card[data-id="${data.cartelaId}"]`);
        if (cartelaElement && !selectedCartelas.has(data.cartelaId)) {
            cartelaElement.classList.remove('taken');
            const btn = cartelaElement.querySelector('.select-cartela-btn');
            if (btn && gameState.status === 'selection' && gameState.canPlay) {
                btn.disabled = false;
                btn.textContent = 'Select';
            }
        }
    });
    
    socket.on('selectionConfirmed', (data) => {
        gameState.balance = data.balance;
        updateUI();
        updateCartelaSelectionsUI();
        updateCartelaCount();
        playSound('select');
    });
    
    socket.on('selectionUpdated', (data) => {
        gameState.balance = data.balance;
        updateUI();
        updateCartelaSelectionsUI();
        updateCartelaCount();
    });
    
    socket.on('numberDrawn', (data) => {
        gameState.numbersDrawn = data.numbers;
        updateNumberDisplay(data.number);
        markNumbersOnCartelas(data.number);
        playSound(`number_${data.number}`);
    });
    
    socket.on('gameActive', (data) => {
        gameState.status = 'active';
        updateUI();
        showNotification('🎲 Game Started! Numbers are being drawn...', 'info');
    });
    
    socket.on('roundEnded', (data) => {
        gameState.status = 'pause';
        gameState.winners = data.winners;
        gameState.timer = 6;
        
        showWinners(data);
        if (data.winners.some(w => w.username === userData?.username)) {
            playSound('win');
            playSound('celebration');
        } else {
            playSound('win');
        }
        updateUI();
    });
    
    socket.on('youWon', (data) => {
        gameState.balance = data.newBalance;
        updateUI();
        showWinNotification(data);
        playSound('win');
        playSound('celebration');
        
        // Highlight winning cartela
        highlightWinningCartela(data.cartelaId);
    });
    
    socket.on('error', (data) => {
        showError(data.message);
    });
    
    socket.on('disconnect', () => {
        updateConnectionStatus(false);
        showError('Disconnected from server. Reconnecting...');
        setTimeout(() => connectWebSocket(token), 3000);
    });
    
    socket.on('connect', () => {
        updateConnectionStatus(true);
    });
}

// Render Cartelas (75 types with variations)
function renderCartelas() {
    const container = document.getElementById('cartelasContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Use CSS Grid for responsive layout
    container.style.display = 'grid';
    container.style.gridTemplateColumns = 'repeat(auto-fill, minmax(200px, 250px))';
    container.style.gap = '15px';
    container.style.padding = '20px';
    container.style.justifyContent = 'center';
    
    // Render only cartela types (not all variations)
    for (const cartelaId of ALL_CARTELA_IDS) {
        const cartela = createCartelaElement(cartelaId);
        container.appendChild(cartela);
    }
}

// Create individual cartela element
function createCartelaElement(cartelaId) {
    const div = document.createElement('div');
    div.className = 'cartela-card';
    div.setAttribute('data-id', cartelaId);
    
    // Get BINGO letter
    const letter = cartelaId.charAt(0);
    const letterColor = getBingoColor(letter);
    
    div.innerHTML = `
        <div class="cartela-header" style="border-left-color: ${letterColor}">
            <span class="cartela-bingo-letter" style="background: ${letterColor}">${letter}</span>
            <span class="cartela-id">${cartelaId}</span>
            <span class="cartela-price">${CONFIG.CARTELA_PRICE} ETB</span>
        </div>
        <div class="cartela-preview-grid" id="preview-${cartelaId}">
            <div class="preview-skeleton">
                <div class="skeleton-row">
                    <span>B</span><span>I</span><span>N</span><span>G</span><span>O</span>
                </div>
                <div class="skeleton-numbers">
                    ${Array(5).fill().map(() => '<div class="skeleton-line">???</div>').join('')}
                </div>
            </div>
        </div>
        <div class="cartela-footer">
            <button class="select-cartela-btn" data-cartela="${cartelaId}">
                Select Cartela
            </button>
        </div>
    `;
    
    // Add click handler to button
    const btn = div.querySelector('.select-cartela-btn');
    btn.onclick = (e) => {
        e.stopPropagation();
        selectCartela(cartelaId);
    };
    
    // Check if cartela is already selected
    if (selectedCartelas.has(cartelaId)) {
        div.classList.add('selected');
        btn.textContent = 'Selected';
        btn.disabled = true;
    }
    
    // Lazy load grid preview on hover
    div.onmouseenter = () => loadCartelaPreview(cartelaId);
    
    return div;
}

// Load cartela preview grid
async function loadCartelaPreview(cartelaId) {
    const previewContainer = document.getElementById(`preview-${cartelaId}`);
    if (!previewContainer || previewContainer.dataset.loaded === 'true') return;
    
    try {
        const response = await fetch(`/api/cartela/${cartelaId}`);
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.grid) {
                previewContainer.innerHTML = generateCartelaGridHTML(data.grid);
                previewContainer.dataset.loaded = 'true';
            }
        }
    } catch (error) {
        console.warn(`Failed to load preview for ${cartelaId}:`, error);
    }
}

// Generate cartela grid HTML
function generateCartelaGridHTML(grid) {
    if (!grid) return '<div class="preview-error">⚠️</div>';
    
    let html = '<div class="cartela-grid">';
    html += '<div class="grid-row header-row">';
    html += '<span>B</span><span>I</span><span>N</span><span>G</span><span>O</span>';
    html += '</div>';
    
    for (let row = 0; row < 5; row++) {
        html += '<div class="grid-row">';
        for (let col = 0; col < 5; col++) {
            const value = grid[row][col];
            const isFree = (value === 0 || value === 'FREE');
            const displayValue = isFree ? 'FREE' : value;
            html += `<div class="${isFree ? 'free-space' : 'number'}" data-number="${value}">${displayValue}</div>`;
        }
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// Select cartela
async function selectCartela(cartelaId) {
    // Validation
    if (gameState.status !== 'selection') {
        showError('Cannot select cartela now. Wait for next round.');
        return;
    }
    
    if (selectedCartelas.has(cartelaId)) {
        showError('Cartela already selected');
        return;
    }
    
    if (selectedCartelas.size >= CONFIG.MAX_CARTELAS) {
        showError(`Maximum ${CONFIG.MAX_CARTELAS} cartelas per player`);
        return;
    }
    
    if (!gameState.canPlay || gameState.balance < CONFIG.CARTELA_PRICE) {
        showError('Insufficient balance. Please deposit to play.');
        return;
    }
    
    // Send selection to server
    socket.emit('selectCartela', { 
        cartelaId: cartelaId,
        price: CONFIG.CARTELA_PRICE 
    }, (response) => {
        if (response && response.success) {
            // Optimistic UI update
            selectedCartelas.set(cartelaId, { selectedAt: Date.now() });
            updateCartelaSelectionsUI();
            updateCartelaCount();
            playSound('select');
        } else if (response && response.error) {
            showError(response.error);
        }
    });
}

// Update cartela selections UI
function updateCartelaSelectionsUI() {
    document.querySelectorAll('.cartela-card').forEach(card => {
        const cartelaId = card.getAttribute('data-id');
        const btn = card.querySelector('.select-cartela-btn');
        
        if (selectedCartelas.has(cartelaId)) {
            card.classList.add('selected');
            if (btn) {
                btn.textContent = 'Selected';
                btn.disabled = true;
            }
        } else {
            card.classList.remove('selected');
            if (btn && gameState.status === 'selection' && gameState.canPlay && !card.classList.contains('taken')) {
                btn.disabled = false;
                btn.textContent = 'Select Cartela';
            } else if (btn && !gameState.canPlay) {
                btn.disabled = true;
            }
        }
    });
}

// Update cartela availability based on balance
function updateCartelaAvailability() {
    const canSelect = gameState.canPlay && gameState.status === 'selection' 
                      && selectedCartelas.size < CONFIG.MAX_CARTELAS;
    
    document.querySelectorAll('.cartela-card').forEach(card => {
        const cartelaId = card.getAttribute('data-id');
        const btn = card.querySelector('.select-cartela-btn');
        
        if (!selectedCartelas.has(cartelaId) && !card.classList.contains('taken')) {
            if (btn) {
                btn.disabled = !canSelect;
                btn.style.opacity = canSelect ? '1' : '0.5';
            }
        }
    });
}

// Get BINGO color
function getBingoColor(letter) {
    const colors = {
        'B': '#ff6b6b',
        'I': '#4ecdc4',
        'N': '#45b7d1',
        'G': '#96ceb4',
        'O': '#ffeaa7'
    };
    return colors[letter] || '#ddd';
}

// Get BINGO letter for number
function getNumberLetter(number) {
    if (number <= 15) return 'B';
    if (number <= 30) return 'I';
    if (number <= 45) return 'N';
    if (number <= 60) return 'G';
    return 'O';
}

// Update number display with animation
function updateNumberDisplay(number) {
    const container = document.getElementById('currentNumber');
    if (!container) return;
    
    const letter = getNumberLetter(number);
    
    container.innerHTML = `
        <div class="bingo-ball animate">
            <span class="bingo-ball-letter">${letter}</span>
            <span class="bingo-ball-number">${number}</span>
        </div>
    `;
    
    // Add to history
    const historyContainer = document.getElementById('numbersHistory');
    if (historyContainer) {
        const numberSpan = document.createElement('span');
        numberSpan.className = 'history-number';
        numberSpan.textContent = number;
        historyContainer.prepend(numberSpan);
        
        // Keep only last 20 numbers
        while (historyContainer.children.length > 20) {
            historyContainer.removeChild(historyContainer.lastChild);
        }
    }
}

// Mark numbers on cartelas
function markNumbersOnCartelas(number) {
    const visibleCartelas = document.querySelectorAll('.cartela-card');
    visibleCartelas.forEach(cartela => {
        const numberElements = cartela.querySelectorAll(`.number[data-number="${number}"]`);
        numberElements.forEach(el => {
            el.classList.add('marked');
            el.style.background = '#4caf50';
            el.style.color = 'white';
        });
    });
}

// Timer display with color change
function updateTimerDisplay(phase) {
    const timerElement = document.getElementById('timer');
    if (!timerElement) return;
    
    timerElement.textContent = gameState.timer;
    
    if (phase === 'selection') {
        if (gameState.timer <= 10) {
            timerElement.style.color = '#ff4444';
            timerElement.style.animation = 'blink 0.5s infinite';
        } else {
            timerElement.style.color = '#ffd700';
            timerElement.style.animation = 'none';
        }
    }
}

// Blink timer effect
function blinkTimer() {
    const timerElement = document.getElementById('timer');
    if (timerElement && gameState.timer <= 10 && gameState.timer > 0) {
        timerElement.classList.add('blinking');
    } else if (timerElement) {
        timerElement.classList.remove('blinking');
    }
}

// Show winners and winning patterns
function showWinners(data) {
    const winnersContainer = document.getElementById('winnersDisplay');
    if (!winnersContainer) return;
    
    winnersContainer.style.display = 'block';
    
    if (data.winners.length === 0) {
        winnersContainer.innerHTML = '<div class="no-winner">😢 No winners this round!</div>';
        return;
    }
    
    winnersContainer.innerHTML = `
        <div class="winners-list">
            <h3>🏆 Winners 🏆</h3>
            ${data.winners.map(winner => `
                <div class="winner-card">
                    <div class="winner-info">
                        <strong>${escapeHtml(winner.username || 'Player')}</strong>
                        <span>Cartela: ${winner.cartelaId}</span>
                        <span class="winning-pattern">${winner.pattern || winner.winningLines?.join(', ')}</span>
                        <span class="winning-amount">+${data.prizePerWinner.toFixed(2)} ETB</span>
                    </div>
                </div>
            `).join('')}
            <div class="round-stats">
                <div>💰 Total Prize: ${data.totalPrize.toFixed(2)} ETB</div>
                <div>📊 Commission: ${data.commission.toFixed(2)} ETB</div>
            </div>
        </div>
    `;
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (winnersContainer) {
            winnersContainer.style.display = 'none';
        }
    }, 10000);
}

// Highlight winning cartela
function highlightWinningCartela(cartelaId) {
    const cartelaElement = document.querySelector(`.cartela-card[data-id="${cartelaId}"]`);
    if (cartelaElement) {
        cartelaElement.classList.add('winner-highlight');
        cartelaElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => {
            cartelaElement.classList.remove('winner-highlight');
        }, 5000);
    }
}

// Start balance checker (every 3 seconds)
function startBalanceChecker() {
    setInterval(async () => {
        if (socket && socket.connected && userData) {
            socket.emit('checkBalance', { telegram_id: userData.telegram_id });
        }
    }, CONFIG.BALANCE_CHECK_INTERVAL);
}

// Update connection status
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (statusEl) {
        statusEl.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
    }
}

// Initialize sounds
async function initSounds() {
    const soundFiles = {
        select: 'select.mp3',
        win: 'win.mp3',
        newRound: 'newRound.mp3',
        countdown: 'countdown.mp3',
        celebration: 'celebration.mp3'
    };
    
    // Load number sounds 1-75
    for (let i = 1; i <= 75; i++) {
        const audio = new Audio(`/sounds/${currentSoundPack}/${i}.mp3`);
        audio.preload = 'auto';
        sounds[`number_${i}`] = audio;
    }
    
    // Load effect sounds
    for (const [key, file] of Object.entries(soundFiles)) {
        const audio = new Audio(`/sounds/${currentSoundPack}/${file}`);
        audio.preload = 'auto';
        sounds[key] = audio;
    }
}

// Play sound
function playSound(soundName) {
    const soundEnabled = localStorage.getItem('soundEnabled') !== 'false';
    if (!soundEnabled) return;
    
    const sound = sounds[soundName];
    if (sound) {
        sound.currentTime = 0;
        sound.play().catch(e => console.log('Sound play error:', e));
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `<div class="notification-message">${message}</div>`;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

function showWinNotification(data) {
    showNotification(`🎉 YOU WON! 🎉\n+${data.amount.toFixed(2)} ETB\nPattern: ${data.pattern || 'BINGO!'}`, 'success');
}

function showError(message) {
    showNotification(message, 'error');
}

// Update UI elements
function updateUI() {
    // Update balance display
    const balanceElement = document.getElementById('balance');
    if (balanceElement) {
        balanceElement.textContent = `${gameState.balance.toFixed(2)} ETB`;
        if (gameState.balance < CONFIG.CARTELA_PRICE) {
            balanceElement.classList.add('balance-negative');
        } else {
            balanceElement.classList.remove('balance-negative');
        }
    }
    
    // Update round display
    const roundElement = document.getElementById('round');
    if (roundElement) {
        roundElement.textContent = gameState.round;
    }
    
    // Update pool amount
    const poolElement = document.getElementById('poolAmount');
    if (poolElement) {
        poolElement.textContent = `${gameState.poolAmount.toFixed(2)} ETB`;
    }
    
    // Update win percentage
    const winPercentElement = document.getElementById('winPercentage');
    if (winPercentElement) {
        winPercentElement.textContent = `${gameState.winPercentage}%`;
    }
    
    // Update status
    const statusElement = document.getElementById('gameStatus');
    if (statusElement) {
        let statusText = '';
        switch(gameState.status) {
            case 'selection':
                statusText = '🎯 SELECTION PHASE - Choose your cartelas!';
                break;
            case 'active':
                statusText = '🎲 GAME ACTIVE - Numbers being drawn!';
                break;
            case 'pause':
                statusText = '⏸️ NEXT ROUND STARTING SOON...';
                break;
        }
        statusElement.textContent = statusText;
    }
    
    // Update watch-only mode
    const watchOnlyMessage = document.getElementById('watchOnlyMessage');
    if (watchOnlyMessage) {
        watchOnlyMessage.style.display = gameState.canPlay ? 'none' : 'block';
    }
    
    // Update cartela availability
    updateCartelaAvailability();
}

function updateCartelaCount() {
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = `${selectedCartelas.size}/${CONFIG.MAX_CARTELAS}`;
    }
}

// Loading state
function showLoading() {
    const loader = document.getElementById('loadingOverlay');
    if (loader) loader.style.display = 'flex';
}

function hideLoading() {
    const loader = document.getElementById('loadingOverlay');
    if (loader) loader.style.display = 'none';
}

// Escape HTML
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initGame();
    
    // Initialize sound controls
    const soundToggleBtn = document.getElementById('soundToggleBtn');
    if (soundToggleBtn) {
        soundToggleBtn.addEventListener('click', () => {
            const enabled = localStorage.getItem('soundEnabled') !== 'false';
            localStorage.setItem('soundEnabled', !enabled);
            soundToggleBtn.textContent = !enabled ? '🔊 Sound On' : '🔇 Sound Off';
        });
    }
    
    const soundPackSelect = document.getElementById('soundPackSelect');
    if (soundPackSelect) {
        soundPackSelect.addEventListener('change', (e) => {
            currentSoundPack = e.target.value;
            localStorage.setItem('soundPack', currentSoundPack);
            initSounds();
            playSound('select');
        });
        soundPackSelect.value = localStorage.getItem('soundPack') || 'pack1';
    }
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .blinking {
            animation: blink 0.5s infinite;
            color: #ff4444 !important;
            font-weight: bold;
        }
        .bingo-ball {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #fff, #ffd700);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .bingo-ball.animate {
            animation: pulse 0.5s ease-out;
        }
        .bingo-ball-letter {
            font-size: 24px;
            font-weight: bold;
            color: #e94560;
        }
        .bingo-ball-number {
            font-size: 36px;
            font-weight: bold;
            color: #1a1a2e;
        }
        .winner-cartela {
            animation: pulse 1s infinite;
            border: 3px solid gold !important;
            box-shadow: 0 0 20px gold !important;
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #1e1e2f;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            max-width: 300px;
            white-space: pre-line;
        }
        .notification.success {
            background: linear-gradient(135deg, #00b09b, #96c93d);
        }
        .notification.error {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        }
        .notification.info {
            background: linear-gradient(135deg, #667eea, #764ba2);
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .fade-out {
            opacity: 0;
            transition: opacity 0.5s;
        }
        .connection-status {
            position: fixed;
            bottom: 10px;
            left: 10px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            z-index: 1000;
        }
        .connection-status.connected {
            background: #4caf50;
            box-shadow: 0 0 5px #4caf50;
        }
        .connection-status.disconnected {
            background: #f44336;
            box-shadow: 0 0 5px #f44336;
        }
        .cartela-card.winner-highlight {
            animation: winnerPulse 0.5s 3;
            border: 3px solid gold !important;
        }
        @keyframes winnerPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }
    `;
    document.head.appendChild(style);
});