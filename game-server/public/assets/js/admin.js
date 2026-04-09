// Estif Bingo 24/7 - Admin Module
// Updated to support string-based cartela IDs and enhanced features

// Admin State
let adminToken = null;
let refreshInterval = null;
let currentReportType = 'daily';
let currentViewingPlayer = null;

// ==================== LOGIN & AUTH ====================

// Login
async function adminLogin() {
    const email = document.getElementById('adminEmail').value;
    const password = document.getElementById('adminPassword').value;
    
    if (!email || !password) {
        showError('Please enter email and password');
        return;
    }
    
    try {
        const response = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            adminToken = data.token;
            localStorage.setItem('adminToken', adminToken);
            showAdminPanel();
            startLiveUpdates();
            showSuccess('Login successful!');
        } else {
            showError(data.message || 'Invalid credentials');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Login failed. Please try again.');
    }
}

// Logout
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('adminToken');
        adminToken = null;
        if (refreshInterval) clearInterval(refreshInterval);
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('adminPanel').style.display = 'none';
        showSuccess('Logged out successfully');
    }
}

// Show admin panel
function showAdminPanel() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('adminPanel').style.display = 'block';
    loadDashboard();
    loadActivePlayers();
}

// ==================== DASHBOARD STATS ====================

// Load dashboard stats
async function loadDashboard() {
    try {
        const response = await fetch('/api/admin/stats', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        const data = await response.json();
        
        if (data.success) {
            updateStats(data);
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Update statistics display
function updateStats(stats) {
    document.getElementById('onlinePlayers').textContent = stats.playersCount || 0;
    document.getElementById('currentRound').textContent = stats.round || 1;
    document.getElementById('poolAmount').textContent = `${(stats.totalBet || 0).toFixed(2)} ETB`;
    document.getElementById('winPercentage').textContent = `${stats.winPercentage || 75}%`;
    document.getElementById('totalBets').textContent = stats.globalSelectedCartelas || 0;
    document.getElementById('totalWinners').textContent = stats.winnersCount || 0;
    document.getElementById('totalCommission').textContent = `${(stats.adminCommission || 0).toFixed(2)} ETB`;
    
    // Update win percentage select if available
    const winPercentSelect = document.getElementById('winPercentageSelect');
    if (winPercentSelect && stats.winPercentage) {
        winPercentSelect.value = stats.winPercentage;
    }
}

// ==================== GAME CONTROLS ====================

// Change win percentage
async function changeWinPercentage() {
    const percentage = parseInt(document.getElementById('winPercentageSelect').value);
    
    try {
        const response = await fetch('/api/admin/win-percentage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`
            },
            body: JSON.stringify({ percentage })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Win percentage changed to ${percentage}%`);
            loadDashboard();
        } else {
            showError(data.message || 'Failed to change win percentage');
        }
    } catch (error) {
        console.error('Change win percentage error:', error);
        showError('Failed to change win percentage');
    }
}

// Force start round
async function forceStartRound() {
    if (confirm('Force start the next round? This will skip the selection phase.')) {
        try {
            const response = await fetch('/api/admin/start-game', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${adminToken}` }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess('Round started forcefully!');
                loadDashboard();
            } else {
                showError(data.message || 'Failed to start round');
            }
        } catch (error) {
            console.error('Force start error:', error);
            showError('Failed to force start');
        }
    }
}

// Force end round
async function forceEndRound() {
    if (confirm('Force end current round? No winners will be declared.')) {
        try {
            const response = await fetch('/api/admin/end-game', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${adminToken}` }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess('Round ended forcefully!');
                loadDashboard();
            } else {
                showError(data.message || 'Failed to end round');
            }
        } catch (error) {
            console.error('Force end error:', error);
            showError('Failed to force end');
        }
    }
}

// Reset game
async function resetGame() {
    if (confirm('⚠️ WARNING: Reset entire game to round 1? This action cannot be undone! All current selections will be lost.')) {
        try {
            const response = await fetch('/api/admin/reset-game', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${adminToken}` }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess('Game reset to round 1');
                loadDashboard();
            } else {
                showError(data.message || 'Failed to reset game');
            }
        } catch (error) {
            console.error('Reset game error:', error);
            showError('Failed to reset game');
        }
    }
}

