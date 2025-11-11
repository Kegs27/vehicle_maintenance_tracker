// Import Data functionality for all pages
// This file provides consistent import functionality across the application

// Global import functions
function showImportModal() {
    // Create modal for import options
    const modalHtml = `
        <div class="modal fade" id="importModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <span class="icon-row"><i class="fa-solid fa-upload me-2"></i><span>Import Data</span></span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted mb-3">Import maintenance records from CSV files:</p>
                        <div class="d-grid gap-2">
                            <a href="/import" class="btn-action btn-action-primary text-center">
                                <i class="fa-solid fa-upload me-1"></i>
                                <span>Import CSV Data</span>
                            </a>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-action btn-action-outline" data-bs-dismiss="modal">
                            <i class="fa-solid fa-xmark me-1"></i>Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('importModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('importModal'));
    modal.show();
}

// Initialize import functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Import Data functionality loaded');
});
