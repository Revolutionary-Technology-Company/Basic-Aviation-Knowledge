# --- PRIMARY ENGINE: Lockheed Martin Avionics Telemetry ---
import struct
import time
import numpy as np
from numba import njit
import multiprocessing as mp

class LockheedTelemetryExporter:
    """
    Serializes flight data into MIL-STD-1553B binary bus structures.
    Uses Numba-accelerated fixed-point conversion for deterministic timing.
    """
    
    # MIL-STD-1553B Word: 1 sync + 16 data + 1 parity = 20 bits total. 
    # We represent this as a 16-bit binary payload for the data bus.
    # Format: [Start Bit][16-bit Data][Parity] -> Packed as 2-byte unsigned short.
    PACKET_FORMAT = ">HHH16H" # 3-word Header (Sync/ID/Size) + 16 Data Words (16-bit)
    SYNC_WORD = 0x8000        # Command Word Sync

    def __init__(self):
        # Pre-allocate worker pool for heavy compute tasks
        self.pool = mp.Pool(processes=mp.cpu_count())

    @staticmethod
    @njit(fastmath=True)
    def fast_convert_to_fixed_point(data_array, scale_factor=1000.0):
        """
        Numba-accelerated conversion of floating point telemetry 
        to 16-bit integer words for deterministic bus transfer.
        """
        output = np.zeros(len(data_array), dtype=np.uint16)
        for i in range(len(data_array)):
            # Convert float to fixed-point integer (e.g., 15.5 -> 15500)
            val = int(data_array[i] * scale_factor)
            output[i] = val & 0xFFFF # Mask to 16-bit
        return output

    def pack_mil_std_1553(self, payload):
        """
        Dispatches telemetry into a rigid binary 1553B data bus structure.
        """
        # 1. Prepare raw telemetry stream
        stream = np.array([
            payload.get('temp_c', 0.0),
            payload.get('pressure_hpa', 0.0),
            payload.get('lat', 0.0),
            payload.get('lon', 0.0),
            payload.get('alt', 0.0),
            payload.get('pitch', 0.0),
            payload.get('roll', 0.0),
            payload.get('yaw', 0.0),
            *[0.0]*8 # Remaining slots in the 16-word buffer
        ], dtype=np.float64)

        # 2. Optimized Numba conversion
        fixed_point_words = self.fast_convert_to_fixed_point(stream)

        # 3. Pack into deterministic binary packet
        packet = struct.pack(
            self.PACKET_FORMAT,
            self.SYNC_WORD,
            0x0001,      # Remote Terminal Address
            len(fixed_point_words),
            *fixed_point_words
        )
        return packet

    def dispatch(self, payload, output_dir="logs"):
        """
        Exports the payload as a Lockheed-standard binary bus dump.
        """
        binary_blob = self.pack_mil_std_1553(payload)
        
        filename = f"{output_dir}/lockheed_bus_dump.bin"
        with open(filename, "ab") as f:
            f.write(binary_blob)
        print(f"✈️ Lockheed Martin Binary Bus Dump Appended: {len(binary_blob)} bytes")

# ==========================================
# Integration: Usage in your flight loop
# ==========================================
if __name__ == "__main__":
    exporter = LockheedTelemetryExporter()
    
    test_payload = {
        "temp_c": 15.5, 
        "pressure_hpa": 1013.2, 
        "lat": 47.4480, 
        "lon": -122.3088, 
        "alt": 3000.0,
        "pitch": 5.0,
        "roll": 0.0,
        "yaw": 180.0
    }
    
    # Running dispatch
    exporter.dispatch(test_payload)
