USE wildfire_historical;

CREATE TABLE historical_fire_incidents (
    id VARCHAR(36) PRIMARY KEY,
    fire_name VARCHAR(200),
    discovery_date DATE NOT NULL,
    fire_year INTEGER NOT NULL,
    fire_size_acres DECIMAL(10,2),
    fire_size_class VARCHAR(1),
    latitude DECIMAL(10,6) NOT NULL,
    longitude DECIMAL(11,6) NOT NULL,
    state VARCHAR(2),
    county VARCHAR(50),
    cause_description VARCHAR(100),
    reporting_agency VARCHAR(10),
    archive_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100),
    INDEX idx_hist_year (fire_year),
    INDEX idx_hist_state (state),
    INDEX idx_hist_coords (latitude, longitude)
);

CREATE TABLE seasonal_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INTEGER NOT NULL,
    season ENUM('Spring', 'Summer', 'Fall', 'Winter') NOT NULL,
    state VARCHAR(2),
    total_fires INTEGER DEFAULT 0,
    total_acres DECIMAL(15,2) DEFAULT 0,
    avg_fire_size DECIMAL(10,2) DEFAULT 0,
    max_fire_size DECIMAL(10,2) DEFAULT 0,
    dominant_cause VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_year_season_state (year, season, state)
);

CREATE TABLE fire_trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    state VARCHAR(2),
    fire_count INTEGER DEFAULT 0,
    total_acres DECIMAL(15,2) DEFAULT 0,
    avg_response_time INTEGER,
    suppression_cost DECIMAL(15,2),
    weather_severity_index DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trends_year_month (year, month),
    INDEX idx_trends_state (state)
);

CREATE TABLE risk_assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id VARCHAR(50) NOT NULL,
    state VARCHAR(2) NOT NULL,
    county VARCHAR(50),
    risk_level ENUM('Low', 'Moderate', 'High', 'Extreme') NOT NULL,
    risk_score DECIMAL(5,2) NOT NULL,
    primary_risk_factors JSON,
    assessment_date DATE NOT NULL,
    valid_until DATE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_risk_region (region_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_risk_date (assessment_date)
);

CREATE TABLE climate_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id VARCHAR(50) NOT NULL,
    latitude DECIMAL(10,6) NOT NULL,
    longitude DECIMAL(11,6) NOT NULL,
    date DATE NOT NULL,
    temperature_avg DECIMAL(5,2),
    temperature_max DECIMAL(5,2),
    temperature_min DECIMAL(5,2),
    humidity_avg DECIMAL(5,2),
    wind_speed_avg DECIMAL(5,2),
    precipitation DECIMAL(6,2),
    drought_index DECIMAL(5,2),
    fire_weather_index DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_climate_location_date (location_id, date),
    INDEX idx_climate_coords (latitude, longitude)
);

INSERT INTO seasonal_statistics (year, season, state, total_fires, total_acres, avg_fire_size, dominant_cause) VALUES
(2023, 'Summer', 'CA', 4253, 1847362.5, 434.2, 'Lightning'),
(2023, 'Fall', 'CA', 2156, 892341.8, 414.1, 'Equipment Use'),
(2023, 'Spring', 'CA', 1832, 456789.3, 249.3, 'Debris Burning'),
(2023, 'Winter', 'CA', 543, 123456.7, 227.4, 'Campfire'),
(2023, 'Summer', 'TX', 3421, 1234567.9, 361.0, 'Lightning'),
(2023, 'Fall', 'TX', 1987, 567890.1, 285.9, 'Equipment Use'),
(2023, 'Spring', 'TX', 2341, 789012.3, 337.2, 'Debris Burning'),
(2023, 'Winter', 'TX', 892, 234567.8, 263.1, 'Miscellaneous');

INSERT INTO risk_assessments (region_id, state, county, risk_level, risk_score, primary_risk_factors, assessment_date, valid_until) VALUES
('CA_001', 'CA', 'Los Angeles', 'High', 7.8, '["drought_conditions", "high_temperature", "low_humidity", "dense_vegetation"]', '2024-01-15', '2024-07-15'),
('CA_002', 'CA', 'Riverside', 'Extreme', 9.2, '["extreme_drought", "heat_wave", "santa_ana_winds", "fuel_accumulation"]', '2024-01-15', '2024-07-15'),
('TX_001', 'TX', 'Harris', 'Moderate', 5.4, '["moderate_drought", "urban_interface", "equipment_use"]', '2024-01-15', '2024-07-15'),
('FL_001', 'FL', 'Miami-Dade', 'Low', 3.2, '["high_humidity", "frequent_precipitation"]', '2024-01-15', '2024-07-15'),
('OR_001', 'OR', 'Jackson', 'High', 8.1, '["dry_conditions", "dense_forest", "lightning_activity"]', '2024-01-15', '2024-07-15');