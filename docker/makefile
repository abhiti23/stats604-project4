.PHONY: clean raw data predictions

# The default task (first target) will run when you just type `make`
all:
  @echo "Running all analyses (except downloading raw data and making current predictions)..."
  cd analysis && python cleaning.py
  python model.py  

clean:
	echo "Deleting all cleaned data and output..."
	rm -f data/cleaned/*
	rm -f analysis/*.html	
	rm -f output/*

raw data:
  rm -f data/original/*.csv
  cd analysis && python historical_data.py

predictions:
  cd analysis && python predictions.py 
