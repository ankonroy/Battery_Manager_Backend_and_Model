import pandas as pd
import numpy as np

def engineer_features_from_sessions(sessions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw session logs into feature vectors for ML models.
    """
    # 1. Basic cleaning
    sessions_df = sessions_df.copy()
    
    # 2. Time-based features
    sessions_df['hour_of_day'] = pd.to_datetime(sessions_df['session_timestamp_utc']).dt.hour
    sessions_df['day_of_week'] = pd.to_datetime(sessions_df['session_timestamp_utc']).dt.dayofweek
    
    # 3. Aggregated metrics (per device)
    # This requires grouped data by device_id
    sessions_df = sessions_df.sort_values(['device_id', 'session_timestamp_utc'])
    
    # Rolling averages for health trajectory
    sessions_df['health_30d_avg'] = sessions_df.groupby('device_id')['health_pct'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())
    sessions_df['health_delta_30d'] = sessions_df.groupby('device_id')['health_pct'].transform(lambda x: x.diff(periods=30).fillna(0))
    
    # Cumulative stress exposure
    sessions_df['cumulative_stress'] = sessions_df.groupby('device_id')['stress_score'].cumsum()
    
    # C-rate (current / capacity)
    sessions_df['c_rate'] = sessions_df['avg_current_ma'] / sessions_df['design_capacity_mah']
    
    # 4. Normalization / Encoding
    # For models like LSTM, we'll need specific scaling
    return sessions_df

def extract_time_series_features(voltage_samples: list, current_samples: list):
    """
    Extracts statistical features from the downsampled voltage/current curves (20 points each).
    """
    v = np.array(voltage_samples)
    i = np.array(current_samples)
    
    features = {
        'v_mean': np.mean(v),
        'v_std': np.std(v),
        'v_skew': pd.Series(v).skew(),
        'i_mean': np.mean(i),
        'i_std': np.std(i),
        'i_cv': np.std(i) / np.abs(np.mean(i)) if np.mean(i) != 0 else 0
    }
    return features
