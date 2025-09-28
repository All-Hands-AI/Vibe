# OpenVibe Development Makefile
.PHONY: install dev frontend-install backend-install frontend-dev backend-dev clean help

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "OpenVibe Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies (frontend + backend)
	@echo "$(GREEN)Installing OpenVibe dependencies...$(NC)"
	@$(MAKE) frontend-install
	@$(MAKE) backend-install
	@echo "$(GREEN)✓ All dependencies installed successfully!$(NC)"

frontend-install: ## Install frontend dependencies
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	cd frontend && npm ci
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

backend-install: ## Install backend dependencies with virtual environment
	@echo "$(GREEN)Installing backend dependencies...$(NC)"
	cd backend && uv venv --clear
	cd backend && bash -c "source .venv/bin/activate && uv pip install .[dev]"
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

dev: ## Start development servers (frontend + backend)
	@echo "$(GREEN)Starting OpenVibe development servers...$(NC)"
	@$(MAKE) -j2 frontend-dev backend-dev

frontend-dev: ## Start frontend development server
	@echo "$(GREEN)Starting frontend development server on port 12000...$(NC)"
	cd frontend && npm run dev -- --host 0.0.0.0 --port 12000

backend-dev: ## Start backend development server
	@echo "$(GREEN)Starting backend development server on port 12001...$(NC)"
	cd backend && bash -c "source .venv/bin/activate && DATA_DIR=../data PORT=12001 python app.py"

test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	@$(MAKE) frontend-test
	@$(MAKE) backend-test

frontend-test: ## Run frontend tests
	@echo "$(GREEN)Running frontend tests...$(NC)"
	cd frontend && npm run test:run

backend-test: ## Run backend tests
	@echo "$(GREEN)Running backend tests...$(NC)"
	cd backend && bash -c "source .venv/bin/activate && mkdir -p /tmp/test-data && DATA_DIR=/tmp/test-data pytest --cov=. --cov-report=term-missing -v"

lint: ## Run linting for both frontend and backend
	@echo "$(GREEN)Running linting...$(NC)"
	@$(MAKE) frontend-lint
	@$(MAKE) backend-lint

frontend-lint: ## Run frontend linting
	@echo "$(GREEN)Running frontend linting...$(NC)"
	cd frontend && npm run lint

backend-lint: ## Run backend linting
	@echo "$(GREEN)Running backend linting...$(NC)"
	cd backend && bash -c "source .venv/bin/activate && black --check --diff . && flake8 . && mypy ."

clean: ## Clean all build artifacts and dependencies
	@echo "$(RED)Cleaning build artifacts...$(NC)"
	cd frontend && rm -rf node_modules dist
	cd backend && rm -rf .venv __pycache__ .pytest_cache htmlcov .coverage
	@echo "$(GREEN)✓ Cleaned successfully$(NC)"

status: ## Show development environment status
	@echo "$(GREEN)OpenVibe Development Status:$(NC)"
	@echo ""
	@echo "Frontend:"
	@if [ -d "frontend/node_modules" ]; then echo "  $(GREEN)✓ Dependencies installed$(NC)"; else echo "  $(RED)✗ Dependencies not installed$(NC)"; fi
	@echo ""
	@echo "Backend:"
	@if [ -d "backend/.venv" ]; then echo "  $(GREEN)✓ Virtual environment created$(NC)"; else echo "  $(RED)✗ Virtual environment not created$(NC)"; fi
	@if [ -d "backend/.venv" ] && [ -f "backend/.venv/pyvenv.cfg" ]; then echo "  $(GREEN)✓ Dependencies installed$(NC)"; else echo "  $(RED)✗ Dependencies not installed$(NC)"; fi