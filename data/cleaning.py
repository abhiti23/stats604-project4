import numpy as np
import pandas as pd
import os
# import scipy
'''
previous code:
for i in range(20):
    name = 'city' + str(i) + '.csv'
    df = pd.read_csv(name)
    df_inter = df[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter = df_inter.interpolate(axis=0) # linear interpolation
    df_inter = df_inter.assign(time=df.time)
    df_inter = df_inter[['time','temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter.to_csv("city" + str(i) + "clean.csv")
'''

# Ensure the 'cleaned' directory exists
os.makedirs(os.path.join('cleaned'), exist_ok=True)

# Loop through the city files, assuming they exist in the 'original' folder
for i in range(20):
    # Construct the input and output file paths
    input_file = os.path.join('original', 'city' + str(i) + '.csv')
    output_file = os.path.join('cleaned', 'city' + str(i) + 'clean.csv')
    
    # Read the CSV file from the 'original' folder
    df = pd.read_csv(input_file)
    
    # Process the data
    df_inter = df[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter = df_inter.interpolate(axis=0)  # linear interpolation
    df_inter = df_inter.assign(time=df.time)
    df_inter = df_inter[['time','temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    NA_column = df_inter.isna().any()

    if NA_column.any():
        bad_cols = np.where(NA_column)[0]
        if np.sum(np.array(df_inter.iloc[:, list(NA_column)].isna(), dtype=bool))  < 10:
            df_inter = df_inter.fillna(0)
    # Save the cleaned data to the 'cleaned' folder
    df_inter.to_csv(output_file, index=False)  # index=False to avoid writing row indices
