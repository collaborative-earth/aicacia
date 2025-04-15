#!/bin/bash

set -e

POSTGRES_PASSWORD=$(aws ssm get-parameter --name "/aicacia-app/postgres-password" --with-decryption --query "Parameter.Value" --output text)

export POSTGRES_PASSWORD

echo "Starting services..."
docker compose down
docker compose pull aicacia-postgres
docker compose up -d