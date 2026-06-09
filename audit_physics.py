import rossby_model
import aviation_physics
import telemetry_link
from telemetry_link import time_manager
import flight_control_dynamics
def audit():
    print("--- AEROSPACE CODE AUDIT ---")
    # This verifies the math kernels are loaded and their functions are present
    print(f"Rossby Model: {dir(rossby_model)}") 
    print(f"Physics Kernel: {dir(aviation_physics)}")
    print(f"Flight Dynamics: {dir(flight_control_dynamics)}")
    print("\n[STATUS]: All high-fidelity math kernels successfully detected.")
if __name__ == "__main__":
    audit()
    try:
    import cupy as xp
    HAS_GPU = True
    print("NVIDIA CUDA Cores Engaged: Array Batching Active (Performance)")
except ImportError:
    import numpy as xp
    HAS_GPU = False
    print("CPU Fallback: Standard Vectorization Active (Performance)")
from dynamic_memory_cache import DynamicMemoryCache
shared_cache = DynamicMemoryCache(percentage=0.75)
