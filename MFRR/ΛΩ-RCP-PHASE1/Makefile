.PHONY: init venv deps all l1 l1_lap l2 l3 rg pc clean

PYTHON := env/.venv/bin/python
PIP := env/.venv/bin/pip

init: venv deps

venv:
	python3 -m venv env/.venv

deps:
	$(PIP) install -U pip
	$(PIP) install numpy scipy networkx pandas matplotlib numba pyyaml

all: l1_lap l2 l3 rg pc

l1:
	$(PYTHON) -m src.rcp.run_l1

l1_lap:
	$(PYTHON) -m src.rcp.run_l1_lap

l1_curv:
	$(PYTHON) -m src.rcp.run_l1_curvature_variants

l2:
	$(PYTHON) -m src.rcp.run_l2

l3:
	$(PYTHON) -m src.rcp.run_l3

rg:
	$(PYTHON) -m src.rcp.run_rg

pc:
	$(PYTHON) -m src.rcp.run_pc

clean:
	rm -rf results/* logs/*

