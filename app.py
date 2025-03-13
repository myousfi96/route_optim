"""
app.py

Flask server:
 - DB init & random warehouses
 - Train 6D model (distance, time_window_start, time_window_end, traffic, inv, requested_qty)
 - /optimize => returns best route + all routes
 - /warehouses => returns warehouse info
"""

import logging
import random
from flask import Flask, request, jsonify
from pydantic import ValidationError

from database import init_db, SessionLocal
from models import Warehouse
from training import train_regression_model
from route_optimizer import Order, generate_candidate_routes, predict_cost
from schemas import OptimizeRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
MODEL = None

def populate_random_warehouses(num_warehouses: int = 3) -> None:
    session = SessionLocal()
    try:
        session.query(Warehouse).delete()
        session.commit()

        for i in range(num_warehouses):
            lat = 48.137 + random.uniform(-0.1, 0.1)
            lon = 11.576 + random.uniform(-0.1, 0.1)
            inv = random.uniform(0, 500)
            wh = Warehouse(
                name=f"Warehouse_{i+1}",
                latitude=lat,
                longitude=lon,
                inventory=inv
            )
            session.add(wh)
        session.commit()
        logger.info("Populated %d random warehouses.", num_warehouses)
    finally:
        session.close()

def startup():
    global MODEL
    logger.info("Initializing DB...")
    init_db()
    populate_random_warehouses(num_warehouses=3)

    logger.info("Training 6D regression model (with time_window_{start,end}) penalty approach.")
    MODEL = train_regression_model(samples=2000)
    logger.info("Model training complete.")

with app.app_context():
    startup()

@app.route("/")
def index():
    return "Route Optimization – using time_window_start/time_window_end & inventory constraints."

@app.route("/warehouses", methods=["GET"])
def list_warehouses():
    session = SessionLocal()
    try:
        whs = session.query(Warehouse).all()
        data = []
        for w in whs:
            data.append({
                "id": w.id,
                "name": w.name,
                "latitude": w.latitude,
                "longitude": w.longitude,
                "inventory": w.inventory
            })
        return jsonify(data)
    finally:
        session.close()

@app.route("/optimize", methods=["POST"])
def optimize():
    raw_data = request.get_json()
    if not raw_data:
        return jsonify({"error":"No JSON body provided"}), 400

    try:
        req_model = OptimizeRequest(**raw_data)
    except ValidationError as e:
        return jsonify({"validation_error": e.errors()}), 400

    order = Order(
        lat=req_model.latitude,
        lon=req_model.longitude,
        time_window_start=req_model.time_window_start,
        time_window_end=req_model.time_window_end,
        quantity=req_model.quantity
    )

    session = SessionLocal()
    try:
        whs = session.query(Warehouse).all()

        if all(w.inventory < order.quantity for w in whs):
            return jsonify({"error":"Not enough inventory in all warehouses."}), 400

        all_routes_info = []
        best_route = None
        best_cost = float('inf')

        for w in whs:
            wh_routes = generate_candidate_routes(
                order=order,
                warehouse_id=w.id,
                warehouse_lat=w.latitude,
                warehouse_lon=w.longitude,
                warehouse_inventory=w.inventory,
                num_routes=5
            )
            for r in wh_routes:
                c = predict_cost(MODEL, r, order)
                route_data = {
                    "route_id": r["route_id"],
                    "warehouse_id": r["warehouse_id"],
                    "distance": round(r["distance"],3),
                    "traffic": round(r["traffic"],2),
                    "inventory": round(r["warehouse_inventory"],2),
                    "predicted_cost": round(c,3)
                }
                all_routes_info.append(route_data)
                if c < best_cost:
                    best_cost = c
                    best_route = route_data

        if best_cost >= 999999:
            return jsonify({"error":"All routes penalized; none feasible."}), 400

        response = {
            "best_route": best_route,
            "all_routes": all_routes_info
        }
        return jsonify(response)
    finally:
        session.close()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
