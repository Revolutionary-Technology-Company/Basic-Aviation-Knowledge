# --- PRIMARY ENGINE: Cloud Radiative Flux Balance ---
import math
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

@njit(fastmath=True)
def calculate_radiative_flux(cloud_fraction, surface_albedo, temp_surface_k, temp_cloud_base_k, solar_zenith_deg):
    """
    Computes the Shortwave (Solar) and Longwave (Infrared) energy balance.
    Compiled via Numba for high-performance floating point operations.
    """
    # 1. Physical Constants
    sigma = 5.670374e-8    # Stefan-Boltzmann constant (W/m^2*K^4)
    solar_constant = 1361.0 # W/m^2 at top of atmosphere
    
    # 2. Shortwave (Solar) Flux Calculation
    # Convert zenith angle to radians and calculate solar incidence
    zenith_rad = solar_zenith_deg * (math.pi / 180.0)
    cos_zenith = max(0.0, math.cos(zenith_rad))
    
    # Dynamic Albedo factoring in cloud cover
    cloud_albedo_factor = 0.55 * cloud_fraction
    total_effective_albedo = surface_albedo + cloud_albedo_factor - (surface_albedo * cloud_albedo_factor)
    
    sw_down_surface = solar_constant * cos_zenith * (1.0 - cloud_albedo_factor)
    sw_net = sw_down_surface * (1.0 - total_effective_albedo)

    # 3. Longwave (Infrared) Flux Calculation
    # Upwelling from the surface
    lw_up = sigma * (temp_surface_k ** 4)
    
    # Downwelling from the atmosphere/clouds
    # Clear sky emissivity ~0.76, dense cloud emissivity ~0.95
    effective_emissivity = 0.76 + (0.95 - 0.76) * cloud_fraction
    lw_down = effective_emissivity * sigma * (temp_cloud_base_k ** 4)
    
    lw_net = lw_down - lw_up

    # 4. Total Net Radiative Flux Balance
    # Positive = Surface is warming (absorbing energy)
    # Negative = Surface is cooling (radiating energy away)
    net_flux = sw_net + lw_net
    
    return sw_net, lw_net, net_flux

def run_radiation_layer(telemetry_override=None):
    """
    Main orchestration function. Extracts live telemetry, computes the radiative
    flux balance, and reports findings directly to the Boeing JSON payload.
    """
    print("☀️ Running Cloud Radiative Flux Balance Layer...")
    
    # 1. Parse incoming live telemetry (with safe standard atmosphere fallbacks)
    c_frac = 0.5            # 50% Cloud Cover
    s_albedo = 0.2          # Standard land albedo
    t_surf_c = 15.0         # Surface Temp
    t_cloud_c = 5.0         # Cloud Base Temp
    zenith = 45.0           # Mid-day solar angle
    
    if telemetry_override:
        c_frac = telemetry_override.get('cloud_fraction', c_frac)
        s_albedo = telemetry_override.get('surface_albedo', s_albedo)
        t_surf_c = telemetry_override.get('temp_c', t_surf_c)
        t_cloud_c = telemetry_override.get('cloud_base_temp_c', t_cloud_c)
        zenith = telemetry_override.get('solar_zenith_deg', zenith)

    # Convert Celsius to Kelvin for Stefan-Boltzmann math
    t_surf_k = t_surf_c + 273.15
    t_cloud_k = t_cloud_c + 273.15

    # 2. Execute FastMath Physics Engine
    sw_net, lw_net, total_net = calculate_radiative_flux(
        cloud_fraction=c_frac,
        surface_albedo=s_albedo,
        temp_surface_k=t_surf_k,
        temp_cloud_base_k=t_cloud_k,
        solar_zenith_deg=zenith
    )
    
    # 3. Format Data for the Flight Computer
    payload = {
        "shortwave_net_flux_w_m2": round(sw_net, 2),
        "longwave_net_flux_w_m2": round(lw_net, 2),
        "total_net_flux_w_m2": round(total_net, 2),
        "cooling_regime_active": bool(total_net < 0.0), # True if radiating more heat than absorbing
        "solar_zenith_deg": zenith,
        "cloud_fraction": c_frac
    }
    
    # 4. Push to Global Pipeline
    telemetry_link.update_global_state("atmospheric_models", "radiation_flux", payload)
    print(f"✅ Radiative Flux parameters reported to global state.")
    
    return payload

if __name__ == "__main__":
    print("=================================================================")
    print("      AEROSPACE CLOUD RADIATIVE FLUX BALANCE ENGINE              ")
    print("=================================================================")
    
    # Test Run
    result = run_radiation_layer()
    print("-" * 65)
    print(f"📡 Net Shortwave (Solar) Absorption: {result['shortwave_net_flux_w_m2']} W/m²")
    print(f"📡 Net Longwave (IR) Emission:       {result['longwave_net_flux_w_m2']} W/m²")
    print(f"🌍 TOTAL NET ENERGY FLUX:            {result['total_net_flux_w_m2']} W/m²")
    print(f"❄️ Surface Cooling Regime Active:   {result['cooling_regime_active']}")
    print("=================================================================")
