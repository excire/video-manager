#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "Creating test video..."
./scripts/create_test_video.sh

echo "Starting Docker backend..."
docker compose -f docker-compose.integration.yml up -d --build

echo "Waiting for API..."
for i in $(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/settings/video-dir | grep -q 200; then
    echo "API ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "API did not become ready"
    docker compose -f docker-compose.integration.yml down
    exit 1
  fi
  sleep 1
done

echo "Running integration tests..."
pip install -q httpx pytest
API_BASE=http://localhost:8000 pytest backend/tests/test_integration_docker.py -v

echo "Stopping Docker..."
docker compose -f docker-compose.integration.yml down

echo "Integration tests passed."
