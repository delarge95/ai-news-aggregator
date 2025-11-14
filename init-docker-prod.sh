#!/bin/bash

# AI News Aggregator - Initialize Docker Production Environment
# This script creates the necessary directories for Docker volumes

set -e

echo "🚀 Initializing Docker production environment for AI News Aggregator..."

# Create base directory structure
echo "📁 Creating directory structure..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/logs/backend
mkdir -p data/logs/nginx
mkdir -p data/frontend

# Set appropriate permissions
echo "🔒 Setting permissions..."
chmod 755 data/postgres
chmod 755 data/redis
chmod 755 data/logs/backend
chmod 755 data/logs/nginx
chmod 755 data/frontend

# Create log files with proper permissions
touch data/logs/backend/app.log
touch data/logs/nginx/access.log
touch data/logs/nginx/error.log

chmod 644 data/logs/backend/app.log
chmod 644 data/logs/nginx/access.log
chmod 644 data/logs/nginx/error.log

echo "✅ Directory structure created successfully!"
echo ""
echo "📋 Directory structure:"
echo "   data/postgres/     - PostgreSQL data files"
echo "   data/redis/        - Redis data files"
echo "   data/logs/         - Application logs"
echo "   data/frontend/     - Frontend build files"
echo ""
echo "📝 Next steps:"
echo "1. Copy .env.prod.example to .env and update with your values"
echo "2. Run: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🎉 Environment initialized! Ready for production deployment."