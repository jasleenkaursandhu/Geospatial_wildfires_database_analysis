#!/bin/bash

set -e

echo "🔥 Deploying Scalable Wildfire Analytics Platform..."

check_dependencies() {
    echo "📋 Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    echo "✅ Dependencies check passed"
}

setup_directories() {
    echo "📁 Setting up directory structure..."
    
    mkdir -p data models logs nginx/ssl monitoring/grafana monitoring/prometheus
    
    echo "✅ Directory structure created"
}

setup_environment() {
    echo "🔧 Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# Database Configuration
POSTGRES_DB=wildfire_db
POSTGRES_USER=wildfire_user
POSTGRES_PASSWORD=secure_password
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=wildfire_historical
MYSQL_USER=historical_user
MYSQL_PASSWORD=historical_password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# API Configuration
JWT_SECRET_KEY=$(openssl rand -base64 32)
API_PORT=5000

# Application Configuration
FLASK_ENV=production
DEBUG=false
EOF
    fi
    
    echo "✅ Environment configuration ready"
}

build_images() {
    echo "🐳 Building Docker images..."
    
    docker-compose build --parallel
    
    echo "✅ Docker images built successfully"
}

start_databases() {
    echo "🗄️ Starting database services..."
    
    docker-compose up -d postgres mysql redis
    
    echo "⏳ Waiting for databases to be ready..."
    sleep 30
    
    echo "✅ Database services started"
}

migrate_data() {
    echo "📊 Running data migration..."
    
    if [ -f "data/wildfire_data.csv" ] || [ -f "data/FW_Veg_Rem_Combined.csv" ]; then
        python3 scripts/migrate_data.py
        echo "✅ Data migration completed"
    else
        echo "⚠️ No data files found. Skipping migration."
        echo "   Place your wildfire CSV data in the 'data/' directory"
    fi
}

start_services() {
    echo "🚀 Starting all services..."
    
    docker-compose up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 45
    
    echo "✅ All services started"
}

health_check() {
    echo "🏥 Performing health checks..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost/api/health > /dev/null 2>&1; then
            echo "✅ API health check passed"
            break
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts - waiting for API..."
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ API health check failed"
        show_logs
        exit 1
    fi
}

show_status() {
    echo ""
    echo "🎉 Wildfire Analytics Platform deployed successfully!"
    echo ""
    echo "📊 Access Points:"
    echo "   • Main Application: http://localhost"
    echo "   • API Documentation: http://localhost/api/health"
    echo "   • Load Balancer Status: http://localhost"
    echo ""
    echo "🗄️ Database Access:"
    echo "   • PostgreSQL: localhost:5432 (wildfire_db)"
    echo "   • MySQL: localhost:3306 (wildfire_historical)"
    echo "   • Redis: localhost:6379"
    echo ""
    echo "📈 Services Status:"
    docker-compose ps
    echo ""
    echo "📝 View logs: docker-compose logs -f"
    echo "🛑 Stop platform: docker-compose down"
    echo "🔄 Restart platform: docker-compose restart"
}

show_logs() {
    echo "📋 Recent logs:"
    docker-compose logs --tail=20
}

cleanup() {
    echo "🧹 Cleaning up..."
    docker-compose down
    docker system prune -f
    echo "✅ Cleanup completed"
}

case "${1:-deploy}" in
    "deploy")
        check_dependencies
        setup_directories
        setup_environment
        build_images
        start_databases
        migrate_data
        start_services
        health_check
        show_status
        ;;
    "start")
        docker-compose up -d
        health_check
        show_status
        ;;
    "stop")
        docker-compose down
        echo "✅ Platform stopped"
        ;;
    "restart")
        docker-compose restart
        health_check
        show_status
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "cleanup")
        cleanup
        ;;
    "migrate")
        migrate_data
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|logs|status|cleanup|migrate}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  start    - Start existing services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show live logs"
        echo "  status   - Show service status"
        echo "  cleanup  - Stop and clean up"
        echo "  migrate  - Run data migration only"
        exit 1
        ;;
esac