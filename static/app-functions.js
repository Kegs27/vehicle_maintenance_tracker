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
// ACCOUNT SELECTION HELPERS
// ============================================================================

const ACCOUNT_COOKIE_NAME = 'vmt.accountId';
const ACCOUNT_STORAGE_KEY = 'vmt.selectedAccountId';
const ACCOUNT_GLOBAL_CONTEXT = typeof window !== 'undefined' ? (window.__ACCOUNT_CONTEXT__ || {}) : {};
let accountCache = null;

function setCookie(name, value, days = 365) {
    const d = new Date();
    d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
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

function saveAccountIdToStorage(accountId) {
    if (!accountId || accountId === 'all') {
        removeFromLocalStorage(ACCOUNT_STORAGE_KEY);
        return;
    }
    saveToLocalStorage(ACCOUNT_STORAGE_KEY, accountId);
}

function loadAccountIdFromStorage() {
    return loadFromLocalStorage(ACCOUNT_STORAGE_KEY, null);
}

function getSelectedAccountId() {
    try {
        const urlAccount = new URL(window.location.href).searchParams.get('accountId');
        if (urlAccount && urlAccount.toLowerCase() !== 'all') {
            return urlAccount;
        }
    } catch (error) {
        console.error('Failed to resolve accountId from URL:', error);
    }

    const stored = loadAccountIdFromStorage();
    if (stored && stored.toLowerCase() !== 'all') {
        return stored;
    }

    if (window.__ACCOUNT_CONTEXT__ && window.__ACCOUNT_CONTEXT__.account_id) {
        return window.__ACCOUNT_CONTEXT__.account_id;
    }

    return null;
}

function buildAccountAwareUrl(path) {
    const accountId = getSelectedAccountId();
    if (!accountId) {
        return path;
    }
    const url = new URL(path, window.location.origin);
    url.searchParams.set('accountId', accountId);
    return url.pathname + url.search;
}

async function fetchAccountsFromApi(forceRefresh = false) {
    if (accountCache && !forceRefresh) {
        return accountCache;
    }

    try {
        const response = await fetch('/api/accounts', { credentials: 'same-origin' });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Unknown error loading accounts');
        }
        accountCache = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch accounts:', error);
        accountCache = null;
        throw error;
    }
}

function determineInitialAccountId(accounts, defaultAccountId) {
    const url = new URL(window.location.href);
    const paramId = url.searchParams.get('accountId');

    const hasAccount = (id) => accounts.some((acc) => acc.id === id);

    if (paramId) {
        if (paramId.toLowerCase() === 'all' || !hasAccount(paramId)) {
            return 'all';
        }
        return paramId;
    }

    const storedId = loadAccountIdFromStorage();
    if (storedId && hasAccount(storedId)) {
        return storedId;
    }

    if (ACCOUNT_GLOBAL_CONTEXT.account_id && hasAccount(ACCOUNT_GLOBAL_CONTEXT.account_id)) {
        return ACCOUNT_GLOBAL_CONTEXT.account_id;
    }

    if (defaultAccountId && hasAccount(defaultAccountId)) {
        return defaultAccountId;
    }

    return 'all';
}

function updateAccountDropdownButton(button, account, totalVehicleCount, isAllSelected) {
    if (!button) return;

    if (isAllSelected) {
        button.innerHTML = `<span class="icon-row"><i class="fa-solid fa-circle-user fa-fw icon-primary" aria-hidden="true"></i><span>All Accounts${typeof totalVehicleCount === 'number' ? ` (${totalVehicleCount})` : ''}</span></span>`;
        return;
    }

    if (!account) {
        button.innerHTML = `<span class="icon-row"><i class="fa-solid fa-circle-user fa-fw icon-primary" aria-hidden="true"></i><span>Accounts</span></span>`;
        return;
    }

    const countLabel = typeof account.vehicle_count === 'number' ? ` (${account.vehicle_count})` : '';
    const defaultBadge = account.is_default ? ' <i class="fa-solid fa-star fa-fw icon-right text-warning" title="Default account" aria-hidden="true"></i>' : '';
    button.innerHTML = `<span class="icon-row"><i class="fa-solid fa-circle-user fa-fw icon-primary" aria-hidden="true"></i><span>${account.name}${countLabel}${defaultBadge}</span></span>`;
    }

