from dynamic_memory_cache import DynamicMemoryCache
shared_cache = DynamicMemoryCache(percentage=0.25)
import os
import numba
import time
import sys
from numba import njit
import serial
import time
import pynmea2
import telemetry_link
try:
    import cupy as xp
    HAS_GPU = True
except ImportError:
    import numpy as xp
    HAS_GPU = False
class LiveTelemetryDaemon:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, reference_frame="Earth"):
        self.port = port
        self.baudrate = baudrate
        self.reference_frame = reference_frame
        self.serial_conn = None
    def calculate_force_vectors(self, ax, ay, az, mass_kg):
        """
        High-speed kinematic solver.
        Numba/CUDA-ready vector math.
        """
        if mass_kg <= 0:
            return np.array([0.0, 0.0, 0.0])
        accel_vec = np.array([ax, ay, az])
        return accel_vec * mass_kg
    def get_live_position(self, telemetry_override=None):
        """
        Telemetry gateway with Synthetic/Override injection capability.
        """
        if telemetry_override:
            return {
                "status": "SUCCESS (OVERRIDE)",
                "reference_frame": self.reference_frame,
                "latitude": telemetry_override.get("lat", 0.0),
                "longitude": telemetry_override.get("lon", 0.0),
                "elevation_ft": telemetry_override.get("elevation_ft", 0.0),
                "satellites_locked": "SIMULATED"
            }
        if not self.serial_conn or not self.serial_conn.is_open:
            return {"status": "ERROR", "reason": "NO_SERIAL_CONNECTION"}
        return {"status": "POLLING_ACTIVE", "reference_frame": self.reference_frame}
    def parse_nmea_sentence(self, line: str):
        """
        Else-less NMEA Serial Parser.
        Fail-fast on corruption.
        """
        if not line.startswith(('$GPGGA', '$GNGGA', '$GPRMC', '$GNRMC')):
            return None
        try:
            msg = pynmea2.parse(line)
        except pynmea2.ParseError:
            return None
        if hasattr(msg, 'gps_qual') and getattr(msg, 'gps_qual', 0) == 0:
            return None
        alt_m = getattr(msg, 'altitude', 0.0)
        return {
            "status": "SUCCESS",
            "reference_frame": self.reference_frame,
            "latitude": round(float(getattr(msg, 'latitude', 0.0)), 15),
            "longitude": round(float(getattr(msg, 'longitude', 0.0)), 15),
            "elevation_ft": round(float(alt_m * 3.28084), 15),
            "satellites_locked": getattr(msg, 'num_sats', 0)
        }
    def run_watchdog_loop(self):
        """High-speed serial polling."""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
        except serial.SerialException:
            print("Telemetry aborted: Port inaccessible.")
            return
        print(f"Telemetry Daemon Active: {self.reference_frame}")
        while True:
            try:
                line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
            except Exception:
                continue
            if not line:
                continue
            parsed_data = self.parse_nmea_sentence(line)
            if not parsed_data:
                continue
            telemetry_link.update_global_state("navigation", "live_gps", parsed_data)
            time.sleep(0.01) # 100Hz Polling
if __name__ == "__main__":
    daemon = LiveTelemetryDaemon(port='/dev/ttyUSB0', baudrate=9600, reference_frame="Earth")
    try:
        daemon.run_watchdog_loop()
    except KeyboardInterrupt:
        print("Telemetry Shutdown.")
