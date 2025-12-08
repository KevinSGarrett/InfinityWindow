PYTHON ?= python
PYTHONPATH_ROOT ?= .
# Windows cmd.exe style env set; include repo root (..) when running from backend
SET_PYTHONPATH := set PYTHONPATH=..;.;backend;$(PYTHONPATH)
COVERAGE_ARGS ?= --cov=app --cov-report=xml:../coverage-api.xml
COVERAGE_FAIL_UNDER ?=

.PHONY: ci backend-tests frontend-build smoke

ci: backend-tests frontend-build

backend-tests:
	cd backend && $(SET_PYTHONPATH) && $(PYTHON) -m pytest ..\qa\tests_api $(COVERAGE_ARGS) $(if $(COVERAGE_FAIL_UNDER),--cov-fail-under=$(COVERAGE_FAIL_UNDER),)

frontend-build:
	cd frontend && npm run build

smoke:
	cd backend && $(SET_PYTHONPATH) && $(PYTHON) -m qa.run_smoke

.PHONY: perf
perf:
	cd backend && $(SET_PYTHONPATH) && $(PYTHON) ..\tools\perf_smoke.py

