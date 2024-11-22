.PHONY: clean rawdata predictions

# The default task (first target) will run when you just type `make`
all:
    @cd data && python cleaning.py 2>/dev/null
    @cd analysis && python training.py 2>/dev/null

clean:
    @rm -f data/cleaned/* 2>/dev/null
    @rm -f analysis/current_data/original/* 2>/dev/null
    @rm -f analysis/current_data/cleaned/* 2>/dev/null
    @rm -f output/* 2>/dev/null

rawdata:
    @rm -f data/original/*.csv 2>/dev/null
    @cd data && python historical_data.py 2>/dev/null

predictions:
    @cd analysis && python get_current_data.py 2>/dev/null
    @cd analysis && python predictions.py
