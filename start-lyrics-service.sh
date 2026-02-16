#!/bin/bash
# Quick start script for lyrics extraction service

set -e

echo "=========================================="
echo "Lyrics Extraction Service - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Determine which docker compose command to use
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "Step 1: Creating environment file..."
if [ ! -f .env.lyrics ]; then
    cp .env.lyrics.example .env.lyrics
    echo "✓ Created .env.lyrics from template"
    echo "  You can edit .env.lyrics to customize settings"
else
    echo "✓ .env.lyrics already exists"
fi

echo ""
echo "Step 2: Building Docker images..."
$DOCKER_COMPOSE -f docker-compose.lyrics.yml build

echo ""
echo "Step 3: Starting services..."
$DOCKER_COMPOSE -f docker-compose.lyrics.yml up -d

echo ""
echo "Step 4: Waiting for services to be ready..."
sleep 5

# Check health
echo "Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "✓ Service is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠ Service health check timed out. Check logs with:"
        echo "  $DOCKER_COMPOSE -f docker-compose.lyrics.yml logs"
        exit 1
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "=========================================="
echo "✓ Lyrics Extraction Service is running!"
echo "=========================================="
echo ""
echo "API endpoint:    http://localhost:8000"
echo "API docs:        http://localhost:8000/docs"
echo "Health check:    http://localhost:8000/healthz"
echo ""
echo "Example usage:"
echo "  # Submit a job"
echo "  curl -X POST http://localhost:8000/v1/lyrics \\"
echo "    -F \"file=@your_song.mp3\" \\"
echo "    -F \"language_hint=auto\""
echo ""
echo "  # Check job status (replace JOB_ID with actual ID)"
echo "  curl http://localhost:8000/v1/lyrics/JOB_ID"
echo ""
echo "View logs:"
echo "  $DOCKER_COMPOSE -f docker-compose.lyrics.yml logs -f"
echo ""
echo "Stop services:"
echo "  $DOCKER_COMPOSE -f docker-compose.lyrics.yml down"
echo ""
