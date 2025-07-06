#!/bin/bash
# Deployment script for RAG Pipeline

set -e

echo "🚀 Starting RAG Pipeline Deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.docker .env
    echo "✅ Please edit .env file with your configuration before continuing."
    exit 1
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🏃 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🏥 Checking application health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Application failed to start properly"
        docker-compose logs rag-app
        exit 1
    fi
    
    echo "Attempt $attempt/$max_attempts - waiting for application..."
    sleep 5
    ((attempt++))
done

echo "🎉 RAG Pipeline deployed successfully!"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Application: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"

# Show running containers
echo "📦 Running containers:"
docker-compose ps
