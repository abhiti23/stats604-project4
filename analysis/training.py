import os
import datetime
import joblib
from sklearn.linear_model import HuberRegressor
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error
import warnings
import numpy as np
import pandas as pd
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

def get_training_data(data, response_type, step_size, lag_level):
    """
    Generate training data for predictive modeling with lagged features.
    """
    response_map = {
        'min': 'temp_min',
        'max': 'temp_max',
        'mean': 'temp_mean'
    }
    data['YFuture'] = data[response_map[response_type]].shift(-step_size)
    lagged_data = data.copy()

    for col in data.columns:
        if col.startswith('temp'):
            for lag in range(1, lag_level + 1):
                lagged = data[col].shift(lag)
                lagged_data[f"{col}_lag{lag}"] = lagged
        elif col not in ['date', 'YFuture', response_map[response_type]]:
            for lag in range(1, 5 + 1):
                lagged = data[col].shift(lag)
                lagged_data[f"{col}_lag{lag}"] = lagged
    columns = ['date', 'YFuture'] + [col for col in lagged_data.columns if col not in ['date', 'YFuture']]
    lagged_data = lagged_data[columns]
    lagged_data.dropna(inplace=True)

    return lagged_data

def get_huber_tuning_res(daily_stats_df, response_type, step_size):
    """
    Tune Huber Regression parameters (epsilon and lag_level) using a rolling validation approach.
    """
    epsilon_values = np.linspace(1, 3, 5)  # 10 values between 0.5 and 2.5
    lag_levels = range(1, 6)  # Lag levels from 1 to 10
    daily_stats_df['date'] = pd.to_datetime(daily_stats_df['date'],utc = True)
    year = daily_stats_df['date'].dt.year
    best_combination = None
    best_mse = float('inf')
    for epsilon in epsilon_values:
        for lag_level in lag_levels:
            mse_scores = []
            training_data = get_training_data(daily_stats_df, response_type, step_size, lag_level)
            unique_years = sorted(year.unique())
            for i in range(len(unique_years) - 1):
                train_years = unique_years[:i + 1]
                test_year = unique_years[i + 1]
                train_data = training_data[training_data['date'].dt.year.isin(train_years)]
                test_data = training_data[training_data['date'].dt.year == test_year]
                X_train = train_data.drop(columns=['date', 'YFuture'])
                y_train = train_data['YFuture']
                X_test = test_data.drop(columns=['date', 'YFuture'])
                y_test = test_data['YFuture']
                model = HuberRegressor(epsilon=epsilon)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                mse_scores.append(mse)
            avg_mse = np.mean(mse_scores)
            if avg_mse < best_mse:
                best_mse = avg_mse
                best_combination = (epsilon, lag_level)
    
    return best_combination

def get_huber_res(daily_stats_df, best_params, step_size, response_type, save, index):
    """
    Fit a Huber Regression model using the best parameters and training data.
    """
    epsilon, lag_level = best_params
    training_data = get_training_data(
        data=daily_stats_df,
        response_type=response_type,
        step_size=step_size,
        lag_level=lag_level
    )
    X_train = training_data.drop(columns=['date', 'YFuture'])
    y_train = training_data['YFuture']
    model = HuberRegressor(epsilon=epsilon)
    model.fit(X_train, y_train)
    if save:
        output_dir = "../output/models/Huber"
        os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist
        model_filename = os.path.join(
            output_dir,
            f"hubermodel_city_{index}_response_type_{response_type}_step_size_{step_size}.joblib"
        )
        save_obj = {
            "model": model,
            "best_params": best_params
        }
        joblib.dump(save_obj, model_filename)
        print(f"Model and parameters saved as {model_filename}")
    return model

def huber_training(city_index, step_size, response_type, save):
    """
    The whole process for fitting a Huber Regression
    """
    file_path = os.path.join("..", "data", "cleaned", f"city{city_index}clean.csv")
    daily_stats_df = get_daily_stats(file_path,training = True)
    log_info = 'Tuning Huber Parameters for city' + str(city_index) + ' with ' + response_type + ' response step ' + str(step_size)
    print(log_info)
    best_params = get_huber_tuning_res(daily_stats_df, response_type=response_type, step_size=step_size)
    trained_model = get_huber_res(
    daily_stats_df=daily_stats_df,
    best_params=best_params,
    step_size=step_size,
    response_type=response_type,
    save=save,
    index=city_index
)
    res_obj = {"model": trained_model,"best_params": best_params}
    return res_obj

