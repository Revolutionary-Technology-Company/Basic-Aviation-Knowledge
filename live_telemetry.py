# live_telemetry.py
# Interfaces with USB DGPS/RTK and Barometric Elevation Dongles

import serial
import pynmea2

def get_live_position(com_port="COM3", baudrate=9600):
    """
    Connects to the USB DGPS dongle and reads the latest GPGGA sentence 
    to extract live coordinates and elevation.
    """
    try:
        # Open the serial connection to the USB dongle
        with serial.Serial(com_port, baudrate, timeout=1) as ser:
            # Read lines until we find the 3D location sentence (GGA)
            for _ in range(20): 
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                    msg = pynmea2.parse(line)
                    
                    # Convert meters to feet for US Aviation standards
                    elevation_ft = msg.altitude * 3.28084 if msg.altitude else 0.0
                    
                    return {
                        "status": "SUCCESS",
                        "latitude": msg.latitude,
                        "longitude": msg.longitude,
                        "elevation_ft": round(elevation_ft, 2),
                        "satellites_locked": msg.num_sats
                    }
                    
        return {"status": "ERROR", "message": "No GPS fix available from dongle."}
        
    except serial.SerialException:
        return {"status": "ERROR", "message": f"Could not connect to dongle on {com_port}."}
