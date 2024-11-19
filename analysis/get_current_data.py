import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
from meteostat import Point, Daily, Stations, Hourly
from datetime import datetime
import numpy as np
import pandas as pd
import os

# dictionary for places and their dummies
filetxt = open('cities.txt','r')
stringnum = filetxt.read()
stringnum = stringnum.split("\n")[:-2]
city_names = [i.split("  ")[0] for i in stringnum]
city_ids = [i.split("  ")[-1].strip() for i in stringnum]
city_info = pd.DataFrame({"name" : city_names, "id" : city_ids, "wmo": "", "lat":"", "long":""})

# trying to find the exact weather stations we need based on IDs
stations = Stations()
stations = stations.bounds((90, -180), (0, 180))
c = stations.count()
station_ids_all = stations.fetch(c).icao
station_ids_all = station_ids_all.replace(pd.NA, "Missing")
for i in range(len(station_ids_all)):
    for j in range(20):
        if station_ids_all.iloc[i] == city_ids[j]:
            city_info.iloc[j,2] = stations.fetch(i).iloc[-1,:].wmo
            city_info.iloc[j,3] = stations.fetch(i).iloc[-1,:].latitude
            city_info.iloc[j,4] = stations.fetch(i).iloc[-1,:].longitude

# Ensure the 'current_data' directory exists
os.makedirs(os.path.join('current_data'), exist_ok=True)


for i in range(20):
    weather_data_temp = pd.DataFrame()
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.utcnow()
    data = Hourly(  # access individual weather stations using WMO id
        city_info.iloc[i, 2], start, end)
    weather_data_temp = pd.concat([weather_data_temp, data.fetch()])
    output_path = os.path.join('current_data', 'original', 'city' + str(i) + '.csv')
    weather_data_temp.to_csv(output_path)
    
    

    # Process the data
    df = pd.read_csv(output_path)
    df_inter = df[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter = df_inter.interpolate(axis=0)  # linear interpolation
    df_inter = df_inter.assign(time=df.time)
    df_inter = df_inter[['time','temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    output_path = os.path.join('current_data', 'cleaned', 'city' + str(i) + 'clean.csv')
    df_inter.to_csv(output_path)