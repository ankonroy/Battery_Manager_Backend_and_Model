import marimo

__generated_with = "0.21.1"
app = marimo.App()


@app.cell
def _():
    # notebooks/02_prepare_rul_data.py
    # Prepare battery data for RUL prediction

    import marimo as mo
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    return Path, mo, np, pd, plt


@app.cell
def _(Path, mo):
    # ============================================
    # CONFIGURATION
    # ============================================

    NOTEBOOK_DIR = Path(__file__).parent if '__file__' in dir() else Path.cwd()
    MODEL_DIR = NOTEBOOK_DIR.parent
    DATA_PROCESSED = MODEL_DIR / "data" / "processed"

    # Input file
    input_csv = DATA_PROCESSED / "nasa_training_data.csv"

    # Output files
    output_csv = DATA_PROCESSED / "nasa_rul_training_data.csv"
    features_csv = DATA_PROCESSED / "nasa_rul_features.csv"

    mo.md("# Prepare RUL Training Dataset")
    mo.md(f"**Input:** `{input_csv}`")
    mo.md(f"**Output:** `{output_csv}`")
    return MODEL_DIR, input_csv


@app.cell
def _(input_csv, mo, pd):
    # ============================================
    # SECTION 1: Load Data
    # ============================================

    mo.md("## 1. Loading Data")

    df = pd.read_csv(input_csv)
    mo.md(f"**Shape:** {df.shape[0]:,} rows, {df.shape[1]} columns")
    mo.md(f"**Batteries:** {df['battery_id'].nunique()}")
    mo.md(f"**Health range:** {df['soh_percent'].min():.1f}% - {df['soh_percent'].max():.1f}%")

    df.head(10)
    return (df,)


@app.cell
def _(df, mo, pd):
    # ============================================
    # SECTION 2 (Revised): Calculate RUL to 70% health
    # ============================================

    mo.md("## 2. Calculate Remaining Useful Life (RUL)")

    # Change target to 70% (since many batteries only go to 70%)
    TARGET_HEALTH = 70

    mo.md(f"**Target:** Predict cycles until battery reaches {TARGET_HEALTH}% health")

    def calculate_rul_for_battery(battery_df):
        """Calculate RUL for each cycle in a battery"""
        battery_df = battery_df.copy()
        battery_df = battery_df.sort_values('cycle_number')

        # Find first cycle where health drops below target
        below_target = battery_df[battery_df['soh_percent'] <= TARGET_HEALTH]

        if len(below_target) > 0:
            eol_cycle = below_target['cycle_number'].iloc[0]
            battery_df['rul_cycles'] = battery_df['cycle_number'].apply(
                lambda x: max(0, eol_cycle - x)
            )
            battery_df['reached_target'] = True
        else:
            # Use last cycle as proxy (didn't reach target)
            max_cycle = battery_df['cycle_number'].max()
            battery_df['rul_cycles'] = battery_df['cycle_number'].apply(
                lambda x: max(0, max_cycle - x)
            )
            battery_df['reached_target'] = False

        return battery_df

    # Apply to each battery
    rul_dfs = []
    for battery_id in df['battery_id'].unique():
        battery_df = df[df['battery_id'] == battery_id].copy()
        battery_df = calculate_rul_for_battery(battery_df)
        rul_dfs.append(battery_df)

    rul_df = pd.concat(rul_dfs, ignore_index=True)

    mo.md(f"### RUL Statistics (Target: {TARGET_HEALTH}%):")
    mo.md(f"**Max RUL:** {rul_df['rul_cycles'].max()} cycles")
    mo.md(f"**Mean RUL:** {rul_df['rul_cycles'].mean():.1f} cycles")

    # Now check training size
    training_df_temp = rul_df[rul_df['rul_cycles'] > 0].copy()
    mo.md(f"**Training samples (RUL > 0):** {len(training_df_temp):,}")

    training_df_temp[['battery_id', 'cycle_number', 'soh_percent', 'rul_cycles']].head(10)
    return (rul_df,)


