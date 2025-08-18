// Dashboard JavaScript for Comprehensive Trading System

// Global variables
let currentUser = null;
let sessionId = null;
let currentSection = 'overview';
let refreshInterval = null;
let isDemoMode = true;
let priceChart = null;
let watchlistSymbols = [];
let symbolChart = null;
let marketWebSocket = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    initializeDashboard();
});

// Initialize dashboard
async function initializeDashboard() {
    // Check authentication
    await checkAuthentication();
    
    // Initialize trading mode toggle
    initializeTradingModeToggle();
    
    // Load market watch symbols (only once)
    await loadMarketWatchSymbols();
    
    // Load only overview data initially
    await loadOverviewData();
    
    // Disable auto-refresh by default; user can manually refresh
    
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize tooltips
    initializeTooltips();

    // Initialize market WebSocket for live ticks
    initializeMarketWebSocket();
}

// Check authentication
async function checkAuthentication() {
    sessionId = localStorage.getItem('sessionId');
    if (!sessionId) {
        // User not authenticated, but allow demo mode
        document.getElementById('userInfo').textContent = 'Demo User';
        return;
    }
    
    // Get user details from API
    try {
        const response = await fetch('/api/user/details');
        const data = await response.json();
        
        if (data.status === 'success' && data.user_details) {
            const userName = data.user_details.idirect_user_name || 'User';
            document.getElementById('userInfo').textContent = userName;
        } else if (data.status === 'demo') {
            document.getElementById('userInfo').textContent = data.user_details.idirect_user_name;
        } else {
            // Fallback to API key
            const apiKey = localStorage.getItem('apiKey');
            if (apiKey) {
                document.getElementById('userInfo').textContent = `User (${apiKey.substring(0, 8)}...)`;
            }
        }
    } catch (error) {
        console.error('Error fetching user details:', error);
        // Fallback to API key
        const apiKey = localStorage.getItem('apiKey');
        if (apiKey) {
            document.getElementById('userInfo').textContent = `User (${apiKey.substring(0, 8)}...)`;
        }
    }
}

// Initialize trading mode toggle
function initializeTradingModeToggle() {
    const toggle = document.getElementById('tradingModeToggle');
    const label = document.getElementById('tradingModeLabel');
    const alert = document.getElementById('demoModeAlert');
    
    // Set initial state
    isDemoMode = toggle.checked;
    updateTradingModeUI();
    
    // Add event listener
    toggle.addEventListener('change', function() {
        isDemoMode = this.checked;
        updateTradingModeUI();
        
        // Reload current section data
        if (currentSection) {
            loadSectionData(currentSection);
        }
    });
}

// Update trading mode UI
function updateTradingModeUI() {
    const label = document.getElementById('tradingModeLabel');
    const alert = document.getElementById('demoModeAlert');
    
    if (isDemoMode) {
        label.textContent = 'Demo Mode';
        alert.style.display = 'block';
        alert.className = 'alert alert-info alert-dismissible fade show';
        alert.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            <strong>Demo Mode Active:</strong> All trading operations are simulated. No real orders will be placed.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
    } else {
        label.textContent = 'Real Mode';
        alert.style.display = 'block';
        alert.className = 'alert alert-warning alert-dismissible fade show';
        alert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Real Mode Active:</strong> All trading operations will be executed with real money. Proceed with caution.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
    }
}

// Load market watch symbols from server
async function loadMarketWatchSymbols() {
    try {
        const response = await fetch('/api/market-watch/symbols');
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            watchlistSymbols = data.data;
            console.log('Loaded market watch symbols:', watchlistSymbols);
        } else {
            console.error('Failed to load market watch symbols:', data.message);
        }
    } catch (error) {
        console.error('Error loading market watch symbols:', error);
    }
}

// Load overview data (dashboard cards only)
async function loadOverviewData() {
    showLoading(true);
    
    try {
        // Load only portfolio summary for overview cards
        await loadPortfolioSummary();
        
    } catch (error) {
        console.error('Error loading overview data:', error);
        showAlert('Error loading overview data. Please refresh the page.', 'danger');
    } finally {
        showLoading(false);
    }
}

// Load dashboard data (legacy function - now deprecated)
async function loadDashboardData() {
    console.warn('loadDashboardData is deprecated. Use loadOverviewData() for overview or loadSectionData() for specific sections.');
    await loadOverviewData();
}

// Load portfolio summary
async function loadPortfolioSummary() {
    try {
        const response = await fetch('/api/portfolio/summary');
        const data = await response.json();
        
        console.log('Portfolio summary response:', data);
        
        if (response.ok) {
            updatePortfolioCards(data);
        } else {
            console.error('Portfolio summary request failed:', response.status, data);
        }
    } catch (error) {
        console.error('Error loading portfolio summary:', error);
    }
}

// Update portfolio cards
function updatePortfolioCards(data) {
    const totalValueEl = document.getElementById('totalValue');
    const totalPnlEl = document.getElementById('totalPnl');
    const cashBalanceEl = document.getElementById('cashBalance');
    const holdingsCountEl = document.getElementById('holdingsCount');
    
    console.log('updatePortfolioCards called with data:', data);
    console.log('isDemoMode:', isDemoMode);
    
    // Get data source based on mode
    const dataSource = isDemoMode ? data.fake_trading : data;
    const sourceLabel = isDemoMode ? 'Demo Data' : 'Real Data';
    
    console.log('dataSource:', dataSource);
    
    if (totalValueEl) {
        const totalValue = dataSource?.total_balance || dataSource?.net_worth || 0;
        console.log('Setting totalValue:', totalValue);
        totalValueEl.textContent = formatCurrency(totalValue);
        document.getElementById('totalValueSource').textContent = sourceLabel;
    } else {
        console.error('totalValueEl not found');
    }
    
    if (totalPnlEl) {
        const pnl = dataSource?.total_unrealized_pnl || 0;
        console.log('Setting pnl:', pnl);
        totalPnlEl.textContent = formatCurrency(pnl);
        totalPnlEl.className = `h5 mb-0 font-weight-bold ${pnl >= 0 ? 'text-success' : 'text-danger'}`;
        document.getElementById('totalPnlSource').textContent = sourceLabel;
    } else {
        console.error('totalPnlEl not found');
    }
    
    if (cashBalanceEl) {
        const cashBalance = dataSource?.cash_balance || 0;
        console.log('Setting cashBalance:', cashBalance);
        cashBalanceEl.textContent = formatCurrency(cashBalance);
        document.getElementById('cashBalanceSource').textContent = sourceLabel;
    } else {
        console.error('cashBalanceEl not found');
    }
    
    if (holdingsCountEl) {
        const holdingsCount = dataSource?.holdings_count || 0;
        console.log('Setting holdingsCount:', holdingsCount);
        holdingsCountEl.textContent = holdingsCount;
        document.getElementById('holdingsCountSource').textContent = sourceLabel;
    } else {
        console.error('holdingsCountEl not found');
    }
    
    // Log the data for debugging
    console.log('Portfolio Summary Data:', {
        isDemoMode,
        dataSource,
        totalValue: dataSource?.total_balance,
        cashBalance: dataSource?.cash_balance,
        pnl: dataSource?.total_unrealized_pnl,
        holdingsCount: dataSource?.holdings_count
    });
    

}

// Load market watch
async function loadMarketWatch() {
    try {
        await updateMarketWatchTable();
    } catch (error) {
        console.error('Error loading market watch:', error);
    }
}

// Update market watch table
function updateMarketWatchTable(marketData) {
    const tbody = document.querySelector('#marketWatchTable tbody');
    tbody.innerHTML = '';
    
    marketData.forEach(quote => {
        const row = document.createElement('tr');
        const change = quote.change || 0;
        const changePercent = quote.change_percent || 0;
        
        row.innerHTML = `
            <td><strong>${quote.symbol}</strong></td>
            <td>₹${formatNumber(quote.ltp || 0)}</td>
            <td class="${change >= 0 ? 'text-success' : 'text-danger'}">
                ${change >= 0 ? '+' : ''}₹${formatNumber(change)}
            </td>
            <td class="${changePercent >= 0 ? 'text-success' : 'text-danger'}">
                ${changePercent >= 0 ? '+' : ''}${formatNumber(changePercent)}%
            </td>
            <td>${formatNumber(quote.volume || 0)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="quickTrade('${quote.symbol}', 'buy')">
                    <i class="fas fa-arrow-up"></i> Buy
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="quickTrade('${quote.symbol}', 'sell')">
                    <i class="fas fa-arrow-down"></i> Sell
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Load recent orders
async function loadRecentOrders() {
    try {
        const endpoint = isDemoMode ? '/api/fake/orders' : '/api/orders/list';
        const response = await fetch(endpoint);
        const data = await response.json();
        
        if (response.ok) {
            updateRecentOrdersTable(data.slice(0, 5)); // Show last 5 orders
        }
    } catch (error) {
        console.error('Error loading recent orders:', error);
    }
}

// Update recent orders table
function updateRecentOrdersTable(orders) {
    const tbody = document.querySelector('#recentOrdersTable tbody');
    tbody.innerHTML = '';
    
    if (!orders || orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No recent orders</td></tr>';
        return;
    }
    
    orders.forEach(order => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${order.symbol || order.stock_code}</td>
            <td><span class="badge ${order.action === 'buy' ? 'bg-success' : 'bg-danger'}">${order.action}</span></td>
            <td><span class="badge ${getStatusBadgeClass(order.status)}">${order.status}</span></td>
            <td>${formatDateTime(order.timestamp || order.order_datetime)}</td>
        `;
        tbody.appendChild(row);
    });
}

// Show section
function showSection(sectionName, event = null) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    document.getElementById(`${sectionName}-section`).style.display = 'block';
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Only update active nav link if event is provided (clicked from UI)
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // Find and activate the correct nav link programmatically
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            if (link.getAttribute('onclick')?.includes(`'${sectionName}'`)) {
                link.classList.add('active');
            }
        });
    }
    
    currentSection = sectionName;
    
    // Load section-specific data
    loadSectionData(sectionName);
    
    // Auto-refresh disabled; manual only
}

// Load section-specific data
async function loadSectionData(sectionName) {
    // Load data without blocking the UI
    try {
        switch (sectionName) {
            case 'overview':
                await loadOverviewData();
                break;
            case 'portfolio':
                await loadPortfolioData();
                break;
            case 'orders':
                await loadOrdersData();
                await loadMarketStatus();
                break;
            case 'market':
                await loadMarketWatch();
                break;
            case 'ledger':
                await loadLedgerData();
                break;
            case 'historical':
                // Historical data is loaded on demand
                break;
            case 'jobs':
                await refreshJobs();
                updateActiveJobsBadge();
                break;
            default:
                console.warn(`Unknown section: ${sectionName}`);
        }
    } catch (error) {
        console.error(`Error loading ${sectionName} data:`, error);
        showAlert(`Error loading ${sectionName} data`, 'danger');
    }
}

