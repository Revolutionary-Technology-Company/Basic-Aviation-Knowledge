# --- PRIMARY ENGINE: Multi-Domain Waypoint Manager ---
import os
import json
import math
import pandas as pd
from numba import njit

# Astropy for high-precision frame transformations and Earth rotation
from astropy.coordinates import EarthLocation, GCRS
from astropy.time import Time, TimeDelta
import astropy.units as u

try:
    import cupy as np  # Attempt to use GPU-accelerated array math
    print("🚀 NVIDIA GPU Acceleration Engaged (Waypoint Manager)")
except ImportError:
    import numpy as np # Fallback to standard CPU math
    print("⚡ Using CPU (NVIDIA acceleration not detected)")


# =====================================================================
# TERRESTRIAL AVIATION CLASSES
# =====================================================================
class Waypoint:
    """Standard Atmospheric/Terrestrial Waypoint"""
    def __init__(self, name, lat, lon, alt, target_heading, turn_radius=0.5):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.target_heading = target_heading
        self.turn_radius = turn_radius # NM radius to start the smooth turn

    def to_dict(self):
        return self.__dict__


# =====================================================================
# MULTI-DOMAIN WAYPOINT MANAGER
# =====================================================================
class WaypointManager:
    def __init__(self, config_path="config.json", dso_catalog_path="dso_processed_metrics.csv"):
        # 1. Terrestrial Avionics State
        self.config_path = config_path
        self.config_data = {}
        self.waypoints = []
        
        # 2. Space/Kinematic State
        self.dso_catalog_path = dso_catalog_path
        self.dso_database = None
        self.active_space_target = None
        
        # 3. SAFETY INTERLOCK: Defaults to False to prevent atmospheric jets 
        # from accidentally routing to deep space targets.
        self.space_mode_enabled = False 
        
        # Initialize Boot Sequence
        self.load_config()
        self.load_waypoints()
        self._load_space_catalog()

    # --- INITIALIZATION & SAFETY TOGGLES ---
    def load_config(self):
        """Loads the master configuration file to access sensor registries."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config_data = json.load(f)
                
            # Check if space mode was persisted in avionics state
            avionics = self.config_data.get("avionics_state", {})
            self.space_mode_enabled = avionics.get("space_routing_mode_enabled", False)

    def set_space_routing_mode(self, state: bool):
        """
        Manually enables or disables the deep space routing computer.
        Must be True to engage kinematic intercept protocols.
        """
        self.space_mode_enabled = state
        mode_str = "ENGAGED" if state else "DISABLED"
        print(f"\n⚠️ AVIONICS OVERRIDE: Deep Space Routing is now {mode_str}.")
        
        # Clear active space targets if disabled mid-flight
        if not state and self.active_space_target:
            print(f"Aborting space intercept. Dropping lock on: {self.active_space_target['name']}")
            self.active_space_target = None

    # --- TERRESTRIAL ROUTING (Atmospheric) ---
    def register_waypoint(self, name, lat, lon, alt, heading):
        new_wp = Waypoint(name, lat, lon, alt, heading)
        self.waypoints.append(new_wp)
        self.save_waypoints()
        print(f"✅ Registered Terrestrial Waypoint: {name}")

    def save_waypoints(self):
        """Persists terrestrial waypoints to config.json"""
        self.config_data["waypoints"] = [wp.to_dict() for wp in self.waypoints]
        with open(self.config_path, "w") as f:
            json.dump(self.config_data, f, indent=4)

    def load_waypoints(self):
        """Loads terrestrial waypoints from config.json"""
        self.waypoints = [Waypoint(**wp) for wp in self.config_data.get("waypoints", [])]

    def get_active_waypoint(self, index=0):
        if index < len(self.waypoints):
            return self.waypoints[index]
        return None

    # --- SPACE ROUTING (Kinematic Intercept) ---
    def _load_space_catalog(self):
        """Loads the pre-calculated thermodynamic and mass catalog."""
        if os.path.exists(self.dso_catalog_path):
            self.dso_database = pd.read_csv(self.dso_catalog_path)
            print(f"🛰️ Space Nav Computer online with {len(self.dso_database)} physical targets.")
            
            # Ensure Earth is always available in the local memory for return trips
            if not (self.dso_database['Name'] == 'EARTH').any():
                earth_row = pd.DataFrame([{
                    "ID": 0, "Name": "EARTH", "Estimated_Mass_Solar": 0.000003, 
                    "Surface_Temp_Kelvin": 288, "Light_Output_Lumens": 0, "Heat_Output_Watts": 0
                }])
                self.dso_database = pd.concat([earth_row, self.dso_database], ignore_index=True)
        else:
            print("⚠️ Space Nav Catalog offline. Awaiting pipeline update.")

    def lock_space_target(self, identifier):
        """
        Locks onto a specific deep sky object by ID or Name. 
        Will reject the command if space_mode_enabled is False.
        """
        if not self.space_mode_enabled:
            return False, "ROUTING REJECTED: Space Routing Mode is DISABLED. Enable override to target celestial bodies."

        if self.dso_database is None or self.dso_database.empty:
            return False, "Space catalog offline."

        try:
            target_row = self.dso_database[
                (self.dso_database['ID'].astype(str) == str(identifier)) | 
                (self.dso_database['Name'].astype(str).str.contains(str(identifier), case=False, na=False))
            ]
            
            if target_row.empty:
                return False, f"Target {identifier} not found in physics matrix."
                
            target_data = target_row.iloc[0]
            
            self.active_space_target = {
                "id": target_data['ID'],
                "name": target_data.get('Name', f"DSO-{target_data['ID']}"),
                "mass_solar": target_data.get('Estimated_Mass_Solar', 0.0),
                "heat_kelvin": target_data.get('Surface_Temp_Kelvin', 0.0),
                # If target is Earth, lock to center (0,0,0) as origin. Otherwise, simulate drift.
                "position_vec": np.array([0.0, 0.0, 0.0]) if target_data.get('Name') == 'EARTH' else np.array([1.5e11, 0.0, 0.0]), 
                "velocity_vec": np.array([0.0, 0.0, 0.0]) if target_data.get('Name') == 'EARTH' else np.array([25000.0, -5000.0, 1200.0])
            }
            
            print(f"🎯 SPACE TARGET LOCKED: {self.active_space_target['name']}")
            return True, self.active_space_target
            
        except Exception as e:
            return False, f"Locking error: {str(e)}"

    def get_departure_state(self, current_lat, current_alt_m, current_heading, current_speed_m_s):
        """
        Maps terrestrial GPS speed/location to Earth's absolute space velocity 
        to calculate the initial escape vector.
        """
        EARTH_ORBITAL_VELOCITY = np.array([30000.0, 0.0, 0.0]) # Simplified base vector
        absolute_ship_velocity = EARTH_ORBITAL_VELOCITY + current_speed_m_s
        return absolute_ship_velocity

    def calculate_space_interception_route(self, ship_position_m, ship_velocity_m_s):
        """
        Calculates the kinematic intercept vectors to the moving target.
        Returns the required heading vector, closing speed, and Time To Intercept (TTI).
        """
        if not self.space_mode_enabled:
            return None, "Space mode disabled."
            
        if not self.active_space_target:
            return None, "No active space target locked."

        p_ship = np.array(ship_position_m)
        v_ship = np.array(ship_velocity_m_s)
        
        p_target = self.active_space_target["position_vec"]
        v_target = self.active_space_target["velocity_vec"]

        # 1. Relative Distance Vector
        r_rel_vec = p_target - p_ship
        distance_meters = np.linalg.norm(r_rel_vec)
        
        if distance_meters == 0:
            return {"status": "ARRIVED", "distance_m": 0, "tti_seconds": 0}

        heading_unit_vec = r_rel_vec / distance_meters

        # 2. Closing Velocity
        v_rel_vec = v_ship - v_target
        closing_velocity = np.dot(v_rel_vec, heading_unit_vec)

        # 3. Time to Intercept (TTI)
        tti_seconds = float('inf')
        if closing_velocity > 0:
            tti_seconds = distance_meters / closing_velocity

        return {
            "target_name": self.active_space_target['name'],
            "distance_meters": float(distance_meters),
            "required_heading_vector": heading_unit_vec.tolist(),
            "closing_velocity_m_s": float(closing_velocity),
            "time_to_intercept_sec": float(tti_seconds),
            "target_outrunning": bool(closing_velocity <= 0)
        }

    def step_space_simulation(self, dt_seconds):
        """Advances the target's position in space based on its velocity and dt."""
        if self.space_mode_enabled and self.active_space_target:
            displacement = self.active_space_target["velocity_vec"] * dt_seconds
            self.active_space_target["position_vec"] += displacement

    # --- DEPARTURE & RE-ENTRY SEQUENCE (The Atmospheric Handshakes) ---
    def calculate_departure_vector(self, ship_position_m, current_velocity_m_s):
        """
        Calculates the escape burn required to leave Earth's gravity well 
        and transition to deep space kinematic routing.
        """
        if not self.space_mode_enabled:
            return None, "Space mode disabled. Cannot calculate escape vectors."

        if not self.active_space_target:
            return None, "No active deep space target locked for departure."

        EARTH_RADIUS_M = 6371000.0
        ATMOSPHERE_BOUNDARY_M = 100000.0 # 100km Karman Line
        
        # Calculate distance from Earth's center of mass
        r_from_core = np.linalg.norm(ship_position_m)
        altitude_m = r_from_core - EARTH_RADIUS_M

        # 1. Phase One: Atmospheric Climb
        if altitude_m < ATMOSPHERE_BOUNDARY_M:
            return {
                "status": "ATMOSPHERIC CLIMB",
                "altitude_m": float(altitude_m),
                "cleared_for_space_nav": False,
                "message": f"Maintain terrestrial climb. {(ATMOSPHERE_BOUNDARY_M - altitude_m):.0f} meters to Karman Line."
            }

        # 2. Phase Two: The Escape Burn
        # Calculate standard escape velocity: v_e = sqrt((2 * G * M) / r)
        G = 6.67430e-11
        M_EARTH = 5.972e24
        
        escape_velocity = math.sqrt((2 * G * M_EARTH) / r_from_core)
        current_speed = np.linalg.norm(current_velocity_m_s)

        # 3. Phase Three: Deep Space Handoff
        if current_speed >= escape_velocity:
            target_vec = self.active_space_target["position_vec"] - np.array(ship_position_m)
            target_distance = np.linalg.norm(target_vec)
            heading_unit_vec = target_vec / target_distance
            
            return {
                "status": "ESCAPE VELOCITY ACHIEVED - SPACE NAV ACTIVE",
                "altitude_m": float(altitude_m),
                "cleared_for_space_nav": True,
                "escape_velocity_threshold_m_s": float(escape_velocity),
                "current_speed_m_s": float(current_speed),
                "deep_space_aiming_vector": heading_unit_vec.tolist()
            }
        else:
            return {
                "status": "SUB-ORBITAL - ACCELERATE FOR ESCAPE",
                "altitude_m": float(altitude_m),
                "cleared_for_space_nav": False,
                "escape_velocity_threshold_m_s": float(escape_velocity),
                "current_speed_m_s": float(current_speed),
                "delta_v_required_m_s": float(escape_velocity - current_speed)
            }


    def calculate_reentry_vector(self, ship_position_m, closing_velocity_m_s, target_airport_icao):
        """
        Calculates the exact 3D space vector required to intercept a specific 
        airport on Earth, accounting for planetary rotation during the approach.
        """
        airport_data = self.config_data.get("nws_sensor_registry", {}).get(target_airport_icao)
        if not airport_data:
            return None, f"Airport {target_airport_icao} not found in registry."

        lat = airport_data["latitude"]
        lon = airport_data["longitude"]
        alt_m = airport_data["elevation_ft"] * 0.3048 # Convert ft to meters

        EARTH_RADIUS_M = 6371000.0
        ATMOSPHERE_BOUNDARY_M = 100000.0 # 100km Karman Line
        
        distance_to_core = np.linalg.norm(ship_position_m)
        distance_to_atmo = distance_to_core - (EARTH_RADIUS_M + ATMOSPHERE_BOUNDARY_M)

        if distance_to_atmo <= 0:
            return None, "Ship is already inside the atmosphere. Switch to Terrestrial Waypoints."

        if closing_velocity_m_s <= 0:
            return None, "Ship is moving away from Earth. Cannot calculate re-entry."

        # Project Time Forward based on closing velocity
        tti_seconds = distance_to_atmo / closing_velocity_m_s
        current_time = Time.now()
        arrival_time = current_time + TimeDelta(tti_seconds, format='sec')

        # Map Airport to Earth Ellipsoid
        airport_loc = EarthLocation.from_geodetic(
            lat=lat * u.deg, 
            lon=lon * u.deg, 
            height=alt_m * u.m
        )

        # Transform Airport to Deep Space Vector (GCRS) at EXACT time of arrival
        projected_space_vector = airport_loc.get_gcrs(obstime=arrival_time)
        
        target_x = projected_space_vector.cartesian.x.to(u.m).value
        target_y = projected_space_vector.cartesian.y.to(u.m).value
        target_z = projected_space_vector.cartesian.z.to(u.m).value
        
        projected_target_array = np.array([target_x, target_y, target_z])

        # Calculate the new Route Vector
        route_vector = projected_target_array - np.array(ship_position_m)
        distance_to_runway = np.linalg.norm(route_vector)
        required_heading_unit_vec = route_vector / distance_to_runway

        return {
            "status": "RE-ENTRY VECTOR LOCKED",
            "airport": target_airport_icao,
            "tti_seconds": float(tti_seconds),
            "projected_arrival_utc": arrival_time.iso,
            "earth_rotation_offset_applied": True,
            "reentry_aiming_vector": required_heading_unit_vec.tolist(),
            "distance_to_runway_m": float(distance_to_runway)
        }


