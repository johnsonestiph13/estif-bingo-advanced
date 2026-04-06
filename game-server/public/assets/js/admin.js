// assets/js/admin.js - Admin Panel Logic

// ==================== GLOBALS ====================
let adminToken = localStorage.getItem('adminToken');
let statsInterval = null;
let playersInterval = null;

// DOM Elements
let loginSection, adminPanel, statsGrid, reportResult, playersListContainer;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    loginSection = document.getElementById('loginSection');
    adminPanel = document.getElementById('adminPanel');
    statsGrid = document.getElementById('statsGrid');
    reportResult = document.getElementById('reportResult');
    playersListContainer = document.getElementById('playersListContainer');
    
    // Check if already logged in
    if (adminToken) {
        verifyToken();
    } else {
        showLogin();
    }
    
    // Setup event listeners
    setupEventListeners();
});

// ==================== LOGIN / LOGOUT ====================
async function verifyToken() {
    try {
        const response = await fetch('/api/admin/verify', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (response.ok) {
            showAdminPanel();
        } else {
            logout();
        }
    } catch {
        logout();
    }
}

async function login() {
    const email = document.getElementById('adminEmail').value;
    const password = document.getElementById('adminPassword').value;
    
    try {
        const response = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        
        if (data.success && data.token) {
            adminToken = data.token;
            localStorage.setItem('adminToken', adminToken);
            showAdminPanel();
        } else {
            document.getElementById('loginError').innerText = 'Invalid credentials';
        }
    } catch (err) {
        document.getElementById('loginError').innerText = 'Login failed';
    }
}

function logout() {
    localStorage.removeItem('adminToken');
    adminToken = null;
    if (statsInterval) clearInterval(statsInterval);
    if (playersInterval) clearInterval(playersInterval);
    showLogin();
}

function showLogin() {
    loginSection.style.display = 'block';
    adminPanel.style.display = 'none';
}

function showAdminPanel() {
    loginSection.style.display = 'none';
    adminPanel.style.display = 'block';
    
    // Start auto-refresh
    refreshGameStats();
    loadOnlinePlayers();
    statsInterval = setInterval(refreshGameStats, 5000);
    playersInterval = setInterval(loadOnlinePlayers, 10000);
    
    // Load sound pack selection
    loadSoundPackSelection();
}

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    document.getElementById('loginBtn')?.addEventListener('click', login);
    document.getElementById('logoutBtn')?.addEventListener('click', logout);
    document.getElementById('setWinPercentBtn')?.addEventListener('click', setWinPercentage);
    document.getElementById('startGameBtn')?.addEventListener('click', startGame);
    document.getElementById('endGameBtn')?.addEventListener('click', endGame);
    document.getElementById('resetGameBtn')?.addEventListener('click', resetGame);
    document.getElementById('reportType')?.addEventListener('change', updateDateInputs);
    document.getElementById('fetchReportBtn')?.addEventListener('click', fetchReport);
    document.getElementById('applySoundPackBtn')?.addEventListener('click', applySoundPack);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.getElementById(`${tabId}Tab`).classList.add('active');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (tabId === 'players') loadOnlinePlayers();
            if (tabId === 'reports') updateDateInputs();
        });
    });
}