// Load portfolio data
async function loadPortfolioData() {
    try {
        const endpoint = isDemoMode ? '/api/fake/holdings' : '/api/portfolio/holdings';
        console.log('Loading portfolio data from:', endpoint, 'isDemoMode:', isDemoMode);
        
        const response = await fetch(endpoint);
        const data = await response.json();
        
        console.log('Portfolio data response:', data);
        
        if (response.ok) {
            updateHoldingsTable(data);
        } else {
            console.error('Portfolio data request failed:', response.status, data);
            // Show error message in table
            const tbody = document.querySelector('#holdingsTable tbody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading portfolio data</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error loading portfolio data:', error);
        // Show error message in table
        const tbody = document.querySelector('#holdingsTable tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading portfolio data</td></tr>';
        }
    }
}

// Update holdings table
function updateHoldingsTable(holdings) {
    console.log('updateHoldingsTable called with:', holdings);
    
    const tbody = document.querySelector('#holdingsTable tbody');
    tbody.innerHTML = '';
    
    if (!holdings || holdings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No holdings found</td></tr>';
        return;
    }
    
    holdings.forEach(holding => {
        console.log('Processing holding:', holding);
        const row = document.createElement('tr');
        const pnl = holding.unrealized_pnl || holding.pnl || 0;
        const pnlPercent = holding.average_price ? ((pnl / (holding.average_price * holding.quantity)) * 100) : 0;
        
        row.innerHTML = `
            <td><strong>${holding.symbol || holding.stock_code}</strong></td>
            <td>${holding.quantity}</td>
            <td>₹${formatNumber(holding.average_price)}</td>
            <td>₹${formatNumber(holding.current_price)}</td>
            <td>₹${formatNumber(holding.market_value)}</td>
            <td class="${pnl >= 0 ? 'text-success' : 'text-danger'}">₹${formatNumber(pnl)}</td>
            <td class="${pnlPercent >= 0 ? 'text-success' : 'text-danger'}">${formatNumber(pnlPercent)}%</td>
        `;
        tbody.appendChild(row);
    });
}

// Load orders data
async function loadOrdersData() {
    try {
        // Show a simple loading indicator in the orders table instead of modal
        const tbody = document.querySelector('#ordersTable tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Loading orders...</td></tr>';
        }
        
        const response = await fetch('/api/fake/orders');
        console.log('Orders response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Orders response data:', result);
            
            if (result.status === 'success') {
                updateOrdersTable(result.data);
            } else {
                console.error('Orders API returned error:', result);
                showAlert('Failed to load orders: ' + (result.message || 'Unknown error'), 'danger');
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Failed to load orders</td></tr>';
                }
            }
        } else {
            const errorText = await response.text();
            console.error('Orders API error:', response.status, errorText);
            showAlert('Failed to load orders: ' + response.status, 'danger');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Failed to load orders</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error loading orders:', error);
        showAlert('Error loading orders: ' + error.message, 'danger');
        const tbody = document.querySelector('#ordersTable tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Error loading orders</td></tr>';
        }
    }
}

// Load market status
async function loadMarketStatus() {
    try {
        const response = await fetch('/api/market/status');
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                updateMarketStatus(result.data);
            }
        }
    } catch (error) {
        console.error('Error loading market status:', error);
    }
}

// Update market status display
function updateMarketStatus(status) {
    const statusElement = document.getElementById('marketStatus');
    if (statusElement) {
        const icon = status.is_open ? 'fas fa-check-circle text-success' : 'fas fa-times-circle text-danger';
        const text = status.is_open ? 'Open' : 'Closed';
        statusElement.innerHTML = `
            <span class="text-muted">
                <i class="${icon}"></i> Market: ${text} (${status.current_time})
            </span>
            <div class="text-muted small">Hours: ${status.market_start} - ${status.market_end} IST (Mon-Fri)</div>
        `;
    }
}

// Update orders table
function updateOrdersTable(orders) {
    try {
        console.log('Updating orders table with:', orders);
        const tbody = document.querySelector('#ordersTable tbody');
        if (!tbody) {
            console.error('Orders table tbody not found');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (!orders || orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No orders found</td></tr>';
            return;
        }
        
        orders.forEach(order => {
            try {
                const row = document.createElement('tr');
                const symbol = order.symbol || order.stock_code || 'Unknown';
                const action = order.action || 'Unknown';
                const quantity = order.quantity || 0;
                const price = order.price || 0;
                const status = order.status || 'Unknown';
                const timestamp = order.timestamp || order.order_datetime || '';
                const exchange = order.exchange || 'NSE';
                
                row.innerHTML = `
                    <td>${order.order_id || 'Unknown'}</td>
                    <td>${symbol}</td>
                    <td><span class="badge ${action === 'buy' ? 'bg-success' : 'bg-danger'}">${action}</span></td>
                    <td>${quantity}</td>
                    <td>₹${formatNumber(price)}</td>
                    <td><span class="badge ${getStatusBadgeClass(status)}">${status}</span></td>
                    <td>${formatDateTime(timestamp)}</td>
                    <td>
                        ${status === 'pending' ? `
                            <div class="btn-group" role="group">
                                <button class="btn btn-sm btn-outline-success" onclick="executeOrder('${order.order_id}', ${price})" title="Execute Order">
                                    <i class="fas fa-play"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="cancelOrder('${order.order_id}', '${exchange}')" title="Cancel Order">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        ` : ''}
                    </td>
                `;
                tbody.appendChild(row);
            } catch (orderError) {
                console.error('Error processing order:', orderError, order);
                // Add a row with error info
                const errorRow = document.createElement('tr');
                errorRow.innerHTML = `<td colspan="8" class="text-center text-danger">Error displaying order: ${order.order_id || 'Unknown'}</td>`;
                tbody.appendChild(errorRow);
            }
        });
    } catch (error) {
        console.error('Error updating orders table:', error);
        const tbody = document.querySelector('#ordersTable tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Error loading orders</td></tr>';
        }
    }
}

// Load ledger data
async function loadLedgerData() {
    try {
        const response = await fetch('/api/fake/ledger');
        const data = await response.json();
        
        if (response.ok) {
            updateLedgerTable(data);
        }
    } catch (error) {
        console.error('Error loading ledger data:', error);
    }
}

// Update ledger table
function updateLedgerTable(ledger) {
    const tbody = document.querySelector('#ledgerTable tbody');
    tbody.innerHTML = '';
    
    if (!ledger || ledger.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No ledger entries found</td></tr>';
        return;
    }
    
    ledger.forEach(entry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${entry.transaction_id}</td>
            <td><span class="badge bg-info">${entry.transaction_type}</span></td>
            <td>${entry.symbol}</td>
            <td><span class="badge ${entry.action === 'buy' ? 'bg-success' : 'bg-danger'}">${entry.action}</span></td>
            <td>${entry.quantity}</td>
            <td>₹${formatNumber(entry.price)}</td>
            <td>₹${formatNumber(entry.total_amount)}</td>
            <td><span class="badge ${getStatusBadgeClass(entry.status)}">${entry.status}</span></td>
            <td>${formatDateTime(entry.timestamp)}</td>
        `;
        tbody.appendChild(row);
    });
}

// Load GTT data
async function loadGTTData() {
    try {
        const response = await fetch('/api/gtt/orders');
        const data = await response.json();
        
        if (response.ok) {
            updateGTTTable(data);
        }
    } catch (error) {
        console.error('Error loading GTT data:', error);
    }
}

// Update GTT table
function updateGTTTable(gttOrders) {
    const tbody = document.querySelector('#gttTable tbody');
    tbody.innerHTML = '';
    
    if (!gttOrders || gttOrders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No GTT orders found</td></tr>';
        return;
    }
    
    gttOrders.forEach(order => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${order.gtt_order_id}</td>
            <td>${order.stock_code}</td>
            <td><span class="badge bg-info">${order.gtt_type}</span></td>
            <td>₹${formatNumber(order.trigger_price)}</td>
            <td>₹${formatNumber(order.limit_price)}</td>
            <td><span class="badge ${getStatusBadgeClass(order.status)}">${order.status}</span></td>
            <td>${formatDateTime(order.order_datetime)}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="cancelGTTOrder('${order.gtt_order_id}')">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Search quote
async function searchQuote() {
    const symbol = document.getElementById('symbolSearch').value.trim();
    if (!symbol) {
        showAlert('Please enter a symbol', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/market/quotes?symbol=${symbol}`);
        const data = await response.json();
        
        if (response.ok && data) {
            showQuoteDetails(data);
        } else {
            showAlert('Symbol not found', 'warning');
        }
    } catch (error) {
        console.error('Error searching quote:', error);
        showAlert('Error fetching quote', 'danger');
    }
}

// Show quote details
function showQuoteDetails(quote) {
    const resultsDiv = document.getElementById('quoteResults');
    const detailsDiv = document.getElementById('quoteDetails');
    
    detailsDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h5>${quote.symbol}</h5>
                <p class="text-muted">${quote.stock_name || ''}</p>
                <div class="row">
                    <div class="col-6">
                        <strong>LTP:</strong> ₹${formatNumber(quote.ltp)}
                    </div>
                    <div class="col-6">
                        <strong>Change:</strong> 
                        <span class="${quote.change >= 0 ? 'text-success' : 'text-danger'}">
                            ${quote.change >= 0 ? '+' : ''}₹${formatNumber(quote.change)}
                        </span>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-6">
                        <strong>Change %:</strong> 
                        <span class="${quote.change_percent >= 0 ? 'text-success' : 'text-danger'}">
                            ${quote.change_percent >= 0 ? '+' : ''}${formatNumber(quote.change_percent)}%
                        </span>
                    </div>
                    <div class="col-6">
                        <strong>Volume:</strong> ${formatNumber(quote.volume)}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="row">
                    <div class="col-6">
                        <strong>Open:</strong> ₹${formatNumber(quote.open)}
                    </div>
                    <div class="col-6">
                        <strong>High:</strong> ₹${formatNumber(quote.high)}
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-6">
                        <strong>Low:</strong> ₹${formatNumber(quote.low)}
                    </div>
                    <div class="col-6">
                        <strong>Previous Close:</strong> ₹${formatNumber(quote.previous_close)}
                    </div>
                </div>
                <div class="mt-3">
                    <button class="btn btn-success me-2" onclick="quickTrade('${quote.symbol}', 'buy')">
                        <i class="fas fa-arrow-up"></i> Buy
                    </button>
                    <button class="btn btn-danger" onclick="quickTrade('${quote.symbol}', 'sell')">
                        <i class="fas fa-arrow-down"></i> Sell
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultsDiv.style.display = 'block';
}

// Quick trade
function quickTrade(symbol, action) {
    document.getElementById('tradingSymbol').value = symbol;
    document.getElementById('tradingAction').value = action;
    showSection('trading');
}

// Initialize form handlers
function initializeFormHandlers() {
    // Trading form
    const tradingForm = document.getElementById('tradingForm');
    if (tradingForm) {
        tradingForm.addEventListener('submit', handleTradingFormSubmit);
    }
    
    // Form field listeners for preview
    const formFields = ['tradingSymbol', 'tradingQuantity', 'tradingPrice', 'tradingAction', 'tradingOrderType'];
    formFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', updateOrderPreview);
            field.addEventListener('change', updateOrderPreview);
        }
    });
    
    // Initialize trading symbol autocomplete
    initializeTradingSymbolAutocomplete();
    
    // Initialize watchlist search
    initializeWatchlistSearch();
    
    // Initialize historical symbol autocomplete
    initializeHistoricalSymbolAutocomplete();
    
    // Initialize historical date pickers with default values
    initializeHistoricalDatePickers();
    
    // Handle order type changes to disable/enable price field
    const orderTypeSelect = document.getElementById('tradingOrderType');
    const priceInput = document.getElementById('tradingPrice');
    if (orderTypeSelect && priceInput) {
        orderTypeSelect.addEventListener('change', function() {
            if (this.value === 'market') {
                priceInput.disabled = true;
                priceInput.placeholder = 'Market price (auto)';
                priceInput.value = '';
            } else {
                priceInput.disabled = false;
                priceInput.placeholder = 'Enter limit price';
            }
            updateOrderPreview();
        });
        
        // Initialize on page load
        if (orderTypeSelect.value === 'market') {
            priceInput.disabled = true;
            priceInput.placeholder = 'Market price (auto)';
            priceInput.value = '';
        }
    }
}

