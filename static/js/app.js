// Main JavaScript for Comprehensive Trading System

// Global variables
let currentUser = null;
let sessionId = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Comprehensive Trading System loaded');
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Check if user is already logged in
    checkLoginStatus();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Check login status
function checkLoginStatus() {
    sessionId = localStorage.getItem('sessionId');
    if (sessionId) {
        // User is logged in, redirect to dashboard
        window.location.href = '/dashboard';
    }
}

// Show login modal
function showLoginModal() {
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
}

// Show features section
function showFeatures() {
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
        featuresSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Generate login URL
function generateLoginUrl() {
    const apiKey = document.getElementById('apiKey').value;
    const apiSecret = document.getElementById('apiSecret').value;
    
    // Validate inputs
    if (!apiKey || !apiSecret) {
        showAlert('Please fill in API Key and Secret', 'danger');
        return;
    }
    
    // Generate login URL
    const loginUrl = `https://api.icicidirect.com/apiuser/login?api_key=${encodeURIComponent(apiKey)}`;
    
    // Display the URL
    document.getElementById('loginUrl').value = loginUrl;
    
    // Show step 2
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
    
    // Update buttons
    document.getElementById('step1Btn').style.display = 'none';
    document.getElementById('step2Btn').style.display = 'inline-block';
    
    showAlert('Login URL generated! Copy it and visit to get your session token.', 'success');
}

// Copy login URL to clipboard
function copyLoginUrl() {
    const loginUrl = document.getElementById('loginUrl');
    loginUrl.select();
    loginUrl.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        document.execCommand('copy');
        showAlert('Login URL copied to clipboard!', 'success');
    } catch (err) {
        // Fallback for modern browsers
        navigator.clipboard.writeText(loginUrl.value).then(() => {
            showAlert('Login URL copied to clipboard!', 'success');
        }).catch(() => {
            showAlert('Failed to copy URL. Please copy it manually.', 'warning');
        });
    }
}

// Login function
async function login() {
    const apiKey = document.getElementById('apiKey').value;
    const apiSecret = document.getElementById('apiSecret').value;
    const sessionToken = document.getElementById('sessionToken').value;
    
    // Validate inputs
    if (!apiKey || !apiSecret || !sessionToken) {
        showAlert('Please fill in all fields', 'danger');
        return;
    }
    
    // Show loading
    showLoading(true);
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                api_key: apiKey,
                api_secret: apiSecret,
                session_token: sessionToken
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            // Store session ID
            sessionId = data.session_id;
            localStorage.setItem('sessionId', sessionId);
            
            // Store user credentials (in production, use secure storage)
            localStorage.setItem('apiKey', apiKey);
            localStorage.setItem('apiSecret', apiSecret);
            localStorage.setItem('sessionToken', sessionToken);
            
            showAlert('Login successful! Redirecting to dashboard...', 'success');
            
            // Close modal and redirect
            const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            loginModal.hide();
            
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
            
        } else {
            showAlert(data.detail || 'Login failed', 'danger');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showAlert('Network error. Please try again.', 'danger');
    } finally {
        showLoading(false);
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
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

// Show/hide loading spinner
function showLoading(show = true) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'flex' : 'none';
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Format percentage
function formatPercentage(value) {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
}

// Format number with commas
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

// Animate counter
function animateCounter(element, start, end, duration = 1000) {
    const startTime = performance.now();
    const difference = end - start;
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (difference * progress);
        element.textContent = formatCurrency(current);
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    requestAnimationFrame(updateCounter);
}

// Market ticker animation
function animateMarketTicker() {
    const tickerItems = document.querySelectorAll('.ticker-item');
    tickerItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '0.7';
            setTimeout(() => {
                item.style.opacity = '1';
            }, 200);
        }, index * 1000);
    });
}

// Start market ticker animation
setInterval(animateMarketTicker, 5000);

// Add click event listeners
document.addEventListener('click', function(e) {
    // Handle login form submission
    if (e.target.matches('[onclick="login()"]')) {
        e.preventDefault();
        login();
    }
    
    // Handle generate login URL
    if (e.target.matches('[onclick="generateLoginUrl()"]')) {
        e.preventDefault();
        generateLoginUrl();
    }
    
    // Handle copy login URL
    if (e.target.matches('[onclick="copyLoginUrl()"]')) {
        e.preventDefault();
        copyLoginUrl();
    }
    
    // Handle feature navigation
    if (e.target.matches('[onclick="showFeatures()"]')) {
        e.preventDefault();
        showFeatures();
    }
    
    // Handle login modal
    if (e.target.matches('[onclick="showLoginModal()"]')) {
        e.preventDefault();
        showLoginModal();
    }
});

// Add form submission handler
document.addEventListener('submit', function(e) {
    if (e.target.id === 'loginForm') {
        e.preventDefault();
        login();
    }
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + L to show login modal
    if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault();
        showLoginModal();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Add scroll effects
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const parallax = document.querySelector('.hero-section');
    
    if (parallax) {
        const speed = scrolled * 0.5;
        parallax.style.transform = `translateY(${speed}px)`;
    }
});

// Add intersection observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', function() {
    const animateElements = document.querySelectorAll('.card, .feature-icon');
    animateElements.forEach(el => observer.observe(el));
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        animation: fadeInUp 0.6s ease-out forwards;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .ticker-item {
        transition: opacity 0.3s ease;
    }
`;
document.head.appendChild(style);

// Export functions for global access
window.TradingSystemApp = {
    login,
    generateLoginUrl,
    copyLoginUrl,
    showLoginModal,
    showFeatures,
    showAlert,
    showLoading,
    formatCurrency,
    formatPercentage,
    formatNumber,
    animateCounter
};
