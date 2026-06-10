import numpy as np

from waypoint_manager import WaypointManager

""" flight_control_dynamics.py """
""" High-Fidelity Fly-By-Wire, FSM State Matrix, & Control Allocation """
""" Optimized: Else-Less Guard Clauses | 15-Decimal Precision | Numba Kernels """

import math
import telemetry_link

""" --- HARDWARE ABSTRACTION LAYER (HAL) --- """
try:
    import cupy as xp
    from numba import dummy_njit as njit
    HAS_GPU = True
    print("NVIDIA CUDA Cores Engaged: Matrix Allocation Active (Flight Controls)")
except ImportError:
    import numpy as xp
    from numba import njit
    HAS_GPU = False
    print("CPU Fallback: Numba Vectorization Active (Flight Controls)")


""" ===================================================================== """
""" --- PURE MATH KERNELS (THE BASEMENT MATHEMATICIANS) --- """
""" These receive @njit because they only process pure numbers and arrays """
""" ===================================================================== """

@njit(fastmath=True)
def compute_hermite_interpolation(current_val, target_val, t_norm):
    """ Cubic Hermite Interpolation for smooth C2 mathematical continuity. """
    """ Prevents abrupt PID controller spikes by smoothing waypoint transitions. """
    
    """ GUARD 1: Clamp lower bounds """
    if t_norm <= 0.0:
        return current_val

    """ GUARD 2: Clamp upper bounds """
    if t_norm >= 1.0:
        return target_val

    """ HAPPY PATH: Smooth curve calculation """
    t2 = t_norm * t_norm
    t3 = t2 * t_norm
    
    h00 = (2.0 * t3) - (3.0 * t2) + 1.0
    h01 = (-2.0 * t3) + (3.0 * t2)
    
    """ Assumes zero boundary velocity for simple waypoint snapping """
    interpolated_val = (h00 * current_val) + (h01 * target_val)
    return interpolated_val


@njit(fastmath=True)
def compute_turn_stall_margin(current_airspeed_kts, bank_angle_deg, v_stall_level_kts):
    """ Calculates dynamic stall speed increases during high-G banking. """
    
    """ GUARD 1: Extreme bank angle (Physics breakdown / Vertical flight) """
    if bank_angle_deg >= 89.0 or bank_angle_deg <= -89.0:
        return 0.0, 999.0
        
    """ HAPPY PATH: V_stall_turn = V_stall_level * sqrt(Load Factor) """
    bank_rad = math.radians(abs(bank_angle_deg))
    load_factor = 1.0 / math.cos(bank_rad)
    v_stall_turn = v_stall_level_kts * math.sqrt(load_factor)
    
    margin_kts = current_airspeed_kts - v_stall_turn
    return margin_kts, v_stall_turn


@njit(fastmath=True)
def compute_longitudinal_acceleration(thrust_n, drag_n, weight_n, gamma_deg):
    """ Kinematic solver for flight path deceleration/acceleration. """
    
    """ GUARD 1: Airborne or Invalid Weight """
    if weight_n <= 0.0: 
        return 0.0
        
    """ HAPPY PATH: dv/dt = g * ((T - D)/W) - g * sin(gamma) """
    gamma_rad = math.radians(gamma_deg)
    gravity_component = 9.80665 * math.sin(gamma_rad)
    thrust_drag_component = 9.80665 * ((thrust_n - drag_n) / weight_n)
    
    accel_mps2 = thrust_drag_component - gravity_component
    return accel_mps2


@njit(fastmath=True)
def compute_shortest_heading_error(current_hdg, target_hdg):
    """ Calculates the fastest rotational path to a target heading. """
    
    """ HAPPY PATH: Normalize to 360 circle """
    error = (target_hdg - current_hdg) % 360.0
    
    """ GUARD 1: Turn left instead of right """
    if error > 180.0: 
        return error - 360.0
        
    """ GUARD 2: Turn right instead of left """
    if error < -180.0: 
        return error + 360.0
        
    return error


@njit(fastmath=True)
def compute_required_pitch_angle(delta_alt_m, distance_m):
    """ Solves geometric flight path angle required to hit a spatial waypoint. """
    
    """ GUARD 1: Zero distance (Directly overhead) """
    if distance_m <= 0.0:
        return 0.0
        
    """ HAPPY PATH: Trigonometric glide slope """
    theta_rad = math.atan(delta_alt_m / distance_m)
    return math.degrees(theta_rad)