// Initialize trading symbol autocomplete
function initializeTradingSymbolAutocomplete() {
    const symbolInput = document.getElementById('tradingSymbol');
    const searchResults = document.getElementById('tradingSearchResults');
    let searchTimeout = null;
    
    if (!symbolInput) return;
    
    // Create search results container if it doesn't exist
    if (!searchResults) {
        const resultsDiv = document.createElement('div');
        resultsDiv.id = 'tradingSearchResults';
        resultsDiv.className = 'list-group position-absolute w-100';
        resultsDiv.style.display = 'none';
        resultsDiv.style.zIndex = '1000';
        resultsDiv.style.maxHeight = '300px';
        resultsDiv.style.overflowY = 'auto';
        resultsDiv.style.border = '1px solid #dee2e6';
        resultsDiv.style.borderRadius = '0.375rem';
        resultsDiv.style.backgroundColor = 'white';
        resultsDiv.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
        symbolInput.parentNode.style.position = 'relative';
        symbolInput.parentNode.appendChild(resultsDiv);
    }
    
    symbolInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Hide results if query is empty
        if (!query) {
            document.getElementById('tradingSearchResults').style.display = 'none';
            return;
        }
        
        // Debounce search
        searchTimeout = setTimeout(() => {
            searchInstrumentsForTrading(query);
        }, 300);
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(event) {
        if (!symbolInput.contains(event.target) && !document.getElementById('tradingSearchResults').contains(event.target)) {
            document.getElementById('tradingSearchResults').style.display = 'none';
        }
    });
}

// Search instruments for trading
async function searchInstrumentsForTrading(query) {
    try {
        const response = await fetch(`/api/instruments/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayTradingSearchResults(data.data);
        } else {
            console.error('Trading search failed:', data.message);
        }
    } catch (error) {
        console.error('Error searching instruments for trading:', error);
    }
}

// Display trading search results
function displayTradingSearchResults(instruments) {
    const searchResults = document.getElementById('tradingSearchResults');
    
    if (!instruments || instruments.length === 0) {
        searchResults.innerHTML = '<div class="list-group-item text-muted">No instruments found</div>';
        searchResults.style.display = 'block';
        return;
    }
    
    searchResults.innerHTML = instruments.map(instrument => `
        <div class="list-group-item list-group-item-action" 
             onclick="selectTradingInstrument(${JSON.stringify(instrument).replace(/"/g, '&quot;')})">
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center flex-grow-1">
                    <strong class="me-2">${instrument.short_name || instrument.stock_code}</strong>
                    <small class="text-muted me-2">${instrument.company_name || instrument.display_name || instrument.short_name}</small>
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.series ? `<span class="badge bg-info me-1">${instrument.series}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.expiry_date ? `<span class="badge bg-info me-1">${instrument.expiry_date}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.strike_price && instrument.strike_price > 0 ? `<span class="badge bg-warning me-1">₹${instrument.strike_price}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.option_type ? `<span class="badge bg-danger me-1">${instrument.option_type}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.lot_size ? `<span class="badge bg-dark me-1">Lot: ${instrument.lot_size}</span>` : ''}
                </div>
                <span class="badge bg-secondary">${instrument.exchange_code}</span>
            </div>
        </div>
    `).join('');
    
    searchResults.style.display = 'block';
}

// Select trading instrument
async function selectTradingInstrument(instrumentData) {
    // Parse the instrument data if it's a string
    const instrument = typeof instrumentData === 'string' ? JSON.parse(instrumentData) : instrumentData;
    
    const symbolInput = document.getElementById('tradingSymbol');
    const exchangeSelect = document.getElementById('tradingExchange');
    const priceInput = document.getElementById('tradingPrice');
    
    // Set symbol and exchange
    symbolInput.value = instrument.short_name || instrument.stock_code;
    exchangeSelect.value = instrument.exchange_code;
    
    // Store instrument data for product type determination
    symbolInput.setAttribute('data-instrument', JSON.stringify(instrument));
    
    // Set lot size for options and enforce quantity validation
    const quantityInput = document.getElementById('tradingQuantity');
    if (quantityInput) {
        const lotSize = instrument.lot_size || 1;
        quantityInput.setAttribute('min', lotSize);
        quantityInput.setAttribute('step', lotSize);
        quantityInput.placeholder = `Min: ${lotSize} (lot size)`;
        
        // Add validation message with detailed lot size info
        const quantityLabel = document.querySelector('label[for="tradingQuantity"]');
        if (quantityLabel) {
            if (instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') {
                const instrumentType = instrument.option_type ? 'Option' : 'Future';
                quantityLabel.innerHTML = `Quantity <small class="text-muted">(${instrumentType} - Lot: ${lotSize})</small>`;
            } else {
                quantityLabel.innerHTML = 'Quantity';
            }
        }
        
        // Show lot size info in an alert for options
        if (instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') {
            const instrumentType = instrument.option_type ? 'Option' : 'Future';
            const strikeInfo = instrument.option_type && instrument.strike_price ? ` Strike: ₹${instrument.strike_price}` : '';
            const expiryInfo = instrument.expiry_date ? ` Expiry: ${instrument.expiry_date}` : '';
            showAlert(`Selected: ${instrument.short_name} ${instrumentType}${strikeInfo}${expiryInfo} (Lot Size: ${lotSize})`, 'info');
        }
    }
    
    // Hide search results
    document.getElementById('tradingSearchResults').style.display = 'none';
    
    // Show loading state for price
    const symbolLabel = document.querySelector('label[for="tradingSymbol"]');
    if (symbolLabel) {
        symbolLabel.innerHTML = `Symbol <span class="text-muted">(Loading price...)</span>`;
    }
    
    // Build quote URL with proper parameters for derivatives
    let quoteUrl = `/api/market/quotes?symbol=${encodeURIComponent(instrument.short_name || instrument.stock_code)}&exchange=${encodeURIComponent(instrument.exchange_code)}`;
    
    // Add expiry date for NFO/BFO instruments (if available)
    if ((instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.expiry_date) {
        quoteUrl += `&expiry_date=${encodeURIComponent(instrument.expiry_date)}`;
    }
    
    // Add option type and strike price for NFO/BFO options to ensure we get the right instrument
    if ((instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.option_type) {
        quoteUrl += `&option_type=${encodeURIComponent(instrument.option_type)}`;
        if (instrument.strike_price && instrument.strike_price > 0) {
            quoteUrl += `&strike_price=${encodeURIComponent(instrument.strike_price)}`;
        }
    }
    
    // For NFO/BFO without expiry date, we'll try without it (may not work for all instruments)
    
    // Fetch current market price
    try {
        const response = await fetch(quoteUrl);
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            const quote = data.data;
            const price = quote.ltp || quote.close || 0;
            const change = quote.ltp_percent_change || 0;
            const changeClass = change >= 0 ? 'text-success' : 'text-danger';
            const changeSymbol = change >= 0 ? '+' : '';
            
            priceInput.value = price;
            
            // Update symbol label with price
            if (symbolLabel) {
                symbolLabel.innerHTML = `Symbol <span class="fw-bold text-primary">₹${formatNumber(price)}</span> <span class="${changeClass}">(${changeSymbol}${formatNumber(change)}%)</span>`;
            }
            
            showAlert(`Current price for ${instrument.short_name || instrument.stock_code}: ₹${formatNumber(price)}`, 'info');
        } else {
            priceInput.value = '';
            if (symbolLabel) {
                symbolLabel.innerHTML = `Symbol <span class="text-muted">(Price not available)</span>`;
            }
            showAlert(`Could not fetch price for ${instrument.short_name || instrument.stock_code}`, 'warning');
        }
    } catch (error) {
        console.error('Error fetching price:', error);
        priceInput.value = '';
        if (symbolLabel) {
            symbolLabel.innerHTML = `Symbol <span class="text-muted">(Error loading price)</span>`;
        }
        showAlert(`Error fetching price for ${instrument.short_name || instrument.stock_code}`, 'warning');
    }
    
    // Update order preview
    updateOrderPreview();
}

// Initialize historical symbol autocomplete
function initializeHistoricalSymbolAutocomplete() {
    const symbolInput = document.getElementById('historicalSymbol');
    const searchResults = document.getElementById('historicalSearchResults');
    let searchTimeout = null;
    
    if (!symbolInput) return;
    
    // Create search results container if it doesn't exist
    if (!searchResults) {
        const resultsDiv = document.createElement('div');
        resultsDiv.id = 'historicalSearchResults';
        resultsDiv.className = 'list-group position-absolute w-100';
        resultsDiv.style.display = 'none';
        resultsDiv.style.zIndex = '1000';
        resultsDiv.style.maxHeight = '300px';
        resultsDiv.style.overflowY = 'auto';
        symbolInput.parentNode.appendChild(resultsDiv);
    }
    
    symbolInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/api/instruments/search?query=${encodeURIComponent(query)}`);
                const data = await response.json();
                const instruments = data.data || data || [];
                
                displayHistoricalSearchResults(instruments);
            } catch (error) {
                console.error('Error searching instruments:', error);
            }
        }, 300);
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(e) {
        if (!symbolInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
}

// Display historical search results
function displayHistoricalSearchResults(instruments) {
    const searchResults = document.getElementById('historicalSearchResults');
    const symbolInput = document.getElementById('historicalSymbol');
    
    if (!searchResults || !symbolInput) return;
    
    searchResults.innerHTML = '';
    
    if (instruments.length === 0) {
        searchResults.innerHTML = '<div class="list-group-item text-muted">No instruments found</div>';
        searchResults.style.display = 'block';
        return;
    }
    
    instruments.forEach(instrument => {
        const item = document.createElement('div');
        item.className = 'list-group-item list-group-item-action';
        
        let displayText = `<strong>${instrument.short_name || instrument.stock_code}</strong>`;
        if (instrument.exchange_code) {
            displayText += ` <span class="badge bg-secondary">${instrument.exchange_code}</span>`;
        }
        if (instrument.expiry_date) {
            displayText += ` <span class="badge bg-info">${instrument.expiry_date}</span>`;
        }
        if (instrument.strike_price && instrument.strike_price > 0) {
            displayText += ` <span class="badge bg-warning">₹${instrument.strike_price}</span>`;
        }
        if (instrument.option_type) {
            displayText += ` <span class="badge bg-danger">${instrument.option_type}</span>`;
        }
        
        item.innerHTML = displayText;
        
        item.addEventListener('click', function() {
            // Create a comprehensive display string
            let displayValue = instrument.short_name || instrument.stock_code;
            
            if (instrument.exchange_code) {
                displayValue += ` (${instrument.exchange_code})`;
            }
            
            if (instrument.expiry_date) {
                displayValue += ` - ${instrument.expiry_date}`;
            }
            
            if (instrument.strike_price && instrument.strike_price > 0) {
                displayValue += ` @ ${instrument.strike_price}`;
            }
            
            if (instrument.option_type) {
                displayValue += ` ${instrument.option_type}`;
            }
            
            symbolInput.value = displayValue;
            symbolInput.setAttribute('data-instrument', JSON.stringify(instrument));
            searchResults.style.display = 'none';
        });
        
        searchResults.appendChild(item);
    });
    
    searchResults.style.display = 'block';
}

// Initialize historical date pickers with default values
function initializeHistoricalDatePickers() {
    const fromDateInput = document.getElementById('historicalFromDate');
    const toDateInput = document.getElementById('historicalToDate');
    
    if (!fromDateInput || !toDateInput) return;
    
    // Set default values: last 30 days
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    // Format dates as YYYY-MM-DD for date inputs
    const formatDate = (date) => {
        return date.toISOString().split('T')[0];
    };
    
    fromDateInput.value = formatDate(thirtyDaysAgo);
    toDateInput.value = formatDate(today);
    
    // Set max date to today for both inputs
    fromDateInput.max = formatDate(today);
    toDateInput.max = formatDate(today);
    
    // Validate date range when dates change
    const validateDates = () => {
        const fromDate = new Date(fromDateInput.value);
        const toDate = new Date(toDateInput.value);
        
        if (fromDate > toDate) {
            showAlert('From date cannot be after to date', 'warning');
            fromDateInput.value = formatDate(thirtyDaysAgo);
        }
        
        // Limit date range to maximum 1 year
        const maxDaysDiff = 365;
        const daysDiff = Math.ceil((toDate - fromDate) / (1000 * 60 * 60 * 24));
        
        if (daysDiff > maxDaysDiff) {
            showAlert(`Date range cannot exceed ${maxDaysDiff} days`, 'warning');
            fromDateInput.value = formatDate(new Date(toDate.getTime() - (maxDaysDiff * 24 * 60 * 60 * 1000)));
        }
    };
    
    fromDateInput.addEventListener('change', validateDates);
    toDateInput.addEventListener('change', validateDates);
}

// Initialize watchlist search functionality
function initializeWatchlistSearch() {
    const searchInput = document.getElementById('watchlistSearchInput');
    const searchResults = document.getElementById('watchlistSearchResults');
    let searchTimeout = null;
    
    if (!searchInput) return;
    
    // Ensure search results container exists and has proper styling
    if (searchResults) {
        searchResults.style.maxHeight = '400px';
        searchResults.style.overflowY = 'auto';
    }
    
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Hide results if query is empty
        if (!query) {
            searchResults.style.display = 'none';
            return;
        }
        
        // Debounce search
        searchTimeout = setTimeout(() => {
            searchInstrumentsForWatchlist(query);
        }, 300);
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
            searchResults.style.display = 'none';
        }
    });
}