// ==================== API CALLS ====================
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken}`
    };
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);
    
    const response = await fetch(`/api/admin${endpoint}`, options);
    if (response.status === 401) {
        logout();
        throw new Error('Session expired');
    }
    return response.json();
}

// ==================== GAME CONTROLS ====================
async function refreshGameStats() {
    try {
        const data = await apiCall('/stats');
        if (data.success) {
            document.getElementById('statStatus').innerText = data.status || '-';
            document.getElementById('statRound').innerText = data.round || '-';
            document.getElementById('statTimer').innerText = data.timer || '-';
            document.getElementById('statTotalBet').innerText = (data.totalBet || 0).toFixed(2);
            document.getElementById('statWinnerReward').innerText = (data.winnerReward || 0).toFixed(2);
            document.getElementById('statCommission').innerText = (data.adminCommission || 0).toFixed(2);
            document.getElementById('statPlayersCount').innerText = data.playersCount || 0;
            document.getElementById('statWinPercent').innerText = `${data.winPercentage || 75}%`;
            
            const select = document.getElementById('winPercentSelect');
            if (select && data.winPercentage) select.value = data.winPercentage;
        }
    } catch (err) {
        console.error('Stats error:', err);
    }
}

async function setWinPercentage() {
    const percentage = parseInt(document.getElementById('winPercentSelect').value);
    try {
        const res = await apiCall('/win-percentage', 'POST', { percentage });
        if (res.success) {
            showMessage(`Win percentage set to ${percentage}%`, 'success');
            refreshGameStats();
        } else {
            showMessage(res.message || 'Failed', 'error');
        }
    } catch (err) {
        showMessage('Error setting win percentage', 'error');
    }
}

async function startGame() {
    try {
        const res = await apiCall('/start-game', 'POST');
        if (res.success) {
            showMessage('Game started forcefully!', 'success');
            refreshGameStats();
        } else {
            showMessage(res.message || 'Cannot start game', 'error');
        }
    } catch (err) {
        showMessage('Error starting game', 'error');
    }
}

async function endGame() {
    if (confirm('End current round with no winner? This will skip to next round.')) {
        try {
            const res = await apiCall('/end-game', 'POST');
            if (res.success) {
                showMessage('Round ended', 'success');
                refreshGameStats();
            } else {
                showMessage(res.message || 'Cannot end game', 'error');
            }
        } catch (err) {
            showMessage('Error ending game', 'error');
        }
    }
}

async function resetGame() {
    if (confirm('⚠️ RESET GAME to round 1? All current cartela selections will be lost. Players remain. Proceed?')) {
        try {
            const res = await apiCall('/reset-game', 'POST');
            if (res.success) {
                showMessage('Game reset to round 1', 'success');
                refreshGameStats();
            } else {
                showMessage(res.message || 'Reset failed', 'error');
            }
        } catch (err) {
            showMessage('Error resetting game', 'error');
        }
    }
}

async function loadOnlinePlayers() {
    try {
        const data = await apiCall('/players');
        if (data.success && data.players) {
            playersListContainer.innerHTML = '';
            if (data.players.length === 0) {
                playersListContainer.innerHTML = '<div class="player-card">No players online</div>';
            } else {
                data.players.forEach(p => {
                    const card = document.createElement('div');
                    card.className = 'player-card';
                    card.innerText = `${p.username} - ${p.selectedCount} cartelas | ${p.balance} ETB`;
                    playersListContainer.appendChild(card);
                });
            }
        }
    } catch (err) {
        playersListContainer.innerHTML = '<div class="player-card">Error loading players</div>';
    }
}

// ==================== REPORTS ====================
function updateDateInputs() {
    const type = document.getElementById('reportType').value;
    const container = document.getElementById('dynamicDateInputs');
    container.innerHTML = '';
    
    if (type === 'daily') {
        container.innerHTML = '<input type="date" id="reportDate" value="' + new Date().toISOString().slice(0,10) + '">';
    } else if (type === 'weekly') {
        const now = new Date();
        const week = getWeekNumber(now);
        container.innerHTML = `
            <input type="number" id="weekYear" placeholder="Year" value="${now.getFullYear()}" style="width:100px">
            <input type="number" id="weekNum" placeholder="Week" value="${week}" style="width:100px">
        `;
    } else if (type === 'monthly') {
        const now = new Date();
        container.innerHTML = `
            <input type="number" id="monthYear" placeholder="Year" value="${now.getFullYear()}" style="width:100px">
            <select id="monthNum">
                ${[...Array(12)].map((_, i) => `<option value="${i+1}" ${i+1 === now.getMonth()+1 ? 'selected' : ''}>${new Date(0, i).toLocaleString('default', {month:'long'})}</option>`).join('')}
            </select>
        `;
    } else if (type === 'range') {
        container.innerHTML = `
            <input type="date" id="startDate" placeholder="Start Date">
            <input type="date" id="endDate" placeholder="End Date">
        `;
    }
}

function getWeekNumber(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + 3 - (d.getDay() + 6) % 7);
    const week1 = new Date(d.getFullYear(), 0, 4);
    return 1 + Math.round(((d - week1) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
}

async function fetchReport() {
    const type = document.getElementById('reportType').value;
    let url = '';
    
    if (type === 'daily') {
        const date = document.getElementById('reportDate').value;
        if (!date) return showMessage('Select date', 'error');
        url = `/api/reports/daily?date=${date}`;
    } else if (type === 'weekly') {
        const year = document.getElementById('weekYear').value;
        const week = document.getElementById('weekNum').value;
        if (!year || !week) return showMessage('Enter year and week', 'error');
        url = `/api/reports/weekly?year=${year}&week=${week}`;
    } else if (type === 'monthly') {
        const year = document.getElementById('monthYear').value;
        const month = document.getElementById('monthNum').value;
        url = `/api/reports/monthly?year=${year}&month=${month}`;
    } else if (type === 'range') {
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        if (!start || !end) return showMessage('Select start and end dates', 'error');
        url = `/api/reports/range?startDate=${start}&endDate=${end}`;
    } else if (type === 'commission') {
        url = `/api/reports/commission`;
    }
    
    try {
        const data = await fetch(url, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        }).then(res => res.json());
        
        if (data.success) {
            displayReport(data, type);
        } else {
            showMessage('No data or error', 'error');
        }
    } catch (err) {
        showMessage('Failed to fetch report', 'error');
    }
}

function displayReport(data, type) {
    if (type === 'commission') {
        let html = '<h3>Commission Breakdown</h3><table class="admin-table"><thead><tr><th>Round ID</th><th>Date</th><th>Total Pool</th><th>Winner Reward</th><th>Admin Commission</th><th>Win %</th></tr></thead><tbody>';
        (data.commissionByRound || []).forEach(r => {
            html += `<tr>
                <td>${r.round_id}</td>
                <td>${new Date(r.timestamp).toLocaleString()}</td>
                <td>${r.total_pool}</td>
                <td>${r.winner_reward}</td>
                <td>${r.admin_commission}</td>
                <td>${r.win_percentage}%</td>
            </tr>`;
        });
        html += '</tbody></table>';
        reportResult.innerHTML = html;
    } else {
        const report = data.report;
        let html = `<h3>Report: ${report.date || report.startDate || 'Range'}</h3>`;
        html += `<p><strong>Total Games:</strong> ${report.totalGames} | <strong>Total Bet:</strong> ${report.totalBet} ETB | <strong>Total Won:</strong> ${report.totalWon} ETB | <strong>Total Commission:</strong> ${report.totalCommission} ETB</p>`;
        
        if (report.rounds && report.rounds.length) {
            html += '<table class="admin-table"><thead><tr><th>Round ID</th><th>Round #</th><th>Total Cartelas</th><th>Total Pool</th><th>Winner Reward</th><th>Commission</th><th>Winners</th><th>Time</th></tr></thead><tbody>';
            report.rounds.forEach(r => {
                let winners = r.winners ? (Array.isArray(r.winners) ? r.winners.join(', ') : '-') : '-';
                html += `<tr>
                    <td>${r.round_id}</td>
                    <td>${r.round_number}</td>
                    <td>${r.total_cartelas}</td>
                    <td>${r.total_pool}</td>
                    <td>${r.winner_reward}</td>
                    <td>${r.admin_commission}</td>
                    <td>${winners}</td>
                    <td>${new Date(r.timestamp).toLocaleString()}</td>
                </tr>`;
            });
            html += '</tbody></table>';
        } else {
            html += '<p>No rounds found.</p>';
        }
        reportResult.innerHTML = html;
    }
}

// ==================== SOUND SETTINGS ====================
function loadSoundPackSelection() {
    const saved = localStorage.getItem('soundPack');
    if (saved) {
        document.getElementById('soundPackSelect').value = saved;
    }
}

function applySoundPack() {
    const pack = document.getElementById('soundPackSelect').value;
    localStorage.setItem('soundPack', pack);
    showMessage(`Sound pack set to ${pack}. It will be used on the player page.`, 'success');
}

// ==================== UTILITIES ====================
function showMessage(msg, type = 'info') {
    const msgDiv = document.createElement('div');
    msgDiv.className = `action-message ${type}`;
    msgDiv.innerText = msg;
    document.querySelector('.admin-container').prepend(msgDiv);
    setTimeout(() => msgDiv.remove(), 3000);
}

// ==================== INITIALIZE DATE INPUTS ====================
updateDateInputs();