.PHONY: init venv deps all t7 t8 t9 t10 t11 phase2 clean

PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := env/.venv

init: venv deps

venv:
	$(PYTHON) -m venv $(VENV)

deps:
	$(VENV)/bin/$(PIP) install -U pip
	$(VENV)/bin/$(PIP) install numpy scipy pandas pyyaml matplotlib

all: phase2

phase2: t7 t8 t9 t10 t11

t7:
	$(VENV)/bin/$(PYTHON) -m src.rcp2.run_t7

t8:
	$(VENV)/bin/$(PYTHON) -m src.rcp2.run_t8

t9:
	$(VENV)/bin/$(PYTHON) -m src.rcp2.run_t9

t10:
	$(VENV)/bin/$(PYTHON) -m src.rcp2.run_t10

t11:
	$(VENV)/bin/$(PYTHON) -m src.rcp2.run_t11

clean:
	rm -rf results/* logs/*