@app.cell
def _(mo, np, rul_df):
    # ============================================
    # SECTION 3: Feature Engineering
    # ============================================

    mo.md("## 3. Feature Engineering")

    def create_features(df):
        """Create features for RUL prediction"""
        df = df.copy()
        df = df.sort_values(['battery_id', 'cycle_number'])

        # 1. Degradation rate (change in SOH per cycle)
        df['soh_change'] = df.groupby('battery_id')['soh_percent'].diff()
        df['degradation_rate'] = -df['soh_change']  # Positive = degradation

        # 2. Rolling statistics (last 5 cycles)
        df['soh_ma5'] = df.groupby('battery_id')['soh_percent'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        )
        df['temp_ma5'] = df.groupby('battery_id')['avg_temperature_c'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        )

        # 3. Cumulative features
        df['cycles_so_far'] = df['cycle_number']
        df['soh_loss_so_far'] = 100 - df['soh_percent']

        # 4. Time-based features
        df['log_cycle'] = np.log1p(df['cycle_number'])
        df['sqrt_cycle'] = np.sqrt(df['cycle_number'])

        # 5. Temperature features
        df['temp_range'] = df['max_temperature_c'] - df['min_temperature_c']

        return df

    feature_df = create_features(rul_df)

    mo.md(f"### Feature Summary")
    mo.md(f"**Original columns:** {len(rul_df.columns)}")
    mo.md(f"**After feature engineering:** {len(feature_df.columns)}")
    mo.md(f"**New features:** soh_change, degradation_rate, soh_ma5, temp_ma5, log_cycle, sqrt_cycle, temp_range")

    feature_df.head(10)
    return (feature_df,)


@app.cell
def _(feature_df, mo, pd):
    # ============================================
    # SECTION 4: Filter for Training
    # ============================================

    mo.md("## 4. Filter for Training")

    # Only use early cycles for training (first 80% of battery life)
    # This mimics real-world scenario where we predict from early data

    def filter_early_cycles(df, early_ratio=0.8):
        """Keep only early cycles for training"""
        filtered_dfs = []

        for battery_id in df['battery_id'].unique():
            battery_df = df[df['battery_id'] == battery_id].copy()
            max_cycle = battery_df['cycle_number'].max()
            early_max = int(max_cycle * early_ratio)

            early_df = battery_df[battery_df['cycle_number'] <= early_max]
            filtered_dfs.append(early_df)

        return pd.concat(filtered_dfs, ignore_index=True)

    # Keep cycles where RUL > 0 (still has life left)
    training_df = feature_df[feature_df['rul_cycles'] > 0].copy()
    mo.md(f"**Cycles with RUL > 0:** {len(training_df):,}")

    # Optional: Filter to early cycles
    training_df_early = filter_early_cycles(training_df, early_ratio=0.8)
    mo.md(f"**Early cycles (first 70% of life):** {len(training_df_early):,}")
    return training_df, training_df_early


@app.cell
def _(mo, training_df, training_df_early):
    # ============================================
    # SECTION 5: Select Features for ML
    # ============================================

    mo.md("## 5. Select Features for ML")

    # Features to use for prediction
    feature_columns = [
        'cycle_number',
        'soh_percent',
        'avg_temperature_c',
        'max_temperature_c',
        'duration_seconds',
        'degradation_rate',
        'soh_ma5',
        'temp_ma5',
        'cycles_so_far',
        'soh_loss_so_far',
        'log_cycle',
        'sqrt_cycle',
        'temp_range'
    ]

    # Target
    target_column = 'rul_cycles'

    # Check which features exist
    available_features = [f for f in feature_columns if f in training_df.columns]
    mo.md(f"**Available features:** {len(available_features)}")
    mo.md(f"Features: {available_features}")

    # Create final dataset
    X = training_df_early[available_features]
    y = training_df_early[target_column]

    mo.md(f"**X shape:** {X.shape}")
    mo.md(f"**y shape:** {y.shape}")
    return (available_features,)


