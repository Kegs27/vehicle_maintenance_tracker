// Export Data functionality for all pages
// This file provides consistent export functionality across the application

// Global export functions
function exportAllVehicles() {
    // Export all vehicles to CSV
    window.location.href = '/api/export/vehicles';
}

function exportAllVehiclesToPDF() {
    // Export all vehicles to PDF
    window.location.href = '/api/export/vehicles/pdf';
}

function exportAllMaintenance() {
    // Export all maintenance records to CSV
    window.location.href = '/api/export/maintenance';
}

function exportAllMaintenanceToPDF() {
    // Export all maintenance records to PDF
    window.location.href = '/api/export/maintenance/pdf';
}

function exportSingleVehicle() {
    console.log('exportSingleVehicle called - should show both vehicle and maintenance options');
    // Show vehicle selection modal for single vehicle export with both vehicle and maintenance options
    showVehicleSelectionModal('single');
}

function exportSingleVehicleMaintenance() {
    // Show vehicle selection modal for single vehicle maintenance export
    showVehicleSelectionModal('maintenance');
}

function exportToPDF() {
    // Show vehicle selection modal for PDF export
    showVehicleSelectionModal('pdf');
}

function showVehicleSelectionModal(exportType) {
    console.log('showVehicleSelectionModal called with exportType:', exportType);
    // Create modal for vehicle selection
    const modalHtml = `
        <div class="modal fade" id="vehicleSelectionModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-download me-2"></i>Select Vehicle to Export
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted mb-3">Choose a vehicle to export:</p>
                        <div id="vehicleList">
                            <!-- Vehicles will be loaded here -->
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('vehicleSelectionModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Load vehicles
    loadVehiclesForExport(exportType);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('vehicleSelectionModal'));
    modal.show();
}

function loadVehiclesForExport(exportType) {
    // Fetch vehicles from the API
    fetch('/vehicles')
        .then(response => response.text())
        .then(html => {
            // Parse HTML to extract vehicle data
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const vehicleRows = doc.querySelectorAll('[data-vehicle-id]');
            
            const vehicleList = document.getElementById('vehicleList');
            vehicleList.innerHTML = '';
            
            vehicleRows.forEach((row, index) => {
                const vehicleId = row.getAttribute('data-vehicle-id');
                
                // Find the vehicle name in the link within the first column
                const firstTd = row.querySelector('td:first-child');
                const vehicleNameLink = firstTd ? firstTd.querySelector('a') : null;
                
                let vehicleName = 'Unknown Vehicle';
                if (vehicleNameLink) {
                    // Clean up the text content - remove the external link icon text
                    vehicleName = vehicleNameLink.textContent.trim();
                    // Remove the external link icon text if present
                    vehicleName = vehicleName.replace(/\s*<i.*?<\/i>\s*/g, '').trim();
                }
                
                // Debug logging
                console.log(`Row ${index}: vehicleId=${vehicleId}, vehicleName="${vehicleName}"`);
                console.log(`First TD:`, firstTd);
                console.log(`Vehicle name link:`, vehicleNameLink);
                
                const vehicleItem = document.createElement('div');
                vehicleItem.className = 'form-check mb-2';
                vehicleItem.innerHTML = `
                    <input class="form-check-input" type="radio" name="selectedVehicle" value="${vehicleId}" id="vehicle${vehicleId}">
                    <label class="form-check-label" for="vehicle${vehicleId}">
                        ${vehicleName}
                    </label>
                `;
                vehicleList.appendChild(vehicleItem);
            });
            
            // Add export buttons based on export type
            const exportBtnContainer = document.createElement('div');
            exportBtnContainer.className = 'mt-3';
            
            console.log('Setting up export buttons for exportType:', exportType);
            if (exportType === 'maintenance') {
                console.log('Setting up maintenance export buttons');
                exportBtnContainer.innerHTML = `
                    <button class="btn btn-success me-2" onclick="exportMaintenanceRecords()">
                        <i class="fas fa-file-csv me-2"></i>Export to CSV
                    </button>
                    <button class="btn btn-danger" onclick="exportMaintenanceRecordsToPDF()">
                        <i class="fas fa-file-pdf me-2"></i>Export to PDF
                    </button>
                `;
            } else if (exportType === 'pdf') {
                exportBtnContainer.innerHTML = `
                    <button class="btn btn-success me-2" onclick="exportVehicleToCSV()">
                        <i class="fas fa-file-csv me-2"></i>Export to CSV
                    </button>
                    <button class="btn btn-danger" onclick="exportVehicleToPDF()">
                        <i class="fas fa-file-pdf me-2"></i>Export to PDF
                    </button>
                `;
            } else if (exportType === 'single') {
                console.log('Setting up single vehicle export buttons - maintenance only');
                // Single vehicle export - show only maintenance options (since vehicle info is included)
                exportBtnContainer.innerHTML = `
                    <div class="text-center">
                        <h6 class="text-muted mb-3">Export Maintenance Records for Selected Vehicle</h6>
                        <p class="text-muted small mb-3">Includes vehicle information with each maintenance record</p>
                        <button class="btn btn-success me-2" onclick="exportMaintenanceRecords()">
                            <i class="fas fa-file-csv me-2"></i>Export to CSV
                        </button>
                        <button class="btn btn-danger" onclick="exportMaintenanceRecordsToPDF()">
                            <i class="fas fa-file-pdf me-2"></i>Export to PDF
                        </button>
                    </div>
                `;
            } else {
                // Default single vehicle export (uses API endpoint)
                exportBtnContainer.innerHTML = `
                    <button class="btn btn-success me-2" onclick="exportVehicleToCSV()">
                        <i class="fas fa-file-csv me-2"></i>Export to CSV
                    </button>
                    <button class="btn btn-danger" onclick="exportVehicleToPDF()">
                        <i class="fas fa-file-pdf me-2"></i>Export to PDF
                    </button>
                `;
            }
            
            vehicleList.appendChild(exportBtnContainer);
        })
        .catch(error => {
            console.error('Error loading vehicles:', error);
            document.getElementById('vehicleList').innerHTML = '<p class="text-danger">Error loading vehicles. Please try again.</p>';
        });
}

// Export functions for the buttons
function exportMaintenanceRecords() {
    console.log('exportMaintenanceRecords called!');
    const selectedVehicle = document.querySelector('input[name="selectedVehicle"]:checked');
    if (selectedVehicle) {
        const vehicleId = selectedVehicle.value;
        console.log(`Exporting maintenance records for vehicle ID: ${vehicleId}`);
        window.location.href = `/api/export/maintenance?vehicle_id=${vehicleId}`;
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('vehicleSelectionModal'));
        modal.hide();
    } else {
        alert('Please select a vehicle to export.');
    }
}

function exportMaintenanceRecordsToPDF() {
    const selectedVehicle = document.querySelector('input[name="selectedVehicle"]:checked');
    if (selectedVehicle) {
        const vehicleId = selectedVehicle.value;
        window.location.href = `/api/export/maintenance/pdf?vehicle_id=${vehicleId}`;
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('vehicleSelectionModal'));
        modal.hide();
    } else {
        alert('Please select a vehicle to export.');
    }
}

function exportVehicleToCSV() {
    const selectedVehicle = document.querySelector('input[name="selectedVehicle"]:checked');
    if (selectedVehicle) {
        const vehicleId = selectedVehicle.value;
        window.location.href = `/api/export/vehicles?vehicle_ids=${vehicleId}`;
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('vehicleSelectionModal'));
        modal.hide();
    } else {
        alert('Please select a vehicle to export.');
    }
}

function exportVehicleToPDF() {
    const selectedVehicle = document.querySelector('input[name="selectedVehicle"]:checked');
    if (selectedVehicle) {
        const vehicleId = selectedVehicle.value;
        // Export single vehicle to PDF
        window.location.href = `/api/export/vehicles/pdf?vehicle_ids=${vehicleId}`;
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('vehicleSelectionModal'));
        modal.hide();
    } else {
        alert('Please select a vehicle to export.');
    }
}

// Initialize export functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Export Data functionality loaded');
});
