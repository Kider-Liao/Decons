import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def fit_latency_models(workload, memory_bandwidth, network_utilization, cpu_utilization, latency, cut_off_points=3):
    cut_points = np.linspace(workload.min(), workload.max(), cut_off_points + 1)

    models = []

    for i in range(cut_off_points):
        mask = (workload >= cut_points[i]) & (workload < cut_points[i + 1])

        if np.any(mask):
            B_w = memory_bandwidth[mask] * workload[mask]
            N_w = network_utilization[mask] * workload[mask]
            w = workload[mask]
            U = cpu_utilization[mask]

            X = np.vstack((B_w, N_w, w, U)).T
            y = latency[mask]

            model = LinearRegression()
            model.fit(X, y)

            models.append(model)
        else:

            models.append(None)

    return models, cut_points


def load_data(file_path):
    df = pd.read_csv(file_path)
    workload = df['workload'].values
    memory_bandwidth = df['memory_bandwidth'].values
    network_utilization = df['network_utilization'].values
    cpu_utilization = df['cpu_utilization'].values
    latency = df['latency'].values
    return workload, memory_bandwidth, network_utilization, cpu_utilization, latency


def print_model_info(models, cut_points):
    print("Cut-off points:", cut_points)
    print("Number of models:", len(models))
    for i, model in enumerate(models):
        if model is not None:
            print(f"Model {i}: Coefficients {model.coef_}, Intercept {model.intercept_}")
        else:
            print(f"Model {i}: No data in this segment.")

