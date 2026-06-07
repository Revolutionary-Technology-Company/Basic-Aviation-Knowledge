import numpy as np

class FlightControlDynamics:
    def __init__(self, mode="CIVILIAN"):
        self.mode = mode # "CIVILIAN" or "SPORT"
        self.bank_limit = 30.0 if mode == "CIVILIAN" else 60.0 # Sport mode limit
        
    def calculate_required_attitude(self, current_heading, target_heading, target_elevation, current_alt, ground_speed):
        """
        Calculates Roll, Rudder, and Attitude for a specific waypoint.
        """
        # 1. Roll Calculation (Bank angle for turn)
        heading_diff = target_heading - current_heading
        roll_angle = np.clip(heading_diff * 0.5, -self.bank_limit, self.bank_limit)
        
        # 2. Attitude (Pitch) for Elevation Change (using 3:1 descent or climb gradient)
        alt_diff = target_elevation - current_alt
        pitch_angle = np.clip(alt_diff * 0.05, -15, 15) # Simplified pitch gradient
        
        # 3. Rudder (Coordination)
        rudder = roll_angle * 0.1 # Simplified slip/skid coordination
        
        return {"roll": roll_angle, "rudder": rudder, "pitch": pitch_angle}

    def set_mode(self, dynamic_on=True, mode="CIVILIAN"):
        self.dynamic = dynamic_on
        self.bank_limit = 30.0 if mode == "CIVILIAN" else 60.0
