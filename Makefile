.PHONY: settings test backend-test frontend-test build up down

# Reconcile .claude/settings.json with the committed template.
# Run after a Claude Code session if the file drifted.
settings:
	cp .claude/settings.json.template .claude/settings.json
	@echo "settings.json reconciled with template"

# Run all tests.
test: backend-test frontend-test

backend-test:
	cd backend && pytest -q

frontend-test:
	cd frontend && npm test --silent

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down