// Search instruments
async function searchInstruments(query) {
    try {
        const response = await fetch(`/api/instruments/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displaySearchResults(data.data);
        } else {
            console.error('Search failed:', data.message);
        }
    } catch (error) {
        console.error('Error searching instruments:', error);
    }
}

async function searchInstrumentsForWatchlist(query) {
    try {
        const response = await fetch(`/api/instruments/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayWatchlistSearchResults(data.data);
        } else {
            console.error('Watchlist search failed:', data.message);
        }
    } catch (error) {
        console.error('Error searching instruments for watchlist:', error);
    }
}

// Display search results
function displaySearchResults(instruments) {
    const searchResults = document.getElementById('searchResults');
    
    if (!instruments || instruments.length === 0) {
        searchResults.innerHTML = '<div class="list-group-item text-muted">No instruments found</div>';
        searchResults.style.display = 'block';
        return;
    }
    
    let html = '';
    instruments.forEach(instrument => {
        const exchangeColor = getExchangeColor(instrument.exchange_code);
        html += `
            <div class="list-group-item list-group-item-action" 
                 onclick="selectInstrument('${instrument.short_name}', '${instrument.exchange_code}', '${instrument.token}')"
                 style="cursor: pointer;">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${instrument.short_name}</strong>
                        <span class="badge bg-${exchangeColor} ms-2">${instrument.exchange_code}</span>
                        <br>
                        <small class="text-muted">${instrument.company_name}</small>
                    </div>
                    <div class="text-end">
                        <small class="text-muted">Token: ${instrument.token}</small><br>
                        <small class="text-muted">Lot: ${instrument.lot_size}</small>
                    </div>
                </div>
            </div>
        `;
    });
    
    searchResults.innerHTML = html;
    searchResults.style.display = 'block';
}

function displayWatchlistSearchResults(instruments) {
    const searchResults = document.getElementById('watchlistSearchResults');
    
    if (!instruments || instruments.length === 0) {
        searchResults.innerHTML = '<div class="list-group-item text-muted">No instruments found</div>';
        searchResults.style.display = 'block';
        return;
    }
    
    let html = '';
    instruments.forEach(instrument => {
        const exchangeColor = getExchangeColor(instrument.exchange_code);
        const isAlreadyInWatchlist = watchlistSymbols.some(s => s.symbol === instrument.short_name && s.exchange === instrument.exchange_code);
        
        html += `
            <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" 
                 style="cursor: pointer;">
                <div class="flex-grow-1 d-flex align-items-center" onclick="selectInstrumentForWatchlist('${instrument.short_name}', '${instrument.exchange_code}', '${instrument.company_name}')">
                    <strong class="me-2">${instrument.short_name}</strong>
                    <small class="text-muted me-2">${instrument.company_name}</small>
                    <span class="badge bg-${exchangeColor} me-1">${instrument.exchange_code}</span>
                    ${isAlreadyInWatchlist ? '<span class="badge bg-secondary me-1">Added</span>' : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.series ? `<span class="badge bg-info me-1">${instrument.series}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.expiry_date ? `<span class="badge bg-info me-1">${instrument.expiry_date}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.strike_price && instrument.strike_price > 0 ? `<span class="badge bg-warning me-1">₹${instrument.strike_price}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.option_type ? `<span class="badge bg-danger me-1">${instrument.option_type}</span>` : ''}
                    ${(instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.lot_size ? `<span class="badge bg-dark me-1">Lot: ${instrument.lot_size}</span>` : ''}
                </div>
                ${!isAlreadyInWatchlist ? `
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="addToWatchlist('${instrument.short_name}', '${instrument.exchange_code}', ${JSON.stringify(instrument).replace(/"/g, '&quot;')})"
                            title="Add to watchlist">
                        <i class="fas fa-plus"></i>
                    </button>
                ` : `
                    <button class="btn btn-sm btn-outline-secondary" disabled title="Already in watchlist">
                        <i class="fas fa-check"></i>
                    </button>
                `}
            </div>
        `;
    });
    
    searchResults.innerHTML = html;
    searchResults.style.display = 'block';
}

// Get exchange color for badges
function getExchangeColor(exchange) {
    switch (exchange) {
        case 'NSE': return 'primary';
        case 'BSE': return 'success';
        case 'NFO': return 'warning';
        case 'BFO': return 'info';
        default: return 'secondary';
    }
}

// Select instrument from search results
function selectInstrument(shortName, exchange, token) {
    // Hide search results
    document.getElementById('searchResults').style.display = 'none';
    
    // Clear search input
    document.getElementById('stockSearchInput').value = `${shortName} (${exchange})`;
    
    // Show selected instrument info
    showAlert(`Selected: ${shortName} (${exchange}) - Token: ${token}`, 'success');
    
    // You can add more functionality here like:
    // - Adding to watchlist
    // - Opening order form
    // - Showing detailed info
    console.log('Selected instrument:', { shortName, exchange, token });
}

// Select instrument for watchlist
function selectInstrumentForWatchlist(shortName, exchange, companyName) {
    const searchInput = document.getElementById('watchlistSearchInput');
    const searchResults = document.getElementById('watchlistSearchResults');
    
    // Set the input value
    searchInput.value = `${shortName} (${exchange})`;
    
    // Hide search results
    searchResults.style.display = 'none';
    
    console.log('Selected instrument for watchlist:', { shortName, exchange, companyName });
}

// Add to watchlist directly
async function addToWatchlist(symbol, exchange, instrumentData = null) {
    try {
        // Parse instrument data if it's a string
        let instrument = null;
        if (typeof instrumentData === 'string') {
            try {
                instrument = JSON.parse(instrumentData);
            } catch (e) {
                console.warn('Failed to parse instrument data:', e);
            }
        } else {
            instrument = instrumentData;
        }
        
        // Check if already in watchlist
        if (watchlistSymbols.some(s => s.symbol === symbol && s.exchange === exchange)) {
            showAlert(`${symbol} is already in your watchlist`, 'info');
            return;
        }
        
        // Add to server
        const response = await fetch('/api/market-watch/symbols', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbol, exchange })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Add to local array with full instrument data
            const watchlistItem = { symbol, exchange };
            if (instrument) {
                watchlistItem.instrumentData = instrument;
                console.log('Added to watchlist with instrument data:', instrument);
            }
            watchlistSymbols.push(watchlistItem);
            
            // Clear search input
            document.getElementById('watchlistSearchInput').value = '';
            document.getElementById('watchlistSearchResults').style.display = 'none';
            
            // Refresh market watch
            await updateMarketWatchTable();
            
            // Show detailed success message for options
            let successMessage = `Added ${symbol} to watchlist`;
            if (instrument && instrument.option_type && instrument.strike_price) {
                successMessage += ` (${instrument.option_type} ₹${instrument.strike_price})`;
            } else if (instrument && instrument.expiry_date) {
                successMessage += ` (Future ${instrument.expiry_date})`;
            }
            
            showAlert(successMessage, 'success');
        } else {
            showAlert('Failed to add symbol', 'error');
        }
    } catch (error) {
        console.error('Error adding to watchlist:', error);
        showAlert('Failed to add symbol', 'error');
    }
}

// Handle trading form submit
async function handleTradingFormSubmit(event) {
    event.preventDefault();
    
    const quantity = parseInt(document.getElementById('tradingQuantity').value);
    const quantityInput = document.getElementById('tradingQuantity');
    const lotSize = parseInt(quantityInput.getAttribute('min')) || 1;
    
    // Validate lot size for options
    if (quantity % lotSize !== 0) {
        showAlert(`Quantity must be a multiple of lot size (${lotSize})`, 'warning');
        return;
    }
    
    // Determine product type based on selected instrument
    const exchange = document.getElementById('tradingExchange').value;
    let product = 'cash'; // Default for equity
    
    if (exchange === 'NFO' || exchange === 'BFO') {
        // Check if we have instrument data stored (from selection)
        const symbolInput = document.getElementById('tradingSymbol');
        const instrumentData = symbolInput.getAttribute('data-instrument');
        if (instrumentData) {
            try {
                const instrument = JSON.parse(instrumentData);
                if (instrument.option_type && (instrument.option_type === 'CE' || instrument.option_type === 'PE')) {
                    product = 'options';
                } else {
                    product = 'futures';
                }
            } catch (e) {
                // Fallback to futures if parsing fails
                product = 'futures';
            }
        } else {
            product = 'futures'; // Default for derivatives
        }
    }
    
    const orderType = document.getElementById('tradingOrderType').value;
    
    const formData = {
        stock_code: document.getElementById('tradingSymbol').value,
        exchange_code: document.getElementById('tradingExchange').value,
        product: product,
        action: document.getElementById('tradingAction').value,
        quantity: quantity,
        order_type: orderType,
        price: orderType === 'market' ? 0 : (parseFloat(document.getElementById('tradingPrice').value) || 0),
        validity: 'day'
    };
    
    console.log('Placing order with data:', formData);
    
    try {
        const endpoint = isDemoMode ? '/api/fake/orders' : '/api/orders/place';
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const result = await response.json();
        console.log('Order placement response:', result);
        
        if (response.ok) {
            // Handle different response structures
            let orderId = 'N/A';
            if (result.order_id) {
                orderId = result.order_id;
            } else if (result.order_data && result.order_data.order_id) {
                orderId = result.order_data.order_id;
            } else if (result.data && result.data.order_id) {
                orderId = result.data.order_id;
            }
            
            const message = result.message || 'Order placed successfully!';
            showAlert(`${message} Order ID: ${orderId}`, 'success');
            tradingForm.reset();
            
            // Refresh data without blocking the UI
            if (currentSection === 'orders') {
                // For orders section, just reload orders data without modal
                loadOrdersData();
                loadMarketStatus();
            } else {
                // For other sections, refresh without loading modal
                refreshCurrentSectionData();
            }
        } else {
            const errorMessage = result.detail || result.message || 'Unknown error occurred';
            showAlert(`Order failed: ${errorMessage}`, 'danger');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        if (error.name === 'AbortError') {
            showAlert('Order placement timed out. Please try again.', 'warning');
        } else {
            showAlert('Error placing order: ' + error.message, 'danger');
        }
    }
}



// Refresh current section data without showing loading modal
async function refreshCurrentSectionData() {
    try {
        switch (currentSection) {
            case 'overview':
                await loadOverviewData();
                break;
            case 'portfolio':
                await loadPortfolioData();
                break;
            case 'market':
                await loadMarketWatch();
                break;
            case 'ledger':
                await loadLedgerData();
                break;
            default:
                // For other sections, do nothing or use default behavior
                break;
        }
    } catch (error) {
        console.error(`Error refreshing ${currentSection} data:`, error);
        // Don't show alerts for background refreshes to avoid spam
    }
}

// Update order preview
function updateOrderPreview() {
    const symbol = document.getElementById('tradingSymbol').value;
    const exchange = document.getElementById('tradingExchange').value;
    const quantity = document.getElementById('tradingQuantity').value;
    const price = document.getElementById('tradingPrice').value;
    const action = document.getElementById('tradingAction').value;
    const orderType = document.getElementById('tradingOrderType').value;

    
    const previewDiv = document.getElementById('orderPreview');
    
    if (symbol && quantity) {
        const totalAmount = quantity * (price || 0);
        const quantityInput = document.getElementById('tradingQuantity');
        const lotSize = quantityInput ? parseInt(quantityInput.getAttribute('min')) || 1 : 1;
        const exchange = document.getElementById('tradingExchange').value;
        
        // Check if this is a derivative
        const isDerivative = exchange === 'NFO' || exchange === 'BFO';
        const lotInfo = isDerivative ? ` (Lot Size: ${lotSize})` : '';
        
        // Determine product type for display
        const symbolInput = document.getElementById('tradingSymbol');
        const instrumentData = symbolInput.getAttribute('data-instrument');
        let productDisplay = 'Cash';
        
        if (instrumentData) {
            try {
                const instrument = JSON.parse(instrumentData);
                if (instrument.option_type && (instrument.option_type === 'CE' || instrument.option_type === 'PE')) {
                    productDisplay = 'Options';
                } else if (exchange === 'NFO' || exchange === 'BFO') {
                    productDisplay = 'Futures';
                }
            } catch (e) {
                // Keep default
            }
        }
        
        previewDiv.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6>Order Preview</h6>
                    <p><strong>Symbol:</strong> ${symbol}</p>
                    <p><strong>Action:</strong> <span class="badge ${action === 'buy' ? 'bg-success' : 'bg-danger'}">${action.toUpperCase()}</span></p>
                    <p><strong>Product:</strong> ${productDisplay}</p>
                    <p><strong>Quantity:</strong> ${quantity}${lotInfo}</p>
                    <p><strong>Order Type:</strong> ${orderType}</p>

                    ${orderType === 'market' ? 
                        `<p><strong>Price:</strong> <span class="text-muted">Market price (current rate)</span></p>` : 
                        (price ? `<p><strong>Price:</strong> ₹${formatNumber(price)}</p>` : `<p><strong>Price:</strong> <span class="text-warning">Enter limit price</span></p>`)
                    }
                    ${orderType === 'limit' && totalAmount > 0 ? `<p><strong>Total Amount:</strong> ₹${formatNumber(totalAmount)}</p>` : ''}
                    ${orderType === 'market' ? `<p><strong>Total Amount:</strong> <span class="text-muted">Will be calculated at market price</span></p>` : ''}
                    <div class="alert alert-info">
                        <small><i class="fas fa-info-circle"></i> This is a ${isDemoMode ? 'demo' : 'real'} order</small>
                    </div>
                </div>
            </div>
        `;
    } else {
        previewDiv.innerHTML = '<p class="text-muted">Fill the form to see order preview</p>';
    }
}

// Load historical data using background jobs
async function loadHistoricalData() {
    const symbolInput = document.getElementById('historicalSymbol');
    const symbol = symbolInput.value.trim();
    const interval = document.getElementById('historicalInterval').value;
    const fromDate = document.getElementById('historicalFromDate').value;
    const toDate = document.getElementById('historicalToDate').value;
    
    if (!symbol || symbol.trim() === '') {
        showAlert('Please enter a symbol', 'warning');
        return;
    }
    
    if (!fromDate || !toDate) {
        showAlert('Please select both from and to dates', 'warning');
        return;
    }
    
    if (new Date(fromDate) > new Date(toDate)) {
        showAlert('From date cannot be after to date', 'warning');
        return;
    }
    
    // Clean the symbol from display formatting if needed
    let cleanSymbol = symbol.trim();
    if (cleanSymbol.includes('(')) {
        cleanSymbol = cleanSymbol.split('(')[0].trim();
    }
    
    // Get instrument data if available
    const instrumentData = symbolInput.getAttribute('data-instrument');
    let exchange = 'NSE';
    let productType = 'cash';
    let expiryDate = '';
    let strikePrice = '';
    let right = '';
    
    if (instrumentData) {
        try {
            const instrument = JSON.parse(instrumentData);
            exchange = instrument.exchange_code || 'NSE';
            
            if (exchange === 'NFO' || exchange === 'BFO') {
                if (instrument.option_type && (instrument.option_type === 'CE' || instrument.option_type === 'PE')) {
                    productType = 'options';
                } else {
                    productType = 'futures';
                }
            } else {
                productType = 'cash';
            }
            
            expiryDate = instrument.expiry_date || '';
            strikePrice = instrument.strike_price || '';
            
            if (instrument.option_type === 'CE') {
                right = 'call';
            } else if (instrument.option_type === 'PE') {
                right = 'put';
            } else {
                right = 'others';
            }
        } catch (e) {
            console.error('Error parsing instrument data:', e);
        }
    }
    
    // Use the actual stock code
    let actualSymbol = cleanSymbol;
    if (instrumentData) {
        try {
            const instrument = JSON.parse(instrumentData);
            actualSymbol = instrument.stock_code || instrument.short_name || cleanSymbol;
        } catch (e) {
            actualSymbol = cleanSymbol;
        }
    }
    
    if (!actualSymbol || actualSymbol === 'undefined' || actualSymbol.trim() === '') {
        showAlert('Invalid symbol. Please select from the dropdown.', 'warning');
        return;
    }
    
    try {
        // Disable load button
        const loadBtn = document.getElementById('loadHistoricalBtn');
        const originalText = loadBtn.innerHTML;
        loadBtn.disabled = true;
        loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Creating Background Job...';
        
        // Convert dates to ISO format for API
        const fromDateTime = new Date(fromDate + 'T00:00:00.000Z').toISOString();
        const toDateTime = new Date(toDate + 'T23:59:59.999Z').toISOString();
        
        // Build job parameters
        const jobParams = {
            symbol: actualSymbol,
            exchange: exchange,
            interval: interval,
            from_date: fromDateTime,
            to_date: toDateTime
        };
        
        // Add derivative-specific parameters
        if (exchange === 'NFO' || exchange === 'BFO') {
            if (productType) jobParams.product_type = productType;
            if (expiryDate) jobParams.expiry_date = expiryDate;
            if (strikePrice && strikePrice > 0) jobParams.strike_price = strikePrice;
            if (right) jobParams.right = right;
        }
        
        // Create background job
        const response = await fetch('/api/jobs/historical', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobParams)
        });
        
        const result = await response.json();
        
        // Debug logging
        console.log('Job creation response:', {
            status: response.status,
            ok: response.ok,
            result: result
        });
        
        // Restore button
        loadBtn.disabled = false;
        loadBtn.innerHTML = originalText;
        
        if (response.ok && result.status === 'success') {
            showAlert(`🚀 Background job created for ${actualSymbol} (ID: ${result.job_id}). Track progress in Background Jobs section.`, 'info');
            
            // Switch to jobs section to show progress
            setTimeout(() => {
                showSection('jobs');
                refreshJobs();
            }, 1000);
            
        } else {
            console.error('Job creation failed:', {
                responseStatus: response.status,
                responseOk: response.ok,
                result: result
            });
            showAlert(`Error creating background job: ${result.message || result.detail || 'Unknown error'}`, 'danger');
        }
        
    } catch (error) {
        console.error('Error creating background job:', error);
        const loadBtn = document.getElementById('loadHistoricalBtn');
        if (loadBtn.disabled) {
            loadBtn.disabled = false;
            loadBtn.innerHTML = '<i class="fas fa-chart-line me-1"></i>Load Data';
        }
        showAlert('Error creating background job', 'danger');
    }
}

