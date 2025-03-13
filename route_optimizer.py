"""
route_optimizer.py

We keep time_window_start & time_window_end, then compute a big penalty if available_time is small.
The model is trained with 6 features:
   [distance, time_window_start, time_window_end, traffic, inv, requested_qty]
"""

import math
import random
import numpy as np
from typing import List, Dict
from sklearn.linear_model import LinearRegression

class Order:
    """
    lat, lon, time_window_start, time_window_end, quantity
    """
    def __init__(self,
                 lat: float,
                 lon: float,
                 time_window_start: float,
                 time_window_end: float,
                 quantity: float):
        self.latitude = lat
        self.longitude = lon
        self.time_window_start = time_window_start
        self.time_window_end = time_window_end
        self.quantity = quantity

def _compute_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def generate_candidate_routes(order: Order,
                              warehouse_id: int,
                              warehouse_lat: float,
                              warehouse_lon: float,
                              warehouse_inventory: float,
                              num_routes: int = 5
) -> List[Dict[str, float]]:
    """
    Creates route variations, randomizing distance & traffic a bit.
    """
    baseline_dist = _compute_distance(warehouse_lat, warehouse_lon,
                                      order.latitude, order.longitude)
    candidates = []
    for i in range(num_routes):
        dist_var = baseline_dist * random.uniform(-0.2, 0.2)
        distance = abs(baseline_dist + dist_var)
        traffic = random.uniform(1.0, 3.0)

        r = {
            "route_id": f"{warehouse_id}_{i+1}",
            "warehouse_id": warehouse_id,
            "distance": distance,
            "time_window_start": order.time_window_start,
            "time_window_end": order.time_window_end,
            "traffic": traffic,
            "warehouse_inventory": warehouse_inventory
        }
        candidates.append(r)
    return candidates

def predict_cost(model: LinearRegression, route: Dict[str, float], order: Order) -> float:
    """
    Inference with 6 features:
      [distance, time_window_start, time_window_end, traffic, inventory, requested_qty]
    """
    arr = np.array([[
        route["distance"],
        route["time_window_start"],
        route["time_window_end"],
        route["traffic"],
        route["warehouse_inventory"],
        order.quantity
    ]])
    cost = model.predict(arr)[0]
    return float(cost)
