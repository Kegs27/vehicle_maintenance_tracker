# Vehicle Maintenance Tracker

A modern, web-based application for tracking vehicle maintenance records with CSV import capabilities from Google Sheets.

## Features

- **Vehicle Management**: Add and edit vehicles with year, make, model, and optional VIN
- **Maintenance Records**: Track maintenance activities with date, mileage, description, and cost
- **CSV Import**: Import maintenance data from Google Sheets with flexible parsing
- **Modern UI**: Clean, responsive design that works on all devices
- **Data Validation**: Robust parsing for various date, mileage, and cost formats

## CSV Import Support

The application supports importing CSV files with the following column structure:

- **Required**: `description`, `mileage`, `date`
- **Optional**: `cost`

### Supported Formats

- **Dates**: M/D/YYYY, M/Y, M-D-YYYY (e.g., 9/10/2024, 9-10-2024)
- **Mileage**: 145,772, 145k, 145000
- **Costs**: $1,234.56, (123.45), 123.45

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Access the Application

Open your browser and navigate to: `http://localhost:8000`

## Usage

### Adding a Vehicle

1. Click "Add Vehicle" from the home page
2. Fill in the vehicle details (year, make, model, optional VIN)
3. Click "Add Vehicle"

### Importing CSV Data

1. Click "Import CSV" from the navigation
2. Select the vehicle for the maintenance records
3. Upload your Google Sheets CSV file
4. Review the import results

### Adding Maintenance Records

1. Click "Add Maintenance" from the maintenance page
2. Select a vehicle
3. Fill in the maintenance details
4. Click "Add Record"

## Project Structure

```
vehicle_maintenance/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # Database models
│   ├── database.py      # Database configuration
│   ├── importer.py      # CSV import functionality
│   └── templates/       # HTML templates
│       ├── index.html
│       ├── import.html
│       ├── import_result.html
│       ├── vehicles_list.html
│       ├── vehicle_form.html
│       ├── maintenance_list.html
│       └── maintenance_form.html
├── requirements.txt
└── README.md
```

## Technology Stack

- **Backend**: FastAPI (Python web framework)
- **Database**: SQLite with SQLModel ORM
- **Frontend**: Bootstrap 5 + Font Awesome
- **Templates**: Jinja2
- **CSV Processing**: Python built-in csv module with custom parsers

## Database

The application uses SQLite for data storage. The database file (`vehicle_maintenance.db`) is automatically created when you first run the application.

## Contributing

This is a personal project, but feel free to suggest improvements or report issues.

## License

This project is open source and available under the MIT License.
