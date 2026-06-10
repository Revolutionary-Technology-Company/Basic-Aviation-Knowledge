import telemetry_link
from dynamic_memory_cache import DynamicMemoryCache
from telemetry_link import time_manager
shared_cache = DynamicMemoryCache(percentage=0.45)
import multiprocessing as mp
import numpy as np
from numba import njit
@njit(fastmath=True) # fastmath enables hardware-level floating point optimizations
import matplotlib.pyplot as plt
import math
import aviation_physics
import aviation_telemetry
import aircraft_perf
import sensor_thermodynamics
import aerodynamic_matrix
""" aviation_physics.py """
""" Enterprise Batched Atmospheric & Aerodynamic Kernel """
""" Optimized: Else-Less Guard Clauses | CUDA/NumPy HAL | Numba | Memory Cache """
""" --- HARDWARE ABSTRACTION LAYER (HAL) --- """
try:
    import cupy as xp
    from numba import dummy_njit as njit
    """ CuPy handles JIT, mock Numba """
    HAS_GPU = True
    print("NVIDIA CUDA Cores Engaged: Array Batching Active (Aviation Physics)")
except ImportError:
    """ CPU JIT Compilation """
    HAS_GPU = False
    print("CPU Fallback: Numba Vectorization Active (Aviation Physics)")


""" ===================================================================== """
""" --- PURE MATH KERNELS (THE BASEMENT MATHEMATICIANS) --- """
""" These receive @njit because they only process pure numbers and arrays """
""" ===================================================================== """

@njit(fastmath=True)
def compute_moist_air_density(pressure_hpa, temp_c, relative_humidity_pct):
    """ Dynamic Moist Air Density (rho) using precise gas constants. """
    """ Equation: rho = (p_d / R_d*T) + (p_v / R_v*T) """
    
    """ GUARD 1: Extreme Altitude Drop-off (Vacuum) """
    if pressure_hpa <= 0.0:
        return 0.0

    """ HAPPY PATH: Thermodynamic calculation """
    temp_k = temp_c + 273.15
    r_d = 287.058
    """ Gas constant for dry air """
    r_v = 461.495
    """ Gas constant for water vapor """

    """ Calculate vapor pressure using Tetens equation approximation """
    vapor_pressure_hpa = (relative_humidity_pct / 100.0) * 6.1078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    dry_pressure_hpa = pressure_hpa - vapor_pressure_hpa

    """ Convert hPa to Pascals for standard physics units """
    dry_pressure_pa = dry_pressure_hpa * 100.0
    vapor_pressure_pa = vapor_pressure_hpa * 100.0

    rho_dry = dry_pressure_pa / (r_d * temp_k)
    rho_vapor = vapor_pressure_pa / (r_v * temp_k)

    return rho_dry + rho_vapor


@njit(fastmath=True)
def calculate_fundamental_lift(density_kgm3, velocity_mps, wing_area_m2, cl):
    """ The Fundamental Lift Equation """
    """ Equation: L = 0.5 * rho * V^2 * S * C_L """
    
    """ GUARD 1: Aircraft is stationary or in vacuum """
    if velocity_mps <= 0.0 or density_kgm3 <= 0.0:
        return 0.0

    """ HAPPY PATH """
    dynamic_pressure = 0.5 * density_kgm3 * (velocity_mps ** 2)
    lift_newtons = dynamic_pressure * wing_area_m2 * cl
    
    return lift_newtons


@njit(fastmath=True)
def calculate_ground_effect_ratio(height_ft, wingspan_ft):
    """ Ground Effect (Induced Drag Reduction Matrix) """
    if wingspan_ft <= 0.0:
        return 1.0

    if height_ft >= wingspan_ft:
        return 1.0

    h_b_ratio = height_ft / wingspan_ft
    ratio = (33.0 * (h_b_ratio ** 2)) / (1.0 + 33.0 * (h_b_ratio ** 2))
    return ratio


@njit(fastmath=True)
def calculate_crab_angle(wind_speed_kts, wind_dir_deg, runway_heading_deg, tas_kts):
    """ Wind Correction Angle (WCA) """
    if tas_kts <= 0.0:
        return 0.0, 0.0

    alpha_rad = math.radians(wind_dir_deg - runway_heading_deg)
    v_crosswind = wind_speed_kts * math.sin(alpha_rad)

    if tas_kts <= abs(v_crosswind):
        return 0.0, v_crosswind

    theta_rad = math.asin(v_crosswind / tas_kts)
    return math.degrees(theta_rad), v_crosswind