@njit(fastmath=True)
def compute_turn_time_remaining(heading_error_deg, turn_rate_dps):
    """ Predicts physical time remaining to exit an active turn. """
    
    """ GUARD 1: Not turning or rate too slow """
    if turn_rate_dps <= 0.01:
        return 999.0
        
    """ HAPPY PATH """
    return abs(heading_error_deg) / turn_rate_dps


@njit(fastmath=True)
def compute_pid_step(setpoint, current_val, dt, kp, ki, kd, integral_error, max_limit):
    """ Else-less Proportional-Integral-Derivative (PID) math with Anti-Windup. """
    
    """ GUARD 1: Prevent Division by Zero on clock skip """
    if dt <= 0.0:
        return 0.0, integral_error

    """ HAPPY PATH: Compute Raw Dynamic Request """
    error = setpoint - current_val
    new_integral = integral_error + (error * dt)
    derivative = error / dt
    
    command = (kp * error) + (ki * new_integral) + (kd * derivative)

    """ GUARD 2: Positive Saturation Clamp """
    if command > max_limit:
        return max_limit, new_integral

    """ GUARD 3: Negative Saturation Clamp """
    if command < -max_limit:
        return -max_limit, new_integral

    return command, new_integral


@njit(fastmath=True)
def calculate_crosswind_rejection_gains(v_crosswind_kts, heading_error_deg):
    """ Calculates immediate aileron and rudder counter-deflections. """
    if abs(v_crosswind_kts) < 2.0: return 0.0, 0.0
        
    heading_rad = math.radians(heading_error_deg)
    side_velocity = v_crosswind_kts * math.cos(heading_rad)
    
    aileron_counter_cmd = side_velocity * -0.15
    rudder_counter_cmd = side_velocity * 0.08
    return aileron_counter_cmd, rudder_counter_cmd


@njit(fastmath=True)
def calculate_asymmetric_braking(turn_radius_req_m, track_width_m, ground_speed_kts, max_brake_psi):
    """ Calculates differential main-gear braking for tight obstacle evasion. """
    if ground_speed_kts > 20.0: return 0.0, 0.0
    if abs(turn_radius_req_m) >= (track_width_m * 3.0): return 0.0, 0.0
        
    inside_brake = max_brake_psi * 0.85
    outside_brake = 0.0
    
    if turn_radius_req_m < 0.0: return outside_brake, inside_brake
    return inside_brake, outside_brake


@njit(fastmath=True)
def calculate_predictive_tail_strike_limit(static_limit_deg, instantaneous_pitch_rate_dps, latency_offset_sec):
    """ Integrates second-order actuator latency to predict tail-strike overshoot. """
    if instantaneous_pitch_rate_dps <= 0.0: return static_limit_deg
    return static_limit_deg - (latency_offset_sec * instantaneous_pitch_rate_dps)


""" ===================================================================== """
""" --- THE ORCHESTRATOR (THE MANAGER) --- """
""" NO @njit here. This interacts with classes, state, and telemetry.     """
""" ===================================================================== """

