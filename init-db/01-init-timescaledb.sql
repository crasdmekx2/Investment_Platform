-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verify TimescaleDB is installed
SELECT default_version, installed_version 
FROM pg_available_extensions 
WHERE name = 'timescaledb';

