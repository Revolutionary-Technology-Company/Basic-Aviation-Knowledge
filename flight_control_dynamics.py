import numpy as np
from waypoint_manager import WaypointManager

class FlightControlDynamics:
    def __init__(self, mode="CIVILIAN"):
        self.mode = mode
        self.dynamic = True
        self.bank_limit = 30.0 if mode == "CIVILIAN" else 60.0
        self.wp_manager = WaypointManager() # Now the engine manages its own navigation data

    def get_dynamics_for_active_waypoint(self, current_heading, current_alt, ground_speed):
        """
        Fetches the current active waypoint and calculates the required attitude.
        """
        active_wp = self.wp_manager.get_active_waypoint(index=0)
        
        if not active_wp:
            return None # No waypoint registered, no correction possible

        return self.calculate_required_attitude(
            current_heading, 
            active_wp.target_heading, 
            active_wp.alt, 
            current_alt, 
            ground_speed
        )

    def calculate_required_attitude(self, current_heading, target_heading, target_elevation, current_alt, ground_speed):
        # 1. Roll Calculation (Bank angle for turn)
        heading_diff = target_heading - current_heading
        # Normalize heading difference to -180 to 180
        heading_diff = (heading_diff + 180) % 360 - 180
        roll_angle = np.clip(heading_diff * 0.5, -self.bank_limit, self.bank_limit)
        
        # 2. Attitude (Pitch) for Elevation Change
        alt_diff = target_elevation - current_alt
        # Simplified pitch gradient (e.g., 3-degree slope is ~5.2% gradient)
        pitch_angle = np.clip(alt_diff * 0.05, -15, 15)
        
        # 3. Rudder (Coordination)
        rudder = roll_angle * 0.1
        
        return {"roll": roll_angle, "rudder": rudder, "pitch": pitch_angle}

    def set_mode(self, dynamic_on=True, mode="CIVILIAN"):
        self.dynamic = dynamic_on
        self.bank_limit = 30.0 if mode == "CIVILIAN" else 60.0