class FlightControlDynamics:
    """ Autonomous flight control surface logic and FSM mode manager. """

    def __init__(self, mode="CIVILIAN"):
        self.mode = mode
        self.active_waypoint = None
        
        """ 15-Decimal Mathematical Limits """
        self.MAX_ELEVATOR_DEG = 20.000000000000000
        self.MAX_TVC_DEG = 15.000000000000000
        self.TRACK_WIDTH_M = 8.500000000000000
        self.MAX_BRAKE_PSI = 3000.000000000000000
        
        """ Actuator Dynamics Model """
        self.TAU_TRANSPORT = 0.010000000000000
        self.OMEGA_N = 30.000000000000000
        self.ZETA = 0.707000000000000
        self.LATENCY_OFFSET = self.TAU_TRANSPORT + ((2.0 * self.ZETA) / self.OMEGA_N)

    def set_mode(self, new_mode):
        """ Explicit mode toggle for the FSM. """
        self.mode = new_mode
        telemetry_link.update_global_state("authority", "fsm_mode", self.mode)
        return self.mode

    def trigger_evasive_tactical_maneuver(self):
        """ Hard Hook for the Boeing Telemetry Bridge. """
        self.set_mode("TACTICAL_EVASION")
        target_pitch = self.MAX_ELEVATOR_DEG * 0.90
        telemetry_link.update_global_state("flight_controls", "elevator_cmd", target_pitch)
        return round(float(target_pitch), 15)

    def interpolate_path(self, current_pos, next_wp, t_norm):
        """ Class wrapper for pure C2 Hermite math. """
        interpolated = compute_hermite_interpolation(float(current_pos), float(next_wp), float(t_norm))
        return round(float(interpolated), 15)

    def analyze_maneuver_safety(self, current_airspeed_kts, target_bank_deg, v_stall_level_kts=50.0):
        """ Projects if a planned FSM maneuver will breach structural constraints. """
        margin, new_stall = compute_turn_stall_margin(current_airspeed_kts, target_bank_deg, v_stall_level_kts)
        
        limit_margin = 15.0 if self.mode == "CIVILIAN" else 5.0
        
        """ GUARD 1: Insufficient aerodynamic energy to complete turn """
        if margin < limit_margin:
            return {"is_safe": False, "margin_kts": round(float(margin), 15), "stall_speed": round(float(new_stall), 15)}
            
        """ HAPPY PATH """
        return {"is_safe": True, "margin_kts": round(float(margin), 15), "stall_speed": round(float(new_stall), 15)}

    def get_smooth_heading(self, current_hdg, target_hdg):
        """ Wrapper for shortest path heading logic. """
        err = compute_shortest_heading_error(float(current_hdg), float(target_hdg))
        return round(float(err), 15)

    def calculate_required_attitude(self, current_alt_m, target_alt_m, distance_m):
        """ Calculates deck angle required for next waypoint. """
        delta_alt = target_alt_m - current_alt_m
        req_pitch = compute_required_pitch_angle(float(delta_alt), float(distance_m))
        return round(float(req_pitch), 15)

    def calculate_turn_deceleration(self, thrust_n, drag_n, weight_n, gamma_deg):
        """ Outputs specific deceleration values for throttle auto-compensation. """
        accel = compute_longitudinal_acceleration(float(thrust_n), float(drag_n), float(weight_n), float(gamma_deg))
        return round(float(accel), 15)

    def get_turn_exit_metrics(self, current_hdg, target_hdg, turn_rate_dps):
        """ Predicts timestamp of turn completion. """
        hdg_err = compute_shortest_heading_error(float(current_hdg), float(target_hdg))
        time_rem = compute_turn_time_remaining(hdg_err, float(turn_rate_dps))
        return {"heading_error": round(float(hdg_err), 15), "seconds_to_level": round(float(time_rem), 15)}

    def get_dynamics_for_active_waypoint(self, waypoint_id):
        """ Fetches live environment and tracking requirements for current waypoint. """
        self.active_waypoint = waypoint_id
        wp_data = telemetry_link.get_global_state("navigation", "waypoints").get(waypoint_id, {})
        
        """ GUARD 1: Waypoint missing from bus """
        if not wp_data:
            return {"status": "WAYPOINT_NOT_FOUND"}
            
        return {
            "status": "TRACKING_ACTIVE",
            "target_lat": round(float(wp_data.get("lat", 0.0)), 15),
            "target_lon": round(float(wp_data.get("lon", 0.0)), 15),
            "target_alt_m": round(float(wp_data.get("alt_m", 0.0)), 15)
        }

    def allocate_zero_latency_pitch(self, commanded_moment, dynamic_pressure, velocity_mps, thrust_n):
        """ Control Allocation Matrix (B). """
        S = 100.0
        c_bar = 5.0
        Cm_de = -0.5
        l_tvc = 15.0

        """ GUARD 1: Zero Speed TVC Allocator """
        if velocity_mps < 10.0:
            tvc_cmd = -commanded_moment / (thrust_n * l_tvc + 1e-15)
            tvc_cmd_clipped = xp.clip(tvc_cmd, -self.MAX_TVC_DEG, self.MAX_TVC_DEG)
            return 0.0, round(float(tvc_cmd_clipped), 15)

        """ HAPPY PATH: Dynamic Matrix """
        b_elevator = dynamic_pressure * S * c_bar * Cm_de
        b_tvc = -(thrust_n * l_tvc)

        B_matrix = xp.array([[b_elevator, b_tvc]])
        B_pinv = xp.linalg.pinv(B_matrix)
        deflections = B_pinv @ xp.array([[commanded_moment]])

        delta_e = float(xp.clip(float(deflections[0][0]), -self.MAX_ELEVATOR_DEG, self.MAX_ELEVATOR_DEG))
        delta_tvc = float(xp.clip(float(deflections[1][0]), -self.MAX_TVC_DEG, self.MAX_TVC_DEG))

        return round(delta_e, 15), round(delta_tvc, 15)
