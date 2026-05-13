# Makefile for MFRR Figure Generation
# Generates all figures for Appendices G and I

.PHONY: all clean plots tables

# Python interpreter
PYTHON := python3

# Output directories
FIGDIR := ../../figures
DATADIR := ../../data

# Figure targets
PLOTS := $(FIGDIR)/pt_energy_balance.pdf \
         $(FIGDIR)/psi_maps.pdf \
         $(FIGDIR)/psi_grad_maps.pdf \
         $(FIGDIR)/landauer_margins_scatter.pdf \
         $(FIGDIR)/d_phi_correlation.pdf

TABLES := $(FIGDIR)/landauer_table.tex \
          $(FIGDIR)/landauer_margins_stats.csv

# Default target: generate all figures and tables
all: plots tables

# Generate all plots
plots: $(PLOTS)

# Generate all tables
tables: $(TABLES)

# Individual figure rules
$(FIGDIR)/pt_energy_balance.pdf: plot_energy_balance.py $(DATADIR)/energy_timeseries.csv
	@mkdir -p $(FIGDIR)
	$(PYTHON) plot_energy_balance.py

$(FIGDIR)/psi_maps.pdf $(FIGDIR)/psi_grad_maps.pdf: plot_psi_fields.py $(DATADIR)/psi_fields.npz
	@mkdir -p $(FIGDIR)
	$(PYTHON) plot_psi_fields.py

$(FIGDIR)/landauer_margins_scatter.pdf: plot_landauer_margins.py $(DATADIR)/landauer_trials.csv
	@mkdir -p $(FIGDIR)
	$(PYTHON) plot_landauer_margins.py

$(FIGDIR)/d_phi_correlation.pdf: plot_d_phi_correlation.py $(DATADIR)/d_phi_series.csv
	@mkdir -p $(FIGDIR)
	$(PYTHON) plot_d_phi_correlation.py

# Generate LaTeX tables
$(FIGDIR)/landauer_table.tex $(FIGDIR)/landauer_margins_stats.csv: generate_landauer_table.py $(DATADIR)/landauer_trials.csv
	@mkdir -p $(FIGDIR)
	$(PYTHON) generate_landauer_table.py

# Clean generated files
clean:
	rm -rf $(FIGDIR)/*.pdf $(FIGDIR)/*.png $(FIGDIR)/*.tex $(FIGDIR)/*.csv

# Help target
help:
	@echo "MFRR Figure Generation Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all     - Generate all figures and tables (default)"
	@echo "  plots   - Generate all PDF/PNG plots"
	@echo "  tables  - Generate LaTeX tables and CSV summaries"
	@echo "  clean   - Remove all generated files"
	@echo "  help    - Show this message"
	@echo ""
	@echo "Requirements:"
	@echo "  - Python 3.12+"
	@echo "  - See requirements.txt for package dependencies"
	@echo "  - Data files in $(DATADIR)/"
	@echo ""
	@echo "Usage:"
	@echo "  make              # Generate everything"
	@echo "  make plots        # Generate plots only"
	@echo "  make clean all    # Rebuild from scratch"

