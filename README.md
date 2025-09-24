# ARGO NetCDF to PostgreSQL Data Ingestion Pipeline

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## 1. Overview

This project provides a robust and efficient pipeline for parsing oceanographic data from ARGO Core profile NetCDF files and ingesting it into a structured PostgreSQL database. The goal is to transform complex, multi-dimensional scientific data into a queryable, relational format, making it accessible for analysis and visualization.

## 2. Key Features

-   **Efficient Parsing:** Reads and processes standard multi-profile ARGO NetCDF files using `xarray`.
-   **Relational Schema:** Creates a clean and logical database schema from the `db_setup.sql` file.
-   **Data Integrity:** Includes a `_profile_exists` function to check for duplicates based on platform and cycle number before insertion.
-   **Quality Control:** Filters measurements based on official ARGO quality control flags (`TEMP_QC`, `PSAL_QC`, etc.) to ensure data reliability.
-   **Bulk Insertion:** Uses `psycopg2.extras.execute_values` for efficient batch insertion of measurement data.

## 3. Project Structure

The repository is organized as follows:

```
.
├── convertor.py        # The main Python script for data ingestion
├── db_setup.sql        # SQL script to initialize the database schema
├── requirements.txt    # A file listing the required Python libraries
└── README.md           # This documentation file
```

## 4. Prerequisites

Before you begin, ensure you have the following installed:
-   Python 3.9 or higher
-   PostgreSQL 14 or higher
-   Git

## 5. Installation and Setup

Follow these steps to set up the environment and database.

**Step 1: Clone the Repository**
```bash
git clone [https://github.com/GitHub-AmanBhardwaj/Calypso.git](https://github.com/GitHub-AmanBhardwaj/Calypso.git)
cd Calypso
```

**Step 2: Install Python Dependencies**
It is recommended to use a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```
*Your `requirements.txt` file should contain:*
```
psycopg2-binary
xarray
pandas
tqdm
netcdf4
```

**Step 3: Configure PostgreSQL**
1.  Create a new database and user that match the script's configuration.
    ```sql
    CREATE DATABASE argo_db;
    CREATE USER argo_user WITH PASSWORD 'amanjeet';
    GRANT ALL PRIVILEGES ON DATABASE argo_db TO argo_user;
    ```
2.  The connection details are configured in the `DB_CONFIG` dictionary within `convertor.py`.

**Step 4: Initialize the Database Schema**
Run the setup script using `psql`. This will create the necessary tables and indexes.
```bash
psql -h localhost -d argo_db -U argo_user -f db_setup.sql
```

## 6. Usage

To run the ingestion pipeline:

1.  Place your ARGO NetCDF (`.nc`) files inside a directory.
2.  Execute the `convertor.py` script from your terminal, passing the path to your data directory as a command-line argument.

```bash
python convertor.py /path/to/your/data_folder
```
The script will display a progress bar as it processes the files.

## 7. Database Schema

The pipeline creates two main tables as defined in `db_setup.sql`.

#### `argo_profiles`
Stores the metadata for each unique float profile.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `profile_id` | SERIAL | PRIMARY KEY | Unique identifier for each profile. |
| `platform_number` | INT | NOT NULL | The unique WMO ID of the ARGO float. |
| `cycle_number` | INT | NOT NULL | The measurement cycle number for the float. |
| `profile_timestamp` | TIMESTAMP WITH TIME ZONE | | The date and time of the measurement. |
| `latitude` | REAL | | The latitude of the measurement. |
| `longitude` | REAL | | The longitude of the measurement. |
*A `UNIQUE` constraint is applied to `(platform_number, cycle_number)` to prevent duplicates.*

#### `ocean_measurements`
Stores the individual sensor readings for each profile.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `measurement_id`| SERIAL | PRIMARY KEY | Unique identifier for the measurement. |
| `profile_id` | INT | FOREIGN KEY | Links to the `argo_profiles` table. |
| `pressure_dbar` | REAL | | Pressure in decibars (depth). |
| `temperature_celsius`| REAL | | Temperature in Celsius. |
| `salinity_psu` | REAL | | Salinity in Practical Salinity Units. |
*Indexes are created on `profile_id` and `platform_number` for faster query performance.*

## 8. License

This project is licensed under the MIT License.
