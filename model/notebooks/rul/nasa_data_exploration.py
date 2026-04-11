import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    # notebooks/nasa_data_exploration.py
    # NASA Battery Dataset - Data Cleaning & Exploration

    import marimo as mo
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy.io import loadmat
    from pathlib import Path
    import warnings
    warnings.filterwarnings('ignore')
    return Path, loadmat, mo, np, pd, plt


@app.cell
def _(Path, mo):
    # ============================================
    # CONFIGURATION - Using relative paths
    # ============================================

    # Get the current notebook's directory (model/notebooks/)
    NOTEBOOK_DIR = Path(__file__).parent if '__file__' in dir() else Path.cwd()
    # Go up one level to model/ folder
    MODEL_DIR = NOTEBOOK_DIR.parent

    # Define paths relative to model folder
    DATA_RAW = MODEL_DIR / "data" / "raw" / "nasa" / "classic"
    DATA_PROCESSED = MODEL_DIR / "data" / "processed"

    # Create processed directory if it doesn't exist
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    mo.md("# NASA Battery Dataset Analysis")
    mo.md("## Extracting and cleaning data for RUL prediction")
    mo.md(f"**Data source:** `{DATA_RAW}`")
    mo.md(f"**Output path:** `{DATA_PROCESSED}`")
    return DATA_PROCESSED, DATA_RAW


@app.cell
def _(np, pd):
    # ============================================
    # SECTION 1: Function to extract discharge cycles
    # ============================================

    def extract_discharge_cycles(battery_struct, battery_name):
        """
        Extract all discharge cycles from NASA battery .mat file.

        Returns:
            DataFrame with columns: cycle_number, capacity_ah, temperature_c, etc.
        """
        cycles_data = []
        cycles = battery_struct['cycle'][0, 0][0]

        for cycle_idx, cycle in enumerate(cycles):
            cycle_type = cycle['type'][0]

            if cycle_type == 'discharge':
                data = cycle['data'][0, 0]

                # Extract capacity (Ah) - our target variable
                capacity = float(data['Capacity'][0, 0]) if 'Capacity' in data.dtype.names else None

                # Extract temperature measurements
                temp_measured = data['Temperature_measured'][0]
                avg_temp = np.mean(temp_measured) if len(temp_measured) > 0 else None
                max_temp = np.max(temp_measured) if len(temp_measured) > 0 else None
                min_temp = np.min(temp_measured) if len(temp_measured) > 0 else None

                # Extract voltage (start, end, min)
                voltage = data['Voltage_measured'][0]
                start_voltage = voltage[0] if len(voltage) > 0 else None
                end_voltage = voltage[-1] if len(voltage) > 0 else None
                min_voltage = np.min(voltage) if len(voltage) > 0 else None

                # Extract current (should be constant ~2A for discharge)
                current = data['Current_measured'][0]
                avg_current = np.mean(current) if len(current) > 0 else None

                # Time duration of discharge
                time_vec = data['Time'][0]
                duration_seconds = time_vec[-1] if len(time_vec) > 0 else None

                cycles_data.append({
                    'battery_id': battery_name,
                    'cycle_number': cycle_idx + 1,
                    'capacity_ah': capacity,
                    'avg_temperature_c': avg_temp,
                    'max_temperature_c': max_temp,
                    'min_temperature_c': min_temp,
                    'start_voltage_v': start_voltage,
                    'end_voltage_v': end_voltage,
                    'min_voltage_v': min_voltage,
                    'avg_current_a': avg_current,
                    'duration_seconds': duration_seconds,
                })

        return pd.DataFrame(cycles_data)


    return (extract_discharge_cycles,)


@app.cell
def _(DATA_RAW, extract_discharge_cycles, loadmat, mo, pd):
    # ============================================
    # SECTION 2: Load all batteries
    # ============================================

    mo.md("## Loading All Batteries")

    # Find all .mat files in the classic folder
    all_mat_files = list(DATA_RAW.glob("*.mat"))
    mo.md(f"Found {len(all_mat_files)} .mat files")

    all_batteries = []
    load_status = []
    failed_files = []

    for mat_file in all_mat_files:
        battery_name = mat_file.stem
    
        try:
            file_path = DATA_RAW / f"{battery_name}.mat"
            mat_data = loadmat(file_path)
        
            battery_keys = [k for k in mat_data.keys() if not k.startswith('__')]
        
            if battery_keys:
                battery_struct = mat_data[battery_keys[0]]
                df = extract_discharge_cycles(battery_struct, battery_name)
            
                if df is not None and len(df) > 0:
                    all_batteries.append(df)
                    load_status.append(f"✅ {battery_name}: {len(df)} cycles")
                else:
                    failed_files.append(f"{battery_name}: No discharge cycles")
            else:
                failed_files.append(f"{battery_name}: No data structure")
            
        except Exception as e:
            failed_files.append(f"{battery_name}: {str(e)[:40]}")

    # Combine into single markdown strings for display
    if load_status:
        # Show first 20 successful loads
        success_text = "### Successfully loaded:\n" + "\n".join(load_status[:20])
        if len(load_status) > 20:
            success_text += f"\n... and {len(load_status) - 20} more"
        mo.md(success_text)

    if failed_files:
        fail_text = "### Failed to load:\n" + "\n".join(failed_files[:10])
        if len(failed_files) > 10:
            fail_text += f"\n... and {len(failed_files) - 10} more"
        mo.md(fail_text)

    # Combine all batteries
    if all_batteries:
        combined_df = pd.concat(all_batteries, ignore_index=True)
        mo.md(f"### ✅ Total dataset: {len(combined_df)} cycles across {combined_df['battery_id'].nunique()} batteries")
    
        # Get battery names for later use
        battery_names = sorted(combined_df['battery_id'].unique())
        mo.md(f"**Battery IDs:** {', '.join(battery_names[:15])}")
        if len(battery_names) > 15:
            mo.md(f"... and {len(battery_names) - 15} more")
    
        # Display first few rows
        mo.md("### Preview of data:")
        combined_df.head(10)
    else:
        mo.md("❌ No batteries were loaded successfully!")
        combined_df = pd.DataFrame()
        battery_names = []
    return battery_names, combined_df


