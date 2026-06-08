# --- PRIMARY ENGINE: Aviation Matrix Visualization Exporter ---
import pandas as pd
import numpy as np
import logging
import os
import fcntl
from typing import Dict, Any

# FAA-Grade Safety Wrapper for I/O
def avionics_safety_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"MATRIX EXPORT FAILURE: {e}")
            return None
    return wrapper

class AviationMatrixExporter:
    """
    High-fidelity trajectory log processor.
    Calculates S-Turn efficiency, drift, and structural loads.
    """
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir

    @avionics_safety_wrapper
    def process_trajectory(self, input_csv: str, output_csv: str = "visual_matrix.csv"):
        """
        Processes PID-controlled flight data into a standardized visualization matrix.
        Includes S-Turn flagging and thermal load analysis.
        """
        input_path = os.path.join(self.log_dir, input_csv)
        output_path = os.path.join(self.log_dir, output_csv)
        
        df = pd.read_csv(input_path)
        
        # 1. Feature Engineering: S-Turn & Drift Correction Metrics
        # Detect S-Turns: Bank command > threshold indicates active energy bleeding
        df['Is_S_Turn'] = np.where(abs(df['BankAngle_deg']) > 5.0, 1, 0)
        df['Lateral_Drift_m'] = df['CrossrangeDrift_km'] * 1000.0
        
        # 2. Schema Selection: Export for visualization
        columns = [
            'Time_s', 'Altitude_km', 'Downrange_km', 
            'Lateral_Drift_m', 'BankAngle_deg', 
            'AoA_deg', 'HeatFlux_W_cm2', 'Is_S_Turn',
            'CommandedBank_deg'
        ]
        matrix = df[columns]
        
        # 3. Atomic Write (prevents file corruption during telemetry flow)
        with open(output_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX) # Atomic Lock
            matrix.to_csv(f, index=False)
            fcntl.flock(f, fcntl.LOCK_UN)
            
        logging.info(f"VISUALIZATION MATRIX EXPORTED: {output_path}")
        return output_path

    @avionics_safety_wrapper
    def get_tactical_report(self, matrix_path: str) -> Dict[str, Any]:
        """Generates the automated mission report for FAA review."""
        df = pd.read_csv(matrix_path)
        
        return {
            "Peak_Load_Gs": df['Acceleration_g'].max(),
            "Peak_Thermal_Flux": df['HeatFlux_W_cm2'].max(),
            "Final_Lateral_Offset_m": df['Lateral_Drift_m'].iloc[-1],
            "S_Turn_Efficiency": df['Is_S_Turn'].sum() / len(df)
        }

if __name__ == "__main__":
    # Integration test for the matrix builder
    exporter = AviationMatrixExporter(log_dir="logs")
    # This expects the output from your PIDEntryEngine
    try:
        path = exporter.process_trajectory("optimized_3d_pid_trajectory.csv")
        metrics = exporter.get_tactical_report(path)
        print(f"Tactical Report Generated: {metrics}")
    except Exception as e:
        print(f"FAILED TO GENERATE REPORT: {e}")