@njit(fastmath=True)
def compute_isa_temperature(altitude_ft):
    """ ISA Temperature Model (Celsius) """
    if altitude_ft >= 36089.0:
        return -56.5
    return 15.0 - (1.98 * (altitude_ft / 1000.0))


@njit(fastmath=True)
def calculate_mach_number(tas_kts, temp_c):
    """ Calculates Mach Number based on local speed of sound """
    if tas_kts <= 0.0: 
        return 0.0
        
    temp_k = temp_c + 273.15
    speed_of_sound_kts = 38.945 * math.sqrt(temp_k)
    return tas_kts / speed_of_sound_kts


@njit(fastmath=True)
def calculate_ground_acceleration(thrust_n, drag_n, weight_n, friction_coef):
    """ Tactical Takeoff Roll Acceleration (dV/dt) """
    if weight_n <= 0.0: 
        return 0.0
        
    friction_force = friction_coef * weight_n
    net_force = thrust_n - drag_n - friction_force
    
    if net_force <= 0.0: 
        return 0.0
        
    return 9.80665 * (net_force / weight_n)


@njit(fastmath=True)
def calculate_tactical_climb_angle(thrust_n, drag_n, weight_n):
    """ Steep tactical departure climb angle to clear threat rings """
    if drag_n >= thrust_n: 
        return 0.0
        
    excess_thrust = thrust_n - drag_n
    if excess_thrust >= weight_n: 
        return 90.0
        
    return math.degrees(math.asin(excess_thrust / weight_n))


@njit(fastmath=True)
def calculate_accelerated_stall_speed(v_s0_kts, bank_angle_deg):
    """ Tactical Bank Accelerated Stall Limit (V_s,acc) """
    if bank_angle_deg >= 89.0 or bank_angle_deg <= -89.0: 
        return 9999.0
        
    bank_rad = math.radians(abs(bank_angle_deg))
    load_factor = 1.0 / math.cos(bank_rad)
    return v_s0_kts * math.sqrt(load_factor)


""" ===================================================================== """
""" --- THE ORCHESTRATOR (THE MANAGER) --- """
""" NO @njit here. This manages HAL matrices and the RAM cache.           """
""" ===================================================================== """

def get_dynamic_pressure_grid(altitude_ft_arr, local_baro_hpa_arr, temp_c_arr, rh_pct_arr, indicated_airspeed_kts_arr):
    """
    Batched computation of dynamic pressure (q = 0.5 * rho * v^2) across multiple waypoints.
    Utilizes caching to prevent recalculating static mission parameters.
    """
    
    """ GUARD 1: Check Memory Cache first (O(1) lookup) """
    cache_key = f"q_grid_{hash(str(altitude_ft_arr[:5]))}"
    cached_result = shared_cache.check_cache(cache_key)
    if cached_result is not None:
        return cached_result

    """ HAPPY PATH: Compute Grid via Hardware Abstraction Layer """
    alt = xp.array(altitude_ft_arr, dtype=xp.float64)
    baro = xp.array(local_baro_hpa_arr, dtype=xp.float64)
    temp = xp.array(temp_c_arr, dtype=xp.float64)
    rh = xp.array(rh_pct_arr, dtype=xp.float64)
    ias_kts = xp.array(indicated_airspeed_kts_arr, dtype=xp.float64)
    
    """ Vectorized application of the Moist Air function """
    rho_array = xp.array([compute_moist_air_density(p, t, r) for p, t, r in zip(baro, temp, rh)])
    
    velocity_mps = ias_kts * 0.514444
    dynamic_pressure_arr = 0.5 * rho_array * (velocity_mps ** 2)
    
    """ Enforce 15-Decimal Precision Standard for output array """
    if HAS_GPU:
        final_array = xp.round(dynamic_pressure_arr, 15).get().tolist()
    if not HAS_GPU:
        final_array = xp.round(dynamic_pressure_arr, 15).tolist()

    """ Store in memory cache before returning to Boeing telemetry bridge """
    shared_cache.add_to_cache(cache_key, final_array)
    return final_array
