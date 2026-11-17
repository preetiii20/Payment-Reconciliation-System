# Payment Reconciliation System

A web application built with Streamlit that compares payment platform transaction records with bank settlement records to identify and explain discrepancies.

## Project Objective

This system addresses a critical need in financial operations: reconciling payments across multiple sources. It:
- Compares payment platform transactions with bank settlements
- Identifies discrepancies (missing transactions, duplicates, timing mismatches, refunds)
- Explains the root cause of each discrepancy
- Visualizes reconciliation data for easy analysis

## Technology Stack

- **Python 3.9+**: Core language for financial calculations and data processing
- **Streamlit**: Interactive web interface for easy navigation and visualization
- **Pandas**: DataFrames for dataset processing and manipulation
- **Plotly**: Interactive charts and dashboards
- **Python Decimal**: Precise financial calculations (avoiding floating-point errors)
- **Pytest**: Automated testing framework with coverage reporting

## Key Features

1. **Data Import**: Load payment platform and bank settlement datasets
2. **Reconciliation Engine**: Match transactions and identify discrepancies
3. **Scenario Handling**: Addresses mandatory reconciliation scenarios:
   - Timing differences (payment in November, settlement in December)
   - Rounding differences in aggregated amounts
   - Duplicate entries detection
   - Orphaned refunds (refunds without matching original transactions)
4. **Dashboard**: Visual analysis of reconciliation results
5. **Detailed Reports**: Explanation of each discrepancy

## Project Structure

```
payment-reconciliation/
├── app.py                 # Main Streamlit application entry point
├── reconciliation.py      # Core reconciliation logic and matching engine
├── data_generator.py      # Sample dataset generation for testing
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── ASSUMPTIONS.md         # Project assumptions and constraints
├── tests/
│   └── test_reconciliation.py  # Unit and integration tests
└── data/                  # Directory for data files (CSV, JSON)
```

## Getting Started

### Installation

1. Clone or navigate to the project directory:
```bash
cd payment-reconciliation
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Running Tests

Execute the test suite with coverage:
```bash
pytest tests/ -v --cov=.
```

Or run tests without coverage:
```bash
pytest tests/ -v
```

## Architecture Overview

### app.py
- Streamlit interface and user interactions
- File upload handling for datasets
- Dashboard display and visualizations

### reconciliation.py
- Core reconciliation logic
- Transaction matching algorithm
- Discrepancy detection and classification
- Uses Decimal for precise financial calculations

### data_generator.py
- Creates sample datasets with realistic scenarios
- Generates test data with intentional discrepancies
- Supports CSV and JSON export formats

### tests/test_reconciliation.py
- Unit tests for reconciliation functions
- Tests for each mandatory scenario
- Integration tests for end-to-end workflows

## Development Notes

- No external databases required (file-based storage)
- No paid APIs or LLM integration in financial calculations
- All financial calculations use Python Decimal for precision
- Sample data includes all mandatory reconciliation scenarios

## Next Steps

1. ✅ Project initialization (completed)
2. ⏳ Implement data generator with sample scenarios
3. ⏳ Develop reconciliation engine
4. ⏳ Create Streamlit UI
5. ⏳ Add comprehensive tests
