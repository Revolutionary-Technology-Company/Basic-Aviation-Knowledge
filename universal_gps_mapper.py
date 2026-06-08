import math
try:
    import cupy as np
except ImportError:
    import numpy as np

class UniversalGPSMapper:
    """
    Expands the Waypoint Manager to allow GPS (Lat/Lon/Alt) targeting 
    on ANY celestial body, accounting for local planetary rotation and radius.
    """
    
    @staticmethod
    def calculate_extraterrestrial_intercept(
        ship_position_m, 
        closing_velocity_m_s, 
        target_body_pos_vec, 
        target_body_radius_m, 
        target_rotation_period_seconds,
        target_lat_deg, 
        target_lon_deg, 
        target_alt_m
    ):
        """
        Calculates the exact deep-space intercept vector to a specific 
        Latitude/Longitude on the surface of a moving, rotating celestial body.
        """
        if closing_velocity_m_s <= 0:
            return None, "Ship is not closing on target. Cannot calculate WPT intercept."

        # 1. Calculate Distance to the Planet's Core and Time to Intercept (TTI)
        # We subtract the planet's radius to find the time until we hit the atmosphere/surface layer
        distance_to_core = np.linalg.norm(target_body_pos_vec - np.array(ship_position_m))
        distance_to_surface = distance_to_core - target_body_radius_m
        
        if distance_to_surface <= 0:
            return None, "Ship is already within the planetary boundary. Switch to Local Terrestrial Flight."
            
        tti_seconds = distance_to_surface / closing_velocity_m_s

        # 2. Convert Extraterrestrial Lat/Lon to Local Cartesian Vector (Relative to Planet Core)
        lat_rad = math.radians(target_lat_deg)
        lon_rad = math.radians(target_lon_deg)
        total_radius = target_body_radius_m + target_alt_m

        local_x = total_radius * math.cos(lat_rad) * math.cos(lon_rad)
        local_y = total_radius * math.cos(lat_rad) * math.sin(lon_rad)
        local_z = total_radius * math.sin(lat_rad)
        
        local_target_vec = np.array([local_x, local_y, local_z])

        # 3. Apply Planetary Rotation over TTI
        # Calculate how far the planet spins while the ship is en route
        if target_rotation_period_seconds > 0:
            rotation_rate_rad_per_sec = (2 * math.pi) / target_rotation_period_seconds
            rotation_angle = rotation_rate_rad_per_sec * tti_seconds
            
            # Z-Axis Rotation Matrix (Assuming standard polar alignment for baseline engine)
            cos_theta = math.cos(rotation_angle)
            sin_theta = math.sin(rotation_angle)
            
            rotation_matrix = np.array([
                [cos_theta, -sin_theta, 0],
                [sin_theta,  cos_theta, 0],
                [0,          0,         1]
            ])
            
            # Rotate the local landing zone to its future position
            future_local_target_vec = np.dot(rotation_matrix, local_target_vec)
        else:
            # Tidally locked or non-rotating body
            future_local_target_vec = local_target_vec

        # 4. Superposition: Global Space Coordinate
        # Add the planet's absolute position in space to the local landing zone vector
        absolute_waypoint_vec = target_body_pos_vec + future_local_target_vec

        # 5. Final Routing Vector
        route_vector = absolute_waypoint_vec - np.array(ship_position_m)
        distance_to_waypoint = np.linalg.norm(route_vector)
        required_heading_unit_vec = route_vector / distance_to_waypoint

        return {
            "status": "UNIVERSAL GPS WPT LOCKED",
            "target_local_coords": f"{target_lat_deg}°, {target_lon_deg}° | Alt: {target_alt_m}m",
            "tti_seconds": float(tti_seconds),
            "planetary_rotation_offset_rads": float(rotation_angle) if target_rotation_period_seconds > 0 else 0.0,
            "aiming_vector": required_heading_unit_vec.tolist(),
            "distance_to_surface_wpt_m": float(distance_to_waypoint)
        }

# ==========================================
# Execution Example: Mars Landing Handshake
# ==========================================
if __name__ == "__main__":
    mapper = UniversalGPSMapper()
    
    print("\n--- Initiating Extraterrestrial GPS Handshake (Target: MARS) ---")
    
    # Target: Olympus Mons Base, Mars
    mars_radius_m = 3389500.0
    mars_day_seconds = 88775.0 # ~24h 39m
    
    # Spacecraft is 5,000,000 km away, moving at 25,000 m/s
    ship_pos = [0, 0, 0]
    mars_pos = [5e9, 0, 0] 
    closing_speed = 25000.0
    
    # Olympus Mons GPS Coordinates
    target_lat = 18.65
    target_lon = 226.2
    target_alt = 21000.0 # 21km elevation
    
    route = mapper.calculate_extraterrestrial_intercept(
        ship_position_m=ship_pos,
        closing_velocity_m_s=closing_speed,
        target_body_pos_vec=np.array(mars_pos),
        target_body_radius_m=mars_radius_m,
        target_rotation_period_seconds=mars_day_seconds,
        target_lat_deg=target_lat,
        target_lon_deg=target_lon,
        target_alt_m=target_alt
    )
    
    print(f"Status: {route['status']}")
    print(f"Landing Zone: {route['target_local_coords']}")
    print(f"Time to Intercept: {route['tti_seconds']:.2f} seconds")
    print(f"Mars Rotation Lead Angle Applied: {math.degrees(route['planetary_rotation_offset_rads']):.2f} degrees")
    print(f"Kinematic Heading Vector: {np.round(route['aiming_vector'], 4)}")