@app.cell
def _(combined_df, mo):
    # ============================================
    # SECTION 3: Data Quality Check
    # ============================================

    mo.md("## Data Quality Check")

    # Check for missing values
    missing_df = combined_df.isnull().sum().to_frame('missing_count')
    missing_df['missing_pct'] = (missing_df['missing_count'] / len(combined_df)) * 100
    mo.ui.table(missing_df[missing_df['missing_count'] > 0])
    return


@app.cell
def _(battery_names, combined_df, mo, plt):
    # ============================================
    # SECTION 4: Capacity Fade Curves (All Batteries)
    # ============================================

    mo.md("## Capacity Fade Curves")

    def create_capacity_plots():
        """Create capacity fade plots with dynamic grid sizing"""
    
        n_batteries = len(battery_names)
    
        # Calculate grid size (3 columns, auto rows)
        n_cols = 3
        n_rows = (n_batteries + n_cols - 1) // n_cols
    
        # Adjust figure size based on number of batteries
        fig_height = max(8, n_rows * 4)
        fig_width = 15
    
        # Create subplots
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))
    
        # Handle case of single subplot
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
    
        # Plot each battery
        for idx, battery_id in enumerate(battery_names):
            battery_df = combined_df[combined_df['battery_id'] == battery_id]
        
            axes[idx].plot(battery_df['cycle_number'], battery_df['capacity_ah'], 'b-o', markersize=2, linewidth=0.8)
            axes[idx].axhline(y=1.4, color='r', linestyle='--', linewidth=0.8, label='EOL (1.4Ah)')
            axes[idx].set_xlabel('Cycle Number', fontsize=8)
            axes[idx].set_ylabel('Capacity (Ah)', fontsize=8)
            axes[idx].set_title(f'{battery_id}', fontsize=9)
            axes[idx].grid(True, alpha=0.3)
            axes[idx].tick_params(labelsize=7)
        
            # Only show legend for first few plots to avoid clutter
            if idx < 3:
                axes[idx].legend(fontsize=7)
        
            # Mark end of life
            eol_cycles = battery_df[battery_df['capacity_ah'] <= 1.4]['cycle_number']
            if len(eol_cycles) > 0:
                eol_cycle = eol_cycles.iloc[0]
                axes[idx].axvline(x=eol_cycle, color='orange', linestyle=':', alpha=0.5, linewidth=0.8)
                axes[idx].text(eol_cycle + (max(battery_df['cycle_number']) * 0.02), 
                              1.42, f'EOL: {eol_cycle}', fontsize=6, alpha=0.7)
    
        # Hide any unused subplots
        for idx in range(len(battery_names), len(axes)):
            axes[idx].set_visible(False)
    
        plt.tight_layout()
        return fig

    # Call the function and display
    capacity_fig = create_capacity_plots()
    capacity_fig
    return


@app.cell
def _(battery_names, combined_df, plt):
    # ============================================
    # SECTION 5: Temperature Analysis
    # ============================================

    def create_temperature_plots():
        """Create temperature analysis plots"""
        temp_fig, temp_axes = plt.subplots(1, 2, figsize=(12, 5))

        # Temperature vs Cycle
        for battery_id in battery_names:
            battery_df = combined_df[combined_df['battery_id'] == battery_id]
            temp_axes[0].plot(battery_df['cycle_number'], battery_df['avg_temperature_c'], '-', label=battery_id, linewidth=1)

        temp_axes[0].set_xlabel('Cycle Number')
        temp_axes[0].set_ylabel('Average Temperature (°C)')
        temp_axes[0].set_title('Temperature Trends by Battery')
        temp_axes[0].legend()
        temp_axes[0].grid(True, alpha=0.3)

        # Temperature distribution
        for battery_id in battery_names:
            battery_df = combined_df[combined_df['battery_id'] == battery_id]
            temp_axes[1].hist(battery_df['avg_temperature_c'], bins=20, alpha=0.5, label=battery_id)

        temp_axes[1].set_xlabel('Temperature (°C)')
        temp_axes[1].set_ylabel('Frequency')
        temp_axes[1].set_title('Temperature Distribution')
        temp_axes[1].legend()

        plt.tight_layout()
        return temp_fig

    # Call the function and display
    temp_fig = create_temperature_plots()
    temp_fig
    return