def get_lasso_tuning_res(daily_stats_df, response_type, step_size):
    """
    Tune Lasso Regression parameters (lambda and lag_level) using a rolling validation approach.
    """
    lambda_values = np.linspace(0.1, 2.0, 5)  # 10 values between 0.1 and 1.0
    lag_levels = range(1, 6)  # Lag levels from 1 to 10
    daily_stats_df['date'] = pd.to_datetime(daily_stats_df['date'],utc = True)
    year = daily_stats_df['date'].dt.year
    best_combination = None
    best_mse = float('inf')
    
    for lambda_ in lambda_values:
        for lag_level in lag_levels:
            mse_scores = []
            training_data = get_training_data(daily_stats_df, response_type, step_size, lag_level)
            unique_years = sorted(year.unique())
            for i in range(len(unique_years) - 1):
                train_years = unique_years[:i + 1]
                test_year = unique_years[i + 1]
                train_data = training_data[training_data['date'].dt.year.isin(train_years)]
                test_data = training_data[training_data['date'].dt.year == test_year]
                X_train = train_data.drop(columns=['date', 'YFuture'])
                y_train = train_data['YFuture']
                X_test = test_data.drop(columns=['date', 'YFuture'])
                y_test = test_data['YFuture']
                model = Lasso(alpha=lambda_)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                mse_scores.append(mse)
            avg_mse = np.mean(mse_scores)
            if avg_mse < best_mse:
                best_mse = avg_mse
                best_combination = (lambda_, lag_level)
    
    return best_combination

def get_lasso_res(daily_stats_df, best_params, step_size, response_type, save, index):
    """
    Fit a Lasso Regression model using the best parameters and training data.
    """
    lambda_, lag_level = best_params
    training_data = get_training_data(
        data=daily_stats_df,
        response_type=response_type,
        step_size=step_size,
        lag_level=lag_level
    )
    X_train = training_data.drop(columns=['date', 'YFuture'])
    y_train = training_data['YFuture']
    model = Lasso(alpha=lambda_)
    model.fit(X_train, y_train)
    if save:
        output_dir = "../output/models/Lasso"
        os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist
        model_filename = os.path.join(
            output_dir,
            f"lassomodel_city_{index}_response_type_{response_type}_step_size_{step_size}.joblib"
        )
        save_obj = {
            "model": model,
            "best_params": best_params
        }
        joblib.dump(save_obj, model_filename)
        print(f"Model and parameters saved as {model_filename}")
    return model

def lasso_training(city_index, step_size, response_type, save):
    """
    The whole process for fitting a Lasso Regression
    """
    file_path = os.path.join("..", "data", "cleaned", f"city{city_index}clean.csv")
    daily_stats_df = get_daily_stats(file_path,training = True)
    log_info = 'Tuning Lasso Parameters for city' + str(city_index) + ' with ' + response_type + ' response step ' + str(step_size)
    print(log_info)
    best_params = get_lasso_tuning_res(daily_stats_df = daily_stats_df, response_type=response_type, step_size=step_size)
    trained_model = get_lasso_res(
    daily_stats_df=daily_stats_df,
    best_params=best_params,
    step_size=step_size,
    response_type=response_type,
    save=save,
    index=city_index
)
    res_obj = {"model": trained_model,"best_params": best_params}
    return res_obj


from joblib import Parallel, delayed
def run_training(city_index, step_size, response_type, save=True):
    try:
        return {'huber':huber_training(city_index, step_size, response_type, save),
               'lasso': lasso_training(city_index, step_size, response_type, save)}
    except Exception as e:
        print(f"Error in city_index={city_index}, step_size={step_size}, response_type={response_type}: {e}")
        return None
city_indices = range(20)
step_sizes = range(1, 6)
response_types = ['min','mean','max']

tasks = [
    (city_index, step_size, response_type)
    for city_index in city_indices
    for step_size in step_sizes
    for response_type in response_types
]
results = Parallel(n_jobs=6)(
    delayed(run_training)(city_index, step_size, response_type)
    for city_index, step_size, response_type in tasks
)
