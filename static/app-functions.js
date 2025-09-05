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
