PYTHON ?= python
VENV ?= .venv
PIP := $(VENV)/Scripts/pip
PY := $(VENV)/Scripts/python

.PHONY: help setup-backend install-backend run-backend freeze-backend

help:
	@echo "Targets disponiveis:"
	@echo "  setup-backend   - cria .venv e instala dependencias do backend"
	@echo "  install-backend - instala/atualiza dependencias do backend"
	@echo "  run-backend     - sobe API FastAPI em modo reload"
	@echo "  freeze-backend  - gera requirements.txt a partir da venv"

setup-backend:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r backend/requirements.txt

install-backend:
	$(PIP) install -r backend/requirements.txt

run-backend:
	cd backend && ../$(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

freeze-backend:
	$(PIP) freeze > backend/requirements.txt
