#!/bin/bash

set -e

REGION="us-east-2"
ACCOUNT_ID="771589226584"

echo "Pulling secrets..."
POSTGRES_PASSWORD=$(aws ssm get-parameter --name "/aicacia-app/postgres-password" --with-decryption --query "Parameter.Value" --output text)

export POSTGRES_PASSWORD

echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Pulling images..."
docker pull postgres:17
docker pull $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aicacia-api:latest
docker pull $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aicacia-webapp:latest

echo "Tagging ECR images..."
docker tag $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aicacia-api:latest aicacia-api:latest
docker tag $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aicacia-webapp:latest aicacia-webapp:latest

echo "Stopping services..."
docker compose down

echo "Starting services..."
docker compose up -d

echo "Cleaning up unused images"
docker image prune -f