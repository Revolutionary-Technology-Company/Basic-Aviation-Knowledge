# Updated JSON output for the Trim Computer
payload = {
    "correction": {
        "roll": correction['roll'],
        "pitch": correction['pitch'],
        "throttle_compensation": acceleration_kts_per_sec
    },
    "envelope_context": {
        "margin_ratio": stall_margin_kts / v_stall_turn, # 0.0 to 1.0 scale
        "load_factor": n,
        "is_maneuver_optimized": True
    },
  "mode": "SPORT",
  "status": "ACTIVE"
}
# telemetry_link.py (Add this to your existing file)

# --- NEW: Centralized Registry for Boeing Aggregation ---
# This dictionary acts as the master record for the entire flight model
GLOBAL_MODEL_STATE = {
    "telemetry": {},
    "dynamics": {},
    "atmospheric_models": {},
    "navigation": {}
}

def update_global_state(category, data_key, value):
    """
    Unified entry point for all physics engines (Rossby, Fog, Icing, etc.)
    to report their findings.
    """
    if category in GLOBAL_MODEL_STATE:
        GLOBAL_MODEL_STATE[category][data_key] = value

def export_final_model(filename="final_model_output.json"):
    """
    Boeing integration: Aggregates the full state of all physics models
    into a single structured JSON payload.
    """
    with open(filename, "w") as f:
        json.dump(GLOBAL_MODEL_STATE, f, indent=4)
    print(f"✅ Final Flight Physics Model exported to {filename}")
