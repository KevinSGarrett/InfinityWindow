PYTHON ?= python
PYTHONPATH_ROOT ?= .

ifeq ($(OS),Windows_NT)
PATH_SEP := ;
else
PATH_SEP := :
endif

PYTHONPATH_VALUE := $(PYTHONPATH_ROOT)$(PATH_SEP)backend$(if $(PYTHONPATH),$(PATH_SEP)$(PYTHONPATH),)

COVERAGE_REPORT ?= coverage-api.xml
# Leave coverage disabled by default so pytest-cov is optional; set
# COVERAGE_ARGS="--cov=app --cov-report=xml:$(COVERAGE_REPORT)" if desired.
COVERAGE_ARGS ?=
COVERAGE_FAIL_UNDER ?=

.PHONY: ci backend-tests frontend-build smoke perf

ci: backend-tests frontend-build

backend-tests: export PYTHONPATH := $(PYTHONPATH_VALUE)
backend-tests:
	$(PYTHON) -m pytest qa/tests_api $(COVERAGE_ARGS) $(if $(COVERAGE_FAIL_UNDER),--cov-fail-under=$(COVERAGE_FAIL_UNDER),)

frontend-build:
	npm run build --prefix frontend

smoke: export PYTHONPATH := $(PYTHONPATH_VALUE)
smoke:
	$(PYTHON) -m qa.run_smoke

perf: export PYTHONPATH := $(PYTHONPATH_VALUE)
perf:
	$(PYTHON) tools/perf_smoke.py
