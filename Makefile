.PHONY: help test install install-dev lint fmt clean

PYTHON := python3
VENV := ~/venv/dev

help:
	@echo "Available targets:"
	@echo "  make test        - Run tests"
	@echo "  make install     - Install runtime dependencies"
	@echo "  make install-dev - Install dev dependencies"
	@echo "  make lint        - Run linter"
	@echo "  make fmt         - Format code"
	@echo "  make clean       - Remove build artifacts"

test:
	$(PYTHON) -m pytest tests/ -v

install:
	$(PYTHON) -m pip install rich

install-dev:
	$(PYTHON) -m pip install pytest rich ruff

lint:
	$(PYTHON) -m ruff check .

fmt:
	$(PYTHON) -m ruff format .

clean:
	rm -rf __pycache__ .pytest_cache tests/__pycache__
	find . -name "*.pyc" -delete
