from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import redis
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://wildfire_user:secure_password@localhost:5432/wildfire_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
CORS(app)

redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class FireIncident(db.Model):
    __tablename__ = 'fire_incidents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fire_name = db.Column(db.String(200))
    discovery_date = db.Column(db.Date, nullable=False)
    discovery_time = db.Column(db.Time)
    fire_year = db.Column(db.Integer, nullable=False)
    fire_size_acres = db.Column(db.Numeric(10, 2))
    fire_size_class = db.Column(db.String(1))
    latitude = db.Column(db.Numeric(10, 6), nullable=False)
    longitude = db.Column(db.Numeric(11, 6), nullable=False)
    state = db.Column(db.String(2))
    county = db.Column(db.String(50))
    cause_code = db.Column(db.Integer)
    cause_description = db.Column(db.String(100))
    reporting_agency = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'user')
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token, 'user_id': user.id, 'role': user.role})
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/fires', methods=['GET'])
@jwt_required()
def get_fires():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    state = request.args.get('state')
    year = request.args.get('year', type=int)
    size_class = request.args.get('size_class')
    
    cache_key = f"fires_{page}_{per_page}_{state}_{year}_{size_class}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return jsonify(eval(cached_result))
    
    query = FireIncident.query
    
    if state:
        query = query.filter(FireIncident.state == state)
    if year:
        query = query.filter(FireIncident.fire_year == year)
    if size_class:
        query = query.filter(FireIncident.fire_size_class == size_class)
    
    fires = query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'fires': [{
            'id': fire.id,
            'fire_name': fire.fire_name,
            'discovery_date': fire.discovery_date.isoformat() if fire.discovery_date else None,
            'fire_year': fire.fire_year,
            'fire_size_acres': float(fire.fire_size_acres) if fire.fire_size_acres else None,
            'fire_size_class': fire.fire_size_class,
            'latitude': float(fire.latitude),
            'longitude': float(fire.longitude),
            'state': fire.state,
            'county': fire.county,
            'cause_description': fire.cause_description,
            'reporting_agency': fire.reporting_agency
        } for fire in fires.items],
        'total': fires.total,
        'pages': fires.pages,
        'current_page': fires.page
    }
    
    redis_client.setex(cache_key, 300, str(result))
    return jsonify(result)

@app.route('/api/fires', methods=['POST'])
@jwt_required()
def create_fire():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'analyst']:
        return jsonify({'message': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    fire = FireIncident(
        fire_name=data.get('fire_name'),
        discovery_date=datetime.strptime(data['discovery_date'], '%Y-%m-%d').date(),
        fire_year=data['fire_year'],
        fire_size_acres=data.get('fire_size_acres'),
        fire_size_class=data.get('fire_size_class'),
        latitude=data['latitude'],
        longitude=data['longitude'],
        state=data.get('state'),
        county=data.get('county'),
        cause_description=data.get('cause_description'),
        reporting_agency=data.get('reporting_agency')
    )
    
    db.session.add(fire)
    db.session.commit()
    
    return jsonify({'message': 'Fire incident created', 'id': fire.id}), 201

@app.route('/api/analytics/clusters', methods=['GET'])
@jwt_required()
def get_fire_clusters():
    cache_key = "fire_clusters"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return jsonify(eval(cached_result))
    
    fires = FireIncident.query.all()
    coordinates = [[float(fire.latitude), float(fire.longitude)] for fire in fires]
    
    if len(coordinates) < 10:
        return jsonify({'clusters': [], 'message': 'Insufficient data for clustering'})
    
    dbscan = DBSCAN(eps=0.5, min_samples=5)
    cluster_labels = dbscan.fit_predict(coordinates)
    
    clusters = []
    for i, fire in enumerate(fires):
        clusters.append({
            'fire_id': fire.id,
            'latitude': float(fire.latitude),
            'longitude': float(fire.longitude),
            'cluster': int(cluster_labels[i]),
            'fire_size_acres': float(fire.fire_size_acres) if fire.fire_size_acres else 0,
            'fire_year': fire.fire_year
        })
    
    result = {'clusters': clusters}
    redis_client.setex(cache_key, 600, str(result))
    return jsonify(result)

@app.route('/api/analytics/pca', methods=['GET'])
@jwt_required()
def get_pca_analysis():
    cache_key = "pca_analysis"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return jsonify(eval(cached_result))
    
    fires = FireIncident.query.filter(
        FireIncident.fire_size_acres.isnot(None),
        FireIncident.latitude.isnot(None),
        FireIncident.longitude.isnot(None)
    ).all()
    
    if len(fires) < 50:
        return jsonify({'pca_data': [], 'message': 'Insufficient data for PCA'})
    
    features = []
    for fire in fires:
        features.append([
            float(fire.latitude),
            float(fire.longitude),
            float(fire.fire_size_acres),
            fire.fire_year
        ])
    
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(features)
    
    pca_data = []
    for i, fire in enumerate(fires):
        pca_data.append({
            'fire_id': fire.id,
            'pc1': float(pca_result[i][0]),
            'pc2': float(pca_result[i][1]),
            'fire_size_acres': float(fire.fire_size_acres),
            'fire_year': fire.fire_year
        })
    
    result = {
        'pca_data': pca_data,
        'explained_variance': pca.explained_variance_ratio_.tolist()
    }
    
    redis_client.setex(cache_key, 1800, str(result))
    return jsonify(result)

@app.route('/api/stats/summary', methods=['GET'])
@jwt_required()
def get_summary_stats():
    cache_key = "summary_stats"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return jsonify(eval(cached_result))
    
    total_fires = FireIncident.query.count()
    total_acres = db.session.query(db.func.sum(FireIncident.fire_size_acres)).scalar() or 0
    
    fires_by_year = db.session.query(
        FireIncident.fire_year,
        db.func.count(FireIncident.id),
        db.func.sum(FireIncident.fire_size_acres)
    ).group_by(FireIncident.fire_year).all()
    
    fires_by_state = db.session.query(
        FireIncident.state,
        db.func.count(FireIncident.id),
        db.func.sum(FireIncident.fire_size_acres)
    ).group_by(FireIncident.state).all()
    
    result = {
        'total_fires': total_fires,
        'total_acres_burned': float(total_acres),
        'fires_by_year': [
            {
                'year': year,
                'count': count,
                'acres': float(acres) if acres else 0
            } for year, count, acres in fires_by_year
        ],
        'fires_by_state': [
            {
                'state': state,
                'count': count,
                'acres': float(acres) if acres else 0
            } for state, count, acres in fires_by_state
        ]
    }
    
    redis_client.setex(cache_key, 900, str(result))
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'instance': os.getenv('INSTANCE_ID', 'unknown')
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('API_PORT', 5000)), debug=False)