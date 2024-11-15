# not final yet

.PHONY: build rerun download analysis clean archive

# Default target to run when `make` is called with no target.
build: download analysis

# Rerun target: clean up and rerun analysis
rerun: clean analysis

# Download data (run Python script to fetch data)
download:
	@echo "Running download..."
	python3 -c 'import download; download.run()'

# Perform analysis (run Python scripts to preprocess and analyze data)
analysis:
	@echo "Running analysis..."
	python3 -c 'import analysis; analysis.preprocess()'
	python3 -c 'import analysis; analysis.main_analysis()'

# Clean up generated files and outputs
clean:
	@echo "Deleting all processed data and output..."
	rm -rf data/processed/*
	rm -rf analysis/*.html
	rm -rf output/*
	rm -f archive.tar.bz2

# Archive the entire project, excluding the .git folder
archive:
	@echo "Creating archive..."
	rm -f archive.tar.bz2
	tar --exclude='.git' -cjf /tmp/archive.tar.bz2 . && mv /tmp/archive.tar.bz2 .
