from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn

def train_habit_archetypes(X: pd.DataFrame, n_clusters=4):
    """
    Clusters users based on their charging habits.
    """
    # Features mentioned: 
    # plug_in_time, plug_out_time, start_soc, end_soc, frequency_above_80, frequency_below_20
    
    with mlflow.start_run(run_name="HabitClustering_Training"):
        model = KMeans(n_clusters=n_clusters, random_state=42)
        model.fit(X)
        
        # Log to MLflow
        mlflow.sklearn.log_model(model, "habit_kmeans")
        print(f"Habit clustering trained with {n_clusters} clusters.")
        
        # Get cluster centers for rule engine
        centers = model.cluster_centers_
        print(f"Cluster centers: {centers}")
        
        return model

if __name__ == "__main__":
    print("Habit clustering model script ready.")
