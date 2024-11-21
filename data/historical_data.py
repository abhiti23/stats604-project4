#!pip install meteostat
#!pip install --upgrade certifi
#!pip install pip-system-certs
import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
from meteostat import Point, Daily, Stations, Hourly
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os

# Open and read the file
with open('cities.txt', 'r') as filetxt:
    stringnum = filetxt.read()

# Remove any empty lines and trim the content
stringnum = stringnum.strip().split("\n")

# Split lines and extract city names, city IDs, and time zones
city_names, city_ids, time_zones = zip(*[
    (" ".join(line.split()[:-2]), line.split()[-2], line.split()[-1])
    for line in stringnum if len(line.split()) >= 3
])

city_info = pd.DataFrame({"name" : city_names, "id" : city_ids, "wmo": "", "lat":"", "long":"", "time zone" : time_zones})


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
            
# Ensure the 'original' directory exists
os.makedirs(os.path.join('original'), exist_ok=True)    

# use the wmo code to get hourly data using Hourly from meteostat
weird_cities = [0, 5,8,9,16]
for i in range(20):
    weather_data_temp = pd.DataFrame()
    for year in range(2006, 2024):
        start = datetime(year, 9, 1)
        end = datetime(year, 12, 31, 23, 59)
        data = Hourly(  # access individual weather stations using WMO id (also based on time zone of location)
            city_info.iloc[i, 2], start, end, time_zones[i], False)
        data = data.fetch()
        if data.empty:
            stations_near = Stations()
            stations_near = stations_near.nearby(city_info.lat.iloc[i], city_info.long.iloc[i])
            station_near = stations_near.fetch(20)
            possible_wmos = station_near.wmo.dropna()
            l = len(possible_wmos)
            k = 1
            while (k < l):
                start = datetime(year, 9, 1)
                end = datetime(year, 12, 31, 23, 59)
                data = Hourly(  # access individual weather stations using WMO id
                    possible_wmos.iloc[k], start, end, time_zones[i], False)
                data = data.fetch()
                if not data.empty:
                    # weather_data_temp = pd.concat([weather_data_temp, data])
                    break
                k = k + 1

        if i in weird_cities:
            prcpcity0 = pd.DataFrame()
            stations_near = Stations()
            stations_near = stations_near.nearby(city_info.lat.iloc[i], city_info.long.iloc[i])
            station_near = stations_near.fetch(20)
            possible_wmos = station_near.wmo.dropna()
            for k in range(len(possible_wmos)):
                start = datetime(year, 9, 1)
                end = datetime(year, 12, 31, 23, 59)
                data = Hourly(  # access individual weather stations using WMO id
                    possible_wmos.iloc[k], start, end, time_zones[i], False)
                data = data.fetch()
                prcpcity0[str(k)] = data.prcp
            prcpavg = prcpcity0.mean(axis=1)
            data.prcp = prcpavg
            # print(data.head())

        weather_data_temp = pd.concat([weather_data_temp, data])

    # adding current year's data:
    start = datetime(2024, 9, 1)
    end = datetime(2024, 11, 13, 23, 59)
    data = Hourly(  # access individual weather stations using WMO id
        city_info.iloc[i, 2], start, end, time_zones[i], False)
    weather_data_temp = pd.concat([weather_data_temp, data.fetch()])
    
    # Construct the path to save the CSV file in the 'original' folder
    output_path = os.path.join('original', 'city' + str(i) + '.csv')
    
    # Save the DataFrame to the CSV file in the 'original' folder
    weather_data_temp.to_csv(output_path)