// Progress bar helper functions
function shouldShowProgress(interval, daysDiff) {
    // Estimate if chunking might be needed based on interval and days
    const estimates = {
        '1second': daysDiff > 0.01,  // > ~16 minutes
        '1minute': daysDiff > 1,     // > 1 day
        '5minute': daysDiff > 7,     // > 1 week
        '30minute': daysDiff > 30,   // > 1 month
        '1day': false               // Daily rarely needs chunking
    };
    return estimates[interval] || false;
}

function showHistoricalProgress(show) {
    const progressDiv = document.getElementById('historicalProgress');
    if (progressDiv) {
        progressDiv.style.display = show ? 'block' : 'none';
    }
}

function updateProgress(percentage, text, details) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressDetails = document.getElementById('progressDetails');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (progressText) {
        progressText.textContent = text;
    }
    
    if (progressDetails) {
        progressDetails.textContent = details;
    }
}

// Global variables for pagination
let currentHistoricalData = [];
let currentPage = 1;
const rowsPerPage = 500; // Show 500 rows per page max

// Update historical data with pagination
function updateHistoricalData(data) {
    currentHistoricalData = data;
    currentPage = 1;
    
    // Show pagination info
    const totalRows = data.length;
    const totalPages = Math.ceil(totalRows / rowsPerPage);
    
    // Update pagination info
    updatePaginationInfo(totalRows, totalPages);
    
    // Update table with first page
    updateHistoricalTable(currentPage);
    
    // Update chart with downsampled data for performance
    updatePriceChart(downsampleDataForChart(data));
}

function updateHistoricalTable(page) {
    const tbody = document.querySelector('#historicalTable tbody');
    tbody.innerHTML = '';
    
    const startIndex = (page - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, currentHistoricalData.length);
    const pageData = currentHistoricalData.slice(startIndex, endIndex);
    
    if (pageData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No data available</td></tr>';
        return;
    }
    
    pageData.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDateTime(record.datetime)}</td>
            <td>₹${formatNumber(record.open)}</td>
            <td>₹${formatNumber(record.high)}</td>
            <td>₹${formatNumber(record.low)}</td>
            <td>₹${formatNumber(record.close)}</td>
            <td>${formatNumber(record.volume)}</td>
        `;
        tbody.appendChild(row);
    });
}

function updatePaginationInfo(totalRows, totalPages) {
    // Find or create pagination container
    let paginationContainer = document.getElementById('historicalPagination');
    if (!paginationContainer) {
        paginationContainer = document.createElement('div');
        paginationContainer.id = 'historicalPagination';
        paginationContainer.className = 'mt-3 d-flex justify-content-between align-items-center';
        
        // Insert after the table
        const tableContainer = document.querySelector('#historicalTable').closest('.table-responsive');
        tableContainer.parentNode.insertBefore(paginationContainer, tableContainer.nextSibling);
    }
    
    // Create pagination HTML
    paginationContainer.innerHTML = `
        <div>
            <small class="text-muted">
                Showing ${((currentPage - 1) * rowsPerPage) + 1} to ${Math.min(currentPage * rowsPerPage, totalRows)} 
                of ${totalRows.toLocaleString()} records
            </small>
        </div>
        <div>
            <nav>
                <ul class="pagination pagination-sm mb-0">
                    <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="changeHistoricalPage(${currentPage - 1})">Previous</a>
                    </li>
                    <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="changeHistoricalPage(1)">First</a>
                    </li>
                    <li class="page-item active">
                        <span class="page-link">${currentPage} of ${totalPages}</span>
                    </li>
                    <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="changeHistoricalPage(${totalPages})">Last</a>
                    </li>
                    <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                        <a class="page-link" href="#" onclick="changeHistoricalPage(${currentPage + 1})">Next</a>
                    </li>
                </ul>
            </nav>
        </div>
    `;
    
    // Show performance warning for large datasets
    if (totalRows > 10000) {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'alert alert-warning mt-2';
        warningDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Large Dataset:</strong> ${totalRows.toLocaleString()} candles loaded. 
            Chart shows downsampled data for performance. Use pagination to view table data.
        `;
        paginationContainer.appendChild(warningDiv);
    }
}

