// Fake Funds Management JavaScript
// Handles all fake trading funds, balance updates, and related functionality

class FakeFundsManager {
    constructor() {
        this.currentFunds = null;
        this.updateInterval = null;
        this.init();
    }

    async init() {
        await this.loadFunds();
        this.startAutoRefresh();
        this.setupEventListeners();
    }

    async loadFunds() {
        try {
            const response = await fetch('/api/fake/funds');
            if (response.ok) {
                this.currentFunds = await response.json();
                this.updateFundsDisplay();
            } else {
                console.error('Failed to load fake funds');
            }
        } catch (error) {
            console.error('Error loading fake funds:', error);
        }
    }

    async refreshLedger() {
        try {
            // Only refresh if ledger section is visible
            const ledgerSection = document.getElementById('ledger-section');
            if (ledgerSection && ledgerSection.style.display !== 'none') {
                // Load and update ledger data
                const response = await fetch('/api/fake/ledger');
                if (response.ok) {
                    const data = await response.json();
                    if (window.updateLedgerTable) {
                        window.updateLedgerTable(data);
                    }
                }
            }
        } catch (error) {
            console.error('Error refreshing ledger:', error);
        }
    }

    async forceRefreshLedger() {
        try {
            // Always refresh ledger data regardless of section visibility
            const response = await fetch('/api/fake/ledger');
            if (response.ok) {
                const data = await response.json();
                if (window.updateLedgerTable) {
                    window.updateLedgerTable(data);
                }
            }
        } catch (error) {
            console.error('Error force refreshing ledger:', error);
        }
    }

    updateFundsDisplay() {
        if (!this.currentFunds) return;

        // Update cash balance
        const cashBalanceEl = document.getElementById('cashBalance');
        if (cashBalanceEl) {
            cashBalanceEl.textContent = this.formatCurrency(this.currentFunds.cash_balance || 0);
        }

        // Update equity balance
        const equityBalanceEl = document.getElementById('equityBalance');
        if (equityBalanceEl) {
            equityBalanceEl.textContent = this.formatCurrency(this.currentFunds.equity_balance || 0);
        }

        // Update FNO balance
        const fnoBalanceEl = document.getElementById('fnoBalance');
        if (fnoBalanceEl) {
            fnoBalanceEl.textContent = this.formatCurrency(this.currentFunds.fno_balance || 0);
        }

        // Update total balance
        const totalBalanceEl = document.getElementById('totalBalance');
        if (totalBalanceEl) {
            totalBalanceEl.textContent = this.formatCurrency(this.currentFunds.total_balance || 0);
        }

        // Update source label
        const sourceEl = document.getElementById('cashBalanceSource');
        if (sourceEl) {
            sourceEl.textContent = 'Demo Mode';
        }
    }

    async updateFunds(amount, transactionType, segment = 'cash') {
        try {
            const response = await fetch('/api/fake/funds/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: amount,
                    transaction_type: transactionType,
                    segment: segment
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.currentFunds = result.data;
                this.updateFundsDisplay();
                
                // Add ledger entry for manual adjustment
                await this.addLedgerEntry(amount, transactionType, segment);
                
                // Show success message
                this.showNotification(result.message, 'success');
                
                // Trigger portfolio update if needed
                if (window.updatePortfolioTable) {
                    window.updatePortfolioTable();
                }
                
                // Trigger ledger update if needed
                await this.refreshLedger();
                
                return result;
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to update funds', 'error');
                return null;
            }
        } catch (error) {
            console.error('Error updating funds:', error);
            this.showNotification('Failed to update funds', 'error');
            return null;
        }
    }

