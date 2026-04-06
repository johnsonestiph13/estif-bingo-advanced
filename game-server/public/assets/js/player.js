// assets/js/player.js - Main Player Game Logic

// ==================== GLOBALS ====================
let gameState = {
    status: 'selection',
    round: 1,
    timer: 50,
    drawnNumbers: [],
    players: [],
    totalBet: 0,
    winnerReward: 0,
    winPercentage: 75,
    myBalance: 0,
    myUsername: '',
    mySelectedCartelas: [],
    myTelegramId: null
};

// DOM Elements
let balanceEl, roundEl, poolEl, winPercentEl, playersCountEl, timerEl, statusEl;
let cartelasContainer, drawnNumbersContainer, playersListContainer;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', async () => {
    // Get DOM elements
    balanceEl = document.getElementById('balance');
    roundEl = document.getElementById('round');
    poolEl = document.getElementById('pool');
    winPercentEl = document.getElementById('winPercent');
    playersCountEl = document.getElementById('playersCount');
    timerEl = document.getElementById('timer');
    statusEl = document.getElementById('statusMsg');
    cartelasContainer = document.getElementById('cartelasContainer');
    drawnNumbersContainer = document.getElementById('drawnNumbersList');
    playersListContainer = document.getElementById('playersList');
    
    // Get token from URL
    const token = getQueryParam('token');
    const code = getQueryParam('code');
    
    if (!token && !code) {
        document.getElementById('app').innerHTML = '<div class="error-box">❌ Access denied. Please use the Telegram bot to play.</div>';
        return;
    }
    
    // Exchange code for token if needed
    if (code && !token) {
        await exchangeCodeForToken(code);
    } else if (token) {
        gameState.authToken = token;
    }
    
    // Preload sound
    soundManager.preload();
    
    // Initialize socket connection
    socketManager.connect();
    setupSocketEvents();
    
    // Authenticate
    socketManager.authenticate(gameState.authToken);
});