function changeHistoricalPage(page) {
    const totalPages = Math.ceil(currentHistoricalData.length / rowsPerPage);
    
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    updateHistoricalTable(currentPage);
    updatePaginationInfo(currentHistoricalData.length, totalPages);
}

function downsampleDataForChart(data) {
    // For performance, limit chart to max 2000 points
    const maxPoints = 2000;
    
    if (data.length <= maxPoints) {
        return data;
    }
    
    // Take every nth point to downsample
    const step = Math.ceil(data.length / maxPoints);
    const downsampled = [];
    
    for (let i = 0; i < data.length; i += step) {
        downsampled.push(data[i]);
    }
    
    console.log(`Downsampled chart data from ${data.length} to ${downsampled.length} points for performance`);
    return downsampled;
}

// Update price chart
function updatePriceChart(data) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (priceChart) {
        priceChart.destroy();
    }
    
    // Use different date formatting based on interval - show time for intraday data
    const interval = document.getElementById('historicalInterval')?.value || '1day';
    const isIntraday = ['1second', '1minute', '5minute', '30minute'].includes(interval);
    
    const labels = data.map(record => {
        if (isIntraday) {
            // For intraday data, show time prominently
            const date = new Date(record.datetime);
            return date.toLocaleTimeString('en-IN', { 
                hour: '2-digit', 
                minute: '2-digit',
                day: '2-digit',
                month: 'short'
            });
        } else {
            // For daily data, show date only
            return formatDate(record.datetime);
        }
    });
    const prices = data.map(record => record.close);
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Close Price',
                data: prices,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// Export functions
async function exportPortfolio() {
    try {
        const response = await fetch('/api/fake/export/holdings');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'portfolio_holdings.csv';
            a.click();
        }
    } catch (error) {
        console.error('Error exporting portfolio:', error);
        showAlert('Error exporting portfolio', 'danger');
    }
}

async function exportOrders() {
    try {
        const response = await fetch('/api/fake/export/orders');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'orders.csv';
            a.click();
        }
    } catch (error) {
        console.error('Error exporting orders:', error);
        showAlert('Error exporting orders', 'danger');
    }
}

async function exportLedger() {
    try {
        const response = await fetch('/api/fake/export/ledger');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ledger.csv';
            a.click();
        }
    } catch (error) {
        console.error('Error exporting ledger:', error);
        showAlert('Error exporting ledger', 'danger');
    }
}

async function exportHistoricalData() {
    // Check if we have data in the table
    const table = document.querySelector('#historicalTable tbody');
    if (!table || table.children.length === 0) {
        showAlert('No historical data to export. Please load data first.', 'warning');
        return;
    }
    
    try {
        // Get data from the table
        const rows = Array.from(table.children);
        const symbol = document.getElementById('historicalSymbol').value.trim() || 'Unknown';
        const interval = document.getElementById('historicalInterval').value;
        const fromDate = document.getElementById('historicalFromDate').value;
        const toDate = document.getElementById('historicalToDate').value;
        
        // Create CSV content
        let csvContent = 'Date Time,Open,High,Low,Close,Volume\n';
        
        rows.forEach(row => {
            const cells = Array.from(row.children);
            const rowData = cells.map(cell => {
                // Remove currency symbols and format numbers properly
                let text = cell.textContent.trim();
                if (text.startsWith('₹')) {
                    text = text.substring(1).replace(/,/g, '');
                }
                return text;
            });
            csvContent += rowData.join(',') + '\n';
        });
        
        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Create filename with symbol, interval, and date range
        const filename = `${symbol}_${interval}_${fromDate}_to_${toDate}_historical_data.csv`;
        a.download = filename;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showAlert(`✅ Historical data exported as ${filename}`, 'success');
        
    } catch (error) {
        console.error('Error exporting historical data:', error);
        showAlert('Error exporting historical data', 'danger');
    }
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

// WebSocket connection for real-time job updates
let jobWebSocket = null;

function initializeJobWebSocket() {
    if (jobWebSocket && jobWebSocket.readyState === WebSocket.OPEN) {
        return; // Already connected
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/jobs`;
    
    jobWebSocket = new WebSocket(wsUrl);
    
    jobWebSocket.onopen = function(event) {
        console.log('Connected to job WebSocket');
    };
    
    jobWebSocket.onmessage = function(event) {
        try {
            const message = JSON.parse(event.data);
            if (message.type === 'job_progress') {
                handleJobProgressUpdate(message.job);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    jobWebSocket.onclose = function(event) {
        console.log('Job WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(initializeJobWebSocket, 5000);
    };
    
    jobWebSocket.onerror = function(error) {
        console.error('Job WebSocket error:', error);
    };
}

// WebSocket for live market ticks -> updates market watch table in near-real-time
function initializeMarketWebSocket() {
    if (marketWebSocket && marketWebSocket.readyState === WebSocket.OPEN) {
        return;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/market`;
    marketWebSocket = new WebSocket(wsUrl);
    marketWebSocket.onopen = function() {
        console.log('Connected to market WebSocket');
    };
    marketWebSocket.onmessage = function(event) {
        try {
            const message = JSON.parse(event.data);
            if (message.type === 'ticks') {
                handleIncomingTicks(message.data);
            }
        } catch (e) {
            console.error('Market WS parse error', e);
        }
    };
    marketWebSocket.onclose = function() {
        console.log('Market WebSocket disconnected, retrying in 5s...');
        setTimeout(initializeMarketWebSocket, 5000);
    };
    marketWebSocket.onerror = function(err) {
        console.error('Market WebSocket error:', err);
    };
}

// Lightweight merge of incoming ticks into the table if symbol is tracked
function handleIncomingTicks(ticks) {
    try {
        // ticks shape differs by subscription; normalize simple equity quote where possible
        // If tick has 'symbol' like '4.1!3499', we may map via instruments DB if needed.
        // For now, update by stock_name or stock_code where available.
        const tbody = document.querySelector('#marketWatchTable tbody');
        if (!tbody) return;
        if (!Array.isArray(ticks)) {
            ticks = [ticks];
        }
        for (const t of ticks) {
            const stockCode = t.ui_symbol || t.stock_code || t.stock_name || t.symbol || '';
            if (!stockCode) continue;
            // Find row by first cell text match (symbol column)
            const rows = tbody.querySelectorAll('tr');
            for (const row of rows) {
                const symCell = row.querySelector('td:nth-child(1)');
                if (!symCell) continue;
                const symText = symCell.innerText.trim();
                if (!symText) continue;
                // Match exact, or fallback to contains for longer stock names
                const target = stockCode.toString().toUpperCase();
                const current = symText.toUpperCase();
                if (current === target || current.includes(target) || target.includes(current)) {
                    // Update LTP, Change, Change%, Volume
                    const ltp = parseFloat(t.last ?? t.close ?? t.ltp ?? 0);
                    const change = parseFloat(t.change ?? 0);
                    const changePct = parseFloat(t.ltp_percent_change ?? t.change_percent ?? 0);
                    const volume = parseInt(t.volume ?? t.ttq ?? t.total_quantity_traded ?? 0);
                    const ltpCell = row.querySelector('td:nth-child(2)');
                    const chCell = row.querySelector('td:nth-child(3)');
                    const chPctCell = row.querySelector('td:nth-child(4)');
                    const volCell = row.querySelector('td:nth-child(5)');
                    if (ltpCell) ltpCell.textContent = `₹${isFinite(ltp) ? ltp.toFixed(2) : '0.00'}`;
                    if (chCell) {
                        chCell.textContent = isFinite(change) ? change.toFixed(2) : '0.00';
                        chCell.className = (isFinite(change) && change >= 0) ? 'text-success' : 'text-danger';
                    }
                    if (chPctCell) {
                        chPctCell.textContent = isFinite(changePct) ? `${changePct.toFixed(2)}%` : '0.00%';
                        chPctCell.className = (isFinite(changePct) && changePct >= 0) ? 'text-success' : 'text-danger';
                    }
                    if (volCell) volCell.textContent = `${Math.round((volume || 0)/1000)}K`;
                }
            }
        }
    } catch (e) {
        console.error('Failed to merge ticks into table:', e);
    }
}

// Buttons: start/stop live streaming by calling backend endpoints
async function startLiveStreaming() {
    try {
        // Prefer watchlist-based server endpoint (resolves tokens)
        const resp = await fetch('/api/streaming/start-watchlist', { method: 'POST' });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            showAlert(`Failed to start live data: ${err.detail || resp.statusText}`, 'danger');
            return;
        }
        const data = await resp.json();
        showAlert(`Live data started (${data.count} instruments)`, 'success');
        // Ensure market WebSocket connected
        initializeMarketWebSocket();
    } catch (e) {
        console.error('startLiveStreaming error', e);
        showAlert('Error starting live data', 'danger');
    }
}

async function stopLiveStreaming() {
    try {
        const resp = await fetch('/api/streaming/stop', { method: 'POST' });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            showAlert(`Failed to stop live data: ${err.detail || resp.statusText}`, 'danger');
            return;
        }
        showAlert('Live data stopped', 'info');
    } catch (e) {
        console.error('stopLiveStreaming error', e);
        showAlert('Error stopping live data', 'danger');
    }
}

// Expose functions globally for inline onclick handlers in HTML
window.startLiveStreaming = startLiveStreaming;
window.stopLiveStreaming = stopLiveStreaming;

function handleJobProgressUpdate(job) {
    console.log('Job progress update:', job);
    
    // Update job in table if visible (do this first)
    updateJobInTable(job);
    
    // Update counters only if jobs section is visible
    if (document.getElementById('jobs-section').style.display !== 'none') {
        // Don't call updateJobCounters() here to avoid loops
        // Just refresh the jobs once
        refreshJobs();
    }
    
    // Show notification if job completed
    if (job.status === 'completed') {
        showJobCompletionNotification(job);
        // Stop polling for this job by refreshing job list one final time
        setTimeout(() => {
            if (document.getElementById('jobs-section').style.display !== 'none') {
                refreshJobs();
            }
        }, 1000);
    } else if (job.status === 'failed') {
        showJobFailureNotification(job);
        // Also refresh on failure
        setTimeout(() => {
            if (document.getElementById('jobs-section').style.display !== 'none') {
                refreshJobs();
            }
        }, 1000);
    }
    
    // Update active jobs badge in sidebar
    updateActiveJobsBadge();
}

function showJobCompletionNotification(job) {
    const message = `✅ Historical data job completed for ${job.symbol} (${job.data_count} candles)`;
    showAlert(message, 'success', 5000);
    
    // Update the badge with notification count
    updateActiveJobsBadge();
}

function showJobFailureNotification(job) {
    const message = `❌ Historical data job failed for ${job.symbol}: ${job.error_message}`;
    showAlert(message, 'danger', 8000);
}

// Job management functions
async function refreshJobs() {
    try {
        const response = await fetch('/api/jobs');
        const result = await response.json();
        
        if (response.ok) {
            updateJobsTable(result.jobs || []);
            // Don't call updateJobCounters() here - it would create a loop
            // The counters are updated directly from the table data
        } else {
            console.error('Error fetching jobs:', result);
        }
    } catch (error) {
        console.error('Error refreshing jobs:', error);
    }
}

