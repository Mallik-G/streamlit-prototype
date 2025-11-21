.PHONY: help install dev-install test lint format clean docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make run            - Run Streamlit app"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make security       - Run security scan"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo "  make clean          - Clean generated files"
	@echo "  make pre-commit     - Run pre-commit hooks"

# Installation
install:
	pip install -r requirements.txt

dev-install: install
	pip install pytest pytest-cov pytest-mock ruff black isort mypy pre-commit bandit
	pre-commit install

# Running
run:
	streamlit run app.py

run-debug:
	DEBUG=true LOG_LEVEL=DEBUG streamlit run app.py

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

test-unit:
	pytest tests/ -m unit -v

test-integration:
	pytest tests/ -m integration -v

test-watch:
	pytest-watch tests/

# Code Quality
lint:
	@echo "Running ruff..."
	ruff check .
	@echo "Running black..."
	black --check .
	@echo "Running isort..."
	isort --check-only .
	@echo "Running mypy..."
	mypy . --ignore-missing-imports || true

format:
	@echo "Formatting with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .
	@echo "Fixing linting issues with ruff..."
	ruff check . --fix

security:
	@echo "Running bandit security scan..."
	bandit -r . -f json -o bandit-report.json || true
	@echo "Security report: bandit-report.json"

# Pre-commit
pre-commit:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate

# Docker
docker-build:
	docker build -t cortex-ai:latest --target production .

docker-build-dev:
	docker build -t cortex-ai:dev --target development .

docker-run:
	docker run -p 8501:8501 \
		-e OPENAI_API_KEY=${OPENAI_API_KEY} \
		-e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
		-v $(PWD)/agents:/app/agents \
		-v $(PWD)/workflows:/app/workflows \
		cortex-ai:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f app

# Cleaning
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml junit.xml bandit-report.json

# CI simulation
ci: lint security test
	@echo "CI checks passed!"

# Quick checks before commit
check: format lint test-unit
	@echo "Pre-commit checks passed!"

# Setup new environment
setup: dev-install
	@echo "Creating .env file..."
	@test -f .env || cp .env.example .env 2>/dev/null || echo "No .env.example found"
	@echo "Setup complete! Edit .env with your API keys."

# Documentation
docs-serve:
	@echo "Serving documentation..."
	@echo "README.md, DEVELOPMENT.md, WORKFLOW_EXECUTORS.md available"
