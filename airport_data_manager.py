# airport_data_manager.py
import pandas as pd
import os
import telemetry_link

class AirportDataManager:
    def __init__(self, src_path="src"):
        """Initializes the manager and indexes the CSVs for O(1) lookups."""
        self.src_path = src_path
        
        # Load datasets
        self.airports = pd.read_csv(f"{src_path}/airports.csv").set_index('ident')
        self.runways = pd.read_csv(f"{src_path}/runways.csv")
        self.frequencies = pd.read_csv(f"{src_path}/airport-frequencies.csv")
        self.navaids = pd.read_csv(f"{src_path}/navaids.csv").set_index('ident')
        
        # Optimize Runway/Frequency lookup by mapping airport_ident
        self.runways = self.runways.set_index('airport_ident')
        self.frequencies = self.frequencies.set_index('airport_ident')

    def get_airport(self, ident: str):
        # --- NEW: REFERENCE FRAME LOCK ---
        current_frame = telemetry_link.get_global_state("navigation", "planetary_reference_frame")
        
        # If the frame is NOT Earth, Earth airports are inaccessible
        if current_frame != "Earth":
            return None # Or raise an error: "Access Denied: Station not in current PRF"
            
        # Standard lookup
        data = self.df[self.df['ident'] == ident.upper()]
        return data.iloc[0].to_dict() if not data.empty else None

    def get_runways(self, ident):
        """Returns all runways for a given airport code."""
        return self.runways.loc[[ident]] if ident in self.runways.index else None

    def get_frequencies(self, ident):
        """Returns all radio frequencies for a given airport code."""
        return self.frequencies.loc[[ident]] if ident in self.frequencies.index else None

    def find_navaid(self, ident):
        """Returns navaid details."""
        return self.navaids.loc[ident] if ident in self.navaids.index else None

# Singleton instance for easy import
manager = AirportDataManager()
