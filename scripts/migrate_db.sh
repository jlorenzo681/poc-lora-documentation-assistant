#!/bin/bash
set -e

echo "Running database migrations..."

# Check if shared-db container is running
if ! docker ps | grep -q shared-db; then
    echo "Error: shared-db container is not running"
    echo "Please start the services first with: make deploy"
    exit 1
fi

# Run migrations
echo "Applying connector schema migrations..."
docker exec -i shared-db psql -U postgres -d postgres < migrations/001_add_connectors_postgres.sql

echo "✅ Migrations completed successfully"
