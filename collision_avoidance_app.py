# collision_avoidance_app.py
# High-Speed Batched Collision Avoidance (TCAS/TAWS) Engine

import math
import telemetry_link

# --- HARDWARE ABSTRACTION LAYER (HAL) ---
try:
    import cupy as xp  # NVIDIA GPU Acceleration
    HAS_GPU = True
    print("🚀 NVIDIA CUDA Cores Engaged: Array Batching Active (TCAS/TAWS)")
except ImportError:
    import numpy as xp # CPU Fallback
    HAS_GPU = False
    print("⚡ CPU Fallback: Standard Vectorization Active (TCAS/TAWS)")


def calculate_tcas_grid(
    own_pos_x, own_pos_y, own_pos_z,
    own_vel_x, own_vel_y, own_vel_z,
    int_pos_x_arr, int_pos_y_arr, int_pos_z_arr,
    int_vel_x_arr, int_vel_y_arr, int_vel_z_arr,
    safe_distance_m=150.0, lookahead_sec=45.0
):
    """
    Batched Traffic Collision Avoidance System (TCAS).
    Evaluates thousands of radar/lidar tracks simultaneously across the CUDA cores.
    """
    # 1. Load Arrays to Hardware (15-Decimal Standard)
    r_ix = xp.array(int_pos_x_arr, dtype=xp.float64)
    r_iy = xp.array(int_pos_y_arr, dtype=xp.float64)
    r_iz = xp.array(int_pos_z_arr, dtype=xp.float64)

    v_ix = xp.array(int_vel_x_arr, dtype=xp.float64)
    v_iy = xp.array(int_vel_y_arr, dtype=xp.float64)
    v_iz = xp.array(int_vel_z_arr, dtype=xp.float64)

    # 2. Compute Relative Distance Vectors
    rel_x = r_ix - own_pos_x
    rel_y = r_iy - own_pos_y
    rel_z = r_iz - own_pos_z

    # 3. Compute Relative Velocity Vectors (Closure Rates)
    rel_vx = v_ix - own_vel_x
    rel_vy = v_iy - own_vel_y
    rel_vz = v_iz - own_vel_z

    # 4. Dot Products for Closest Point of Approach (CPA)
    dot_r_v = (rel_x * rel_vx) + (rel_y * rel_vy) + (rel_z * rel_vz)
    dot_v_v = (rel_vx**2) + (rel_vy**2) + (rel_vz**2)

    # 🛑 VECTOR GUARD: Prevent division by zero for stationary objects (Terrain)
    dot_v_v = xp.where(dot_v_v == 0.0, 1e-15, dot_v_v)

    # 5. Time to Closest Point of Approach (t_cpa)
    t_cpa = -dot_r_v / dot_v_v

    # 6. Distance at CPA
    d_cpa_x = rel_x + (rel_vx * t_cpa)
    d_cpa_y = rel_y + (rel_vy * t_cpa)
    d_cpa_z = rel_z + (rel_vz * t_cpa)
    d_cpa_mag = xp.sqrt((d_cpa_x**2) + (d_cpa_y**2) + (d_cpa_z**2))

    # 7. Boolean Threat Matrix (Masks act as our else-less gates for arrays)
    # Threat requires: positive time (not behind us), within lookahead time, within safe radius
    is_threat = (t_cpa > 0.0) & (t_cpa <= lookahead_sec) & (d_cpa_mag <= safe_distance_m)

    # 8. Return 15-Decimal Floats to CPU Host
    if HAS_GPU:
        return {
            "t_cpa_sec": xp.round(t_cpa, 15).get().tolist(),
            "d_cpa_meters": xp.round(d_cpa_mag, 15).get().tolist(),
            "is_threat": is_threat.get().tolist()
        }
    return {
        "t_cpa_sec": xp.round(t_cpa, 15).tolist(),
        "d_cpa_meters": xp.round(d_cpa_mag, 15).tolist(),
        "is_threat": is_threat.tolist()
    }


def evaluate_trajectory(trajectory_clear: bool, sensor_status: dict, closure_rate: float, time_to_impact: float):
    """
    Else-Less Command Orchestrator.
    Determines flight maneuvers based purely on failing conditions.
    """
    
    # 🛑 GUARD 1: Sensor Blindness (Immediate Emergency Abort)
    if not sensor_status.get('radar_active', True) or not sensor_status.get('lidar_active', True):
        telemetry_link.update_global_state("evasion", "status", "SENSOR_FAILURE")
        return "ABORT_TERRAIN_FOLLOWING_PULL_UP"

    # 🛑 GUARD 2: Immediate Collision Threat (Resolution Advisory)
    if not trajectory_clear and time_to_impact <= 15.0:
        telemetry_link.update_global_state("evasion", "status", "RESOLUTION_ADVISORY")
        return "EXECUTE_EVASIVE_PITCH_UP_AND_ROLL"

    # 🛑 GUARD 3: High Closure Rate Warning (Traffic Advisory)
    if closure_rate > 300.0 and time_to_impact <= 45.0:
        telemetry_link.update_global_state("evasion", "status", "TRAFFIC_ADVISORY")
        return "COMMAND_SPEED_BRAKES"

    # ✅ HAPPY PATH: Clean flight path, sensors nominal
    telemetry_link.update_global_state("evasion", "status", "NOMINAL_CLEAR")
    return "MAINTAIN_HEADING"


if __name__ == "__main__":
    print("=================================================================")
    print("        TCAS / TAWS AVOIDANCE KERNEL (ELSE-LESS & BATCHED)       ")
    print("=================================================================\n")

    # [TEST 1] Simulated Radar Grid Sweep
    # Our Jet: Flying East at 250 m/s at the origin
    own_x, own_y, own_z = 0.0, 0.0, 10000.0
    own_vx, own_vy, own_vz = 250.0, 0.0, 0.0

    # Intruder Tracks (Simulating 3 Aircraft)
    # 1: Head-on collision course
    # 2: Safe crossing (diverging away)
    # 3: Stationary Terrain Peak
    trk_x = [5000.0, -1000.0, 4000.0]
    trk_y = [0.0, 5000.0, 50.0]
    trk_z = [10000.0, 10000.0, 10000.0]

    trk_vx = [-250.0, -250.0, 0.0]
    trk_vy = [0.0, 0.0, 0.0]
    trk_vz = [0.0, 0.0, 0.0]

    print("📡 Executing Array Batch Radar Scan...")
    results = calculate_tcas_grid(
        own_x, own_y, own_z, own_vx, own_vy, own_vz,
        trk_x, trk_y, trk_z, trk_vx, trk_vy, trk_vz
    )

    # Compile the batched results
    for i in range(3):
        status = "🔴 THREAT DETECTED" if results['is_threat'][i] else "🟢 SAFE"
        print(f"Track {i+1}: {status} | Time to CPA: {round(results['t_cpa_sec'][i], 1)}s | Miss Distance: {round(results['d_cpa_meters'][i], 1)}m")

    # [TEST 2] Else-Less Guard Execution
    print("\n✈️ Routing Track 1 to FSM Orchestrator...")
    
    sensor_health = {"radar_active": True, "lidar_active": True}
    closure = 500.0  # 250m/s + 250m/s head-on
    impact_time = results['t_cpa_sec'][0]
    is_clear = not results['is_threat'][0]

    command = evaluate_trajectory(is_clear, sensor_health, closure, impact_time)
    print(f"🤖 AI Flight Computer Command: {command}")
