# memory_manager.py
from dynamic_memory_cache import DynamicMemoryCache

# Create one shared cache instance for the whole app
shared_cache = DynamicMemoryCache(percentage=0.25)

import multiprocessing as mp
import math
import numpy as np

try:
    import cupy as np  # Attempt to use GPU-accelerated array math
    print("🚀 NVIDIA GPU Acceleration Engaged")
except ImportError:
    import numpy as np # Fallback to standard CPU math
    print("⚡ Using CPU (NVIDIA acceleration not detected)")

class AtmosphericEntryController:
    """
    Consolidated Aero-Thermodynamic and PID Guidance Engine.
    Integrates Heat Flux, Wind Drift, and PID Bank Control.
    """
    def __init__(self, mass, S, cd0, K, R_p, g0, nose_radius=1.5):
        self.m, self.S, self.cd0, self.K = mass, S, cd0, K
        self.R_p, self.g0, self.R_n = R_p, g0, nose_radius
        # PID Constants
        self.kp, self.ki, self.kd = 0.5, 0.01, 0.1
        self.prev_error = 0
        self.integral = 0

    def calculate_thermal_flux(self, rho, v):
        # Sutton-Graves Correlation (W/cm2)
        k_sutton = 1.7415e-4
        return k_sutton * math.sqrt(rho / self.R_n) * (v ** 3)

    def get_pid_bank_angle(self, crossrange_drift_km, dt):
        # Closed-loop feedback to counteract storm drift
        error = crossrange_drift_km
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.prev_error = error
        return np.clip(output, -45, 45) # Limit bank to 45 degrees

    def evaluate_approach_safety(self, v, h, alpha):
        # Return safety boolean and required thermal adjustments
        density = 1.225 * math.exp(-h / 8500)
        q = self.calculate_thermal_flux(density, v)
        
        is_safe = q < 450.0  # Limit for ablation shields
        return {"is_safe": is_safe, "heat_flux": q, "recommended_alpha": alpha if is_safe else 40.0}
