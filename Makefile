PYTHON ?= python
ROOT = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))


clean:
	find . -name '__pycache__' | xargs rm -rf
	rm -rf htmlcov .coverage .pytest_cache


format:
	$(PYTHON) -m black mppwscrapper
	$(PYTHON) -m isort mppwscrapper
