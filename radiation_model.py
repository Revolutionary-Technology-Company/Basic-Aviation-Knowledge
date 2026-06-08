# --- PRIMARY ENGINE: Radiation Modeling & Thermodynamics ---
import math
import pandas as pd
from numba import njit

# --- SECONDARY ENGINE DEPENDENCIES ---
import telemetry_link          # NEW: Integrated Centralized Data Bus
import aviation_physics        # Core math
import aviation_telemetry      # Data flow

try:
    import cupy as np  # Attempt to use GPU-accelerated array math
    print("🚀 NVIDIA GPU Acceleration Engaged (Radiation Matrix)")
except ImportError:
    import numpy as np # Fallback to standard CPU math
    print("⚡ Using CPU (NVIDIA acceleration not detected)")


# =========================================================================
# GLOBAL THERMODYNAMIC CONSTANTS
# =========================================================================
STEFAN_BOLTZMANN = 5.670374419e-8  # W / (m^2 * K^4)
LUMINOSITY_SUN_W = 3.828e26        # Watts
RADIUS_SUN_M     = 6.957e8         # Meters
LUMINOUS_EFFICACY_SUN = 93.0       # Approximate Lumens per Watt for a G-type star


# =========================================================================
# 1. EARTH ATMOSPHERIC RADIATION BALANCE
# =========================================================================
@njit(fastmath=True)
def calculate_radiative_flux_grid(
    cloud_fraction_array, surface_albedo_array, 
    temp_surf_c_array, temp_cloud_c_array, zenith_deg_array
):
    """
    Computes the Shortwave (Solar) and Longwave (Infrared) energy balance
    across an entire geographic grid simultaneously.
    """
    # 1. Load data to hardware
    c_frac = xp.array(cloud_fraction_array, dtype=xp.float64)
    s_albedo = xp.array(surface_albedo_array, dtype=xp.float64)
    t_surf_k = xp.array(temp_surf_c_array, dtype=xp.float64) + 273.15
    t_cloud_k = xp.array(temp_cloud_c_array, dtype=xp.float64) + 273.15
    zenith_deg = xp.array(zenith_deg_array, dtype=xp.float64)
    
    # 2. Shortwave (Solar) Flux Calculation
    zenith_rad = zenith_deg * (xp.pi / 180.0)
    cos_zenith = xp.maximum(0.0, xp.cos(zenith_rad))
    
    # Dynamic Albedo factoring in cloud cover (0.55 standard cloud albedo)
    cloud_albedo_factor = 0.55 * c_frac
    total_effective_albedo = s_albedo + cloud_albedo_factor - (s_albedo * cloud_albedo_factor)
    
    sw_down_surface = SOLAR_CONSTANT * cos_zenith * (1.0 - cloud_albedo_factor)
    sw_net = sw_down_surface * (1.0 - total_effective_albedo)

    # 3. Longwave (Infrared) Flux Calculation
    lw_up = STEFAN_BOLTZMANN * (t_surf_k ** 4)
    
    # Downwelling from the atmosphere/clouds
    effective_emissivity = 0.76 + (0.95 - 0.76) * c_frac
    lw_down = effective_emissivity * STEFAN_BOLTZMANN * (t_cloud_k ** 4)
    lw_net = lw_down - lw_up

    # 4. Total Net Radiative Flux Balance
    net_flux = sw_net + lw_net
    
    # 5. Return to CPU host with 15-decimal standard
    if HAS_GPU:
        return {
            "shortwave_net_w_m2": xp.round(sw_net, 15).get().tolist(),
            "longwave_net_w_m2": xp.round(lw_net, 15).get().tolist(),
            "total_net_w_m2": xp.round(net_flux, 15).get().tolist()
        }
    else:
        return {
            "shortwave_net_w_m2": xp.round(sw_net, 15).tolist(),
            "longwave_net_w_m2": xp.round(lw_net, 15).tolist(),
            "total_net_w_m2": xp.round(net_flux, 15).tolist()
        }

# =========================================================================
# 2. DEEP SPACE STELLAR THERMODYNAMICS (BATCHED GRID)
# =========================================================================
def compute_stellar_thermodynamics_grid(masses_solar, radii_solar):
    """
    Calculates the surface temperature (K) and total thermal output (Watts)
    for an entire catalog of celestial bodies simultaneously based on Main Sequence relations.
    """
    mass_arr = xp.array(masses_solar, dtype=xp.float64)
    radius_arr = xp.array(radii_solar, dtype=xp.float64)

    # 1. Mass-Luminosity Relation: L/L_sun = (M/M_sun)^3.5
    luminosity_solar_ratio = mass_arr ** 3.5
    luminosity_watts = luminosity_solar_ratio * LUMINOSITY_SUN_W

    # 2. Radius scale conversion
    radius_meters = radius_arr * RADIUS_SUN_M

    # 3. Stefan-Boltzmann Law inversion for Temperature
    # T = (L / (4 * pi * R^2 * sigma))^(1/4)
    surface_area = 4.0 * xp.pi * (radius_meters ** 2)
    temperature_k = (luminosity_watts / (surface_area * STEFAN_BOLTZMANN)) ** 0.25

    if HAS_GPU:
        return {
            "luminosity_w": xp.round(luminosity_watts, 15).get().tolist(),
            "surface_temp_k": xp.round(temperature_k, 15).get().tolist()
        }
    else:
        return {
            "luminosity_w": xp.round(luminosity_watts, 15).tolist(),
            "surface_temp_k": xp.round(temperature_k, 15).tolist()
        }

