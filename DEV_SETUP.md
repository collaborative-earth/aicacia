# Development Setup Guide

This guide explains how to set up and run the Aicacia application in development mode with hot reloading.

## Prerequisites

- Docker and Docker Compose installed
- Environment variables configured (see below)

## Environment Variables

The application uses environment variables to differentiate between development and production environments.

### Development Environment
The development environment automatically sets:
- `VITE_API_URL=http://localhost:8000` (local API)
- `POSTGRES_PASSWORD=postgres`
- `OPENAI_API_KEY=placeholder`
- `QDRANT_URL=http://localhost:6333`
- `QDRANT_API_KEY=placeholder`
- `SECRET_KEY=dev_secret_key_123`

### Production Environment
For production, you need to set these environment variables:
```bash
export POSTGRES_PASSWORD=your_secure_password
export OPENAI_API_KEY=your_openai_api_key
export QDRANT_URL=your_qdrant_url
export QDRANT_API_KEY=your_qdrant_api_key
export SECRET_KEY=your_secure_secret_key
```

## Quick Start

### Development Mode
```bash
# Start development environment with hot reloading
./run_dev_server
```

### Production Mode
```bash
# Set your production environment variables first
export POSTGRES_PASSWORD=your_secure_password
export OPENAI_API_KEY=your_openai_api_key
export QDRANT_URL=your_qdrant_url
export QDRANT_API_KEY=your_qdrant_api_key
export SECRET_KEY=your_secure_secret_key

# Start production environment
./run_prod_server
```

## Environment Differences

### Development Mode (`docker-compose-dev.yml`)
- **API**: Local FastAPI server with hot reloading on port 8000
- **Webapp**: Vite dev server with hot reloading on port 5173
- **Database**: Local PostgreSQL with development data
- **API URL**: `http://localhost:8000` (set via `VITE_API_URL`)

### Production Mode (`docker-compose-prod.yml`)
- **API**: Production FastAPI server on port 8000
- **Webapp**: Built React app served on port 3000
- **Database**: Production PostgreSQL with persistent data
- **API URL**: `http://3.137.35.87:8000` (set via `VITE_API_URL`)

## What's Different in Development Mode

### API (Flask/FastAPI)
- **Hot Reloading**: The API server runs with `--reload` flag, automatically restarting when code changes
- **Volume Mounting**: The entire `api/` directory is mounted, so changes are immediately reflected
- **Development Dependencies**: All development packages (like flake8) are installed

### Webapp (React)
- **Hot Reloading**: Vite development server with hot module replacement
- **Volume Mounting**: The entire `webapp/` directory is mounted
- **File Watching**: Uses polling for better file change detection in Docker
- **Environment Variables**: Uses `VITE_API_URL` to connect to the correct API

### Database
- **Named Volume**: Uses `pg_data_dev` volume managed by Docker
- **Same Configuration**: Uses the same PostgreSQL setup as production

## Accessing the Services

### Development
- **API**: http://localhost:8000
- **Webapp**: http://localhost:5173
- **Database**: localhost:5432

### Production
- **API**: http://localhost:8000
- **Webapp**: http://localhost:3000
- **Database**: localhost:5432

## Development Workflow

1. Start the development environment using `./run_dev_server`
2. Make changes to your code in the `api/` or `webapp/` directories
3. Changes will automatically trigger hot reloading
4. Check the logs in the terminal for any errors

## Stopping the Environment

Press `Ctrl+C` in the terminal where docker-compose is running, or run:

```bash
# For development
docker-compose -f docker-compose-dev.yml down

# For production
docker-compose -f docker-compose-prod.yml down
```

## Troubleshooting

### Port Conflicts
If you get port conflicts, make sure no other services are running on the required ports.

### Node Modules Issues
If the webapp has dependency issues, you can rebuild the container:
```bash
docker-compose -f docker-compose-dev.yml build aicacia-webapp-dev
```

### Python Dependencies
If the API has dependency issues, you can rebuild the container:
```bash
docker-compose -f docker-compose-dev.yml build aicacia-api-dev
```

### Database Issues
If you need to reset the database, you can remove the volume:
```bash
docker-compose -f docker-compose-dev.yml down -v
docker volume rm aicacia_pg_data_dev
```

### Environment Variable Issues
If the frontend can't connect to the API, check that `VITE_API_URL` is set correctly:
- Development: `http://localhost:8000`
- Production: `http://3.137.35.87:8000` 