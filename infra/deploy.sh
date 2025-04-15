#!/bin/bash

set -e

BRANCH=${1:-main}

cd /home/ec2-user/aicacia

POSTGRES_PASSWORD=$(aws ssm get-parameter --name "/aicacia-app/postgres-password" --with-decryption --query "Parameter.Value" --output text)

echo "Checking out branch: $BRANCH"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" > .env

echo "Building and starting services..."
docker compose down
docker compose pull
docker compose up -d --build