function updateJobsTable(jobs) {
    const tbody = document.querySelector('#jobsTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No jobs found</td></tr>';
        return;
    }
    
    jobs.forEach(job => {
        const row = document.createElement('tr');
        
        // Status badge
        const statusBadge = getJobStatusBadge(job.status);
        
        // Progress bar
        const progressBar = job.status === 'running' ? 
            `<div class="progress" style="height: 20px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     style="width: ${job.progress.percentage}%">
                    ${Math.round(job.progress.percentage)}%
                </div>
            </div>` : 
            `<span class="text-muted">${job.progress.message}</span>`;
        
        // Date range
        const fromDate = new Date(job.from_date).toLocaleDateString('en-IN');
        const toDate = new Date(job.to_date).toLocaleDateString('en-IN');
        const dateRange = `${fromDate} to ${toDate}`;
        
        // Actions
        let actions = '';
        if (job.status === 'completed') {
            actions = `
                <button class="btn btn-sm btn-primary" onclick="loadJobData('${job.job_id}')">
                    <i class="fas fa-download me-1"></i>Load
                </button>
                <button class="btn btn-sm btn-success" onclick="exportJobData('${job.job_id}')">
                    <i class="fas fa-file-csv me-1"></i>Export
                </button>
            `;
        } else if (job.status === 'running') {
            actions = `
                <button class="btn btn-sm btn-danger" onclick="cancelJob('${job.job_id}')">
                    <i class="fas fa-stop me-1"></i>Cancel
                </button>
            `;
        }
        
        row.innerHTML = `
            <td><small>${job.job_id}</small></td>
            <td><strong>${job.symbol}</strong></td>
            <td><span class="badge bg-secondary">${job.exchange}</span></td>
            <td><span class="badge bg-info">${job.interval}</span></td>
            <td><small>${dateRange}</small></td>
            <td>${statusBadge}</td>
            <td>${progressBar}</td>
            <td><strong>${job.data_count || 0}</strong></td>
            <td><small>${formatDateTime(job.created_at)}</small></td>
            <td>${actions}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Update counters directly from job data
    let activeCount = 0;
    let completedCount = 0;
    let failedCount = 0;
    
    jobs.forEach(job => {
        if (job.status === 'running' || job.status === 'pending') {
            activeCount++;
        } else if (job.status === 'completed') {
            completedCount++;
        } else if (job.status === 'failed') {
            failedCount++;
        }
    });
    
    // Update counter elements
    document.getElementById('activeJobsCounter').textContent = activeCount;
    document.getElementById('completedJobsCounter').textContent = completedCount;
    document.getElementById('failedJobsCounter').textContent = failedCount;
    document.getElementById('totalJobsCounter').textContent = jobs.length;
    
    console.log(`Job counters updated: ${activeCount} active, ${completedCount} completed, ${failedCount} failed`);
}

function updateJobInTable(job) {
    const tbody = document.querySelector('#jobsTable tbody');
    if (!tbody) return;
    
    // Find existing row and update it
    const rows = tbody.querySelectorAll('tr');
    for (let row of rows) {
        const firstCell = row.querySelector('td');
        if (firstCell && firstCell.textContent.trim() === job.job_id) {
            // Update status and progress
            const statusCell = row.cells[5];
            const progressCell = row.cells[6];
            const dataCountCell = row.cells[7];
            const actionsCell = row.cells[9];
            
            statusCell.innerHTML = getJobStatusBadge(job.status);
            dataCountCell.innerHTML = `<strong>${job.data_count || 0}</strong>`;
            
            if (job.status === 'running') {
                progressCell.innerHTML = `
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             style="width: ${job.progress.percentage}%">
                            ${Math.round(job.progress.percentage)}%
                        </div>
                    </div>
                `;
                actionsCell.innerHTML = `
                    <button class="btn btn-sm btn-danger" onclick="cancelJob('${job.job_id}')">
                        <i class="fas fa-stop me-1"></i>Cancel
                    </button>
                `;
            } else if (job.status === 'completed') {
                progressCell.innerHTML = `<span class="text-success">Complete</span>`;
                actionsCell.innerHTML = `
                    <button class="btn btn-sm btn-primary" onclick="loadJobData('${job.job_id}')">
                        <i class="fas fa-download me-1"></i>Load
                    </button>
                    <button class="btn btn-sm btn-success" onclick="exportJobData('${job.job_id}')">
                        <i class="fas fa-file-csv me-1"></i>Export
                    </button>
                `;
            } else if (job.status === 'failed') {
                progressCell.innerHTML = `<span class="text-danger">Failed</span>`;
                actionsCell.innerHTML = '';
            }
            
            break;
        }
    }
}

function getJobStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge bg-secondary">Pending</span>',
        'running': '<span class="badge bg-primary">Running</span>',
        'completed': '<span class="badge bg-success">Completed</span>',
        'failed': '<span class="badge bg-danger">Failed</span>',
        'cancelled': '<span class="badge bg-warning">Cancelled</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
}

function updateJobCounters() {
    // This function now just delegates to refreshJobs since counters are updated there
    const currentActiveCount = parseInt(document.getElementById('activeJobsCounter')?.textContent) || 0;
    const totalJobs = parseInt(document.getElementById('totalJobsCounter')?.textContent) || 0;
    
    // Only refresh if we have active jobs or no jobs loaded yet
    if (currentActiveCount > 0 || totalJobs === 0) {
        console.log('Refreshing jobs...');
        refreshJobs();
    } else {
        console.log('Skipping job refresh - no active jobs');
    }
}

function updateActiveJobsBadge() {
    const badge = document.getElementById('activeJobsCount');
    const counter = document.getElementById('activeJobsCounter');
    
    if (badge && counter) {
        const activeCount = parseInt(counter.textContent) || 0;
        badge.textContent = activeCount;
        badge.style.display = activeCount > 0 ? 'inline' : 'none';
    }
}

async function loadJobData(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/data`);
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            // Load data into historical data section
            updateHistoricalData(result.data);
            
            // Switch to historical data section
            showSection('historical');
            
            // Update the symbol input to show what was loaded
            const symbolInput = document.getElementById('historicalSymbol');
            symbolInput.value = `${result.job_info.symbol} (${result.job_info.exchange}) - ${result.job_info.interval}`;
            
            showAlert(`✅ Loaded ${result.job_info.candles_count} candles from background job`, 'success');
        } else {
            showAlert(`Error loading job data: ${result.message || 'Unknown error'}`, 'danger');
        }
    } catch (error) {
        console.error('Error loading job data:', error);
        showAlert('Error loading job data', 'danger');
    }
}

async function exportJobData(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/data`);
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            // Create CSV content
            let csvContent = 'Date Time,Open,High,Low,Close,Volume\n';
            
            result.data.forEach(candle => {
                csvContent += `${candle.datetime},${candle.open},${candle.high},${candle.low},${candle.close},${candle.volume}\n`;
            });
            
            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            const filename = `${result.job_info.symbol}_${result.job_info.interval}_historical_data.csv`;
            a.download = filename;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showAlert(`✅ Exported ${result.job_info.candles_count} candles as ${filename}`, 'success');
        } else {
            showAlert(`Error exporting job data: ${result.message || 'Unknown error'}`, 'danger');
        }
    } catch (error) {
        console.error('Error exporting job data:', error);
        showAlert('Error exporting job data', 'danger');
    }
}

async function cancelJob(jobId) {
    if (!confirm('Are you sure you want to cancel this job?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('✅ Job cancelled successfully', 'success');
            refreshJobs();
        } else {
            showAlert(`Error cancelling job: ${result.message || 'Unknown error'}`, 'danger');
        }
    } catch (error) {
        console.error('Error cancelling job:', error);
        showAlert('Error cancelling job', 'danger');
    }
}

// Initialize WebSocket when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeJobWebSocket();
    
    // Smart refresh for jobs - only if there are active jobs
    setInterval(() => {
        if (document.getElementById('jobs-section').style.display !== 'none') {
            // Only refresh if there are active jobs
            const activeCount = parseInt(document.getElementById('activeJobsCounter')?.textContent) || 0;
            if (activeCount > 0) {
                updateJobCounters();
            }
        }
    }, 5000); // More frequent updates for active jobs
});

function formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('en-IN');
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN');
}

function getStatusBadgeClass(status) {
    switch (status?.toLowerCase()) {
        case 'executed':
        case 'completed':
            return 'bg-success';
        case 'pending':
        case 'ordered':
            return 'bg-warning';
        case 'cancelled':
        case 'rejected':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

function showLoading(show) {
    const modalElement = document.getElementById('loadingModal');
    if (!modalElement) {
        console.warn('Loading modal element not found');
        return;
    }
    
    console.log(`showLoading called with show=${show}`);
    
    if (show) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log('Loading modal shown');
    } else {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
            console.log('Loading modal hidden');
        } else {
            console.warn('No modal instance found to hide');
        }
    }
}

function hideLoading(section = null) {
    const modalElement = document.getElementById('loadingModal');
    if (!modalElement) {
        console.warn('Loading modal element not found');
        return;
    }
    
    console.log(`hideLoading called for section=${section}`);
    
    const modal = bootstrap.Modal.getInstance(modalElement);
    if (modal) {
        modal.hide();
        console.log('Loading modal hidden');
    } else {
        console.warn('No modal instance found to hide');
    }
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to body instead of container to avoid z-index issues
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function setupAutoRefresh() {
    // Clear any existing interval
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Refresh current section every 30 seconds
    refreshInterval = setInterval(() => {
        if (currentSection) {
            loadSectionData(currentSection);
        }
    }, 30000);
}

function refreshData() {
    if (currentSection) {
        loadSectionData(currentSection);
    }
}

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Add click handler to hide loading modal
document.addEventListener('click', function(event) {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal && event.target === loadingModal) {
        const modal = bootstrap.Modal.getInstance(loadingModal);
        if (modal) {
            modal.hide();
        }
    }
});

function logout() {
    localStorage.removeItem('sessionId');
    localStorage.removeItem('apiKey');
    window.location.href = '/';
}

// Execute order
async function executeOrder(orderId, defaultPrice) {
    // Prompt for execution price
    const executionPrice = prompt(`Enter execution price (default: ₹${defaultPrice}):`, defaultPrice);
    
    if (!executionPrice || isNaN(executionPrice)) {
        showAlert('Invalid execution price', 'warning');
        return;
    }
    
    if (!confirm(`Are you sure you want to execute this order at ₹${executionPrice}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/fake/orders/${orderId}/execute?execution_price=${executionPrice}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showAlert('Order executed successfully', 'success');
            loadOrdersData();
        } else {
            showAlert('Failed to execute order', 'danger');
        }
    } catch (error) {
        console.error('Error executing order:', error);
        showAlert('Error executing order', 'danger');
    }
}

