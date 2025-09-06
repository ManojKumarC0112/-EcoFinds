// EcoFinds Common JavaScript Utilities
const API_BASE = 'http://localhost:5000';

// ============================================================
// API UTILITIES
// ============================================================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 
                'Content-Type': 'application/json',
                ...options.headers 
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============================================================
// USER MANAGEMENT
// ============================================================

function getCurrentUser() {
    try {
        const userData = localStorage.getItem('ecofinds_user');
        return userData ? JSON.parse(userData) : null;
    } catch (error) {
        console.error('Error getting user data:', error);
        return null;
    }
}

function setCurrentUser(user) {
    try {
        localStorage.setItem('ecofinds_user', JSON.stringify(user));
    } catch (error) {
        console.error('Error setting user data:', error);
    }
}

function clearCurrentUser() {
    localStorage.removeItem('ecofinds_user');
}

function logout() {
    clearCurrentUser();
    showToast('Logged out successfully', 'info');
    window.location.href = 'login.html';
}

// ============================================================
// UI UTILITIES
// ============================================================

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toastId = 'toast_' + Date.now();
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';

    const textClass = type === 'warning' ? 'text-dark' : 'text-white';

    const toastHTML = `
        <div class="toast ${bgClass} ${textClass}" role="alert" id="${toastId}">
            <div class="toast-header ${bgClass} ${textClass} border-0">
                <i class="bi bi-${getToastIcon(type)} me-2"></i>
                <strong class="me-auto">EcoFinds</strong>
                <button type="button" class="btn-close ${textClass === 'text-dark' ? '' : 'btn-close-white'}" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();

    // Clean up after toast is hidden
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle-fill',
        'error': 'exclamation-triangle-fill',
        'warning': 'exclamation-triangle-fill',
        'info': 'info-circle-fill'
    };
    return icons[type] || 'info-circle-fill';
}

// ============================================================
// NAVIGATION UTILITIES
// ============================================================

function initializePage() {
    updateNavigation();
    updateCartBadge();
    
    // Test backend connection
    testConnection();
}

function updateNavigation() {
    const user = getCurrentUser();
    const userMenu = document.getElementById('userMenu');
    const authButtons = document.getElementById('authButtons');
    const usernameSpan = document.getElementById('username');

    if (user && userMenu && authButtons) {
        userMenu.style.display = 'block';
        authButtons.style.display = 'none';
        
        if (usernameSpan) {
            usernameSpan.textContent = user.username || user.email.split('@')[0];
        }
    } else if (userMenu && authButtons) {
        userMenu.style.display = 'none';
        authButtons.style.display = 'block';
    }
}

async function updateCartBadge() {
    const user = getCurrentUser();
    const cartBadge = document.getElementById('cartBadge');
    
    if (!user || !cartBadge) return;

    try {
        const data = await apiCall(`/cart?user_id=${user.id}`);
        const count = data.results.length;
        
        if (count > 0) {
            cartBadge.textContent = count;
            cartBadge.style.display = 'inline-block';
        } else {
            cartBadge.style.display = 'none';
        }
    } catch (error) {
        // Silently fail for cart badge updates
        cartBadge.style.display = 'none';
    }
}

// ============================================================
// BACKEND CONNECTION
// ============================================================

async function testConnection() {
    try {
        await apiCall('/health');
        console.log('✅ Backend connection successful');
    } catch (error) {
        console.error('❌ Backend connection failed:', error);
        showToast('Unable to connect to server. Please ensure the backend is running.', 'error');
    }
}

// ============================================================
// FORM UTILITIES
// ============================================================

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password && password.length >= 6;
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(price);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================================
// PRODUCT UTILITIES
// ============================================================

async function addToCartGlobal(productId) {
    const user = getCurrentUser();
    
    if (!user) {
        showToast('Please login to add items to cart', 'warning');
        return false;
    }

    try {
        await apiCall('/cart/add', {
            method: 'POST',
            body: JSON.stringify({
                user_id: user.id,
                product_id: productId
            })
        });
        
        showToast('Added to cart!', 'success');
        updateCartBadge();
        return true;
    } catch (error) {
        if (error.message.includes('already in cart')) {
            showToast('Item already in cart', 'info');
        } else {
            showToast('Error adding to cart', 'error');
        }
        return false;
    }
}

// ============================================================
// SEARCH UTILITIES
// ============================================================

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

// ============================================================
// LOCAL STORAGE UTILITIES
// ============================================================

function getFromStorage(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : defaultValue;
    } catch (error) {
        console.error('Error reading from storage:', error);
        return defaultValue;
    }
}

function setToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error writing to storage:', error);
        return false;
    }
}

// ============================================================
// ERROR HANDLING
// ============================================================

window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Auto-initialize common functionality
    console.log('EcoFinds common utilities loaded');
    
    // Add global click handler for add to cart buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-add-to-cart]')) {
            const productId = e.target.getAttribute('data-add-to-cart');
            addToCartGlobal(parseInt(productId));
        }
    });
});

// Export for use in other scripts
window.EcoFinds = {
    apiCall,
    getCurrentUser,
    setCurrentUser,
    clearCurrentUser,
    logout,
    showToast,
    updateCartBadge,
    addToCartGlobal,
    formatPrice,
    formatDate,
    validateEmail,
    validatePassword,
    debounce
};