# =====================================================================
# EXECUTION BLOCK (Demonstrating the full lifecycle)
# =====================================================================
if __name__ == "__main__":
    nav = WaypointManager()
    
    print("\n=======================================================")
    print("              AEROSPACE ROUTING LIFECYCLE              ")
    print("=======================================================")

    print("\n[PHASE 1] Pre-Flight & Terrestrial Climb")
    nav.register_waypoint("KSEA_CLIMB_OUT", 47.4480, -122.3088, 120000, 180) # 120km straight up
    active_wp = nav.get_active_waypoint(0)
    print(f"Flying Terrestrial Waypoint: {active_wp.name} to {active_wp.alt}m altitude.")
    
    print("\n[PHASE 2] Space Nav Override & Departure Handshake")
    nav.set_space_routing_mode(True)
    success, msg = nav.lock_space_target("Andromeda")
    if success:
        # Simulate breaking the Karman line but still needing escape velocity
        # Distance from core: Earth Radius (6371km) + 120km altitude
        ship_pos_launch = [6491000.0, 0, 0] 
        ship_vel_launch = [7000.0, 0, 0] # Fast, but not quite escape velocity yet
        
        departure = nav.calculate_departure_vector(ship_pos_launch, ship_vel_launch)
        if departure:
            print(f"Status: {departure['status']}")
            if not departure['cleared_for_space_nav']:
                print(f"Delta-V Required: {departure['delta_v_required_m_s']:.2f} m/s")

    print("\n[PHASE 3] Returning Home - The Atmospheric Handshake")
    success, msg = nav.lock_space_target("EARTH")
    if success:
        # Ship is 1,000,000 km away, moving towards Earth at 50,000 m/s
        ship_pos_return = [1e9, 0, 0] 
        ship_vel_return = [-50000.0, 0, 0] 
        
        # Space transit
        route = nav.calculate_space_interception_route(ship_pos_return, ship_vel_return)
        print(f"Deep Space Intercept TTI: {route['time_to_intercept_sec']:.2f} s")

        # Handshake sequence to runway
        reentry = nav.calculate_reentry_vector(ship_pos_return, route['closing_velocity_m_s'], "SEA")
        if reentry:
            print(f"Status: {reentry['status']} -> Airport: {reentry['airport']}")
            print(f"Earth Rotation Projected Arrival: {reentry['projected_arrival_utc']}")
