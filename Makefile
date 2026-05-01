.PHONY: run test

run:
	PYTHONPATH=src python3 -m olfactory_warehouse

test:
	PYTHONPATH=src python3 -m unittest discover -s tests