# =========================================================================
# 3. ORCHESTRATION LAYER
# =========================================================================
def run_radiation_layer(telemetry_override=None):
    """Main orchestration function reporting to Boeing/NASA payloads."""
    print("☀️ Running Batched Radiative Flux Balance Layer...")
    
    # Fallback default scalar lists
    c_fracs = [0.5]
    s_albedos = [0.2]
    t_surfs = [15.0]
    t_clouds = [5.0]
    zeniths = [45.0]
    
    if telemetry_override:
        if isinstance(telemetry_override, dict):
            c_fracs = [telemetry_override.get('cloud_fraction', 0.5)]
            s_albedos = [telemetry_override.get('surface_albedo', 0.2)]
            t_surfs = [telemetry_override.get('temp_c', 15.0)]
            t_clouds = [telemetry_override.get('cloud_base_temp_c', 5.0)]
            zeniths = [telemetry_override.get('solar_zenith_deg', 45.0)]
        elif isinstance(telemetry_override, list):
            c_fracs = [t.get('cloud_fraction', 0.5) for t in telemetry_override]
            s_albedos = [t.get('surface_albedo', 0.2) for t in telemetry_override]
            t_surfs = [t.get('temp_c', 15.0) for t in telemetry_override]
            t_clouds = [t.get('cloud_base_temp_c', 5.0) for t in telemetry_override]
            zeniths = [t.get('solar_zenith_deg', 45.0) for t in telemetry_override]

    results = calculate_radiative_flux_grid(c_fracs, s_albedos, t_surfs, t_clouds, zeniths)
    
    # Extract the first element to maintain backward compatibility with JSON scalar payloads
    payload = {
        "shortwave_net_flux_w_m2": results['shortwave_net_w_m2'][0],
        "longwave_net_flux_w_m2": results['longwave_net_w_m2'][0],
        "total_net_flux_w_m2": results['total_net_w_m2'][0],
        "cooling_regime_active": bool(results['total_net_w_m2'][0] < 0.0),
        "solar_zenith_deg": zeniths[0],
        "cloud_fraction": c_fracs[0]
    }
    
    telemetry_link.update_global_state("atmospheric_models", "radiation_flux", payload)
    return payload


if __name__ == "__main__":
    print("=================================================================")
    print("      AEROSPACE THERMODYNAMICS & RADIATION ENGINE (BATCHED)      ")
    print("=================================================================")
    
    # [TEST 1] Earth Atmospheric Grid (Simulating 3 different geographic sectors)
    print("\n[TEST 1] Earth Surface Radiative Balance")
    test_c_fracs = [0.0, 0.5, 1.0]      # Clear, Scattered, Overcast
    test_albedos = [0.1, 0.2, 0.8]      # Ocean, Land, Snow
    test_t_surfs = [25.0, 15.0, -10.0]  # Tropical, Temperate, Arctic
    test_t_clouds= [10.0, 5.0, -20.0]   
    test_zeniths = [10.0, 45.0, 80.0]   # High sun, Mid sun, Low sun
    
    earth_results = calculate_radiative_flux_grid(
        test_c_fracs, test_albedos, test_t_surfs, test_t_clouds, test_zeniths
    )
    
    for i in range(3):
        print(f"Sector {i+1}: Net Flux = {round(earth_results['total_net_w_m2'][i], 2)} W/m²")

    # [TEST 2] Deep Space Stellar Grid (Simulating Sun, Sirius A, Proxima Centauri B)
    print("\n[TEST 2] Deep Space Stellar Surface Calculation")
    test_masses_solar = [1.0, 2.06, 0.12]
    test_radii_solar  = [1.0, 1.71, 0.14]
    
    stellar_results = compute_stellar_thermodynamics_grid(test_masses_solar, test_radii_solar)
    
    for i, name in enumerate(["Sol (Earth)", "Sirius A", "Proxima Centauri"]):
        temp = round(stellar_results['surface_temp_k'][i], 2)
        print(f"{name}: Surface Temp = {temp} K")
