import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
from meteostat import Point, Daily, Stations, Hourly
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
import pytz

# dictionary for places and their dummies
filetxt = open('cities.txt', 'r')
stringnum = filetxt.read()

# Remove the last two lines (possibly empty or header/footer lines)
stringnum = stringnum.split("\n")[:-1]

# Split lines and extract city names, city IDs, and time zones
city_names, city_ids, time_zones = zip(*[
    (" ".join(line.split()[:-2]), line.split()[-2], line.split()[-1]) 
    for line in stringnum if len(line.split()) >= 3
])
city_info = pd.DataFrame({"name" : city_names, "id" : city_ids, "wmo": "", "lat": "", "long": "", "time zone" : time_zones})

# Trying to find the exact weather stations based on WMO ID
stations = Stations()
stations = stations.bounds((90, -180), (0, 180))
c = stations.count()
station_ids_all = stations.fetch(c).icao
station_ids_all = station_ids_all.replace(pd.NA, "Missing")
for i in range(len(station_ids_all)):
    for j in range(20):
        if station_ids_all.iloc[i] == city_ids[j]:
            city_info.iloc[j, 2] = stations.fetch(i).iloc[-1, :].wmo
            city_info.iloc[j, 3] = stations.fetch(i).iloc[-1, :].latitude
            city_info.iloc[j, 4] = stations.fetch(i).iloc[-1, :].longitude

# Ensure the 'current_data' directory exists
os.makedirs(os.path.join('current_data'), exist_ok=True)

# Get the current weather (the 10 previous days up to today)
for i in range(20):
    weather_data_temp = pd.DataFrame()
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
    end = datetime(2025, 1, 1, 23, 59)

    # Fetch data for the past 10 days with model=False
    model = False
    data = Hourly(
        city_info.iloc[i, 2], start, end, time_zones[i], model
    )
    data = data.fetch()

    if not data.empty:
        if data['prcp'].isnull().sum() > 10:
            data_prcp = Hourly(
                city_info.iloc[i, 2], start, end, time_zones[i]
            )
            data_prcp = data_prcp.fetch()
            data['prcp'] = data_prcp['prcp']
        if data['pres'].isnull().sum() > 10:
            data_pres = Hourly(
                city_info.iloc[i, 2], start, end, time_zones[i]
            )
            data_pres = data_pres.fetch()
            data['pres'] = data_pres['pres']

    # If data is still empty, try with nearby stations
    if data.empty:
        stations_near = Stations()
        stations_near = stations_near.nearby(city_info.lat.iloc[i], city_info.long.iloc[i])
        station_near = stations_near.fetch(20)
        possible_wmos = station_near.wmo.dropna()
        l = len(possible_wmos)
        k = 1
        while k < l:
            start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
            end = datetime(2025, 1, 1, 23, 59)
            data = Hourly(
                possible_wmos.iloc[k], start, end, time_zones[i], model
            )
            data = data.fetch()
            if not data.empty:
                break
            k = k + 1

        # Fill missing data if needed
        if data['prcp'].isnull().sum() > 10:
            data_prcp = Hourly(
                possible_wmos.iloc[k], start, end, time_zones[i]
            )
            data_prcp = data_prcp.fetch()
            data['prcp'] = data_prcp['prcp']
        if data['pres'].isnull().sum() > 10:
            data_pres = Hourly(
                possible_wmos.iloc[k], start, end, time_zones[i]
            )
            data_pres = data_pres.fetch()
            data['pres'] = data_pres['pres']

    # Handle possible missing wind speed data
    if pd.isna(data['wspd'][0]):
        data['wspd'][0] = data['wspd'][1]

    # Save the fetched data to CSV
    weather_data_temp = pd.concat([weather_data_temp, data])
    output_path = os.path.join('current_data', 'original', f'city{i}.csv')
    weather_data_temp.to_csv(output_path)
    
    # Process the data (interpolate missing values)
    df = pd.read_csv(output_path)
    df_inter = df[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter = df_inter.interpolate(axis=0)  # Linear interpolation
    df_inter = df_inter.assign(time=df.time)
    df_inter = df_inter[['time', 'temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    output_path = os.path.join('current_data', 'cleaned', f'city{i}clean.csv')
    df_inter.to_csv(output_path, index=False)

    # **New logic: Check if the latest data needs to be updated**
    # Check if the last date in the current data is today or within the last few hours.
    df = pd.read_csv(output_path)
    local_timezone = pytz.timezone(time_zones[i])
    if pd.to_datetime(df['time'], errors='coerce').apply(lambda x: x if x.tzinfo is not None else local_timezone.localize(x)).max() < pd.Timestamp(datetime.now(local_timezone) - timedelta(hours = 2)):
        
        # Switch to model=True to fetch more recent data
        start = pd.to_datetime(df['time'], errors='coerce').apply(lambda x: x if x.tzinfo is not None else local_timezone.localize(x)).max().to_pydatetime().replace(tzinfo=None) + timedelta(hours = 1)
        end = datetime.now(local_timezone).replace(tzinfo=None)
        data = Hourly(
            city_info.iloc[i, 2], start, end
        )
        data = data.fetch()

        # Fill missing data if needed (similar to above)
        if not data.empty:
            if data['prcp'].isnull().sum() > 10:
                data_prcp = Hourly(
                    city_info.iloc[i, 2], start, end
                )
                data_prcp = data_prcp.fetch()
                data['prcp'] = data_prcp['prcp']
            if data['pres'].isnull().sum() > 10:
                data_pres = Hourly(
                    city_info.iloc[i, 2], start, end
                )
                data_pres = data_pres.fetch()
                data['pres'] = data_pres['pres']
            
            # Process the data (interpolate missing values)
            data = data[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
            data = data.interpolate(axis=0)  # Linear interpolation
            data = data.assign(time=df.time)
            data = data[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
            
            data = data.reset_index()  # This will move 'time' from index to a regular column
            data.rename(columns={'index': 'time'}, inplace=True)  # Rename the 'index' column to 'time'
            # Append the new data to the existing data
            
            weather_data_temp = pd.concat([df, data])

            # Save the updated data
            output_path = os.path.join('current_data', 'cleaned', f'city{i}clean.csv')
            weather_data_temp.to_csv(output_path, index=False)

    # Change formatting of the datetime column
    df = pd.read_csv(output_path)
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    df['time'] = df['time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x)
    output_path = os.path.join('current_data', 'cleaned', 'city' + str(i) + 'clean.csv')
    df.to_csv(output_path, index=False)
