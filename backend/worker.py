from celery import Celery
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
import psycopg2
import pymysql
from sqlalchemy import create_engine
import os
import json
from datetime import datetime, timedelta
import redis

celery = Celery('wildfire_worker')

celery.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'worker.process_clustering': {'queue': 'analytics'},
        'worker.process_forecasting': {'queue': 'analytics'},
        'worker.process_risk_assessment': {'queue': 'risk'},
        'worker.generate_reports': {'queue': 'reports'}
    }
)

def get_postgres_engine():
    return create_engine(os.getenv('DATABASE_URL'))

def get_mysql_engine():
    return create_engine(os.getenv('MYSQL_URL'))

@celery.task(bind=True)
def process_clustering(self, min_samples=5, eps=0.5):
    try:
        engine = get_postgres_engine()
        
        query = """
        SELECT id, latitude, longitude, fire_size_acres, fire_year
        FROM fire_incidents 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        
        df = pd.read_sql(query, engine)
        
        if len(df) < min_samples:
            return {'status': 'insufficient_data', 'message': 'Not enough data points for clustering'}
        
        coordinates = df[['latitude', 'longitude']].values
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(coordinates)
        
        df['cluster'] = clusters
        
        cluster_results = []
        for _, row in df.iterrows():
            cluster_results.append({
                'fire_incident_id': row['id'],
                'analysis_type': 'dbscan_clustering',
                'cluster_id': int(row['cluster']),
                'metadata': json.dumps({
                    'eps': eps,
                    'min_samples': min_samples,
                    'fire_size_acres': float(row['fire_size_acres']) if pd.notna(row['fire_size_acres']) else None
                })
            })
        
        results_df = pd.DataFrame(cluster_results)
        results_df.to_sql('analysis_results', engine, if_exists='append', index=False)
        
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_noise = list(clusters).count(-1)
        
        return {
            'status': 'completed',
            'n_clusters': n_clusters,
            'n_noise_points': n_noise,
            'total_points': len(df)
        }
        
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def process_pca_analysis(self):
    try:
        engine = get_postgres_engine()
        
        query = """
        SELECT id, latitude, longitude, fire_size_acres, fire_year
        FROM fire_incidents 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL 
        AND fire_size_acres IS NOT NULL
        """
        
        df = pd.read_sql(query, engine)
        
        if len(df) < 50:
            return {'status': 'insufficient_data', 'message': 'Need at least 50 data points for PCA'}
        
        features = df[['latitude', 'longitude', 'fire_size_acres', 'fire_year']].values
        
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(features_scaled)
        
        pca_results = []
        for i, row in df.iterrows():
            pca_results.append({
                'fire_incident_id': row['id'],
                'analysis_type': 'pca_analysis',
                'metadata': json.dumps({
                    'pc1': float(pca_result[i][0]),
                    'pc2': float(pca_result[i][1]),
                    'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                    'feature_importance': {
                        'latitude': float(pca.components_[0][0]),
                        'longitude': float(pca.components_[0][1]),
                        'fire_size_acres': float(pca.components_[0][2]),
                        'fire_year': float(pca.components_[0][3])
                    }
                })
            })
        
        results_df = pd.DataFrame(pca_results)
        results_df.to_sql('analysis_results', engine, if_exists='append', index=False)
        
        return {
            'status': 'completed',
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
            'n_components': 2,
            'total_points': len(df)
        }
        
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def process_forecasting(self, forecast_periods=12):
    try:
        engine = get_postgres_engine()
        
        query = """
        SELECT fire_year, COUNT(*) as fire_count
        FROM fire_incidents 
        GROUP BY fire_year 
        ORDER BY fire_year
        """
        
        df = pd.read_sql(query, engine)
        
        if len(df) < 10:
            return {'status': 'insufficient_data', 'message': 'Need at least 10 years of data for forecasting'}
        
        time_series = df.set_index('fire_year')['fire_count']
        
        model = ARIMA(time_series, order=(2, 1, 2))
        fitted_model = model.fit()
        
        forecast = fitted_model.forecast(steps=forecast_periods)
        forecast_ci = fitted_model.get_forecast(steps=forecast_periods).conf_int()
        
        forecast_results = []
        current_year = df['fire_year'].max()
        
        for i in range(forecast_periods):
            forecast_year = current_year + i + 1
            forecast_results.append({
                'analysis_type': 'arima_forecast',
                'prediction_value': float(forecast.iloc[i]),
                'confidence_score': 0.95,
                'metadata': json.dumps({
                    'forecast_year': forecast_year,
                    'lower_ci': float(forecast_ci.iloc[i, 0]),
                    'upper_ci': float(forecast_ci.iloc[i, 1]),
                    'model_params': {
                        'order': (2, 1, 2),
                        'aic': float(fitted_model.aic),
                        'bic': float(fitted_model.bic)
                    }
                })
            })
        
        results_df = pd.DataFrame(forecast_results)
        results_df.to_sql('analysis_results', engine, if_exists='append', index=False)
        
        return {
            'status': 'completed',
            'forecast_periods': forecast_periods,
            'model_aic': float(fitted_model.aic),
            'forecast_values': forecast.tolist()
        }
        
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def process_risk_assessment(self, state=None):
    try:
        mysql_engine = get_mysql_engine()
        postgres_engine = get_postgres_engine()
        
        current_year = datetime.now().year
        
        if state:
            fire_query = f"""
            SELECT state, county, AVG(fire_size_acres) as avg_size,
                   COUNT(*) as fire_count,
                   MAX(fire_size_acres) as max_size
            FROM fire_incidents 
            WHERE fire_year >= {current_year - 5} AND state = '{state}'
            GROUP BY state, county
            """
        else:
            fire_query = f"""
            SELECT state, county, AVG(fire_size_acres) as avg_size,
                   COUNT(*) as fire_count,
                   MAX(fire_size_acres) as max_size
            FROM fire_incidents 
            WHERE fire_year >= {current_year - 5}
            GROUP BY state, county
            """
        
        df = pd.read_sql(fire_query, postgres_engine)
        
        df['risk_score'] = (
            (df['fire_count'] / df['fire_count'].max()) * 0.4 +
            (df['avg_size'] / df['avg_size'].max()) * 0.3 +
            (df['max_size'] / df['max_size'].max()) * 0.3
        ) * 10
        
        def get_risk_level(score):
            if score >= 8: return 'Extreme'
            elif score >= 6: return 'High'
            elif score >= 4: return 'Moderate'
            else: return 'Low'
        
        df['risk_level'] = df['risk_score'].apply(get_risk_level)
        
        risk_assessments = []
        for _, row in df.iterrows():
            risk_factors = []
            if row['fire_count'] > df['fire_count'].median():
                risk_factors.append('high_fire_frequency')
            if row['avg_size'] > df['avg_size'].median():
                risk_factors.append('large_average_fire_size')
            if row['max_size'] > df['max_size'].quantile(0.9):
                risk_factors.append('extreme_fire_events')
            
            risk_assessments.append({
                'region_id': f"{row['state']}_{row['county'][:3].upper()}",
                'state': row['state'],
                'county': row['county'],
                'risk_level': row['risk_level'],
                'risk_score': float(row['risk_score']),
                'primary_risk_factors': json.dumps(risk_factors),
                'assessment_date': datetime.now().date(),
                'valid_until': (datetime.now() + timedelta(days=180)).date(),
                'created_by': 'automated_system'
            })
        
        results_df = pd.DataFrame(risk_assessments)
        results_df.to_sql('risk_assessments', mysql_engine, if_exists='append', index=False)
        
        return {
            'status': 'completed',
            'assessments_created': len(risk_assessments),
            'high_risk_counties': len(df[df['risk_level'].isin(['High', 'Extreme'])])
        }
        
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        return {'status': 'error', 'message': str(e)}

@celery.task
def scheduled_analytics():
    process_clustering.delay()
    process_pca_analysis.delay()
    process_forecasting.delay()
    process_risk_assessment.delay()
    
    return {'status': 'scheduled_all_analytics'}

celery.conf.beat_schedule = {
    'run-analytics-daily': {
        'task': 'worker.scheduled_analytics',
        'schedule': 86400.0,
    },
}

if __name__ == '__main__':
    celery.start()