@app.cell
def _(combined_df, mo):
    # ============================================
    # SECTION 6: Calculate Health Metrics
    # ============================================

    mo.md("## Calculating Health Metrics")

    # Rated capacity is 2.0 Ah for all NASA batteries
    RATED_CAPACITY_AH = 2.0

    # Add health percentage columns
    combined_df['soh_percent'] = (combined_df['capacity_ah'] / RATED_CAPACITY_AH) * 100
    combined_df['capacity_loss_percent'] = 100 - combined_df['soh_percent']

    # Show summary
    mo.md(f"**Health range:** {combined_df['soh_percent'].min():.1f}% - {combined_df['soh_percent'].max():.1f}%")
    mo.md(f"**Mean health:** {combined_df['soh_percent'].mean():.1f}%")

    mo.md("### Health Metrics Added:")
    combined_df[['battery_id', 'cycle_number', 'capacity_ah', 'soh_percent', 'capacity_loss_percent']].head(10)
    return


@app.cell
def _(DATA_PROCESSED, combined_df, mo):
    # ============================================
    # SECTION 7: Save Processed Data
    # ============================================

    mo.md("## Save Processed Data")

    # First, check what columns are available
    mo.md(f"Available columns: {list(combined_df.columns)}")

    # Select columns that actually exist in combined_df
    available_columns = [
        'battery_id', 'cycle_number', 'capacity_ah', 
        'avg_temperature_c', 'max_temperature_c', 'min_temperature_c',
        'duration_seconds', 'start_voltage_v', 'end_voltage_v'
    ]

    # Only include columns that exist
    final_columns = [col for col in available_columns if col in combined_df.columns]

    mo.md(f"Using columns: {final_columns}")

    training_df = combined_df[final_columns].copy()

    # Add soh_percent if it exists, otherwise calculate it
    if 'soh_percent' in combined_df.columns:
        training_df['soh_percent'] = combined_df['soh_percent']
    else:
        training_df['soh_percent'] = (training_df['capacity_ah'] / 2.0) * 100

    # Save as CSV (updated filename to reflect 32 batteries)
    csv_path = DATA_PROCESSED / "nasa_32_batteries_training_data.csv"
    training_df.to_csv(csv_path, index=False)

    # Show confirmation
    mo.md(f"✅ Saved training data to CSV:")
    mo.md(f"   Path: `{csv_path}`")
    mo.md(f"   Shape: {training_df.shape[0]} rows, {training_df.shape[1]} columns")
    mo.md(f"   File size: {csv_path.stat().st_size / 1024:.1f} KB")
    mo.md(f"   Total batteries: {training_df['battery_id'].nunique()}")

    # Show preview
    mo.md("### Preview of saved data:")
    training_df.head(10)
    return


@app.cell
def _(combined_df, mo):
    # ============================================
    # SECTION 8: Summary Statistics
    # ============================================

    mo.md("## Summary Statistics")

    # Summary by battery
    summary = combined_df.groupby('battery_id').agg({
        'cycle_number': 'max',
        'capacity_ah': ['min', 'max', 'mean'],
        'avg_temperature_c': 'mean',
        'duration_seconds': 'mean'
    }).round(2)

    mo.ui.table(summary)
    return


@app.cell
def _(battery_names, combined_df, mo, pd):
    def _():
        # End of Life summary
        eol_summary = []
        for battery_id in battery_names:
            battery_df = combined_df[combined_df['battery_id'] == battery_id]
            eol_cycles = battery_df[battery_df['capacity_ah'] <= 1.4]['cycle_number']

            eol_summary.append({
                'battery_id': battery_id,
                'total_cycles': len(battery_df),
                'eol_cycle': eol_cycles.iloc[0] if len(eol_cycles) > 0 else 'N/A',
                'final_capacity_ah': battery_df['capacity_ah'].iloc[-1],
                'avg_temp_c': battery_df['avg_temperature_c'].mean(),
            })

        mo.md("### End of Life Summary")
        mo.ui.table(pd.DataFrame(eol_summary))
        return mo.md("""
        ## Next Steps

        Now that we have clean data, we can:

        1. **Feature Engineering** - Create degradation rates, rolling averages
        2. **RUL Model Training** - Predict remaining cycles from early data
        3. **Export for Backend** - Save model for API serving

        Run the next notebook: `02_feature_engineering.py`
        """)


    _()
    return


if __name__ == "__main__":
    app.run()
