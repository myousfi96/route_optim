"""
training.py

Generates synthetic data for 6 features:
 [distance,
  time_window_start,
  time_window_end,
  traffic,
  warehouse_inventory,
  requested_quantity]

Trains a linear regression that penalizes:
 - insufficient inventory
 - short (time_window_end - time_window_start)
"""

import random
import math
import numpy as np
from typing import Tuple
from sklearn.linear_model import LinearRegression

def _true_cost_function(distance: float,
                        time_window_start: float,
                        time_window_end: float,
                        traffic: float,
                        warehouse_inventory: float,
                        requested_quantity: float
) -> float:
    """
    cost = distance
          + distance*traffic
          + inventory penalty if inv < requested_qty => +999999
          + an extra penalty if (time_window_end - time_window_start) is small
          - 0.02 * warehouse_inventory
    """
    base_cost = distance
    traffic_cost = distance * traffic

    insufficient_penalty = 0.0
    if warehouse_inventory < requested_quantity:
        insufficient_penalty = 999999

    available_time = time_window_end - time_window_start
    alpha = 10.0
    time_window_penalty = alpha * traffic * (1.0 / available_time)

    inv_benefit = 0.02 * warehouse_inventory

    total = base_cost + traffic_cost + time_window_penalty + insufficient_penalty - inv_benefit
    return max(0.0, total)

def generate_synthetic_training_data(samples: int = 1000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    shape: (samples, 6)
     [distance, time_window_start, time_window_end, traffic, inventory, requested_qty]
    plus cost label
    """
    X_list = []
    y_list = []

    for _ in range(samples):
        distance = random.uniform(1.0, 100.0)
        tw_start = random.uniform(0.0, 8.0)
        tw_end   = tw_start + random.uniform(0.5, 10.0)
        traffic  = random.uniform(1.0, 3.0)
        inv      = random.uniform(0.0, 500.0)
        req_qty  = random.uniform(1.0, 200.0)

        cost = _true_cost_function(
            distance, tw_start, tw_end, traffic, inv, req_qty
        )

        X_list.append([distance, tw_start, tw_end, traffic, inv, req_qty])
        y_list.append(cost)

    return np.array(X_list), np.array(y_list)

def train_regression_model(samples: int = 2000) -> LinearRegression:
    """
    Train a linear regression on the 6D data.
    """
    X, y = generate_synthetic_training_data(samples=samples)
    model = LinearRegression()
    model.fit(X, y)
    return model
