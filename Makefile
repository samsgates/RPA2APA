.PHONY: api-test api-run web-run cli-install demo

api-test:
	cd apps/api && pytest

api-run:
	cd apps/api && .venv/bin/python -m uvicorn rpa2apa_api.main:app --reload --port 8080

web-run:
	cd apps/web && npm run dev

cli-install:
	pip install -e packages/rpa2apa_cli

demo:
	rpa2apa analyze examples/uipath-invoice