// Cancel order
async function cancelOrder(orderId, exchange = 'NSE') {
    if (!confirm('Are you sure you want to cancel this order?')) {
        return;
    }
    
    try {
        let endpoint;
        if (isDemoMode) {
            endpoint = `/api/fake/orders/${orderId}`;
        } else {
            endpoint = `/api/orders/${orderId}?exchange=${encodeURIComponent(exchange)}`;
        }
        
        const response = await fetch(endpoint, { method: 'DELETE' });
        
        if (response.ok) {
            showAlert('Order cancelled successfully', 'success');
            loadOrdersData();
        } else {
            showAlert('Failed to cancel order', 'danger');
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        showAlert('Error cancelling order', 'danger');
    }
}

// Cancel GTT order
async function cancelGTTOrder(gttId) {
    if (!confirm('Are you sure you want to cancel this GTT order?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/gtt/orders/${gttId}/cancel`, { method: 'POST' });
        
        if (response.ok) {
            showAlert('GTT order cancelled successfully', 'success');
            loadGTTData();
        } else {
            showAlert('Failed to cancel GTT order', 'danger');
        }
    } catch (error) {
        console.error('Error cancelling GTT order:', error);
        showAlert('Error cancelling GTT order', 'danger');
    }
}

// Market Watch Functions



async function removeSymbolFromWatch(symbol, exchange) {
    if (confirm(`Remove ${symbol} from watchlist?`)) {
        try {
            // Remove from server
            const response = await fetch(`/api/market-watch/symbols?symbol=${encodeURIComponent(symbol)}&exchange=${encodeURIComponent(exchange)}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Remove from local array
                watchlistSymbols = watchlistSymbols.filter(s => !(s.symbol === symbol && s.exchange === exchange));
                updateMarketWatchTable();
                showAlert(`Removed ${symbol} from watchlist`, 'success');
            } else {
                showAlert('Failed to remove symbol', 'error');
            }
        } catch (error) {
            console.error('Error removing symbol:', error);
            showAlert('Failed to remove symbol', 'error');
        }
    }
}

async function showSymbolChart(symbol, exchange) {
    try {
        // Show loading
        const modal = new bootstrap.Modal(document.getElementById('chartModal'));
        document.getElementById('chartModalTitle').textContent = `${symbol} Price Chart`;
        modal.show();
        
        // Get historical data
        const response = await fetch(`/api/market/historical?symbol=${symbol}&exchange=${exchange}&interval=1day&days=30`);
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            createSymbolChart(data.data, symbol);
        } else {
            showAlert('Failed to load chart data', 'danger');
        }
    } catch (error) {
        console.error('Error loading chart:', error);
        showAlert('Error loading chart', 'danger');
    }
}

function createSymbolChart(data, symbol) {
    const ctx = document.getElementById('symbolChart').getContext('2d');
    
    // Destroy existing chart
    if (symbolChart) {
        symbolChart.destroy();
    }
    
    const labels = data.map(item => item.datetime);
    const prices = data.map(item => parseFloat(item.close));
    
    symbolChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${symbol} Price`,
                data: prices,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
}

async function refreshMarketData() {
    await updateMarketWatchTable();
    showAlert('Market data refreshed', 'success');
}

async function retryQuote(symbol, exchange) {
    try {
        // Show loading state
        const row = event.target.closest('tr');
        const cell = row.querySelector('td:nth-child(2)');
        cell.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Retrying...';
        
        const response = await fetch(`/api/market/quotes?symbol=${symbol}&exchange=${exchange}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            const quote = Array.isArray(data.data) ? data.data[0] : data.data;
            
            // Update the row with new data
            row.innerHTML = `
                <td><strong>${symbol}</strong></td>
                <td>₹${parseFloat(quote.ltp || 0).toFixed(2)}</td>
                <td class="${parseFloat(quote.change || 0) >= 0 ? 'text-success' : 'text-danger'}">
                    ${parseFloat(quote.change || 0).toFixed(2)}
                </td>
                <td class="${parseFloat(quote.change_percent || 0) >= 0 ? 'text-success' : 'text-danger'}">
                    ${parseFloat(quote.change_percent || 0).toFixed(2)}%
                </td>
                <td>${(parseInt(quote.volume || 0) / 1000).toFixed(0)}K</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" onclick="showSymbolChart('${symbol}', '${exchange}')" title="View Chart">
                            <i class="fas fa-chart-line"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="removeSymbolFromWatch('${symbol}', '${exchange}')" title="Remove">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            showAlert(`Successfully updated ${symbol}`, 'success');
        } else {
            // Still failed, show error again
            cell.innerHTML = `
                <i class="fas fa-exclamation-triangle me-1"></i>Temporarily unavailable
                <button class="btn btn-sm btn-outline-warning ms-2" onclick="retryQuote('${symbol}', '${exchange}')" title="Retry">
                    <i class="fas fa-sync-alt"></i>
                </button>
            `;
            showAlert(`Failed to update ${symbol}`, 'warning');
        }
    } catch (error) {
        console.error(`Error retrying quote for ${symbol}:`, error);
        const cell = event.target.closest('tr').querySelector('td:nth-child(2)');
        cell.innerHTML = `
            <i class="fas fa-exclamation-triangle me-1"></i>Connection error
            <button class="btn btn-sm btn-outline-warning ms-2" onclick="retryQuote('${symbol}', '${exchange}')" title="Retry">
                <i class="fas fa-sync-alt"></i>
            </button>
        `;
        showAlert(`Error retrying ${symbol}`, 'error');
    }
}

// Update market watch table with new functionality
async function updateMarketWatchTable() {
    const tbody = document.querySelector('#marketWatchTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    for (const item of watchlistSymbols) {
        try {
            // Construct the API URL based on exchange type
            let url = `/api/market/quotes?symbol=${item.symbol}&exchange=${item.exchange}`;
            
            // For NFO/BFO instruments, use stored instrument data if available
            if (item.exchange === 'NFO' || item.exchange === 'BFO') {
                if (item.instrumentData) {
                    // Use stored instrument data (preferred method)
                    const instrument = item.instrumentData;
                    console.log(`Using stored instrument data for ${item.symbol}:`, instrument);
                    
                    // Build URL with proper parameters like trading section
                    url = `/api/market/quotes?symbol=${encodeURIComponent(instrument.short_name || instrument.stock_code)}&exchange=${encodeURIComponent(instrument.exchange_code)}`;
                    
                    // Add expiry date for NFO/BFO instruments (if available)
                    if ((instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.expiry_date) {
                        url += `&expiry_date=${encodeURIComponent(instrument.expiry_date)}`;
                    }
                    
                    // Add option type and strike price for NFO/BFO options
                    if ((instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.option_type) {
                        url += `&option_type=${encodeURIComponent(instrument.option_type)}`;
                        if (instrument.strike_price && instrument.strike_price > 0) {
                            url += `&strike_price=${encodeURIComponent(instrument.strike_price)}`;
                        }
                    }
                    
                    console.log(`Built URL from stored data for ${item.symbol}:`, url);
                } else {
                    // Fallback: search for instrument details (for old watchlist items)
                    try {
                        console.log(`No stored data, searching for instrument details: ${item.symbol} on ${item.exchange}`);
                        const searchResponse = await fetch(`/api/instruments/search?query=${item.symbol}&exchange=${item.exchange}`);
                        const searchData = await searchResponse.json();
                        
                        // Extract the actual results from the response
                        const instruments = searchData.data || searchData || [];
                        
                        if (instruments && instruments.length > 0) {
                            // Find the most relevant instrument (usually the first one)
                            const instrument = instruments[0];
                            console.log(`Found instrument via search:`, instrument);
                            
                            // Build URL with proper parameters like trading section
                            url = `/api/market/quotes?symbol=${encodeURIComponent(instrument.short_name || instrument.stock_code)}&exchange=${encodeURIComponent(instrument.exchange_code)}`;
                            
                            // Add expiry date for NFO/BFO instruments (if available)
                            if ((instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.expiry_date) {
                                url += `&expiry_date=${encodeURIComponent(instrument.expiry_date)}`;
                            }
                            
                            // Add option type and strike price for NFO/BFO options
                            if ((instrument.exchange_code === 'NFO' || instrument.exchange_code === 'BFO') && instrument.option_type) {
                                url += `&option_type=${encodeURIComponent(instrument.option_type)}`;
                                if (instrument.strike_price && instrument.strike_price > 0) {
                                    url += `&strike_price=${encodeURIComponent(instrument.strike_price)}`;
                                }
                            }
                            
                            console.log(`Built URL from search for ${item.symbol}:`, url);
                        } else {
                            console.warn(`No instrument found for ${item.symbol} on ${item.exchange}`);
                            // Skip this quote and show error
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td><strong>${item.symbol}</strong></td>
                                <td colspan="3" class="text-danger">
                                    <i class="fas fa-exclamation-triangle me-1"></i>Instrument not found
                                    <small class="d-block">Please remove and re-add with full symbol name</small>
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm" role="group">
                                        <button class="btn btn-outline-danger" onclick="removeSymbolFromWatch('${item.symbol}', '${item.exchange}')" title="Remove">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            `;
                            tbody.appendChild(row);
                            continue; // Skip to next item
                        }
                    } catch (searchError) {
                        console.warn(`Could not get instrument details for ${item.symbol}:`, searchError);
                    }
                }
            }
            
            // For NFO/BFO, only make the call if we have the required parameters
            if ((item.exchange === 'NFO' || item.exchange === 'BFO') && 
                !url.includes('expiry_date=')) {
                console.warn(`Skipping quote for ${item.symbol} - missing required parameters`);
                continue;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.status === 'success' && data.data) {
                const quote = Array.isArray(data.data) ? data.data[0] : data.data;
                
                // Build symbol display with badges for derivatives
                let symbolDisplay = `<strong>${item.symbol}</strong>`;
                if (item.instrumentData && (item.exchange === 'NFO' || item.exchange === 'BFO')) {
                    const instrument = item.instrumentData;
                    symbolDisplay += '<div class="mt-1">';
                    
                    // Add expiry date badge
                    if (instrument.expiry_date) {
                        symbolDisplay += `<span class="badge bg-info me-1">${instrument.expiry_date}</span>`;
                    }
                    
                    // Add strike price badge for options
                    if (instrument.strike_price && instrument.strike_price > 0) {
                        symbolDisplay += `<span class="badge bg-warning me-1">₹${instrument.strike_price}</span>`;
                    }
                    
                    // Add option type badge
                    if (instrument.option_type) {
                        symbolDisplay += `<span class="badge bg-danger me-1">${instrument.option_type}</span>`;
                    } else {
                        // Show "Future" for non-option derivatives
                        symbolDisplay += `<span class="badge bg-secondary me-1">Future</span>`;
                    }
                    
                    // Add lot size info
                    if (instrument.lot_size) {
                        symbolDisplay += `<span class="badge bg-dark me-1">Lot: ${instrument.lot_size}</span>`;
                    }
                    
                    symbolDisplay += '</div>';
                }
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${symbolDisplay}</td>
                    <td>₹${parseFloat(quote.ltp || 0).toFixed(2)}</td>
                    <td class="${parseFloat(quote.change || 0) >= 0 ? 'text-success' : 'text-danger'}">
                        ${parseFloat(quote.change || 0).toFixed(2)}
                    </td>
                    <td class="${parseFloat(quote.change_percent || 0) >= 0 ? 'text-success' : 'text-danger'}">
                        ${parseFloat(quote.change_percent || 0).toFixed(2)}%
                    </td>
                    <td>${(parseInt(quote.volume || 0) / 1000).toFixed(0)}K</td>
                    <td>
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-primary" onclick="showSymbolChart('${item.symbol}', '${item.exchange}')" title="View Chart">
                                <i class="fas fa-chart-line"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="removeSymbolFromWatch('${item.symbol}', '${item.exchange}')" title="Remove">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            } else {
                // Add row with temporary error state
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${item.symbol}</strong></td>
                    <td colspan="3" class="text-warning">
                        <i class="fas fa-exclamation-triangle me-1"></i>Temporarily unavailable
                        <button class="btn btn-sm btn-outline-warning ms-2" onclick="retryQuote('${item.symbol}', '${item.exchange}')" title="Retry">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-danger" onclick="removeSymbolFromWatch('${item.symbol}', '${item.exchange}')" title="Remove">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            }
        } catch (error) {
            console.error(`Error fetching data for ${item.symbol}:`, error);
            // Add row with error state
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${item.symbol}</strong></td>
                <td colspan="3" class="text-warning">
                    <i class="fas fa-exclamation-triangle me-1"></i>Connection error
                    <button class="btn btn-sm btn-outline-warning ms-2" onclick="retryQuote('${item.symbol}', '${item.exchange}')" title="Retry">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-danger" onclick="removeSymbolFromWatch('${item.symbol}', '${item.exchange}')" title="Remove">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        }
    }
}
