# app.py
import streamlit as st
import telemetry_link
from waypoint_manager import WaypointManager
from flight_control_dynamics import FlightControlDynamics

# --- 1. GLOBAL INITIALIZATION ---
# Initialize the Centralized Data Bus and Core Navigation Engines
wp_manager = WaypointManager()
computer = FlightControlDynamics(mode="CIVILIAN")

st.set_page_config(page_title="Aviation Knowledge Engine", layout="wide")
st.title("✈️ Aviation Knowledge Engine - Flight Control Dashboard")

# --- 2. SIDEBAR: WAYPOINT REGISTRATION & MODE ---
with st.sidebar:
    st.header("Waypoint Registration")
    wp_name = st.text_input("Waypoint Name", value="KSEA_Arrival")
    lat = st.number_input("Latitude", value=47.4502, format="%.6f")
    lon = st.number_input("Longitude", value=-122.3088, format="%.6f")
    alt = st.number_input("Target Altitude (ft)", value=1500)
    heading = st.number_input("Target Heading", value=160)
    
    if st.button("Register Waypoint"):
        wp_manager.register_waypoint(wp_name, lat, lon, alt, heading)
        st.success(f"Registered {wp_name}")
    
    st.markdown("---")
    st.subheader("Flight Mode Control")
    mode = st.radio("Maneuver Profile", ["CIVILIAN", "SPORT"])
    computer.set_mode(mode=mode)
    
    st.markdown("---")
    st.caption("Centralized Data Bus: ACTIVE")

# --- 3. MAIN DASHBOARD: PERFORMANCE ADVISORY ---
st.subheader("Predictive Performance Envelope")
active_wp = wp_manager.get_active_waypoint(index=0)

if active_wp:
    # Get Safety Advisory (using a simulated 110kts current airspeed for the demo)
    safety = computer.analyze_maneuver_safety(current_airspeed=110, target_bank_deg=30)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Navigation Fix", active_wp.name)
        st.metric("Target Heading", f"{active_wp.target_heading}°")
    with col2:
        st.metric("Target Altitude", f"{active_wp.alt} ft")
        st.metric("Dynamic Stall Margin", f"{safety['margin']} kts")
    with col3:
        if safety['is_unsafe']:
            st.error("⚠️ ADVISORY: Planned maneuver breaches structural safety envelope.")
        else:
            st.success("✅ Maneuver safely within calculated performance envelope.")
else:
    st.info("No active waypoints. Use the sidebar to register a navigation fix.")

st.markdown("---")

# --- 4. ENVIRONMENT & PHYSICS ENGINES ---
st.subheader("Atmospheric & Physics Matrix Integration")

model_choice = st.selectbox("Select Core Prediction Engine to Run", [
    "Wind Dynamics & Cooling Index",
    "Fog Thermodynamics Matrix",
    "Cloud Radiative Flux Balance",
    "Cloud Thermodynamics & Trajectories",
    "Space Weather Astronomical Tracker",
    "Lunar Ephemeris Topocentric Path",
    "Structural Aircraft Icing Hazard"
])

if st.button("Execute High-Performance Engine"):
    with st.spinner("Compiling physics matrix and injecting into global state..."):
        try:
            if model_choice == "Wind Dynamics & Cooling Index":
                import wind_dynamics
                results = wind_dynamics.run_wind_layer()
                st.json(results)
                
            elif model_choice == "Fog Thermodynamics Matrix":
                import fog_thermodynamics
                results = fog_thermodynamics.run_fog_layer()
                st.json(results)
                
            elif model_choice == "Cloud Radiative Flux Balance":
                import radiation_model
                results = radiation_model.run_radiation_layer()
                st.json(results)
                
            elif model_choice == "Cloud Thermodynamics & Trajectories":
                import cloud_model
                results = cloud_model.run_cloud_layer()
                st.json(results)
                
            elif model_choice == "Space Weather Astronomical Tracker":
                import space_weather_engine
                results = space_weather_engine.run_space_layer()
                st.json(results)
                
            elif model_choice == "Lunar Ephemeris Topocentric Path":
                import lunar_model
                results = lunar_model.run_lunar_layer(telemetry_override={"lat": 47.6062, "lon": -122.3321, "elevation_m": 45.0, "year": 2026})
                st.json(results)
                
            elif model_choice == "Structural Aircraft Icing Hazard":
                import aviation_icing
                # Providing mock environment data for the UI trigger
                env_data = {"temp_c": -5, "rh_pct": 85, "rain_mm_hr": 2.5}
                telemetry = {"elevation_ft": 5000}
                pirep, mass = aviation_icing.get_live_icing_pirep_data(telemetry, env_data)
                st.write(f"**Calculated PIREP:** {pirep}")
                st.write(f"**Mass Accretion:** {mass:.2f} kg/hr")
                
            st.success("✅ Engine execution complete. Data injected into Boeing Global State.")
        except Exception as e:
            st.error(f"Engine execution failed: {e}")

st.markdown("---")

# --- 5. BOEING SYSTEM EXPORT ---
st.subheader("Flight
