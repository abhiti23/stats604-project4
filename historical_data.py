pip install meteostat
pip install --upgrade certifi
pip install pip-system-certs
import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
from meteostat import Point, Daily, Stations, Hourly
from datetime import datetime
import numpy as np
import pandas as pd
#%%
# dictionary for places and their dummies
filetxt = open('cities.txt','r')
stringnum = filetxt.read()
stringnum = stringnum.split("\n")[:-2]
city_names = [i.split("  ")[0] for i in stringnum]
city_ids = [i.split("  ")[-1].strip() for i in stringnum]
city_info = pd.DataFrame({"name" : city_names, "id" : city_ids, "wmo": ""})

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

# use the wmo code to get hourly data using Hourly from meteostat
for i in range(20):
    weather_data_temp = pd.DataFrame()
    for year in range(2004, 2024):
        start = datetime(year, 9, 1)
        end = datetime(year, 12, 31, 23, 59)
        data = Hourly(  # access individual weather stations using WMO id
        city_info.iloc[i,-1], start, end)
        weather_data_temp = pd.concat([weather_data_temp, data.fetch()])
    # adding current year's data:
    start = datetime(2024, 9, 1)
    end = datetime(2024, 11, 13, 23, 59)
    data = Hourly(  # access individual weather stations using WMO id
    city_info.iloc[i,-1], start, end)
    weather_data_temp = pd.concat([weather_data_temp, data.fetch()])
    weather_data_temp.to_csv("city"+str(i)+".csv")