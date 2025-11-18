.PHONY: help setup install test clean run-api run-webapp docker-build docker-up lint format

help:
	@echo "Supermarket Brochure AI - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup       - Initial project setup"
	@echo "  make install     - Install dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test        - Run tests with coverage"
	@echo "  make lint        - Run code linting"
	@echo "  make format      - Format code with black"
	@echo ""
	@echo "Run Services:"
	@echo "  make run-api     - Start FastAPI server"
	@echo "  make run-webapp  - Start Streamlit web app"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start services with docker-compose"
	@echo "  make docker-down  - Stop docker-compose services"
	@echo ""
	@echo "Data Collection:"
	@echo "  make scrape-all  - Scrape all supermarkets"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Clean temporary files"

setup:
	@bash scripts/setup.sh

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ --max-line-length=100 --ignore=E203,W503
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	isort src/ tests/

run-api:
	cd src/webapp && python api.py

run-webapp:
	streamlit run src/webapp/app_enhanced.py

run-webapp-basic:
	streamlit run src/webapp/app.py

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

scrape-all:
	python src/data_collection/scrape_brochures.py --all

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
