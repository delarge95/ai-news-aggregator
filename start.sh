#!/bin/bash

# AI News Aggregator Startup Script

echo "🚀 Starting AI News Aggregator..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys before starting services."
fi

# Start database and Redis services first
echo "🗄️  Starting database and Redis..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🔧 Running database migrations..."
cd backend
python -m alembic init alembic
python -m alembic revision --autogenerate -m "Initial migration"
python -m alembic upgrade head
cd ..

# Start all services
echo "🎯 Starting all services..."
docker-compose up --build -d

echo "✅ AI News Aggregator is starting up!"
echo ""
echo "📊 Services:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000/api/v1/docs"
echo "   - Database: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "🔑 Don't forget to add your API keys to the .env file!"
echo "📚 Read the API documentation at: http://localhost:8000/api/v1/docs"