// ==================== REPORTS ====================

// Load reports
async function loadReports() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!startDate || !endDate) {
        showError('Please select start and end dates');
        return;
    }
    
    try {
        const response = await fetch(`/api/reports/range?startDate=${startDate}&endDate=${endDate}`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayReports(data.report);
        } else {
            showError('No data found for this period');
        }
    } catch (error) {
        console.error('Load reports error:', error);
        showError('Failed to load reports');
    }
}

// Display reports
function displayReports(report) {
    const container = document.getElementById('reportsContainer');
    
    if (!report || !report.rounds || report.rounds.length === 0) {
        container.innerHTML = '<p class="no-data">No reports found for this period</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="report-summary">
            <div class="summary-card">
                <span class="summary-label">Total Games</span>
                <span class="summary-value">${report.totalGames}</span>
            </div>
            <div class="summary-card">
                <span class="summary-label">Total Bet</span>
                <span class="summary-value">${report.totalBet} ETB</span>
            </div>
            <div class="summary-card">
                <span class="summary-label">Total Won</span>
                <span class="summary-value">${report.totalWon} ETB</span>
            </div>
            <div class="summary-card">
                <span class="summary-label">Commission</span>
                <span class="summary-value">${report.totalCommission} ETB</span>
            </div>
        </div>
        <div class="table-wrapper">
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>Round #</th>
                        <th>Date</th>
                        <th>Cartelas</th>
                        <th>Pool</th>
                        <th>Payout</th>
                        <th>Commission</th>
                        <th>Win %</th>
                        <th>Winners</th>
                    </tr>
                </thead>
                <tbody>
                    ${report.rounds.map(round => `
                        <tr onclick="viewRoundDetails(${round.round_id})">
                            <td>${round.round_number}</td>
                            <td>${new Date(round.timestamp).toLocaleString()}</td>
                            <td>${round.total_cartelas}</td>
                            <td>${round.total_pool} ETB</td>
                            <td>${round.winner_reward} ETB</td>
                            <td>${round.admin_commission} ETB</td>
                            <td>${round.win_percentage}%</td>
                            <td>${round.winners ? JSON.parse(round.winners).length : 0}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// View round details
async function viewRoundDetails(roundId) {
    try {
        const response = await fetch(`/api/reports/round/${roundId}`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        
        const data = await response.json();
        
        if (data.success && data.round) {
            showRoundDetailsModal(data.round);
        }
    } catch (error) {
        console.error('View round details error:', error);
        showError('Failed to load round details');
    }
}

// Show round details modal
function showRoundDetailsModal(round) {
    const winners = round.winners ? JSON.parse(round.winners) : [];
    const winnerCartelas = round.winner_cartelas ? JSON.parse(round.winner_cartelas) : [];
    
    const modalHtml = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>Round #${round.round_number} Details</h3>
                    <span class="modal-close" onclick="closeModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="round-info-grid">
                        <div><strong>Date:</strong> ${new Date(round.timestamp).toLocaleString()}</div>
                        <div><strong>Total Players:</strong> ${round.total_players}</div>
                        <div><strong>Total Cartelas:</strong> ${round.total_cartelas}</div>
                        <div><strong>Total Pool:</strong> ${round.total_pool} ETB</div>
                        <div><strong>Winner Reward:</strong> ${round.winner_reward} ETB</div>
                        <div><strong>Commission:</strong> ${round.admin_commission} ETB</div>
                        <div><strong>Win Percentage:</strong> ${round.win_percentage}%</div>
                    </div>
                    ${winners.length > 0 ? `
                        <div class="winners-section">
                            <h4>🏆 Winners</h4>
                            ${winners.map((winner, i) => `
                                <div class="winner-detail">
                                    <strong>${winner}</strong>
                                    ${winnerCartelas[i] ? `
                                        <div>Cartela: ${winnerCartelas[i].cartelaId}</div>
                                        <div>Pattern: ${winnerCartelas[i].pattern || winnerCartelas[i].winningLines?.join(', ')}</div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    ` : '<p>No winners this round</p>'}
                </div>
                <div class="modal-footer">
                    <button onclick="closeModal()" class="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();
}

// Export reports
async function exportReports() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!startDate || !endDate) {
        showError('Please select start and end dates');
        return;
    }
    
    try {
        const response = await fetch(`/api/reports/export/range?startDate=${startDate}&endDate=${endDate}`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bingo_report_${startDate}_to_${endDate}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        showSuccess('Export started!');
    } catch (error) {
        console.error('Export error:', error);
        showError('Failed to export reports');
    }
}

// ==================== PLAYER MANAGEMENT ====================

// Search players
async function searchPlayers() {
    const searchTerm = document.getElementById('playerSearch').value.trim();
    
    if (searchTerm.length < 2) {
        showError('Enter at least 2 characters to search');
        return;
    }
    
    try {
        const response = await fetch('/api/admin/search-players', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`
            },
            body: JSON.stringify({ search: searchTerm })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayPlayers(data.players);
        } else {
            showError(data.message || 'No players found');
        }
    } catch (error) {
        console.error('Search players error:', error);
        showError('Failed to search players');
    }
}

// Display players
function displayPlayers(players) {
    const container = document.getElementById('playersContainer');
    
    if (!players || players.length === 0) {
        container.innerHTML = '<p class="no-data">No players found</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="players-grid">
            ${players.map(player => `
                <div class="player-card" onclick="viewPlayerDetails(${player.telegram_id})">
                    <div class="player-avatar">
                        ${getAvatarInitials(player.username || 'Player')}
                    </div>
                    <div class="player-info">
                        <div class="player-name">${escapeHtml(player.username || 'Unknown')}</div>
                        <div class="player-detail">🆔 ID: ${player.telegram_id}</div>
                        <div class="player-detail">📱 Phone: ${player.phone || 'Not registered'}</div>
                        <div class="player-balance">💰 ${parseFloat(player.balance || 0).toFixed(2)} ETB</div>
                        <div class="player-detail">💳 Deposited: ${parseFloat(player.total_deposited || 0).toFixed(2)} ETB</div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Get avatar initials
function getAvatarInitials(name) {
    if (!name) return '👤';
    const words = name.split(' ');
    if (words.length >= 2) {
        return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

// View player details
async function viewPlayerDetails(telegramId) {
    currentViewingPlayer = telegramId;
    
    try {
        const response = await fetch(`/api/admin/player/${telegramId}`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        
        const data = await response.json();
        
        if (data.success && data.player) {
            showPlayerDetailsModal(data.player);
        } else {
            showError('Failed to load player details');
        }
    } catch (error) {
        console.error('View player error:', error);
        showError('Failed to load player details');
    }
}

// Show player details modal
function showPlayerDetailsModal(player) {
    const modalHtml = `
        <div class="modal-overlay" onclick="closePlayerModal()">
            <div class="modal player-modal" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>👤 Player Details</h3>
                    <span class="modal-close" onclick="closePlayerModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="player-detail-card">
                        <div class="player-detail-row">
                            <strong>Username:</strong> ${escapeHtml(player.username || 'N/A')}
                        </div>
                        <div class="player-detail-row">
                            <strong>Telegram ID:</strong> ${player.telegram_id}
                        </div>
                        <div class="player-detail-row">
                            <strong>Phone:</strong> ${player.phone || 'Not registered'}
                        </div>
                        <div class="player-detail-row">
                            <strong>Language:</strong> ${player.language === 'am' ? 'አማርኛ' : 'English'}
                        </div>
                        <div class="player-detail-row">
                            <strong>Balance:</strong> <span class="player-balance-large">${parseFloat(player.balance || 0).toFixed(2)} ETB</span>
                        </div>
                        <div class="player-detail-row">
                            <strong>Total Deposited:</strong> ${parseFloat(player.total_deposited || 0).toFixed(2)} ETB
                        </div>
                        <div class="player-detail-row">
                            <strong>Total Withdrawn:</strong> ${parseFloat(player.total_withdrawn || 0).toFixed(2)} ETB
                        </div>
                        <div class="player-detail-row">
                            <strong>Registered:</strong> ${new Date(player.created_at).toLocaleString()}
                        </div>
                        ${player.currentGame && player.currentGame.online ? `
                            <div class="player-detail-row">
                                <strong>Status:</strong> <span class="online-status">🟢 Online</span>
                            </div>
                            <div class="player-detail-row">
                                <strong>Current Cartelas:</strong> ${player.currentGame.selectedCartelas?.join(', ') || 'None'}
                            </div>
                        ` : '<div class="player-detail-row"><strong>Status:</strong> ⚫ Offline</div>'}
                    </div>
                    <div class="action-buttons">
                        <button onclick="adjustBalance(${player.telegram_id}, 10)" class="btn btn-success">+10 ETB</button>
                        <button onclick="adjustBalance(${player.telegram_id}, 50)" class="btn btn-success">+50 ETB</button>
                        <button onclick="adjustBalance(${player.telegram_id}, 100)" class="btn btn-success">+100 ETB</button>
                        <button onclick="adjustBalance(${player.telegram_id}, -10)" class="btn btn-warning">-10 ETB</button>
                        <button onclick="adjustBalance(${player.telegram_id}, -50)" class="btn btn-warning">-50 ETB</button>
                        <button onclick="viewPlayerTransactions(${player.telegram_id})" class="btn btn-info">📜 Transactions</button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button onclick="closePlayerModal()" class="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closePlayerModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();
    currentViewingPlayer = null;
}

// Adjust player balance
async function adjustBalance(telegramId, amount) {
    const action = amount >= 0 ? 'add' : 'deduct';
    const absAmount = Math.abs(amount);
    
    if (confirm(`${action.toUpperCase()} ${absAmount} ETB for this player?`)) {
        try {
            const response = await fetch('/api/admin/adjust-balance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${adminToken}`
                },
                body: JSON.stringify({ telegram_id: telegramId, amount: amount })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess(`Balance adjusted by ${amount} ETB. New balance: ${data.new_balance} ETB`);
                closePlayerModal();
                viewPlayerDetails(telegramId);
            } else {
                showError(data.message || 'Failed to adjust balance');
            }
        } catch (error) {
            console.error('Adjust balance error:', error);
            showError('Failed to adjust balance');
        }
    }
}

// View player transactions
async function viewPlayerTransactions(telegramId) {
    try {
        const response = await fetch(`/api/admin/player-transactions/${telegramId}`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showTransactionsModal(data.transactions, data.playerName);
        }
    } catch (error) {
        console.error('View transactions error:', error);
        showError('Failed to load transactions');
    }
}

// Show transactions modal
function showTransactionsModal(transactions, playerName) {
    const modalHtml = `
        <div class="modal-overlay" onclick="closeTransactionsModal()">
            <div class="modal transactions-modal" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>📜 Transaction History: ${escapeHtml(playerName)}</h3>
                    <span class="modal-close" onclick="closeTransactionsModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="table-wrapper">
                        <table class="admin-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Type</th>
                                    <th>Amount</th>
                                    <th>Cartela</th>
                                    <th>Round</th>
                                    <th>Note</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${transactions.map(tx => `
                                    <tr>
                                        <td>${new Date(tx.timestamp).toLocaleString()}</td>
                                        <td><span class="tx-type ${tx.type}">${tx.type}</span></td>
                                        <td class="${tx.amount >= 0 ? 'text-success' : 'text-danger'}">${tx.amount >= 0 ? '+' : ''}${tx.amount} ETB</td>
                                        <td>${tx.cartela || '-'}</td>
                                        <td>${tx.round || '-'}</td>
                                        <td>${tx.note || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button onclick="closeTransactionsModal()" class="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeTransactionsModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();
}

// ==================== ACTIVE PLAYERS ====================

// Load active players
async function loadActivePlayers() {
    try {
        const response = await fetch('/api/admin/players', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayActivePlayers(data.players);
        }
    } catch (error) {
        console.error('Failed to load active players:', error);
    }
}

// Display active players
function displayActivePlayers(players) {
    const container = document.getElementById('activePlayersContainer');
    
    if (!players || players.length === 0) {
        container.innerHTML = '<p class="no-data">No active players</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="active-players-list">
            ${players.map(player => `
                <div class="active-player" onclick="viewPlayerDetails(${player.telegramId})">
                    <div class="active-player-info">
                        <span class="active-player-name">🎮 ${escapeHtml(player.username || 'Player')}</span>
                        <span class="active-player-cartelas">🎯 Cartelas: ${player.selectedCount || 0}</span>
                        <span class="active-player-balance">💰 ${(player.balance || 0).toFixed(2)} ETB</span>
                    </div>
                    <div class="active-player-cartelas-list">
                        ${player.selectedCartelas?.map(c => `<span class="cartela-badge">${c}</span>`).join('') || 'No cartelas selected'}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// ==================== SOUND SETTINGS ====================

// Change sound pack (admin preview)
function changeSoundPack(packName) {
    localStorage.setItem('adminSoundPack', packName);
    showSuccess(`Sound pack changed to ${packName}`);
    
    // Play preview sound
    const preview = new Audio(`/sounds/${packName}/win.mp3`);
    preview.play().catch(e => console.log('Preview error:', e));
    
    // Update active button styling
    document.querySelectorAll('.sound-pack-btn').forEach(btn => {
        if (btn.textContent.toLowerCase().includes(packName.replace('pack', ''))) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// ==================== UTILITIES ====================

// Start live updates
function startLiveUpdates() {
    if (refreshInterval) clearInterval(refreshInterval);
    
    refreshInterval = setInterval(() => {
        loadDashboard();
        loadActivePlayers();
    }, 5000);
}

// Show tab
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Update button active state
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.textContent.toLowerCase().includes(tabName)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Refresh data if needed
    if (tabName === 'players') {
        loadActivePlayers();
    }
    if (tabName === 'reports') {
        const today = new Date();
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);
        
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        if (startDate && !startDate.value) {
            startDate.value = weekAgo.toISOString().split('T')[0];
        }
        if (endDate && !endDate.value) {
            endDate.value = today.toISOString().split('T')[0];
        }
    }
}

// Show success message
function showSuccess(message) {
    showToast(message, 'success');
}

// Show error message
function showError(message) {
    showToast(message, 'error');
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">${message}</div>
        <div class="toast-progress"></div>
    `;
    
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
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

// ==================== INITIALIZATION ====================

// Initialize admin panel
document.addEventListener('DOMContentLoaded', () => {
    // Check for existing token
    const savedToken = localStorage.getItem('adminToken');
    if (savedToken) {
        adminToken = savedToken;
        // Verify token is still valid
        fetch('/api/admin/stats', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        }).then(response => {
            if (response.status === 401) {
                logout();
            } else {
                showAdminPanel();
                startLiveUpdates();
            }
        }).catch(() => logout());
    }
    
    // Set default dates for reports
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) {
        startDateInput.value = weekAgo.toISOString().split('T')[0];
    }
    if (endDateInput) {
        endDateInput.value = today.toISOString().split('T')[0];
    }
    
    // Enter key for login
    const passwordInput = document.getElementById('adminPassword');
    if (passwordInput) {
        passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') adminLogin();
        });
    }
    
    // Enter key for player search
    const playerSearch = document.getElementById('playerSearch');
    if (playerSearch) {
        playerSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchPlayers();
        });
    }
    
    // Add CSS for new components
    const style = document.createElement('style');
    style.textContent = `
        .toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .toast {
            background: #1e1e2f;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            min-width: 250px;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .toast.success { background: linear-gradient(135deg, #00b09b, #96c93d); }
        .toast.error { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
        .toast.info { background: linear-gradient(135deg, #667eea, #764ba2); }
        .toast.fade-out {
            animation: fadeOut 0.3s forwards;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeOut {
            to { transform: translateX(100%); opacity: 0; }
        }
        .player-card {
            cursor: pointer;
            transition: transform 0.2s;
        }
        .player-card:hover {
            transform: translateY(-3px);
        }
        .cartela-badge {
            display: inline-block;
            background: rgba(255,215,0,0.2);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px;
        }
        .tx-type {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }
        .tx-type.win { background: #4caf50; color: white; }
        .tx-type.bet { background: #ff9800; color: white; }
        .tx-type.refund { background: #2196f3; color: white; }
        .online-status { color: #4caf50; }
        .report-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .summary-card {
            background: linear-gradient(135deg, #1e1e2f, #16162a);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
        }
        .summary-label {
            font-size: 12px;
            opacity: 0.7;
            display: block;
        }
        .summary-value {
            font-size: 20px;
            font-weight: bold;
            color: #ffd966;
        }
    `;
    document.head.appendChild(style);
});