function buildAccountListMarkup(accounts, selectedAccountId, totalVehicleCount) {
    const items = [];
    const isAll = selectedAccountId === 'all' || !selectedAccountId;

    items.push(`
        <li>
            <a class="dropdown-item d-flex justify-content-between align-items-center ${isAll ? 'active' : ''}"
               href="#" data-account-id="all" data-account-name="All">
                <span class="icon-row"><i class="fa-solid fa-layer-group fa-fw icon-primary" aria-hidden="true"></i><span>All Accounts</span></span>
                <span class="badge bg-light text-dark border">${typeof totalVehicleCount === 'number' ? totalVehicleCount : '-'}</span>
            </a>
        </li>
        <li><hr class="dropdown-divider"></li>
    `);

    if (!accounts.length) {
        items.push('<li class="dropdown-item text-muted">No accounts yet</li>');
    } else {
        accounts.forEach((account) => {
            const isActive = selectedAccountId === account.id;
            const defaultIcon = account.is_default ? '<i class="fa-solid fa-star fa-fw icon-right text-warning" title="Default account" aria-hidden="true"></i>' : '';
            items.push(`
                <li>
                    <a class="dropdown-item d-flex justify-content-between align-items-center ${isActive ? 'active' : ''}"
                       href="#" data-account-id="${account.id}" data-account-name="${account.name}">
                        <span class="icon-row"><i class="fa-solid fa-user fa-fw icon-primary" aria-hidden="true"></i><span>${account.name}${defaultIcon}</span></span>
                        <span class="badge bg-light text-dark border">${account.vehicle_count ?? 0}</span>
                    </a>
                </li>
            `);
        });
    }

    items.push('<li><hr class="dropdown-divider"></li>');
    items.push(`
        <li>
            <a class="dropdown-item d-flex align-items-center" href="/accounts" data-manage-accounts="true">
                <span class="icon-row"><i class="fa-solid fa-users-gear fa-fw icon-primary" aria-hidden="true"></i><span>Manage Accounts</span></span>
            </a>
        </li>
    `);

    return items.join('');
}

function rewriteAccountAwareLinks(selectedAccountId) {
    const normalizedId = selectedAccountId && selectedAccountId !== 'all' ? selectedAccountId : null;
    const accountAwareLinks = document.querySelectorAll('a[data-account-aware="true"]');

    accountAwareLinks.forEach((link) => {
        const baseHref = link.dataset.baseHref || link.getAttribute('href');
        if (!baseHref || baseHref === '#' || baseHref.toLowerCase().startsWith('javascript')) {
            return;
        }
        if (!link.dataset.baseHref) {
            link.dataset.baseHref = baseHref;
        }

        try {
            const url = new URL(link.dataset.baseHref, window.location.origin);
            if (normalizedId) {
                url.searchParams.set('accountId', normalizedId);
            } else {
                url.searchParams.delete('accountId');
            }
            const query = url.search ? url.search : '';
            link.setAttribute('href', url.pathname + query + url.hash);
        } catch (error) {
            console.warn('Unable to rewrite account-aware link:', baseHref, error);
        }
    });

    const accountAwareForms = document.querySelectorAll('form[action^="/"]:not([data-ignore-account])');
    accountAwareForms.forEach((form) => {
        const baseAction = form.dataset.baseAction || form.getAttribute('action');
        if (baseAction && !form.dataset.baseAction) {
            form.dataset.baseAction = baseAction;
        }

        if (form.dataset.baseAction) {
            try {
                const url = new URL(form.dataset.baseAction, window.location.origin);
                if (normalizedId) {
                    url.searchParams.set('accountId', normalizedId);
                } else {
                    url.searchParams.delete('accountId');
                }
                const query = url.search ? url.search : '';
                form.setAttribute('action', url.pathname + query);
            } catch (error) {
                console.warn('Unable to rewrite account-aware form action:', form.dataset.baseAction, error);
            }
        }

        let hidden = form.querySelector('input[name="accountId"][data-generated-account="true"]');
        if (!hidden) {
            hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'accountId';
            hidden.dataset.generatedAccount = 'true';
            form.appendChild(hidden);
        }
        hidden.value = normalizedId || '';
    });
}

