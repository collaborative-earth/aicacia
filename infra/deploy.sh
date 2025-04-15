#!/bin/bash

set -e

POSTGRES_PASSWORD=$(aws ssm get-parameter --name "/aicacia-app/postgres-password" --with-decryption --query "Parameter.Value" --output text)

echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" > ./api/.env

echo "Building and starting services..."
docker compose down
docker compose pull
docker compose up -d --build