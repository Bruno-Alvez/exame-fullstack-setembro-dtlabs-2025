# DeviceWatch - IoT Monitoring Platform
# Makefile for development and deployment

.PHONY: help build up down logs clean test lint format install

# Default target
help: ## Show this help message
	@echo "DeviceWatch - IoT Monitoring Platform"
	@echo "====================================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing simulator dependencies..."
	cd device-simulator && pip install -r requirements.txt

build: ## Build all Docker images
	@echo "Building Docker images..."
	docker-compose build

up: ## Start all services
	@echo "Starting DeviceWatch platform..."
	docker-compose up -d
	@echo "Services started:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

down: ## Stop all services
	@echo "Stopping DeviceWatch platform..."
	docker-compose down

restart: ## Restart all services
	@echo "Restarting DeviceWatch platform..."
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-simulator: ## Show simulator logs
	docker-compose logs -f simulator

# Database commands
db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	docker-compose exec backend alembic upgrade head

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 10
	docker-compose exec backend alembic upgrade head

db-shell: ## Open database shell
	docker-compose exec postgres psql -U devicewatch -d devicewatch

# Testing commands
test: ## Run all tests
	@echo "Running backend tests..."
	docker-compose exec backend pytest
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test

test-backend: ## Run backend tests only
	docker-compose exec backend pytest

test-frontend: ## Run frontend tests only
	docker-compose exec frontend npm test

# Code quality commands
lint: ## Run linting for all services
	@echo "Linting backend..."
	docker-compose exec backend flake8 app/
	@echo "Linting frontend..."
	docker-compose exec frontend npm run lint

format: ## Format code for all services
	@echo "Formatting backend..."
	docker-compose exec backend black app/
	docker-compose exec backend isort app/
	@echo "Formatting frontend..."
	docker-compose exec frontend npm run format

# Development commands
dev-backend: ## Start backend in development mode
	@echo "Starting backend in development mode..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend in development mode
	@echo "Starting frontend in development mode..."
	cd frontend && npm run dev

dev-simulator: ## Start simulator in development mode
	@echo "Starting simulator in development mode..."
	cd device-simulator && python simulator.py

# Utility commands
clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

status: ## Show status of all services
	@echo "Service Status:"
	@docker-compose ps

health: ## Check health of all services
	@echo "Health Check:"
	@curl -s http://localhost:8000/health || echo "Backend: DOWN"
	@curl -s http://localhost:3000 || echo "Frontend: DOWN"

# Production commands
prod-build: ## Build production images
	@echo "Building production images..."
	docker-compose -f docker-compose.prod.yaml build

prod-up: ## Start production services
	@echo "Starting production services..."
	docker-compose -f docker-compose.prod.yaml up -d

prod-down: ## Stop production services
	@echo "Stopping production services..."
	docker-compose -f docker-compose.prod.yaml down

# Documentation commands
docs: ## Generate API documentation
	@echo "Generating API documentation..."
	docker-compose exec backend python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')"

# Monitoring commands
monitor: ## Show real-time monitoring
	@echo "Real-time monitoring (Ctrl+C to exit):"
	@watch -n 2 'docker-compose ps && echo "" && curl -s http://localhost:8000/health | jq . || echo "Backend health check failed"'

# Backup commands
backup: ## Backup database
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U devicewatch devicewatch > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Quick setup for new developers
setup: install build up db-migrate ## Complete setup for new developers
	@echo "Setup complete! DeviceWatch is ready to use."
	@echo "Access the application at: http://localhost:3000"
	@echo "API documentation at: http://localhost:8000/docs"

