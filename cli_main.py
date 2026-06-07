# cli_main.py
import sys
import importlib
import telemetry_link
from waypoint_manager import WaypointManager
from flight_control_dynamics import FlightControlDynamics

# --- 1. GLOBAL INITIALIZATION ---
wp_manager = WaypointManager()
computer = FlightControlDynamics(mode="CIVILIAN")

MODULES = [
    "wind_dynamics", 
    "fog_thermodynamics", 
    "radiation_model", 
    "cloud_model", 
    "space_weather_engine", 
    "lunar_model", 
    "aviation_icing",
    "rossby_model",
    "cloud_temperature_drop",
    "cloud_calendar",
    "aita_model",
    "sfo_model"
]

def verify_modules():
    print("\n✈️ --- Verifying Module Integrity ---")
    loaded_modules = {}
    for mod_name in MODULES:
        try:
            loaded_modules[mod_name] = importlib.import_module(mod_name)
            print(f"✅ [LOADED] {mod_name}")
        except ImportError as e:
            print(f"❌ [FAILED] {mod_name} | Error: {e}")
    return loaded_modules

def run_boeing_master_sequence(loaded_engines, override_data):
    """Executes the engines in strict thermodynamic and physical order."""
    print("\n🚀 ENGAGING BOEING MASTER PHYSICS SEQUENCE...")
    
    sequence = [
        ("space_weather_engine", "run_space_layer"),
        ("radiation_model", "run_radiation_layer"),
        ("cloud_model", "run_cloud_layer"),
        ("fog_thermodynamics", "run_fog_layer"),
        ("aviation_icing", "run_icing_layer"),
        ("wind_dynamics", "run_wind_layer"),
        ("lunar_model", "run_lunar_layer")
    ]
    
    for mod_name, func_name in sequence:
        if mod_name in loaded_engines:
            engine = loaded_engines[mod_name]
            if hasattr(engine, func_name):
                print(f"\n--- Sequence Step: {mod_name} ---")
                getattr(engine, func_name)(telemetry_override=override_data)
            else:
                print(f"⚠️ Skipping {mod_name}: Missing {func_name}()")
        else:
            print(f"⚠️ Skipping {mod_name}: Module failed to load.")
            
    print("\n✅ MASTER SEQUENCE COMPLETE.")

def run_flight_controller():
    loaded_engines = verify_modules()
    
    # NEW: Expanded Telemetry Mock Data (Fixes Issue #3)
    override_data = {
        "lat": 47.6062, "lon": -122.3321, "elevation_m": 45.0, "elevation_ft": 147.6, 
        "year": 2026, "temp_c": 15.0, "rh_pct": 0.85, "wind_mph": 15.0,
        "rain_mm_hr": 2.5, "solar_flux_f107": 150.0, "galactic_ray_count": 5000.0,
        "lwp": 120.0, "cloud_base_temp_c": 8.0, "solar_insolation": 800.0,
        "pdo_index": 1.2, "amo_index": -0.5
    }
    
    while True:
        print("\n==================================================")
        print("✈️ Basic Aviation Knowledge - iOS Flight Controller")
        print("==================================================")
        
        active_wp = wp_manager.get_active_waypoint(index=0)
        wp_name = active_wp.name if active_wp else 'None'
        print(f"📍 Active Waypoint: {wp_name}")
        print(f"⚙️ Dynamics Mode:   {computer.mode}")
        
        if active_wp:
            safety = computer.analyze_maneuver_safety(current_airspeed=110, target_bank_deg=30)
            margin_status = "⚠️ UNSAFE" if safety['is_unsafe'] else "✅ SAFE"
            print(f"🛡️ Stall Margin:    {safety['margin']} kts ({margin_status})")

        print("\n--- Available Execution Engines ---")
        available = list(loaded_engines.keys())
        for i, name in enumerate(available, 1):
            print(f"{i}. Run {name}")
            
        print("\n--- System Commands ---")
        print("B. Run Boeing Master Physics Sequence (Strict Order)")
        print("E. Export Boeing Final Model JSON")
        print("Q. Quit Application")
        
        choice = input("\nEnter selection: ").strip().upper()
        
        if choice == 'Q':
            print("Shutting down flight controller. Fly safe.")
            sys.exit(0)
            
        elif choice == 'B':
            run_boeing_master_sequence(loaded_engines, override_data)
            
        elif choice == 'E':
            print("\n📦 Generating Master Payload...")
            telemetry_link.export_final_model("final_model_output.json")
            
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    selected_mod_name = available[idx]
                    engine = loaded_engines[selected_mod_name]
                    func_name = next((attr for attr in dir(engine) if attr.startswith("run_")), None)
                    
                    if func_name:
                        print(f"\n🚀 Engaging {func_name} in {selected_mod_name}...\n")
                        getattr(engine, func_name)(telemetry_override=override_data)
                    else:
                        print(f"⚠️ Error: Could not find a 'run_' orchestration function in {selected_mod_name}")
                else:
                    print("⚠️ Invalid numerical selection.")
            except ValueError:
                print("⚠️ Invalid input. Please select a number, 'B', 'E', or 'Q'.")

if __name__ == "__main__":
    try:
        run_flight_controller()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by pilot. Exiting.")
        sys.exit(0)