@app.cell
def _(mo, training_df_early):
    # ============================================
    # SECTION 6: Train/Validation/Test Split (Fixed for 4 Batteries)
    # ============================================

    mo.md("## 6. Train/Validation/Test Split")

    # Fixed split (not random) for small dataset
    # This ensures each battery is used consistently
    train_batteries = ["B0005", "B0006"]      # 2 batteries for training
    val_batteries = ["B0007"]                  # 1 battery for validation
    test_batteries = ["B0018"]                 # 1 battery for testing

    # Apply the split using training_df_early (filtered data)
    train_df = training_df_early[training_df_early['battery_id'].isin(train_batteries)]
    val_df = training_df_early[training_df_early['battery_id'].isin(val_batteries)]
    test_df = training_df_early[training_df_early['battery_id'].isin(test_batteries)]

    mo.md(f"**Train batteries:** {train_batteries} ({len(train_df):,} cycles)")
    mo.md(f"**Validation batteries:** {val_batteries} ({len(val_df):,} cycles)")
    mo.md(f"**Test batteries:** {test_batteries} ({len(test_df):,} cycles)")

    # Show cycle range for each split (using different variable names)
    mo.md("### Cycle Distribution:")

    # For training batteries
    for b in train_batteries:
        b_df = train_df[train_df['battery_id'] == b]
        mo.md(f"**{b} (Train):** cycles {b_df['cycle_number'].min()}-{b_df['cycle_number'].max()} ({len(b_df)} cycles)")

    # For validation batteries
    for b in val_batteries:
        b_df = val_df[val_df['battery_id'] == b]
        mo.md(f"**{b} (Val):** cycles {b_df['cycle_number'].min()}-{b_df['cycle_number'].max()} ({len(b_df)} cycles)")

    # For test batteries
    for b in test_batteries:
        b_df = test_df[test_df['battery_id'] == b]
        mo.md(f"**{b} (Test):** cycles {b_df['cycle_number'].min()}-{b_df['cycle_number'].max()} ({len(b_df)} cycles)")
    return test_df, train_df, val_df


@app.cell
def _(available_features, mo, test_df, train_df, val_df):
        # ============================================
        # DIAGNOSTIC: Check for NaN values
        # ============================================

    def _():
        mo.md("## Checking for Missing Values")

        # Check each split
        for name, df_split in [('Train', train_df), ('Validation', val_df), ('Test', test_df)]:
            nan_counts = df_split[available_features].isnull().sum()
            nan_cols = nan_counts[nan_counts > 0]
        
            if len(nan_cols) > 0:
                mo.md(f"**{name} set has {len(nan_cols)} features with NaN:**")
                for col, count in nan_cols.items():
                    mo.md(f"  - {col}: {count} NaN values ({count/len(df_split)*100:.1f}%)")
            else:
                mo.md(f"**{name} set:** ✅ No NaN values")

        # Show first few rows with NaN
        mo.md("### Sample of training data (showing NaN positions):")
        return train_df[available_features].head(10)


    _()
    return


@app.cell
def _(available_features, mo, test_df, train_df, val_df):
    # ============================================
    # SECTION 6.5: Remove NaN values (using new variable names)
    # ============================================

    mo.md("## 6.5 Remove Missing Values (NaN)")

    # Create CLEAN versions (new variable names)
    train_df_clean = train_df.copy()
    val_df_clean = val_df.copy()
    test_df_clean = test_df.copy()

    # Drop rows with NaN in any feature column
    original_train_len = len(train_df_clean)
    original_val_len = len(val_df_clean)
    original_test_len = len(test_df_clean)

    train_df_clean = train_df_clean.dropna(subset=available_features)
    val_df_clean = val_df_clean.dropna(subset=available_features)
    test_df_clean = test_df_clean.dropna(subset=available_features)

    mo.md(f"**Train:** {original_train_len} → {len(train_df_clean)} rows ({original_train_len - len(train_df_clean)} removed)")
    mo.md(f"**Validation:** {original_val_len} → {len(val_df_clean)} rows ({original_val_len - len(val_df_clean)} removed)")
    mo.md(f"**Test:** {original_test_len} → {len(test_df_clean)} rows ({original_test_len - len(test_df_clean)} removed)")

    # Verify no NaN remain
    nan_check_train = train_df_clean[available_features].isnull().sum().sum()
    nan_check_val = val_df_clean[available_features].isnull().sum().sum()
    nan_check_test = test_df_clean[available_features].isnull().sum().sum()

    mo.md(f"**NaN remaining:** Train={nan_check_train}, Val={nan_check_val}, Test={nan_check_test}")
    return test_df_clean, train_df_clean, val_df_clean


@app.cell
def _(available_features, mo, plt, train_df_clean):
    def _():
        # ============================================
        # DIAGNOSTIC: Check RUL distribution
        # ============================================

        mo.md("## Diagnostic: RUL Value Distribution")

        # Check RUL in training data
        mo.md(f"**Train RUL stats:**")
        mo.md(f"  - Min: {train_df_clean['rul_cycles'].min()}")
        mo.md(f"  - Max: {train_df_clean['rul_cycles'].max()}")
        mo.md(f"  - Mean: {train_df_clean['rul_cycles'].mean():.1f}")
        mo.md(f"  - Unique values: {train_df_clean['rul_cycles'].nunique()}")

        # Check if RUL is constant (all same value)
        if train_df_clean['rul_cycles'].nunique() == 1:
            mo.md("❌ **PROBLEM: RUL is constant!** All values are the same.")
        else:
            mo.md("✅ RUL has variation")

        # Show distribution
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(train_df_clean['rul_cycles'], bins=30, edgecolor='black')
        ax.set_xlabel('RUL (cycles)')
        ax.set_ylabel('Frequency')
        ax.set_title('Distribution of RUL Values in Training Data')
        ax.axvline(train_df_clean['rul_cycles'].mean(), color='r', linestyle='--', label=f'Mean: {train_df_clean["rul_cycles"].mean():.1f}')
        ax.legend()
        fig

        # Show sample of data with features and RUL
        mo.md("### Sample of training data:")
        return train_df_clean[['battery_id', 'cycle_number', 'soh_percent', 'rul_cycles'] + available_features[:3]].head(10)


    _()
    return