    async addLedgerEntry(amount, transactionType, segment) {
        try {
            const action = transactionType === 'credit' ? 'Credit' : 'Debit';
            const remarks = `Manual ${action.toLowerCase()} of ₹${amount.toLocaleString('en-IN')} in ${segment.toUpperCase()}`;
            
            await fetch('/api/fake/ledger/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    transaction_type: 'manual_adjustment',
                    total_amount: amount,
                    segment: segment,
                    remarks: remarks
                })
            });
        } catch (error) {
            console.error('Error adding ledger entry:', error);
        }
    }

    async showFundsModal() {
        // Force refresh ledger data for modal
        await this.forceRefreshLedger();
        
        const modal = `
            <div class="modal fade" id="fundsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title text-dark">Manage Demo Funds</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <div class="card bg-light">
                                        <div class="card-body text-center">
                                            <h6 class="card-title text-dark">Current Balances</h6>
                                            <div class="mb-2 text-dark">
                                                <strong>Cash:</strong> <span id="modalCashBalance" class="text-dark">${this.formatCurrency(this.currentFunds?.cash_balance || 0)}</span>
                                            </div>
                                            <div class="mb-2 text-dark">
                                                <strong>Equity:</strong> <span id="modalEquityBalance" class="text-dark">${this.formatCurrency(this.currentFunds?.equity_balance || 0)}</span>
                                            </div>
                                            <div class="mb-2 text-dark">
                                                <strong>FNO:</strong> <span id="modalFnoBalance" class="text-dark">${this.formatCurrency(this.currentFunds?.fno_balance || 0)}</span>
                                            </div>
                                            <div class="border-top pt-2 text-dark">
                                                <strong>Total:</strong> <span id="modalTotalBalance" class="text-dark">${this.formatCurrency(this.currentFunds?.total_balance || 0)}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-body">
                                            <h6 class="card-title">Quick Actions</h6>
                                            <div class="d-grid gap-2">
                                                <button class="btn btn-success btn-sm" onclick="fakeFundsManager.quickAddFunds(100000)">
                                                    <i class="fas fa-plus me-1"></i>Add ₹1L
                                                </button>
                                                <button class="btn btn-success btn-sm" onclick="fakeFundsManager.quickAddFunds(500000)">
                                                    <i class="fas fa-plus me-1"></i>Add ₹5L
                                                </button>
                                                <button class="btn btn-success btn-sm" onclick="fakeFundsManager.quickAddFunds(1000000)">
                                                    <i class="fas fa-plus me-1"></i>Add ₹10L
                                                </button>
                                                <button class="btn btn-warning btn-sm" onclick="fakeFundsManager.resetFunds()">
                                                    <i class="fas fa-undo me-1"></i>Reset to ₹0
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">Custom Amount</h6>
                                    <form id="customFundsForm">
                                        <div class="row">
                                            <div class="col-md-4">
                                                <label class="form-label">Amount</label>
                                                <input type="number" class="form-control" id="customAmount" placeholder="Enter amount" min="0" step="1000">
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Action</label>
                                                <select class="form-select" id="customAction">
                                                    <option value="credit">Add Funds</option>
                                                    <option value="debit">Deduct Funds</option>
                                                </select>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Segment</label>
                                                <select class="form-select" id="customSegment">
                                                    <option value="cash">Cash</option>
                                                    <option value="equity">Equity</option>
                                                    <option value="fno">FNO</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="mt-3">
                                            <button type="submit" class="btn btn-primary">
                                                <i class="fas fa-save me-1"></i>Update Funds
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('fundsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modal);

        // Show modal
        const modalInstance = new bootstrap.Modal(document.getElementById('fundsModal'));
        modalInstance.show();

        // Setup form handler
        document.getElementById('customFundsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCustomFundsUpdate();
        });
    }

    async quickAddFunds(amount) {
        await this.updateFunds(amount, 'credit', 'cash');
    }

    async resetFunds() {
        if (confirm('Are you sure you want to reset all funds to ₹0?')) {
            // Set all balances to 0
            await this.updateFunds(-this.currentFunds.cash_balance, 'debit', 'cash');
            await this.updateFunds(-this.currentFunds.equity_balance, 'debit', 'equity');
            await this.updateFunds(-this.currentFunds.fno_balance, 'debit', 'fno');
            
            this.showNotification('Funds reset to ₹0', 'success');
        }
    }

    async handleCustomFundsUpdate() {
        const amount = parseFloat(document.getElementById('customAmount').value);
        const action = document.getElementById('customAction').value;
        const segment = document.getElementById('customSegment').value;

        if (!amount || amount <= 0) {
            this.showNotification('Please enter a valid amount', 'warning');
            return;
        }

        await this.updateFunds(amount, action, segment);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('fundsModal'));
        modal.hide();
    }

    startAutoRefresh() {
        // Refresh funds every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadFunds();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    setupEventListeners() {
        // Funds management button removed from portfolio page
    }

    addFundsManagementButton() {
        // Look for portfolio section header
        const portfolioHeaders = document.querySelectorAll('h1.h2');
        let portfolioHeader = null;
        
        for (const header of portfolioHeaders) {
            if (header.textContent.includes('Portfolio')) {
                portfolioHeader = header;
                break;
            }
        }
        
        if (portfolioHeader) {
            // Check if button already exists
            const existingButton = portfolioHeader.parentNode.querySelector('.btn-manage-funds');
            if (!existingButton) {
                const button = document.createElement('button');
                button.className = 'btn btn-sm btn-outline-primary ms-2 btn-manage-funds';
                button.innerHTML = '<i class="fas fa-coins me-1"></i>Manage Funds';
                button.onclick = () => this.showFundsModal();
                portfolioHeader.parentNode.appendChild(button);
            }
        }
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(amount);
    }

    showNotification(message, type = 'info') {
        // Use existing showAlert function if available
        if (window.showAlert) {
            window.showAlert(message, type);
        } else {
            // Fallback notification - positioned to avoid sidebar
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(alertDiv);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    destroy() {
        this.stopAutoRefresh();
    }
}

// Initialize fake funds manager when DOM is loaded
let fakeFundsManager;

document.addEventListener('DOMContentLoaded', function() {
    fakeFundsManager = new FakeFundsManager();
});

// Make it globally available
window.fakeFundsManager = fakeFundsManager;