// ==================== TOKEN EXCHANGE ====================
async function exchangeCodeForToken(code) {
    try {
        const response = await fetch('/api/exchange-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        const data = await response.json();
        if (data.success && data.token) {
            gameState.authToken = data.token;
            // Clean URL
            window.history.replaceState({}, '', window.location.pathname);
        } else {
            throw new Error(data.message || 'Code exchange failed');
        }
    } catch (err) {
        showMessage(`Authentication failed: ${err.message}`, 'error');
        document.getElementById('app').innerHTML = `<div class="error-box">❌ ${err.message}</div>`;
    }
}

// ==================== SOCKET EVENTS ====================
function setupSocketEvents() {
    // Authentication response
    socketManager.on('authenticated', (data) => {
        gameState.myUsername = data.username;
        gameState.myBalance = data.balance;
        gameState.mySelectedCartelas = data.selectedCartelas || [];
        gameState.myTelegramId = data.telegramId;
        
        updateBalanceUI(gameState.myBalance);
        cartelaManager.selectedCartelas = gameState.mySelectedCartelas;
        cartelaManager.render();
        
        statusEl.innerText = '✅ Connected! Game active';
    });
    
    // Game state update
    socketManager.on('gameState', (state) => {
        gameState.status = state.status;
        gameState.round = state.round;
        gameState.timer = state.timer;
        gameState.winPercentage = state.winPercentage;
        gameState.totalBet = state.totalBet;
        gameState.winnerReward = state.winnerReward;
        
        roundEl.innerText = state.round;
        winPercentEl.innerText = `${state.winPercentage}%`;
        poolEl.innerText = state.totalBet.toFixed(2);
        
        statusEl.innerText = state.status === 'selection' ? '🎲 SELECTION PHASE - Pick cartelas!' : 
                            (state.status === 'active' ? '🎯 GAME ACTIVE' : '🏁 Round ended');
        
        if (state.players) updatePlayersUI(state.players);
        cartelaManager.updateAvailability(gameState.myBalance, gameState.status);
    });
    
    // Timer update
    socketManager.on('timerUpdate', (data) => {
        gameState.timer = data.seconds;
        timerEl.innerText = formatTime(data.seconds);
        
        const timerBox = document.getElementById('timerBox');
        if (data.seconds <= 10 && data.seconds > 0) {
            timerBox.classList.add('warning');
            if (data.seconds === 10) soundManager.playCountdown();
        } else {
            timerBox.classList.remove('warning');
        }
    });
    
    // Reward pool update
    socketManager.on('rewardPoolUpdate', (data) => {
        poolEl.innerText = data.totalBetAmount.toFixed(2);
        winPercentEl.innerText = `${data.winPercentage}%`;
    });
    
    // Selection confirmed
    socketManager.on('selectionConfirmed', (data) => {
        gameState.mySelectedCartelas = data.selectedCartelas;
        gameState.myBalance = data.balance;
        updateBalanceUI(gameState.myBalance);
        cartelaManager.selectedCartelas = gameState.mySelectedCartelas;
        cartelaManager.render();
        showMessage(`✅ Cartela ${data.cartela} selected! Remaining slots: ${data.remainingSlots}`, 'success', 1200);
        soundManager.playSelect();
    });
    
    // Selection updated (deselect)
    socketManager.on('selectionUpdated', (data) => {
        gameState.mySelectedCartelas = data.selectedCartelas;
        gameState.myBalance = data.balance;
        updateBalanceUI(gameState.myBalance);
        cartelaManager.selectedCartelas = gameState.mySelectedCartelas;
        cartelaManager.render();
    });
    
    // Cartela taken by someone else
    socketManager.on('cartelaTaken', (data) => {
        showMessage(`⚠️ Cartela ${data.cartelaNumber} taken by ${data.takenBy}`, 'warning', 2000);
        cartelaManager.render();
    });
    
    // Cartela released
    socketManager.on('cartelaReleased', (data) => {
        showMessage(`📢 Cartela ${data.cartelaNumber} released by ${data.releasedBy}`, 'info', 1500);
        cartelaManager.render();
    });
    
    // Number drawn
    socketManager.on('numberDrawn', (data) => {
        gameState.drawnNumbers.push(data.number);
        updateDrawnNumbersUI(gameState.drawnNumbers);
        soundManager.playNumber(data.number);
    });
    
    // Game started
    socketManager.on('gameStarted', (data) => {
        gameState.drawnNumbers = [];
        updateDrawnNumbersUI([]);
        showMessage(data.message, 'success', 4000);
        gameState.status = 'active';
        cartelaManager.updateAvailability(gameState.myBalance, 'active');
    });
    
    // Round ended
    socketManager.on('roundEnded', (data) => {
        showMessage(data.message, 'success', 5000);
        gameState.status = 'ended';
        cartelaManager.updateAvailability(gameState.myBalance, 'ended');
    });
    
    // You won!
    socketManager.on('youWon', (data) => {
        gameState.myBalance = data.newBalance;
        updateBalanceUI(gameState.myBalance);
        showMessage(`🎉🎉 YOU WON ${data.amount.toFixed(2)} ETB! 🎉🎉`, 'success', 8000);
        soundManager.playWin();
        
        if (data.cartelaId && data.winningLines) {
            showMessage(`🏆 Winning cartela #${data.cartelaId} - Lines: ${data.winningLines.join(', ')}`, 'success', 6000);
        }
        
        // Add winner glow effect
        document.body.classList.add('winner-glow');
        setTimeout(() => document.body.classList.remove('winner-glow'), 1000);
    });
    
    // Next round
    socketManager.on('nextRound', (data) => {
        gameState.mySelectedCartelas = [];
        gameState.drawnNumbers = [];
        updateDrawnNumbersUI([]);
        cartelaManager.selectedCartelas = [];
        cartelaManager.render();
        gameState.status = 'selection';
        gameState.round = data.round;
        roundEl.innerText = data.round;
        showMessage(data.message, 'info', 3000);
        cartelaManager.updateAvailability(gameState.myBalance, 'selection');
    });
    
    // Players update
    socketManager.on('playersUpdate', (data) => {
        updatePlayersUI(data.players);
        playersCountEl.innerText = data.count;
    });
    
    // Balance updated (from admin or other devices)
    socketManager.on('balanceUpdated', (data) => {
        if (data.added) {
            gameState.myBalance = data.balance;
            updateBalanceUI(gameState.myBalance);
            showMessage(`💰 Balance increased by ${data.added.toFixed(2)} ETB`, 'success', 2000);
        } else if (data.removed) {
            gameState.myBalance = data.balance;
            updateBalanceUI(gameState.myBalance);
            showMessage(`💸 Balance decreased by ${data.removed.toFixed(2)} ETB`, 'warning', 2000);
        } else {
            gameState.myBalance = data.balance;
            updateBalanceUI(gameState.myBalance);
        }
        cartelaManager.updateAvailability(gameState.myBalance, gameState.status);
    });
    
    // State sync (multi-device)
    socketManager.on('stateSync', (data) => {
        gameState.myBalance = data.balance;
        gameState.mySelectedCartelas = data.selectedCartelas;
        updateBalanceUI(gameState.myBalance);
        cartelaManager.selectedCartelas = gameState.mySelectedCartelas;
        cartelaManager.render();
        showMessage('🔄 Synced with other device', 'info', 2000);
    });
    
    // Error
    socketManager.on('error', (err) => {
        showMessage(`⚠️ ${err.message}`, 'error', 3000);
    });
}

// ==================== UI UPDATE FUNCTIONS ====================
function updateBalanceUI(balance) {
    gameState.myBalance = balance;
    balanceEl.innerText = balance.toFixed(2);
}

function updateDrawnNumbersUI(numbers) {
    drawnNumbersContainer.innerHTML = '';
    numbers.forEach(num => {
        const ball = document.createElement('div');
        ball.className = 'number-ball';
        ball.innerText = num;
        drawnNumbersContainer.appendChild(ball);
    });
    drawnNumbersContainer.scrollTop = drawnNumbersContainer.scrollHeight;
}

function updatePlayersUI(players) {
    playersListContainer.innerHTML = '';
    players.forEach(p => {
        const badge = document.createElement('div');
        badge.className = 'player-badge';
        badge.innerText = `${p.username} (${p.selectedCount})`;
        playersListContainer.appendChild(badge);
    });
}

// ==================== CARTELA ACTIONS ====================
function onCartelaSelect(cartelaId) {
    if (gameState.status !== 'selection') {
        showMessage('⏳ Cannot select now, wait for next round', 'warning', 1500);
        return false;
    }
    
    if (gameState.myBalance < 10) {
        showMessage(`⚠️ Insufficient balance: ${gameState.myBalance} ETB`, 'warning', 1500);
        return false;
    }
    
    socketManager.selectCartela(cartelaId, (response) => {
        if (!response.success) {
            showMessage(response.error, 'error', 2000);
        }
    });
    return true;
}

function onCartelaDeselect(cartelaId) {
    if (gameState.status !== 'selection') {
        showMessage('⏳ Cannot deselect now', 'warning', 1500);
        return false;
    }
    socketManager.deselectCartela(cartelaId);
    return true;
}

// ==================== INITIALIZE CARTELA MANAGER ====================
cartelaManager.init('cartelasContainer', onCartelaSelect, onCartelaDeselect);
cartelaManager.maxPerPlayer = 2;
cartelaManager.selectedCartelas = gameState.mySelectedCartelas;

// ==================== EXPOSE FOR DEBUG ====================
window.gameState = gameState;
window.socketManager = socketManager;
window.cartelaManager = cartelaManager;
window.soundManager = soundManager;