import pandas as pd
# import scipy
for i in range(20):
    name = 'city' + str(i) + '.csv'
    df = pd.read_csv(name)
    df_inter = df[['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter = df_inter.interpolate(axis=0) # linear interpolation
    df_inter = df_inter.assign(time=df.time)
    df_inter = df_inter[['time','temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']]
    df_inter.to_csv("city" + str(i) + "clean.csv")
