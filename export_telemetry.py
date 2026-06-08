# --- PRIMARY ENGINE: Multi-Protocol Telemetry Dispatcher ---
import os
import json
import time
import struct
import h5py
import numpy as np
from numba import njit

# Protocol Exporters
from nasa_telemetry_exporter import NASATelemetryExporter
from lockheed_telemetry_exporter import LockheedTelemetryExporter
from axiom_telemetry_exporter import AxiomTelemetryExporter

class TelemetryDispatcher:
    def __init__(self, output_dir="logs"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        
        # Initialize specialized stream engines
        self.nasa = NASATelemetryExporter()
        self.lockheed = LockheedTelemetryExporter()
        self.axiom = AxiomTelemetryExporter()

    def dispatch(self, payload):
        """
        Dispatches telemetry to all active aerospace standards.
        """
        # 1. Boeing Standard (Ground Monitoring)
        with open(f"{self.output_dir}/telemetry_{int(time.time())}.json", "w") as f:
            json.dump(payload, f, indent=4)
            
        # 2. NASA Standards (Archival & Deep Space Interop)
        self.nasa.dispatch(payload, self.output_dir)
        
        # 3. Lockheed Martin Standards (1553B Avionics Bus)
        self.lockheed.dispatch(payload, self.output_dir)
        
        # 4. Axiom Space Standards (Hybrid ISS Docking + ODC Edge)
        self.axiom.dispatch(payload, self.output_dir)
        
        print(f"🚀 Global Telemetry Dispatched: [Boeing] [NASA] [Lockheed] [Axiom]")

# ==========================================
# TEST HOOK
# ==========================================
if __name__ == "__main__":
    dispatcher = TelemetryDispatcher()
    test_payload = {
        "temp_c": 15.5, "pressure_hpa": 1013.2, 
        "lat": 47.4480, "lon": -122.3088, "alt": 3000.0,
        "pitch": 5.0, "roll": 0.0, "yaw": 180.0,
        "grid_data": np.random.rand(10, 10)
    }
    dispatcher.dispatch(test_payload)
