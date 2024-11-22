import os
import joblib
from sklearn.linear_model import HuberRegressor
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

def get_daily_stats(file_path,training):
    """
    Calculate the daily maximum, minimum, and average values for temp, dwpt, rhum, prcp, wspd, and pres columns.
    Convert temperature columns (temp and dwpt) from Celsius to Fahrenheit.
    """
    data = pd.read_csv(file_path)
    data['time'] = pd.to_datetime(data['time'],utc = True)
    data['date'] = data['time'].dt.date
    data['temp'] = data['temp'] * 9 / 5 + 32
    data['dwpt'] = data['dwpt'] * 9 / 5 + 32
    data['pres'] = data['pres'] - 1000
    columns_to_aggregate = ['temp', 'dwpt', 'rhum', 'prcp', 'wspd', 'pres']
    daily_stats = data.groupby('date')[columns_to_aggregate].agg(['max', 'min', 'mean'])
    daily_stats.columns = ['_'.join(col).strip() for col in daily_stats.columns.values]
    daily_stats.reset_index(inplace=True)

    daily_stats['year'] = daily_stats['date'].astype(str).str[:4]
    rows_2024 = daily_stats[daily_stats['year'] == '2024']
    if len(rows_2024) < 2:
        daily_stats = daily_stats[daily_stats['year'] != '2024']
    daily_stats.drop(columns=['year'], inplace=True)

    
    if training:
        daily_stats = daily_stats[~daily_stats['date'].astype(str).str.startswith('2024-11')]

    return daily_stats

def get_prediction_data(data, response_type,lag_level):
    """
    Generate training data for predictive modeling with lagged features.
    """
    response_map = {
        'min': 'temp_min',
        'max': 'temp_max',
        'mean': 'temp_mean'
    }
    lagged_data = data.copy()

    for col in data.columns:
        if col.startswith('temp'):
            for lag in range(1, lag_level + 1):
                lagged = data[col].shift(lag)
                lagged_data[f"{col}_lag{lag}"] = lagged
        elif col not in ['date', response_map[response_type]]:
            for lag in range(1, 5 + 1):
                lagged = data[col].shift(lag)
                lagged_data[f"{col}_lag{lag}"] = lagged
    columns = ['date',] + [col for col in lagged_data.columns if col not in ['date', 'YFuture']]
    lagged_data = lagged_data[columns]
    lagged_data.dropna(inplace=True)

    return lagged_data

def get_prediction_value(index, response_type, step_size, approach):
    if(approach == 1):
        model_dir = os.path.join(
            '../output/models/Huber',
            f"hubermodel_city_{index}_response_type_{response_type}_step_size_{step_size}.joblib"
        )
    elif(approach == 2):
        model_dir = os.path.join(
        '../output/models/Lasso',
        f"lassomodel_city_{index}_response_type_{response_type}_step_size_{step_size}.joblib"
    )
    model_obj = joblib.load(model_dir)
    lag_level = model_obj['best_params'][1]
    model_trained = model_obj['model']
    current_dir = os.path.join(
            'current_data/cleaned',
            f"city{index}clean.csv"
        )
    current_data = pd.read_csv(current_dir)
    daily_stats_df = get_daily_stats(current_dir,training = False)
    daily_stats_df
    prediction_data = get_prediction_data(data = daily_stats_df, response_type = response_type, lag_level = lag_level).tail(1).drop(columns = ['date'])
    prediction_value = model_trained.predict(prediction_data)
    return prediction_value


prediction_results = []
for c in range(20):
    for s in range(1,6):
        for r in ['min','mean','max']:
            value = get_prediction_value(index = c, response_type = r, step_size =s, approach = 1)
            prediction_results.append(float(value))


if isinstance(prediction_results, np.ndarray):
    prediction_results = prediction_results.tolist()
current_date = datetime.now()
print_res = f"\"{current_date.strftime('%Y-%m-%d')}\"" + "," + ",".join(f"{v:04.1f}" for v in prediction_results)
print(print_res)
output_dir = "../output/prediction_results"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

df_res = pd.DataFrame(prediction_results, columns=["Values"])
output_file = os.path.join(output_dir, current_date.strftime('%Y-%m-%d')+".csv")
df_res.to_csv(output_file, index=False)
