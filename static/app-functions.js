/**
 * Vehicle Maintenance Tracker - Centralized Functions
 * This file contains all common functions used across the application
 * to maintain consistency and reduce code duplication.
 */

// ============================================================================
// NAVIGATION FUNCTIONS
// ============================================================================

/**
 * Show oil change menu - redirects to vehicles page with oil change parameter
 */
function showOilChangeMenu() {
    window.location.href = '/vehicles?oil_change=true';
}

// ============================================================================
// EXPORT FUNCTIONS
// ============================================================================

/**
 * Export all vehicles to CSV format
 */
function exportAllVehicles() {
    // Implementation will be moved from export-data.js
    console.log('Export all vehicles to CSV - function called');
}

/**
 * Export all vehicles to PDF format
 */
function exportToPDF() {
    // Implementation will be moved from export-data.js
    console.log('Export all vehicles to PDF - function called');
}

/**
 * Export single vehicle to CSV format
 */
function exportSingleVehicle() {
    // Implementation will be moved from export-data.js
    console.log('Export single vehicle to CSV - function called');
}

/**
 * Export all vehicles to PDF format (alternative function name)
 */
function exportAllVehiclesToPDF() {
    // Implementation will be moved from export-data.js
    console.log('Export all vehicles to PDF - function called');
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Close any open modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const bootstrapModal = bootstrap.Modal.getInstance(modal);
        if (bootstrapModal) {
            bootstrapModal.hide();
        }
    }
}

/**
 * Show success notification
 */
function showSuccess(message) {
    // Implementation for consistent success notifications
    console.log('Success:', message);
}

/**
 * Show error notification
 */
function showError(message) {
    // Implementation for consistent error notifications
    console.log('Error:', message);
}

/**
 * Show info notification
 */
function showInfo(message) {
    // Implementation for consistent info notifications
    console.log('Info:', message);
}

// ============================================================================
// DATA VALIDATION FUNCTIONS
// ============================================================================

/**
 * Validate mileage input
 */
function validateMileage(mileage) {
    return mileage > 0 && mileage < 1000000;
}

/**
 * Validate date input
 */
function validateDate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date);
}

/**
 * Format currency consistently
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Format date consistently
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US');
}

// ============================================================================
// LOCAL STORAGE FUNCTIONS
// ============================================================================

/**
 * Save data to localStorage with error handling
 */
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

// ============================================================================
// ACCOUNT (TESTER) SELECTION HELPERS
// ============================================================================

const ACCOUNT_COOKIE_NAME = 'selected_account';
const ACCOUNTS_STORAGE_KEY = 'accounts_list_v1';

function setCookie(name, value, days = 365) {
    const d = new Date();
    d.setTime(d.getTime() + (days*24*60*60*1000));
    const expires = 'expires=' + d.toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) + ';' + expires + ';path=/';
}

function getCookie(name) {
    const decoded = decodeURIComponent(document.cookie);
    const parts = decoded.split(';');
    for (let c of parts) {
        c = c.trim();
        if (c.indexOf(name + '=') === 0) {
            return c.substring(name.length + 1);
        }
    }
    return '';
}

function getAccountsList() {
    const list = loadFromLocalStorage(ACCOUNTS_STORAGE_KEY, []);
    // Ensure unique, simple strings
    const unique = Array.from(new Set((list || []).filter(Boolean)));
    // Provide a sensible starter set if empty
    if (unique.length === 0) {
        return ['kory'];
    }
    return unique;
}

function saveAccountsList(list) {
    const cleaned = Array.from(new Set((list || []).map(s => (s || '').trim()).filter(Boolean)));
    return saveToLocalStorage(ACCOUNTS_STORAGE_KEY, cleaned);
}

function getSelectedAccount() {
    return getCookie(ACCOUNT_COOKIE_NAME) || 'All';
}

function setSelectedAccount(name) {
    setCookie(ACCOUNT_COOKIE_NAME, name || 'All');
}

function buildAccountDropdown(menuId, buttonId) {
    const menu = document.getElementById(menuId);
    const button = document.getElementById(buttonId);
    if (!menu || !button) return;

    const accounts = getAccountsList();
    const current = getSelectedAccount();
    button.innerHTML = `<i class="fas fa-user-circle me-2"></i>${current === 'All' ? 'All Accounts' : current}`;

    let html = '';
    html += `<li><a class="dropdown-item" href="#" data-account="All">All Accounts</a></li>`;
    html += '<li><hr class="dropdown-divider"></li>';
    accounts.forEach(acc => {
        html += `<li><a class="dropdown-item" href="#" data-account="${acc}"><i class=\"fas fa-user me-2 text-purple-600\"></i>${acc}</a></li>`;
    });
    html += '<li><hr class="dropdown-divider"></li>';
    html += `<li><a class="dropdown-item" href="/accounts"><i class=\"fas fa-users-cog me-2 text-purple-600\"></i>Manage Accounts</a></li>`;

    menu.innerHTML = html;

    menu.querySelectorAll('a[data-account]').forEach(a => {
        a.addEventListener('click', (e) => {
            e.preventDefault();
            const selected = a.getAttribute('data-account');
            setSelectedAccount(selected);
            // Update button label
            button.innerHTML = `<i class=\"fas fa-user-circle me-2\"></i>${selected === 'All' ? 'All Accounts' : selected}`;
            // Simple reload to apply filters across pages (server/client can read cookie)
            window.location.reload();
        });
    });
}

// Initialize account switcher if present on a page
function initializeAccountSwitcher() {
    buildAccountDropdown('accountDropdownMenu', 'accountDropdownButton');
}

/**
 * Load data from localStorage with error handling
 */
function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

/**
 * Remove data from localStorage
 */
function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Failed to remove from localStorage:', error);
        return false;
    }
}

// ============================================================================
// INITIALIZATION FUNCTIONS
// ============================================================================

/**
 * Initialize common functionality for all pages
 */
function initializeCommonFeatures() {
    // Set up common event listeners
    // Initialize common UI components
    // Set up common error handling
    console.log('Common features initialized');
}

/**
 * Initialize page-specific functionality
 */
function initializePageFeatures() {
    // This will be overridden by individual pages
    console.log('Page features initialized');
}

// ============================================================================
// EXPORT STATEMENTS
// ============================================================================

// Make functions available globally
window.showOilChangeMenu = showOilChangeMenu;
window.exportAllVehicles = exportAllVehicles;
window.exportToPDF = exportToPDF;
window.exportSingleVehicle = exportSingleVehicle;
window.exportAllVehiclesToPDF = exportAllVehiclesToPDF;
window.closeModal = closeModal;
window.showSuccess = showSuccess;
window.showError = showError;
window.showInfo = showInfo;
window.validateMileage = validateMileage;
window.validateDate = validateDate;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.saveToLocalStorage = saveToLocalStorage;
window.loadFromLocalStorage = loadFromLocalStorage;
window.removeFromLocalStorage = removeFromLocalStorage;
window.initializeCommonFeatures = initializeCommonFeatures;
window.initializePageFeatures = initializePageFeatures;
