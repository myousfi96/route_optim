import pytest
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app as flask_app
@pytest.fixture
def client():
    """
    Fixture to provide a test client for Flask.
    """
    flask_app.testing = True
    return flask_app.test_client()

def test_get_warehouses_success(client):
    """
    Test GET /warehouses returns a 200 and a JSON list.
    """
    resp = client.get("/warehouses")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list), "Expected a list of warehouses"
    if data:
        assert "id" in data[0]
        assert "name" in data[0]
        assert "inventory" in data[0]

def test_optimize_success(client):
    """
    Test POST /optimize with a valid request body.
    Should return 200 and a JSON with best_route + all_routes.
    """
    payload = {
        "latitude": 48.14,
        "longitude": 11.58,
        "time_window_start": 2.0,
        "time_window_end": 6.0,
        "quantity": 50
    }
    resp = client.post("/optimize",
                       data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.get_json()
    assert "best_route" in data
    assert "all_routes" in data
    assert isinstance(data["all_routes"], list)
    assert "predicted_cost" in data["best_route"]

def test_optimize_missing_field(client):
    """
    Missing a required field (time_window_end) => should fail with 400
    """
    payload = {
        "latitude": 48.14,
        "longitude": 11.58,
        "time_window_start": 2.0,
        # "time_window_end": 6.0  # missing
        "quantity": 50
    }
    resp = client.post("/optimize",
                       data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 400
    data = resp.get_json()
    # Expecting some validation_error
    assert "validation_error" in data or "error" in data

def test_optimize_insufficient_inventory(client):
    """
    If the quantity is extremely high, we might get a "Not enough inventory" error (400).
    Because all warehouses might have random inventory < requested quantity.
    """
    payload = {
        "latitude": 48.14,
        "longitude": 11.58,
        "time_window_start": 2.0,
        "time_window_end": 6.0,
        "quantity": 99999
    }
    resp = client.post("/optimize",
                       data=json.dumps(payload),
                       content_type="application/json")
    if resp.status_code == 200:
        data = resp.get_json()
        assert "best_route" in data
        assert "all_routes" in data
    else:
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
