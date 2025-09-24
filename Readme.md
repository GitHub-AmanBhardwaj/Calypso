# ARGO NetCDF to PostgreSQL Data Ingestion Pipeline

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## 1. Overview

This project provides a robust and efficient pipeline for parsing oceanographic data from ARGO Core profile NetCDF files and ingesting it into a structured PostgreSQL database. The goal is to transform complex, multi-dimensional scientific data into a queryable, relational format, making it accessible for analysis, visualization, and use in applications like the Calypso chatbot.

This pipeline was successfully used to process 5 years of historical ARGO data from **1999 to 2004**.

## 2. Key Features

-   **Efficient Parsing:** Reads and processes standard multi-profile ARGO NetCDF files.
-   **Relational Schema:** Creates a clean and logical database schema with separate tables for profile metadata and measurements.
-   **Data Integrity:** Includes checks to prevent duplicate profile entries.
-   **Quality Control:** Filters measurements based on the official ARGO quality control flags to ensure data reliability.
-   **Scalable:** Designed to process large directories of NetCDF files efficiently.

## 3. Project Structure

The repository is organized as follows:

```
.
├── convertor.py        # The main Python script for data ingestion
├── db_setup.sql        # SQL script to initialize the database schema
├── 5_year_data/        # Example folder for storing source NetCDF files
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
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name
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
1.  Create a new database and user.
    ```sql
    CREATE DATABASE argo_db;
    CREATE USER argo_user WITH PASSWORD 'your_secure_password';
    GRANT ALL PRIVILEGES ON DATABASE argo_db TO argo_user;
    ```
2.  Update the database connection details in the `DB_CONFIG` dictionary at the top of `convertor.py`.

**Step 4: Initialize the Database Schema**
Run the setup script using `psql`. This will create the `argo_profiles` and `ocean_measurements` tables.
```bash
psql -h localhost -d argo_db -U argo_user -f db_setup.sql
```

## 6. Usage

To run the ingestion pipeline:

1.  Place your ARGO NetCDF (`.nc`) files inside a directory (e.g., `5_year_data`).
2.  Execute the `convertor.py` script from your terminal, passing the path to your data directory as an argument.

```bash
python convertor.py ./5_year_data
```
The script will display a progress bar as it processes the files.

## 7. Database Schema

The pipeline creates two main tables:

#### `argo_profiles`
Stores the metadata for each unique float profile.
| Column | Type | Description |
| :--- | :--- | :--- |
| `profile_id` | SERIAL PRIMARY KEY | Unique identifier for each profile. |
| `platform_number` | INTEGER | The unique WMO ID of the ARGO float. |
| `cycle_number` | INTEGER | The measurement cycle number for the float. |
| `profile_timestamp` | TIMESTAMP | The date and time of the measurement. |
| `latitude` | DOUBLE PRECISION | The latitude of the measurement. |
| `longitude` | DOUBLE PRECISION | The longitude of the measurement. |

#### `ocean_measurements`
Stores the individual sensor readings for each profile.
| Column | Type | Description |
| :--- | :--- | :--- |
| `measurement_id`| SERIAL PRIMARY KEY | Unique identifier for the measurement. |
| `profile_id` | INTEGER (FOREIGN KEY)| Links to the `argo_profiles` table. |
| `pressure_dbar` | DOUBLE PRECISION | Pressure in decibars (depth). |
| `temperature_celsius`| DOUBLE PRECISION | Temperature in Celsius. |
| `salinity_psu` | DOUBLE PRECISION | Salinity in Practical Salinity Units. |

## 8. License

This project is licensed under the MIT License - see the `LICENSE` file for details.
