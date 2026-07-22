#!/bin/bash
set -e

echo "  URJA Development Setup"
echo "========================="

command -v docker >/dev/null 2>&1 || { echo "  Docker required. Install from https://docker.com"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "  Docker Compose required."; exit 1; }

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "  Created backend/.env from .env.example"
fi

mkdir -p docker-data/postgres docker-data/redis

echo "  Starting URJA services..."
docker compose -f docker/docker-compose.yml up -d

echo "  Waiting for database..."
until docker compose exec db pg_isready -U urja > /dev/null 2>&1; do
    sleep 2
done
echo "  Database ready"

echo "   Running database migrations..."
docker compose exec api alembic upgrade head

echo "  Loading seed data..."
docker compose exec api python scripts/seed.py

echo ""
echo "  URJA is running!"
echo "   Dashboard: http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   TUI:       docker compose exec api python dashboard-tui/app.py"
echo ""
echo "   Login: admin@example.com / admin123"
