import os
import sys
import logging
from datetime import datetime, timedelta

import pandas as pd
import psycopg2
import xarray as xr
from tqdm import tqdm

# --- Configuration ---

# Configure logging to show progress and errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Configuration (UPDATE WITH YOUR DETAILS)
DB_CONFIG = {
    "host": "localhost",
    "database": "argo_db",
    "user": "argo_user",
    "password": "amanjeet"
}

# --- Database Management ---

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("Successfully connected to the PostgreSQL database.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Could not connect to the database: {e}")
        logging.error("Please ensure PostgreSQL is running and the DB_CONFIG details are correct.")
        sys.exit(1)

def setup_database(conn):
    """Sets up the database schema by executing the db_setup.sql script."""
    try:
        with conn.cursor() as cur:
            with open("db_setup.sql", "r") as f:
                cur.execute(f.read())
        conn.commit()
        logging.info("Database schema verified and set up successfully.")
    except Exception as e:
        logging.error(f"Failed to set up database schema: {e}")
        conn.rollback()
        sys.exit(1)

# --- Data Conversion Logic ---

class ArgoDataConverter:
    """A class to handle the conversion of ARGO NetCDF files to SQL."""

    def __init__(self, db_conn):
        self.db_conn = db_conn

    def process_file(self, file_path):
        """Processes a single NetCDF file and ingests its data into the database."""
        try:
            with xr.open_dataset(file_path, decode_times=False) as ds:
                ref_date = datetime(1950, 1, 1)

                # Each file can contain multiple profiles (measurements).
                for i in range(len(ds.N_PROF)):
                    platform_number = int(ds['PLATFORM_NUMBER'].isel(N_PROF=i).values)
                    cycle_number = int(ds['CYCLE_NUMBER'].isel(N_PROF=i).values)

                    if self._profile_exists(platform_number, cycle_number):
                        logging.debug(f"Skipping existing profile: Float {platform_number}, Cycle {cycle_number}")
                        continue

                    # Extract metadata for the current profile
                    julian_day = ds['JULD'].isel(N_PROF=i).values
                    profile_date = ref_date + timedelta(days=float(julian_day))
                    latitude = float(ds['LATITUDE'].isel(N_PROF=i).values)
                    longitude = float(ds['LONGITUDE'].isel(N_PROF=i).values)

                    profile_id = self._insert_profile_metadata(
                        platform_number, cycle_number, profile_date, latitude, longitude
                    )
                    if not profile_id:
                        continue

                    # Extract and insert measurement data for this profile
                    measurements = self._extract_measurements(ds, i, profile_id)
                    if measurements:
                        self._bulk_insert_measurements(measurements)

        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {e}")

    def _profile_exists(self, platform_number, cycle_number):
        """Checks if a profile already exists in the database to prevent duplicates."""
        with self.db_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM argo_profiles WHERE platform_number = %s AND cycle_number = %s",
                (platform_number, cycle_number)
            )
            return cur.fetchone() is not None

    def _insert_profile_metadata(self, platform, cycle, date, lat, lon):
        """Inserts profile metadata and returns the new profile_id."""
        sql = """
            INSERT INTO argo_profiles (platform_number, cycle_number, profile_timestamp, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s) RETURNING profile_id;
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute(sql, (platform, cycle, date, lat, lon))
                profile_id = cur.fetchone()[0]
                self.db_conn.commit()
                return profile_id
        except Exception as e:
            logging.error(f"Error inserting profile metadata for float {platform}, cycle {cycle}: {e}")
            self.db_conn.rollback()
            return None

    def _extract_measurements(self, ds, profile_index, profile_id):
        """Extracts measurements into a list of tuples for bulk insertion."""
        try:
            profile_data = ds.isel(N_PROF=profile_index)
            # Filter data by quality control flags ('1' and '2' are good data)
            temp = profile_data['TEMP'].where(profile_data['TEMP_QC'].isin([b'1', b'2'])).values
            psal = profile_data['PSAL'].where(profile_data['PSAL_QC'].isin([b'1', b'2'])).values
            pres = profile_data['PRES'].where(profile_data['PRES_QC'].isin([b'1', b'2'])).values

            df = pd.DataFrame({
                'pressure_dbar': pres,
                'temperature_celsius': temp,
                'salinity_psu': psal,
            })
            
            df.dropna(subset=['pressure_dbar'], inplace=True)
            df['profile_id'] = profile_id
            df = df[['profile_id', 'pressure_dbar', 'temperature_celsius', 'salinity_psu']]

            # Convert to list of tuples, replacing pandas NaNs with None for the database
            return [tuple(row) for row in df.where(pd.notna(df), None).itertuples(index=False)]
        except Exception as e:
            logging.warning(f"Could not extract valid measurements for profile_id {profile_id}: {e}")
            return []

    def _bulk_insert_measurements(self, measurements):
        """Inserts a batch of measurements efficiently."""
        sql = "INSERT INTO ocean_measurements (profile_id, pressure_dbar, temperature_celsius, salinity_psu) VALUES %s"
        try:
            from psycopg2.extras import execute_values
            with self.db_conn.cursor() as cur:
                execute_values(cur, sql, measurements)
            self.db_conn.commit()
        except Exception as e:
            logging.error(f"Error during bulk insert of measurements: {e}")
            self.db_conn.rollback()

def find_netcdf_files(directory):
    """Finds all .nc files in a directory recursively."""
    nc_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".nc"):
                nc_files.append(os.path.join(root, file))
    return nc_files

def main():
    """Main function to run the conversion tool."""
    if len(sys.argv) != 2:
        print("Usage: python convert_netcdf_to_sql.py <path_to_argo_data_directory>")
        sys.exit(1)

    data_directory = sys.argv[1]
    if not os.path.isdir(data_directory):
        print(f"Error: Directory not found at '{data_directory}'")
        sys.exit(1)

    db_conn = get_db_connection()
    setup_database(db_conn)

    nc_files = find_netcdf_files(data_directory)
    if not nc_files:
        logging.warning(f"No NetCDF (.nc) files found in {data_directory}. Exiting.")
        sys.exit(0)

    logging.info(f"Found {len(nc_files)} NetCDF files to process.")
    converter = ArgoDataConverter(db_conn)

    for file_path in tqdm(nc_files, desc="Converting NetCDF to SQL"):
        converter.process_file(file_path)

    db_conn.close()
    logging.info("Data conversion complete. Database connection closed.")

if __name__ == "__main__":
    main()
