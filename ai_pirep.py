import sensor_thermodynamics
import aviation_telemetry
import aircraft_perf
import aviation_physics
from dynamic_memory_cache import DynamicMemoryCache
    shared_cache = DynamicMemoryCache(percentage=0.1)import multiprocessing as mp
try:
    import cupy as np
    print("NVIDIA GPU Acceleration Engaged")
except ImportError:
    import numpy as np
import pyttsx3 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import aerodynamic_matrix
import streamlit as st
from numba import njit
@njit(fastmath=True)
def generate_pirep_data(live_data, user_inputs):
    """
    Assembles the standard PIREP string and the spoken radio script.
    """
    pirep_string = (
        f"UA /OV {live_data.get('latitude', 'UNK')}/{live_data.get('longitude', 'UNK')} "
        f"/TM 1200 /FL {int(live_data.get('elevation_ft', 0)/100)} "
        f"/TP {user_inputs['ac_type']} "
        f"/TB {user_inputs['turbulence']} "
        f"/IC {user_inputs['icing']} /RM {user_inputs['remarks']}"
    )
    spoken_version = (
        f"Routine Pilot Report. Over coordinates {live_data.get('latitude')}, {live_data.get('longitude')}. "
        f"Flight level {int(live_data.get('elevation_ft', 0))}. Aircraft type {user_inputs['ac_type']}. "
        f"Turbulence: {user_inputs['turbulence'].replace('LGT', 'Light').replace('MOD', 'Moderate')}. "
        f"Icing: {user_inputs['icing']}. Remarks: {user_inputs['remarks']}."
    )
    return pirep_string, spoken_version
def speak_pirep(text):
    """
    Uses system audio to read the report out loud.
    """
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Audio engine error: {e}")
