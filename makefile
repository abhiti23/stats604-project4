.PHONY: clean rawdata predictions

# The default task (first target) will run when you just type `make`
all:
	@echo "Running all analyses (except downloading raw data and making current predictions)..."
	cd data && python cleaning.py 
	cd analysis && python training.py  

clean:
	@echo "Deleting everything except for the code and raw data (as originally downloaded)..."
	rm -f data/cleaned/*
	rm -f data/current_data/original/*
	rm -f data/current_data/cleaned/*
	rm -f analysis/*.html	
	rm -f output/*
	rm -f output/models/Huber/*
	rm -f output/models/Lasso/*

rawdata:
	@echo "Deleting and re-downloading the raw data..."
	rm -f data/original/*.csv
	cd data && python historical_data.py

predictions:
	@echo "Making current prediction..."
	cd analysis && python predictions.py 
