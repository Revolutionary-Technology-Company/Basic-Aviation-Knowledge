# intent_engine.py
import numpy as np

class IntruderIntentAnalyst:
    """
    Isolated Telemetry Module. Tracks historical memory for individual aircraft 
    and handles the high-level kinematic math to diagnose pilot intent profiles.
    """
    def __init__(self, dt=1.0):
        self.dt = dt
        self.G_METERS_SEC2 = 9.81
        self.FT_TO_METERS = 0.3048
        
        # Memory storage dictionary to keep track of previous telemetry states per ICAO hex
        self.history = {}

    def update_history(self, icao, track, baro_rate):
        """ Stores the current second's data to calculate derivatives on the next cycle """
        self.history[icao] = {
            "prev_track": track,
            "prev_baro_rate": baro_rate
        }

    def diagnose_behavior_profile(self, icao, current_gs, current_track, current_baro_rate):
        """
        Executes second-order derivative checks. 
        Returns an intent string and raw computed g-forces.
        """
        # If this is the very first packet seen for this aircraft, initialize memory and assume level
        if icao not in self.history:
            self.update_history(icao, current_track, current_baro_rate)
            return "INITIALIZING_TRACK", 0.0, 0.0
            
        # Extract previous states from memory
        prev_track = self.history[icao]["prev_track"]
        prev_baro_rate = self.history[icao]["prev_baro_rate"]
        
        # --- 1. LATERAL MANEUVER MATHEMATICS (Turning Variants) ---
        delta_track = (current_track - prev_track + 180) % 360 - 180
        omega = np.radians(delta_track) / self.dt  # Yaw rate in rad/sec
        gs_mps = current_gs * 0.514444              # Knots to meters/sec
        a_lat_g = (gs_mps * omega) / self.G_METERS_SEC2
        
        # --- 2. VERTICAL PERFORMANCE MATHEMATICS (Pitch/Climb Variants) ---
        vh_mps_curr = current_baro_rate * (self.FT_TO_METERS / 60.0)
        vh_mps_prev = prev_baro_rate * (self.FT_TO_METERS / 60.0)
        a_vert_g = (vh_mps_curr - vh_mps_prev) / (self.dt * self.G_METERS_SEC2)
        
        # --- 3. INTENT CLASSIFICATION TREE ---
        # This structure allows you to scale up to dozens of intents cleanly!
        intent = "MAINTAINING_PROFILE"
        
        if a_lat_g > 0.18:
            intent = "BANKING_RIGHT"
        elif a_lat_g < -0.18:
            intent = "BANKING_LEFT"
            
        # Check for vertical overrides if vertical rate changes dominantly
        if abs(a_vert_g) > abs(a_lat_g * 0.5):
            if a_vert_g > 0.12:
                intent = "AGGRESSIVE_CLIMB"
            elif a_vert_g < -0.12:
                intent = "AGGRESSIVE_DIVE"
                
        # Update memory states for the next second's update cycle
        self.update_history(icao, current_track, current_baro_rate)
        
        return intent, a_lat_g, a_vert_g
