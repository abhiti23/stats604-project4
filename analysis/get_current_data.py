# get current 
import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
from meteostat import Point, Daily, Stations, Hourly
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os

# dictionary for places and their dummies
filetxt = open('cities.txt','r')
stringnum = filetxt.read()

# Remove the last two lines (possibly empty or header/footer lines)
stringnum = stringnum.split("\n")[:-1]

# Split lines and extract city names, city IDs, and time zones
city_names, city_ids, time_zones = zip(*[
    ( " ".join(line.split()[:-2]), line.split()[-2], line.split()[-1] ) 
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

# Ensure the 'current_data' directory exists
os.makedirs(os.path.join('current_data'), exist_ok=True)

# get the current weather (the 10 previous days up to today)
for i in range(20):
    weather_data_temp = pd.DataFrame()
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
    end = datetime(2025, 1, 1, 23, 59)
    data = Hourly(  # access individual weather stations using WMO id
        city_info.iloc[i, 2], start, end, time_zones[i], False)
    data = data.fetch()
    if not data.empty:
        if data['prcp'].isnull().sum() >10:
            data_prcp = Hourly(  # access individual weather stations using WMO id
            city_info.iloc[i, 2], start, end, time_zones[i])
            data_prcp = data_prcp.fetch()
            data['prcp'] = data_prcp['prcp']
        if data['pres'].isnull().sum() >10:
            data_pres = Hourly(  # access individual weather stations using WMO id
            city_info.iloc[i, 2], start, end, time_zones[i])
            data_pres = data_pres.fetch()
            data['pres'] = data_pres['pres']
    if data.empty:
        stations_near = Stations()
        stations_near = stations_near.nearby(city_info.lat.iloc[i], city_info.long.iloc[i])
        station_near = stations_near.fetch(20)
        possible_wmos = station_near.wmo.dropna()
        l = len(possible_wmos)
        k = 1
        while (k < l):
            start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
            end = datetime(2025, 1, 1, 23, 59)
            data = Hourly(  # access individual weather stations using WMO id
                possible_wmos.iloc[k], start, end, time_zones[i], False)
            data = data.fetch()
            if not data.empty:
                # weather_data_temp = pd.concat([weather_data_temp, data])
                break
            k = k + 1
        if data['prcp'].isnull().sum() >10:
            data_prcp = Hourly(  # access individual weather stations using WMO id
            possible_wmos.iloc[k], start, end, time_zones[i])
            data_prcp = data_prcp.fetch()
            data['prcp'] = data_prcp['prcp']
        if data['pres'].isnull().sum() >10:
            data_pres = Hourly(  # access individual weather stations using WMO id
            possible_wmos.iloc[k], start, end, time_zones[i])
            data_pres = data_pres.fetch()
            data['pres'] = data_pres['pres']

    if pd.isna(data['wspd'][0]):
        data['wspd'][0] = data['wspd'][1]
        
        # print(data.head())

    weather_data_temp = pd.concat([weather_data_temp, data])
            
    output_path = os.path.join('current_data', 'original', 'city' + str(i) + '.csv')
    weather_data_temp.to_csv(output_path)
    
    # change formatting of the datetime column
    df = pd.read_csv(output_path)
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    df['time'] = df['time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x)
    # Save the DataFrame back to the same CSV file (overwrite)
    df.to_csv(output_path, index=False)
    
    

    # Process the data
    df = pd.read_csv(output_path)
    df_inter = df[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter = df_inter.interpolate(axis=0)  # linear interpolation
    df_inter = df_inter.assign(time=df.time)
    df_inter = df_inter[['time','temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    output_path = os.path.join('current_data', 'cleaned', 'city' + str(i) + 'clean.csv')
    df_inter.to_csv(output_path, index=False)
