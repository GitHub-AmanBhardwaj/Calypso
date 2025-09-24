-- This script creates the necessary tables for storing processed ARGO float data.

-- Table to store metadata for each individual ARGO profile.
CREATE TABLE IF NOT EXISTS argo_profiles (
    profile_id SERIAL PRIMARY KEY,
    platform_number INT NOT NULL,
    cycle_number INT NOT NULL,
    profile_timestamp TIMESTAMP WITH TIME ZONE,
    latitude REAL,
    longitude REAL,
    -- Add a unique constraint to prevent duplicate profile entries
    UNIQUE (platform_number, cycle_number)
);

-- Table to store the detailed measurements for each profile.
CREATE TABLE IF NOT EXISTS ocean_measurements (
    measurement_id SERIAL PRIMARY KEY,
    profile_id INT REFERENCES argo_profiles(profile_id) ON DELETE CASCADE,
    pressure_dbar REAL,
    temperature_celsius REAL,
    salinity_psu REAL
);

-- Create indexes for faster querying.
CREATE INDEX IF NOT EXISTS idx_profile_id ON ocean_measurements(profile_id);
CREATE INDEX IF NOT EXISTS idx_platform_number ON argo_profiles(platform_number);