@app.cell
def _(available_features, mo, pd, test_df_clean, train_df_clean, val_df_clean):
    # ============================================
    # SECTION 7: Compare Multiple Models
    # ============================================

    mo.md("## 7. Compare Multiple Models")

    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    import xgboost as xgb
    from lightgbm import LGBMRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import time

    # Use CLEAN data (after removing NaN values)
    # Note: Using train_df_clean, val_df_clean, test_df_clean from Section 6.5
    X_train = train_df_clean[available_features]
    y_train = train_df_clean['rul_cycles']
    X_val = val_df_clean[available_features]
    y_val = val_df_clean['rul_cycles']
    X_test = test_df_clean[available_features]
    y_test = test_df_clean['rul_cycles']

    mo.md(f"**Training samples:** {len(X_train)}")
    mo.md(f"**Validation samples:** {len(X_val)}")
    mo.md(f"**Test samples:** {len(X_test)}")

    # Quick sanity check - ensure no NaN values
    assert X_train.isnull().sum().sum() == 0, "NaN values found in training data!"
    assert X_val.isnull().sum().sum() == 0, "NaN values found in validation data!"
    assert X_test.isnull().sum().sum() == 0, "NaN values found in test data!"

    mo.md("✅ No NaN values in any dataset")

    # Define models to compare
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42),
        'LightGBM': LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1)
    }

    # Train and evaluate each model
    results = []

    for name, model in models.items():
        start_time = time.time()
    
        # Train
        model.fit(X_train, y_train)
        train_time = time.time() - start_time
    
        # Predict
        y_train_pred = model.predict(X_train)
        y_val_pred = model.predict(X_val)
        y_test_pred = model.predict(X_test)
    
        # Calculate metrics
        train_mae = mean_absolute_error(y_train, y_train_pred)
        val_mae = mean_absolute_error(y_val, y_val_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
    
        train_r2 = r2_score(y_train, y_train_pred)
        val_r2 = r2_score(y_val, y_val_pred)
        test_r2 = r2_score(y_test, y_test_pred)
    
        results.append({
            'Model': name,
            'Train MAE': f'{train_mae:.1f}',
            'Val MAE': f'{val_mae:.1f}',
            'Test MAE': f'{test_mae:.1f}',
            'Train R²': f'{train_r2:.3f}',
            'Val R²': f'{val_r2:.3f}',
            'Test R²': f'{test_r2:.3f}',
            'Train Time (s)': f'{train_time:.2f}'
        })

    # Display results
    results_df = pd.DataFrame(results)
    mo.md("### Model Comparison")
    mo.ui.table(results_df)

    # Find best model by Test MAE
    best_idx = results_df['Test MAE'].astype(float).idxmin()
    best_model_name = results_df.loc[best_idx, 'Model']
    best_test_mae = results_df.loc[best_idx, 'Test MAE']
    best_test_r2 = results_df.loc[best_idx, 'Test R²']

    mo.md(f"**🏆 Best model:** {best_model_name}")
    mo.md(f"   - Test MAE: {best_test_mae} cycles")
    mo.md(f"   - Test R²: {best_test_r2}")

    # Store the best model
    best_model = models[best_model_name]
    return (
        X_test,
        best_idx,
        best_model,
        best_model_name,
        models,
        results_df,
        y_test,
    )


@app.cell
def _(mo, plt, results_df):
    # ============================================
    # SECTION 8: Visualize Model Comparison
    # ============================================

    mo.md("## 8. Model Comparison Visualization")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Test MAE comparison
    models_list = results_df['Model'].tolist()
    test_mae_values = [float(x) for x in results_df['Test MAE']]

    axes[0].barh(models_list, test_mae_values, color='skyblue')
    axes[0].set_xlabel('Test MAE (cycles)')
    axes[0].set_title('Test MAE by Model (lower is better)')
    axes[0].grid(True, alpha=0.3)

    # Test R² comparison
    test_r2_values = [float(x) for x in results_df['Test R²']]

    axes[1].barh(models_list, test_r2_values, color='lightgreen')
    axes[1].set_xlabel('Test R² (higher is better)')
    axes[1].set_title('Test R² by Model')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    fig
    return


@app.cell
def _(X_test, mo, models, plt, test_df, y_test):
    # ============================================
    # SECTION 9: Compare Predictions on Test Battery
    # ============================================

    mo.md("## 9. Compare Predictions on B0018")

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot actual RUL
    ax.plot(test_df['cycle_number'], y_test, 'k-', linewidth=2, label='Actual RUL', marker='o', markersize=4)

    # Plot predictions from each model
    colors = ['blue', 'red', 'green', 'orange']
    for (name, model), color in zip(models.items(), colors):
        y_pred = model.predict(X_test)
        ax.plot(test_df['cycle_number'], y_pred, '--', color=color, label=f'{name}', alpha=0.7)

    ax.set_xlabel('Cycle Number')
    ax.set_ylabel('Remaining Useful Life (cycles)')
    ax.set_title('B0018: Actual vs Predicted RUL by Different Models')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig
    return


@app.cell
def _(
    MODEL_DIR,
    available_features,
    best_idx,
    best_model_name,
    mo,
    models,
    results_df,
):
    # ============================================
    # SECTION 10: Save Best Model
    # ============================================

    mo.md("## 10. Save Best Model")

    import joblib

    # Create models directory
    models_dir = MODEL_DIR / "models" / "saved_models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Save the best model
    best_model = models[best_model_name]
    model_path = models_dir / f"{best_model_name.lower().replace(' ', '_')}_rul_model.pkl"
    joblib.dump(best_model, model_path)

    # Save feature names
    feature_path = models_dir / "features.pkl"
    joblib.dump(available_features, feature_path)

    # Save comparison results for reference
    comparison_path = models_dir / "model_comparison.csv"
    results_df.to_csv(comparison_path, index=False)

    mo.md(f"✅ Best model ({best_model_name}) saved to: `{model_path}`")
    mo.md(f"✅ Features saved to: `{feature_path}`")
    mo.md(f"✅ Comparison saved to: `{comparison_path}`")

    # Show final recommendation
    mo.md("### Recommendation")
    mo.md(f"""
    Based on Test MAE, **{best_model_name}** performs best with **{results_df.loc[best_idx, 'Test MAE']} cycles** average error.

    This model will be used in your backend API.
    """)
    return (best_model,)


@app.cell
def _(available_features, best_model, mo, np):
    # ============================================
    # SECTION 11: Test Prediction Function
    # ============================================

    mo.md("## 11. Test Prediction Function")

    def predict_rul(model, features_dict):
        """
        Predict remaining cycles using the best model.
    
        Args:
            model: Trained model (best_model)
            features_dict: Dictionary with feature values
    
        Returns:
            Predicted remaining cycles (integer)
        """
        import pandas as pd
        import numpy as np
    
        # Create DataFrame with correct feature order
        input_df = pd.DataFrame([features_dict])[available_features]
    
        # Predict
        rul = model.predict(input_df)[0]
        return max(0, int(rul))

    # Test with sample scenarios
    mo.md("### Sample Predictions (using best model):")

    test_scenarios = [
        (95, 50, 25, 3000, "New-ish battery"),
        (90, 100, 26, 3000, "Moderately used"),
        (85, 200, 27, 3000, "Well used"),
        (80, 300, 28, 3000, "Approaching replacement"),
    ]

    for soh, cycle, temp, duration, desc in test_scenarios:
        features = {
            'cycle_number': cycle,
            'soh_percent': soh,
            'avg_temperature_c': temp,
            'max_temperature_c': temp + 2,
            'duration_seconds': duration,
            'degradation_rate': 0.1,
            'soh_ma5': soh,
            'temp_ma5': temp,
            'cycles_so_far': cycle,
            'soh_loss_so_far': 100 - soh,
            'log_cycle': np.log1p(cycle),
            'sqrt_cycle': np.sqrt(cycle),
            'temp_range': 4.0,
        }
        rul = predict_rul(best_model, features)
        mo.md(f"**{desc}** ({soh}% health, cycle {cycle}): **{rul}** cycles remaining")
    return


if __name__ == "__main__":
    app.run()
