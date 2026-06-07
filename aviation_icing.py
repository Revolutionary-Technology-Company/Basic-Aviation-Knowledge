# --- PRIMARY ENGINE: Aviation Icing ---
import multiprocessing as mp
import telemetry_link  # Integrated Centralized Data Bus
import numpy as np # Fallback to standard CPU math
import pandas as pd

try:
    import cupy as np  # Attempt to use GPU-accelerated array math
    print("🚀 NVIDIA GPU Acceleration Engaged")
except ImportError:
    print("⚡ Engaging CPU")

def calculate_icing_accretion(temp_c, rh_pct, rainfall_mm_hr, elevation_m, wind_mph=30.0):
    """Solves the coupled mass collection and thermodynamic freezing equations."""
    L_f = 3.34e5  # Latent heat of fusion for water (J/kg)
    
    # Elevation Pressure Shift Correction
    P_pascals = 101325.0 * (1.0 - 2.25577e-5 * elevation_m) ** 5.25588

    # Derive Airborne Liquid Water Content (LWC)
    if rainfall_mm_hr > 0 and temp_c <= 2.0:
        lwc_g_m3 = 0.072 * (rainfall_mm_hr**0.88)
    else:
        lwc_g_m3 = 0.0

    v_m_s = wind_mph * 0.44704
    lwc_kg_m3 = lwc_g_m3 / 1000.0

    # Thermodynamic Freezing Fraction Matrix
    if temp_c < 0.0 and lwc_g_m3 > 0.0:
        q_evap_loss = (1.0 - rh_pct) * 15.0
        q_convective_loss = 12.5 * np.sqrt(v_m_s) * (0.0 - temp_c)
        total_cooling_energy = q_convective_loss + q_evap_loss
        latent_heat_available = lwc_kg_m3 * v_m_s * L_f
        n_freezing = total_cooling_energy / latent_heat_available
        n_freezing = max(0.0, min(1.0, n_freezing))
    else:
        n_freezing = 0.0

    # Mass Collection Accumulation
    e_collection = 0.65 if temp_c <= 0.0 else 0.0
    mass_accretion_rate_sec = e_collection * n_freezing * lwc_kg_m3 * v_m_s
    mass_accretion_hr_kg = mass_accretion_rate_sec * 3600.0

    return P_pascals / 100.0, lwc_g_m3, n_freezing, mass_accretion_hr_kg

def get_live_icing_pirep_data(live_telemetry, env_data):
    """Bridge function mapping physical mass rates to standard FAA PIREP codes."""
    _, _, _, mass = calculate_icing_accretion(
        temp_c=env_data.get('temp_c', 0.0),
        rh_pct=env_data.get('rh_pct', 0.5),
        rainfall_mm_hr=env_data.get('rain_mm_hr', 0.0),
        elevation_m=live_telemetry.get('elevation_ft', 0.0) * 0.3048,
        wind_mph=env_data.get('wind_mph', 30.0)
    )

    if mass < 0.1:
        intensity = "NONE"
    elif mass < 2.0:
        intensity = "LGT"
    elif mass < 5.0:
        intensity = "MOD"
    else:
        intensity = "SEV"

    icing_type = "RIME" if env_data.get('temp_c', 0.0) < -10 else "CLEAR"
    pirep_code = f"{intensity} {icing_type}" if intensity != "NONE" else "NONE"
    
    return pirep_code, mass

def run_icing_layer(telemetry_override=None):
    """
    Main orchestration function. Extracts live telemetry, runs the simulation, 
    and reports findings directly to the Boeing JSON payload.
    """
    print("❄️ Running Structural Aircraft Icing Hazard Matrix...")
    
    # Build dictionaries to match the existing internal API requirements
    live_telemetry = {"elevation_ft": 5000.0}
    env_data = {"temp_c": -2.0, "rh_pct": 0.85, "rain_mm_hr": 1.5, "wind_mph": 45.0}
    
    if telemetry_override:
        live_telemetry["elevation_ft"] = telemetry_override.get('elevation_ft', live_telemetry["elevation_ft"])
        env_data["temp_c"] = telemetry_override.get('temp_c', env_data["temp_c"])
        env_data["rh_pct"] = telemetry_override.get('rh_pct', env_data["rh_pct"])
        env_data["rain_mm_hr"] = telemetry_override.get('rain_mm_hr', env_data["rain_mm_hr"])
        env_data["wind_mph"] = telemetry_override.get('wind_mph', env_data["wind_mph"])

    pirep_code, mass = get_live_icing_pirep_data(live_telemetry, env_data)
    
    payload = {
        "environmental_temp_c": round(env_data["temp_c"], 2),
        "accretion_rate_kg_hr": round(mass, 4),
        "faa_pirep_code": pirep_code,
        "hazard_active": bool(mass > 0.1)
    }
    
    telemetry_link.update_global_state("atmospheric_models", "structural_icing", payload)
    print(f"✅ Icing calculations reported to global state (Status: {pirep_code}).")
    
    return payload

if __name__ == "__main__":
    print("=================================================================")
    print("         STRUCTURAL AIRCRAFT ICING HAZARD ENGINE                 ")
    print("=================================================================")
    results = run_icing_layer()
    print("\n--- TEST RESULTS ---")
    print(f"Accretion Rate: {results['accretion_rate_kg_hr']} kg/hr")
    print(f"PIREP Output:   {results['faa_pirep_code']}")
