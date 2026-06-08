# --- PRIMARY ENGINE: Multi-Domain Waypoint Manager ---
# Supports: Terrestrial GPS, Universal Extraterrestrial GPS, and Kinematic Space Routing
import os
import json
import math
import pandas as pd
from numba import njit
from astropy.coordinates import EarthLocation, GCRS
from astropy.time import Time, TimeDelta
import astropy.units as u

try:
    import cupy as np
except ImportError:
    import numpy as np

# =====================================================================
# MULTI-DOMAIN WAYPOINT MANAGER
# =====================================================================
class WaypointManager:
    def __init__(self, config_path="config.json", dso_catalog_path="dso_processed_metrics.csv"):
        self.config_path = config_path
        self.config_data = {}
        self.waypoints = []
        self.dso_catalog_path = dso_catalog_path
        self.dso_database = None
        self.active_space_target = None
        self.space_mode_enabled = False 
        
        self.load_config()
        self.load_waypoints()
        self._load_space_catalog()

    # --- SAFETY INTERLOCKS ---
    def set_space_routing_mode(self, state: bool):
        self.space_mode_enabled = state
        print(f"⚠️ AVIONICS OVERRIDE: Deep Space Routing {'ENGAGED' if state else 'DISABLED'}.")

    # --- TERRESTRIAL ROUTING ---
    def register_waypoint(self, name, lat, lon, alt, heading):
        self.waypoints.append({"name": name, "lat": lat, "lon": lon, "alt": alt, "heading": heading})
        self.save_waypoints()

    def save_waypoints(self):
        self.config_data["waypoints"] = self.waypoints
        with open(self.config_path, "w") as f:
            json.dump(self.config_data, f, indent=4)

    def load_waypoints(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config_data = json.load(f)
                self.waypoints = self.config_data.get("waypoints", [])

    # --- UNIVERSAL SPACE ROUTING ---
    def _load_space_catalog(self):
        if os.path.exists(self.dso_catalog_path):
            self.dso_database = pd.read_csv(self.dso_catalog_path)
            # Ensure Earth is always a default target
            if not (self.dso_database['Name'] == 'EARTH').any():
                earth_row = pd.DataFrame([{"ID": 0, "Name": "EARTH", "Estimated_Mass_Solar": 0.000003, "Radius_M": 6371000, "Rotation_Period_S": 86400}])
                self.dso_database = pd.concat([earth_row, self.dso_database], ignore_index=True)

    def lock_space_target(self, identifier, lat=None, lon=None):
        """GPS coordinates are MANDATORY for all space objects (except Earth)."""
        if not self.space_mode_enabled:
            return False, "ROUTING REJECTED: Space Routing Mode is DISABLED."

        if identifier.upper() != "EARTH" and (lat is None or lon is None):
            return False, f"GPS COORDINATES REQUIRED: Target '{identifier}' requires lat/lon for surface intercept."

        target_row = self.dso_database[
            (self.dso_database['ID'].astype(str) == str(identifier)) | 
            (self.dso_database['Name'].astype(str).str.contains(str(identifier), case=False, na=False))
        ]
        
        if target_row.empty: return False, "Target not found."
        
        target_data = target_row.iloc[0]
        self.active_space_target = {
            "name": target_data['Name'],
            "radius": target_data.get('Radius_M', 6371000),
            "rot_period": target_data.get('Rotation_Period_S', 86400),
            "lat": lat if identifier.upper() != "EARTH" else 0.0,
            "lon": lon if identifier.upper() != "EARTH" else 0.0,
            "position_vec": np.array([0.0, 0.0, 0.0]) if identifier.upper() == "EARTH" else np.array([1.5e11, 0.0, 0.0]),
            "velocity_vec": np.array([0.0, 0.0, 0.0]) if identifier.upper() == "EARTH" else np.array([25000.0, -5000.0, 1200.0])
        }
        return True, self.active_space_target

    def calculate_universal_intercept(self, ship_pos, ship_vel, target_alt_m=0):
        """Calculates 3D intercept to ANY GPS coordinate on ANY planet."""
        if not self.active_space_target: return None
        
        # 1. Physics: Vector to Target
        target_body_pos = self.active_space_target["position_vec"]
        closing_vel = np.linalg.norm(ship_vel)
        dist_to_core = np.linalg.norm(target_body_pos - np.array(ship_pos))
        
        # 2. Rotation Correction (The "Future Landing Pad" Calculation)
        tti = (dist_to_core - self.active_space_target["radius"]) / closing_vel
        rot_angle = ((2 * math.pi) / self.active_space_target["rot_period"]) * tti
        
        # 3. GPS -> Cartesian Conversion
        lat_r, lon_r = math.radians(self.active_space_target["lat"]), math.radians(self.active_space_target["lon"])
        r = self.active_space_target["radius"] + target_alt_m
        
        local_vec = np.array([
            r * math.cos(lat_r) * math.cos(lon_r),
            r * math.cos(lat_r) * math.sin(lon_r),
            r * math.sin(lat_r)
        ])
        
        # Apply Rotation Matrix
        rot_mat = np.array([[math.cos(rot_angle), -math.sin(rot_angle), 0], [math.sin(rot_angle), math.cos(rot_angle), 0], [0, 0, 1]])
        final_wpt = target_body_pos + np.dot(rot_mat, local_vec)
        
        return {"heading": (final_wpt - np.array(ship_pos)) / np.linalg.norm(final_wpt - np.array(ship_pos)), "tti": tti}

# =====================================================================
# SUMMARY
# =====================================================================
