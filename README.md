# Scalable Wildfire Analytics Platform

A comprehensive, production-ready backend services platform for wildfire data analysis with REST APIs, multiple databases, load balancing, and Docker containerization.

## Architecture Overview

### Scalable Backend Services
- **Load Balancer**: NGINX with 3 API instances for high availability
- **REST API**: Flask-based microservices with JWT authentication
- **Databases**: PostgreSQL (operational) + MySQL (historical data)
- **Caching**: Redis for performance optimization
- **Background Processing**: Celery workers for ML analytics

### Key Features
- Multi-database Architecture: PostgreSQL + MySQL + Redis
- Load Balanced APIs: 3 API instances behind NGINX
- Containerized Deployment: Full Docker stack
- Advanced Analytics: DBSCAN clustering, PCA, ARIMA forecasting
- Real-time Processing: Background workers for ML tasks
- REST API Endpoints: Complete CRUD operations
- Authentication & Authorization: JWT-based security
- Scalable Infrastructure: Auto-scaling ready

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- 8GB+ RAM recommended

### Deploy Platform
```bash
git clone <repository>
cd Geospatial_wildfires_database_analysis
chmod +x deploy.sh
./deploy.sh deploy
```

### Access Points
- Main Application: http://localhost
- API Health Check: http://localhost/api/health
- PostgreSQL: localhost:5432
- MySQL: localhost:3306
- Redis: localhost:6379

## Database Architecture

### PostgreSQL (Operational Database)
```
Tables:
- users (authentication & authorization)
- fire_incidents (main wildfire data)
- fire_causes (lookup table)
- reporting_agencies (agency information)
- weather_data (meteorological data)
- analysis_results (ML model outputs)
```

### MySQL (Historical Database)
```
Tables:
- historical_fire_incidents (archived data)
- seasonal_statistics (aggregated metrics)
- fire_trends (temporal analysis)
- risk_assessments (predictive analytics)
- climate_data (environmental factors)
```

## REST API Endpoints

### Authentication
```
POST /api/auth/register  - User registration
POST /api/auth/login     - User login
```

### Fire Data Management
```
GET  /api/fires          - List fires (paginated, filtered)
POST /api/fires          - Create fire incident
GET  /api/fires/{id}     - Get specific fire
PUT  /api/fires/{id}     - Update fire incident
```

### Analytics & ML
```
GET /api/analytics/clusters    - DBSCAN clustering results
GET /api/analytics/pca         - PCA dimensionality reduction
GET /api/analytics/forecast    - ARIMA time series forecasting
GET /api/stats/summary         - Statistical summaries
```

### System Health
```
GET /api/health          - Service health check
```

## Advanced Analytics

### Machine Learning Capabilities
1. **Spatial Clustering**: DBSCAN algorithm for fire hotspot identification
2. **Dimensionality Reduction**: PCA for data visualization
3. **Time Series Forecasting**: ARIMA models for fire prediction
4. **Risk Assessment**: Automated risk scoring by region

### Background Processing
- **Celery Workers**: Async processing for heavy ML computations
- **Scheduled Tasks**: Daily analytics pipeline execution
- **Result Caching**: Redis-based caching for performance

## Container Services

| Service | Description | Port | Health Check |
|---------|-------------|------|--------------|
| nginx | Load Balancer | 80, 443 | HTTP response |
| api1-3 | Flask API instances | 5000 | /api/health |
| postgres | Primary database | 5432 | Connection test |
| mysql | Historical database | 3306 | Connection test |
| redis | Cache & message broker | 6379 | PING command |
| worker | Background processor | - | Task execution |

## Data Migration

### Convert Existing Data
```bash
cp your_wildfire_data.csv data/
./deploy.sh migrate
```

### Supported Formats
- CSV files with wildfire incident data
- USFS Fire Occurrence Database format
- Custom CSV with required columns

## Management Commands

```bash
./deploy.sh start      # Start services
./deploy.sh stop       # Stop services  
./deploy.sh restart    # Restart services
./deploy.sh status     # Check service status
./deploy.sh logs       # View live logs
./deploy.sh cleanup    # Full cleanup
```

### Development Commands
```bash
docker-compose exec api1 flask shell
docker-compose exec postgres psql -U wildfire_user wildfire_db
docker-compose exec mysql mysql -u historical_user -p wildfire_historical
```

## Performance & Scaling

### Load Balancing
- **NGINX**: Routes requests across 3 API instances
- **Health Checks**: Automatic failover for unhealthy instances
- **Session Persistence**: Redis-based session storage

### Database Optimization
- **Connection Pooling**: SQLAlchemy connection management
- **Indexing**: Optimized queries for geographic and temporal data
- **Caching**: Redis caching for frequently accessed data

### Horizontal Scaling
```bash
docker-compose up -d --scale api1=5 --scale api2=5
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Admin, Analyst, User permissions
- **Input Validation**: SQL injection prevention
- **CORS Protection**: Cross-origin request security
- **Password Hashing**: Secure password storage

## Development Setup

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
docker-compose up -d postgres mysql redis
cd backend
export DATABASE_URL="postgresql://wildfire_user:secure_password@localhost:5432/wildfire_db"
export REDIS_URL="redis://localhost:6379/0"
python app.py
```

### API Testing
```bash
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

curl -X GET http://localhost/api/fires \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Monitoring & Observability

### Health Monitoring
- **Health Endpoints**: Each service exposes health status
- **Load Balancer Status**: NGINX status monitoring
- **Database Connections**: Connection pool monitoring

### Logging
```bash
./deploy.sh logs
docker-compose logs api1
docker-compose logs postgres
docker-compose logs worker
```

## Production Deployment

### Environment Variables
```bash
export FLASK_ENV=production
export DEBUG=false
export JWT_SECRET_KEY="your-secure-secret-key"
export DATABASE_URL="postgresql://user:pass@prod-db:5432/wildfire_db"
```

### SSL Configuration
```bash
# Add SSL certificates to nginx/ssl/
# Update nginx.conf for HTTPS
```

**Built with**: Flask, PostgreSQL, MySQL, Redis, Docker, NGINX, Celery, scikit-learn, pandas