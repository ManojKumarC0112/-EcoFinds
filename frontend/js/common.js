// EcoFinds Common JavaScript Utilities (v2 - Secure & Modern)
const API_BASE = 'http://localhost:5000';

// ============================================================
// API UTILITIES
// ============================================================

async function apiCall(endpoint, options = {}) {
    try {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers 
        };
        
        // Attach JWT Token if available
        const token = localStorage.getItem('ecofinds_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Handle global 401 Unauthorized securely
            if (response.status === 401 && !endpoint.includes('/auth/')) {
                logout(false);
                showToast('Session expired. Please log in again.', 'warning');
                setTimeout(() => window.location.href = 'auth.html', 2000);
            }
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
        return null;
    }
}

function setCurrentUser(user, token) {
    localStorage.setItem('ecofinds_user', JSON.stringify(user));
    if (token) localStorage.setItem('ecofinds_token', token);
}

function logout(redirect = true) {
    localStorage.removeItem('ecofinds_user');
    localStorage.removeItem('ecofinds_token');
    if (redirect) {
        window.location.href = 'index.html';
    }
}

// ============================================================
// UI UTILITIES
// ============================================================

function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    const toastId = 'toast_' + Date.now();
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';

    const icon = {
        'success': 'check-circle-fill',
        'error': 'exclamation-triangle-fill',
        'warning': 'exclamation-triangle-fill',
        'info': 'info-circle-fill'
    }[type];

    const toastHTML = `
        <div class="toast align-items-center text-white ${bgClass} border-0 shadow-lg mb-2" role="alert" id="${toastId}">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="bi bi-${icon} me-2 fs-5"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 4000 });
    toast.show();
    toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
}

// ============================================================
// NAVIGATION UTILITIES
// ============================================================

function initializePage() {
    updateNavigation();
    updateCartBadge();
}

function updateNavigation() {
    const user = getCurrentUser();
    const userMenu = document.getElementById('userMenu');
    const authButtons = document.getElementById('authButtons');
    const usernameSpan = document.getElementById('username');

    if (user && userMenu && authButtons) {
        userMenu.style.display = 'block';
        authButtons.style.display = 'none';
        if (usernameSpan) usernameSpan.textContent = user.username;
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
        const data = await apiCall('/cart/');
        const count = data.results.length;
        if (count > 0) {
            cartBadge.textContent = count;
            cartBadge.style.display = 'inline-block';
        } else {
            cartBadge.style.display = 'none';
        }
    } catch (e) {
        cartBadge.style.display = 'none';
    }
}

// ============================================================
// GLOBAL ACTIONS
// ============================================================

async function addToCartGlobal(productId) {
    if (!getCurrentUser()) {
        showToast('Please login to add items to cart', 'warning');
        setTimeout(() => window.location.href = 'auth.html', 1500);
        return false;
    }

    try {
        await apiCall('/cart/add', {
            method: 'POST',
            body: JSON.stringify({ product_id: productId })
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

document.addEventListener('DOMContentLoaded', () => {
    initializePage();
    document.addEventListener('click', e => {
        if (e.target.closest('[data-add-to-cart]')) {
            const btn = e.target.closest('[data-add-to-cart]');
            addToCartGlobal(parseInt(btn.getAttribute('data-add-to-cart')));
        }
    });
});

window.EcoFinds = { apiCall, getCurrentUser, setCurrentUser, logout, showToast, addToCartGlobal, updateCartBadge };