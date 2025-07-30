CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'analyst', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE fire_causes (
    code INTEGER PRIMARY KEY,
    description VARCHAR(100) NOT NULL,
    category VARCHAR(50)
);

CREATE TABLE reporting_agencies (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    agency_type VARCHAR(50),
    contact_info JSONB
);

CREATE TABLE fire_incidents (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    fire_name VARCHAR(200),
    discovery_date DATE NOT NULL,
    discovery_time TIME,
    contained_date DATE,
    fire_year INTEGER NOT NULL,
    fire_size_acres DECIMAL(10,2),
    fire_size_class VARCHAR(1) CHECK (fire_size_class IN ('A', 'B', 'C', 'D', 'E', 'F', 'G')),
    latitude DECIMAL(10,6) NOT NULL,
    longitude DECIMAL(11,6) NOT NULL,
    state VARCHAR(2),
    county VARCHAR(50),
    cause_code INTEGER REFERENCES fire_causes(code),
    cause_description VARCHAR(100),
    reporting_agency VARCHAR(10) REFERENCES reporting_agencies(code),
    reporting_unit VARCHAR(10),
    nwcg_reporting_agency VARCHAR(10),
    source_system VARCHAR(50),
    source_system_type VARCHAR(50),
    local_fire_report_id VARCHAR(50),
    local_incident_id VARCHAR(50),
    complex_name VARCHAR(200),
    fire_mgmt_complexity VARCHAR(50),
    suppression_method VARCHAR(50),
    weather_conditions JSONB,
    fuel_model VARCHAR(50),
    slope_class VARCHAR(10),
    aspect_direction VARCHAR(10),
    elevation_feet INTEGER,
    owner_code INTEGER,
    owner_description VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    fire_incident_id VARCHAR(36) REFERENCES fire_incidents(id),
    date DATE NOT NULL,
    temperature_max DECIMAL(5,2),
    temperature_min DECIMAL(5,2),
    humidity DECIMAL(5,2),
    wind_speed DECIMAL(5,2),
    wind_direction INTEGER,
    precipitation DECIMAL(5,2),
    pressure DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(50) NOT NULL,
    fire_incident_id VARCHAR(36) REFERENCES fire_incidents(id),
    cluster_id INTEGER,
    prediction_value DECIMAL(10,2),
    confidence_score DECIMAL(3,2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fire_incidents_year ON fire_incidents(fire_year);
CREATE INDEX idx_fire_incidents_state ON fire_incidents(state);
CREATE INDEX idx_fire_incidents_size_class ON fire_incidents(fire_size_class);
CREATE INDEX idx_fire_incidents_discovery_date ON fire_incidents(discovery_date);
CREATE INDEX idx_fire_incidents_coords ON fire_incidents(latitude, longitude);
CREATE INDEX idx_weather_data_date ON weather_data(date);
CREATE INDEX idx_analysis_results_type ON analysis_results(analysis_type);

INSERT INTO fire_causes (code, description, category) VALUES
(1, 'Lightning', 'Natural'),
(2, 'Equipment Use', 'Human'),
(3, 'Smoking', 'Human'),
(4, 'Campfire', 'Human'),
(5, 'Debris Burning', 'Human'),
(6, 'Railroad', 'Human'),
(7, 'Arson', 'Human'),
(8, 'Children', 'Human'),
(9, 'Miscellaneous', 'Human'),
(10, 'Fireworks', 'Human'),
(11, 'Powerline', 'Human'),
(12, 'Structure', 'Human'),
(13, 'Missing/Undefined', 'Unknown');

INSERT INTO reporting_agencies (code, name, agency_type) VALUES
('FS', 'US Forest Service', 'Federal'),
('NPS', 'National Park Service', 'Federal'),
('BLM', 'Bureau of Land Management', 'Federal'),
('FWS', 'Fish and Wildlife Service', 'Federal'),
('BIA', 'Bureau of Indian Affairs', 'Federal'),
('ST', 'State', 'State'),
('C&L', 'County and Local', 'Local'),
('PVT', 'Private', 'Private');