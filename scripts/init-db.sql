-- DeviceWatch Database Initialization Script
-- This script sets up the initial database structure

-- Create database if it doesn't exist
-- (This is handled by the POSTGRES_DB environment variable)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE device_status AS ENUM ('online', 'offline', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
-- (These will be created after tables are created by Alembic)

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE devicewatch TO devicewatch;
GRANT ALL PRIVILEGES ON SCHEMA public TO devicewatch;

-- Set timezone
SET timezone = 'UTC';

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

