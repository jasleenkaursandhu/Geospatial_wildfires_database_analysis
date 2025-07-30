import pandas as pd
import psycopg2
import pymysql
from sqlalchemy import create_engine
import os
from datetime import datetime
import uuid
import json

def load_wildfire_data():
    try:
        df = pd.read_csv('data/FW_Veg_Rem_Combined.csv')
        return df
    except FileNotFoundError:
        df = pd.read_csv('data/wildfire_data.csv')
        return df

def create_connections():
    postgres_engine = create_engine(
        'postgresql://wildfire_user:secure_password@localhost:5432/wildfire_db'
    )
    
    mysql_engine = create_engine(
        'mysql+pymysql://historical_user:historical_password@localhost:3306/wildfire_historical'
    )
    
    return postgres_engine, mysql_engine

def clean_and_transform_data(df):
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    
    column_mapping = {
        'FOD_ID': 'local_fire_report_id',
        'FPA_ID': 'local_incident_id',
        'SOURCE_SYSTEM_TYPE': 'source_system_type',
        'SOURCE_SYSTEM': 'source_system',
        'NWCG_REPORTING_AGENCY': 'nwcg_reporting_agency',
        'NWCG_REPORTING_UNIT_ID': 'reporting_unit',
        'NWCG_REPORTING_UNIT_NAME': 'reporting_unit_name',
        'SOURCE_REPORTING_UNIT': 'source_reporting_unit',
        'SOURCE_REPORTING_UNIT_NAME': 'source_reporting_unit_name',
        'LOCAL_FIRE_REPORT_ID': 'local_fire_report_id',
        'LOCAL_INCIDENT_ID': 'local_incident_id',
        'FIRE_CODE': 'fire_code',
        'FIRE_NAME': 'fire_name',
        'ICS_209_INCIDENT_NUMBER': 'ics_209_incident_number',
        'ICS_209_NAME': 'ics_209_name',
        'MTBS_ID': 'mtbs_id',
        'MTBS_FIRE_NAME': 'mtbs_fire_name',
        'COMPLEX_NAME': 'complex_name',
        'FIRE_YEAR': 'fire_year',
        'DISCOVERY_DATE': 'discovery_date',
        'DISCOVERY_DOY': 'discovery_doy',
        'DISCOVERY_TIME': 'discovery_time',
        'STAT_CAUSE_CODE': 'cause_code',
        'STAT_CAUSE_DESCR': 'cause_description',
        'CONT_DATE': 'contained_date',
        'CONT_DOY': 'contained_doy',
        'CONT_TIME': 'contained_time',
        'FIRE_SIZE': 'fire_size_acres',
        'FIRE_SIZE_CLASS': 'fire_size_class',
        'LATITUDE': 'latitude',
        'LONGITUDE': 'longitude',
        'OWNER_CODE': 'owner_code',
        'OWNER_DESCR': 'owner_description',
        'STATE': 'state',
        'COUNTY': 'county',
        'FIPS_CODE': 'fips_code',
        'FIPS_NAME': 'fips_name'
    }
    
    df_renamed = df.rename(columns=column_mapping)
    
    df_renamed['discovery_date'] = pd.to_datetime(df_renamed['discovery_date'], errors='coerce')
    df_renamed['contained_date'] = pd.to_datetime(df_renamed['contained_date'], errors='coerce')
    
    df_renamed['fire_size_acres'] = pd.to_numeric(df_renamed['fire_size_acres'], errors='coerce')
    df_renamed['latitude'] = pd.to_numeric(df_renamed['latitude'], errors='coerce')
    df_renamed['longitude'] = pd.to_numeric(df_renamed['longitude'], errors='coerce')
    
    required_columns = [
        'id', 'fire_name', 'discovery_date', 'fire_year', 'fire_size_acres',
        'fire_size_class', 'latitude', 'longitude', 'state', 'county',
        'cause_code', 'cause_description', 'reporting_agency'
    ]
    
    for col in required_columns:
        if col not in df_renamed.columns:
            df_renamed[col] = None
    
    df_cleaned = df_renamed[required_columns].copy()
    df_cleaned = df_cleaned.dropna(subset=['latitude', 'longitude', 'fire_year'])
    
    return df_cleaned

def migrate_to_postgres(df, postgres_engine):
    df_postgres = df.copy()
    
    df_postgres['created_at'] = datetime.utcnow()
    df_postgres['updated_at'] = datetime.utcnow()
    
    batch_size = 1000
    total_rows = len(df_postgres)
    
    for i in range(0, total_rows, batch_size):
        batch = df_postgres.iloc[i:i + batch_size]
        batch.to_sql('fire_incidents', postgres_engine, if_exists='append', index=False, method='multi')
        print(f"Inserted batch {i//batch_size + 1}/{(total_rows//batch_size) + 1}")

def migrate_to_mysql(df, mysql_engine):
    df_historical = df.copy()
    
    df_historical['archive_date'] = datetime.utcnow()
    df_historical['data_source'] = 'Legacy Migration'
    
    columns_for_mysql = [
        'id', 'fire_name', 'discovery_date', 'fire_year', 'fire_size_acres',
        'fire_size_class', 'latitude', 'longitude', 'state', 'county',
        'cause_description', 'reporting_agency', 'archive_date', 'data_source'
    ]
    
    df_mysql = df_historical[columns_for_mysql].copy()
    
    batch_size = 1000
    total_rows = len(df_mysql)
    
    for i in range(0, total_rows, batch_size):
        batch = df_mysql.iloc[i:i + batch_size]
        batch.to_sql('historical_fire_incidents', mysql_engine, if_exists='append', index=False, method='multi')
        print(f"Inserted historical batch {i//batch_size + 1}/{(total_rows//batch_size) + 1}")

def generate_seasonal_stats(df, mysql_engine):
    seasonal_stats = []
    
    df['season'] = df['discovery_date'].dt.month.map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    })
    
    grouped = df.groupby(['fire_year', 'season', 'state']).agg({
        'id': 'count',
        'fire_size_acres': ['sum', 'mean', 'max'],
        'cause_description': lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown'
    }).reset_index()
    
    grouped.columns = ['year', 'season', 'state', 'total_fires', 'total_acres', 'avg_fire_size', 'max_fire_size', 'dominant_cause']
    
    grouped['created_at'] = datetime.utcnow()
    
    grouped.to_sql('seasonal_statistics', mysql_engine, if_exists='append', index=False, method='multi')
    print(f"Generated seasonal statistics for {len(grouped)} records")

def main():
    print("Starting wildfire data migration...")
    
    df = load_wildfire_data()
    print(f"Loaded {len(df)} records from source data")
    
    df_cleaned = clean_and_transform_data(df)
    print(f"Cleaned data: {len(df_cleaned)} records remain")
    
    postgres_engine, mysql_engine = create_connections()
    
    print("Migrating to PostgreSQL (operational database)...")
    migrate_to_postgres(df_cleaned, postgres_engine)
    
    print("Migrating to MySQL (historical database)...")
    migrate_to_mysql(df_cleaned, mysql_engine)
    
    print("Generating seasonal statistics...")
    generate_seasonal_stats(df_cleaned, mysql_engine)
    
    print("Migration completed successfully!")
    print(f"Total records migrated: {len(df_cleaned)}")

if __name__ == "__main__":
    main()