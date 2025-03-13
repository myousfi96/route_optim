"""
streamlit_app.py

Streamlit UI that:
 - Takes order input: (lat, lon, time_window_start, time_window_end, quantity)
 - Calls /optimize => gets best_route + all_routes
 - fetches /warehouses => for map
 - Displays a table, highlighting best route
 - Uses session_state + callbacks so no flicker
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd

BACKEND_OPTIMIZE_URL = "http://127.0.0.1:5000/optimize"
BACKEND_WAREHOUSES_URL = "http://127.0.0.1:5000/warehouses"

def create_map(order_lat, order_lon, chosen_wh_id, wh_data):
    map_ = folium.Map(location=[order_lat, order_lon], zoom_start=10)

    folium.Marker(
        location=[order_lat, order_lon],
        popup="Order Location",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(map_)

    for w in wh_data:
        wid = w["id"]
        wlat = w["latitude"]
        wlon = w["longitude"]
        wname = w["name"]

        if wid == chosen_wh_id:
            folium.Marker(
                location=[wlat, wlon],
                popup=f"Chosen Warehouse #{wid} ({wname})",
                icon=folium.Icon(color="green", icon="star")
            ).add_to(map_)
        else:
            folium.Marker(
                location=[wlat, wlon],
                popup=f"Warehouse #{wid} ({wname})",
                icon=folium.Icon(color="red", icon="home")
            ).add_to(map_)

    return map_

def on_optimize_click():
    st.session_state["clicked_optimize"] = True

    payload = {
        "latitude": st.session_state["lat"],
        "longitude": st.session_state["lon"],
        "time_window_start": st.session_state["time_window_start"],
        "time_window_end": st.session_state["time_window_end"],
        "quantity": st.session_state["quantity"]
    }

    try:
        resp = requests.post(BACKEND_OPTIMIZE_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state["best_route"] = data["best_route"]
            st.session_state["all_routes"] = data["all_routes"]
            wh_resp = requests.get(BACKEND_WAREHOUSES_URL, timeout=5)
            if wh_resp.status_code == 200:
                st.session_state["warehouses"] = wh_resp.json()
            else:
                st.error(f"Failed GET /warehouses: {wh_resp.status_code} {wh_resp.text}")
                st.session_state["warehouses"] = None
        else:
            st.session_state["best_route"] = None
            st.session_state["all_routes"] = None
            st.session_state["warehouses"] = None
            try:
                err_data = resp.json()
                st.error(f"Optimization error: {err_data.get('error','Unknown')}")
            except:
                st.error(f"Optimization error: status={resp.status_code} {resp.text}")
    except Exception as ex:
        st.error(f"Error calling /optimize: {ex}")
        st.session_state["best_route"] = None
        st.session_state["all_routes"] = None
        st.session_state["warehouses"] = None

def main():
    st.title("Route Optimization")

    if "clicked_optimize" not in st.session_state:
        st.session_state["clicked_optimize"] = False
    if "best_route" not in st.session_state:
        st.session_state["best_route"] = None
    if "all_routes" not in st.session_state:
        st.session_state["all_routes"] = None
    if "warehouses" not in st.session_state:
        st.session_state["warehouses"] = None

    if "lat" not in st.session_state:
        st.session_state["lat"] = 48.14
    if "lon" not in st.session_state:
        st.session_state["lon"] = 11.58
    if "time_window_start" not in st.session_state:
        st.session_state["time_window_start"] = 2.0
    if "time_window_end" not in st.session_state:
        st.session_state["time_window_end"] = 6.0
    if "quantity" not in st.session_state:
        st.session_state["quantity"] = 75.0

    st.sidebar.header("Order Details")
    st.session_state["lat"] = st.sidebar.number_input("Latitude", value=st.session_state["lat"])
    st.session_state["lon"] = st.sidebar.number_input("Longitude", value=st.session_state["lon"])
    st.session_state["time_window_start"] = st.sidebar.number_input("Time Window Start", value=st.session_state["time_window_start"])
    st.session_state["time_window_end"] = st.sidebar.number_input("Time Window End", value=st.session_state["time_window_end"])
    st.session_state["quantity"] = st.sidebar.number_input("Quantity", min_value=1.0, value=st.session_state["quantity"], step=1.0)


    st.button("Optimize Route", on_click=on_optimize_click)

    if st.session_state["clicked_optimize"]:
        best_route = st.session_state["best_route"]
        all_routes = st.session_state["all_routes"]
        wh_data = st.session_state["warehouses"]

        if all_routes:
            st.markdown("### All Candidate Routes (Chosen route highlighted)")
            df = pd.DataFrame(all_routes)
            best_id = best_route["route_id"] if best_route else None

            def highlight_row(row):
                return ["background-color: green" if row["route_id"] == best_id else ""
                        for _ in row]

            styled_df = df.style.apply(highlight_row, axis=1)
            st.dataframe(styled_df)

        if best_route and wh_data:
            st.markdown("### Map Visualization")
            chosen_wh_id = best_route["warehouse_id"]
            map_ = create_map(
                st.session_state["lat"],
                st.session_state["lon"],
                chosen_wh_id,
                wh_data
            )
            st_folium(map_, width=700, height=500)
        else:
            st.info("No map to display yet.")

if __name__ == "__main__":
    main()