function handleAccountSelection(accountId, accountName) {
    const isAll = !accountId || accountId === 'all';
    saveAccountIdToStorage(isAll ? null : accountId);
    setCookie(ACCOUNT_COOKIE_NAME, isAll ? 'all' : accountId);

    window.dispatchEvent(new CustomEvent('account:change', {
        detail: {
            accountId: isAll ? null : accountId,
            accountName: accountName || 'All',
        },
    }));

    const url = new URL(window.location.href);
    if (isAll) {
        url.searchParams.delete('accountId');
    } else {
        url.searchParams.set('accountId', accountId);
    }

    window.location.href = url.toString();
}

async function buildAccountDropdown(menuId, buttonId) {
    const menu = document.getElementById(menuId);
    const button = document.getElementById(buttonId);
    if (!menu || !button) return;

    try {
        const data = await fetchAccountsFromApi();
        const accounts = data.accounts || [];
        const totalVehicleCount = accounts.reduce((sum, acc) => sum + (acc.vehicle_count || 0), 0);
        const selectedAccountId = determineInitialAccountId(accounts, data.default_account_id);
        const selectedAccount = accounts.find((account) => account.id === selectedAccountId);
        const normalizedId = selectedAccountId === 'all' ? null : selectedAccountId;

        updateAccountDropdownButton(button, selectedAccount, totalVehicleCount, selectedAccountId === 'all');
        menu.innerHTML = buildAccountListMarkup(accounts, selectedAccountId, totalVehicleCount);

        if (normalizedId) {
            setCookie(ACCOUNT_COOKIE_NAME, normalizedId);
            saveAccountIdToStorage(normalizedId);
        } else {
            setCookie(ACCOUNT_COOKIE_NAME, 'all');
            saveAccountIdToStorage(null);
        }

        rewriteAccountAwareLinks(selectedAccountId);

        menu.querySelectorAll('a[data-account-id]').forEach((anchor) => {
            anchor.addEventListener('click', (event) => {
                event.preventDefault();
                const accountId = anchor.getAttribute('data-account-id');
                const accountName = anchor.getAttribute('data-account-name');
                if (!accountId) return;
                handleAccountSelection(accountId === 'all' ? 'all' : accountId, accountName);
            });
        });

        // Ensure Manage Accounts preserves selected account in query
        const manageLink = menu.querySelector('a[data-manage-accounts]');
        if (manageLink) {
            manageLink.addEventListener('click', (event) => {
                const url = new URL(manageLink.href, window.location.origin);
                const currentId = determineInitialAccountId(accounts, data.default_account_id);
                if (currentId && currentId !== 'all') {
                    url.searchParams.set('accountId', currentId);
                }
                manageLink.href = url.toString();
            });
        }
    } catch (error) {
        console.error('Unable to populate account dropdown:', error);
        button.innerHTML = `<span class="icon-row"><i class="fa-solid fa-circle-user fa-fw icon-primary" aria-hidden="true"></i><span>Accounts (offline)</span></span>`;
        menu.innerHTML = `
            <li class="dropdown-header text-muted">Unable to load accounts</li>
            <li><a class="dropdown-item" href="/accounts"><span class="icon-row"><i class="fa-solid fa-users-gear fa-fw icon-primary" aria-hidden="true"></i><span>Manage Accounts</span></span></a></li>
        `;
    }
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

document.addEventListener('DOMContentLoaded', () => {
    try {
        const currentAccountId = getSelectedAccountId();
        rewriteAccountAwareLinks(currentAccountId || 'all');
    } catch (error) {
        console.warn('Unable to initialize account-aware links on load:', error);
    }
});

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
window.initializeAccountSwitcher = initializeAccountSwitcher;
window.fetchAccountsFromApi = fetchAccountsFromApi;
window.getSelectedAccountId = getSelectedAccountId;
window.buildAccountAwareUrl = buildAccountAwareUrl;
window.rewriteAccountAwareLinks = rewriteAccountAwareLinks;

document.addEventListener('DOMContentLoaded', () => {
    try {
        const initialId = getSelectedAccountId() || (ACCOUNT_GLOBAL_CONTEXT.account_id ?? null);
        rewriteAccountAwareLinks(initialId);
    } catch (error) {
        console.warn('Unable to initialize account-aware links:', error);
    }
});

window.addEventListener('account:change', (event) => {
    if (event && event.detail) {
        rewriteAccountAwareLinks(event.detail.accountId || null);
    }
});
