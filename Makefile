# ArchBuilder.AI Development Makefile
# Usage: make format, make lint, make test

.PHONY: help format lint test install-dev clean setup

# Default target
help:
	@echo "Available commands:"
	@echo "  make format     - Format all Python code with black and isort"
	@echo "  make lint       - Run linting with flake8"
	@echo "  make test       - Run tests with pytest"
	@echo "  make install-dev - Install development dependencies"
	@echo "  make setup      - Setup pre-commit hooks"
	@echo "  make clean      - Clean cache and temp files"

# Format code
format:
	@echo "🔧 Formatting Python code..."
	python -m black src/cloud-server/app --line-length=88
	python -m isort src/cloud-server/app --profile=black --line-length=88
	@echo "✅ Code formatting complete!"

# Lint code
lint:
	@echo "🔍 Running linting checks..."
	python -m flake8 src/cloud-server/app --count --select=E9,F63,F7,F82 --show-source --statistics
	python -m black --check --diff src/cloud-server/app
	python -m isort --check-only --diff src/cloud-server/app --profile=black
	@echo "✅ Linting complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	cd src/cloud-server && python -m pytest tests/ -v
	@echo "✅ Tests complete!"

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r src/cloud-server/requirements.txt
	pip install -r src/cloud-server/requirements-dev.txt
	@echo "✅ Development dependencies installed!"

# Setup pre-commit hooks
setup:
	@echo "🔗 Setting up pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

# Clean cache and temporary files
clean:
	@echo "🧹 Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Quick development setup
dev-setup: install-dev setup
	@echo "🚀 Development environment ready!"

# CI commands
ci-format:
	python -m black src/cloud-server/app --line-length=88
	python -m isort src/cloud-server/app --profile=black --line-length=88

ci-lint:
	python -m flake8 src/cloud-server/app --count --select=E9,F63,F7,F82 --show-source --statistics
