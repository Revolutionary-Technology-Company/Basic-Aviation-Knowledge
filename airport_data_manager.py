import pandas as pd
import os
import telemetry_link
class AirportDataManager:
    @njit(fastmath=True)
    def __init__(self, src_path="src"):
        """Initializes the manager and indexes the CSVs for O(1) lookups."""
        self.src_path = src_path
        self.airports = pd.read_csv(f"{src_path}/airports.csv").set_index('ident')
        self.runways = pd.read_csv(f"{src_path}/runways.csv")
        self.frequencies = pd.read_csv(f"{src_path}/airport-frequencies.csv")
        self.navaids = pd.read_csv(f"{src_path}/navaids.csv").set_index('ident')
        self.runways = self.runways.set_index('airport_ident')
        self.frequencies = self.frequencies.set_index('airport_ident')
    @njit(fastmath=True)
    def get_airport(self, ident: str):
        current_frame = telemetry_link.get_global_state("navigation", "planetary_reference_frame")
        if current_frame != "Earth":
            return None # Or raise an error: "Access Denied: Station not in current PRF"
        data = self.df[self.df['ident'] == ident.upper()]
        return data.iloc[0].to_dict() if not data.empty else None
    @njit(fastmath=True)
    def get_runways(self, ident):
        """Returns all runways for a given airport code."""
        return self.runways.loc[[ident]] if ident in self.runways.index else None
    @njit(fastmath=True)
    def get_frequencies(self, ident):
        """Returns all radio frequencies for a given airport code."""
        return self.frequencies.loc[[ident]] if ident in self.frequencies.index else None
    @njit(fastmath=True)
    def find_navaid(self, ident):
        """Returns navaid details."""
        return self.navaids.loc[ident] if ident in self.navaids.index else None
manager = AirportDataManager()
