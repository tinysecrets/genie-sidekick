# Makefile — shortcuts for the most common operations.
# All targets are idempotent.

.PHONY: bootstrap deps test lint genie plan audit ui rotate-agent rotate-master clean-cache clean

bootstrap:
	bash bootstrap.sh

deps:
	python3 -m pip install -r requirements.txt

test:
	python3 -m pytest -q tests

lint:
	python3 -m pip install --quiet ruff && ruff check agents keys scripts tests --select E,F,W --exclude '* - JUSTINSPC.py'

# Run Genie with a goal. Usage: make genie GOAL="build me X"
genie:
	python3 agents/genie/genie.py "$(GOAL)"

plan:
	python3 agents/genie/genie.py --dry-run "$(GOAL)"

audit:
	python3 scripts/audit_view.py

ui:
	python3 scripts/ui_server.py

rotate-agent:
	python3 scripts/derive_keys.py --rotate agent

rotate-master:
	python3 scripts/derive_keys.py --rotate master

clean-cache:
	find . -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache

clean:
	rm -rf keys/vault/keys.enc keys/vault/salt.bin keys/vault/meta.json keys/vault/audit.log
	find . -name __pycache__ -prune -exec rm -rf {} +
