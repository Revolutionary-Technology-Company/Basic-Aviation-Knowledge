# cli_main.py
import sys
import importlib
import telemetry_link
from waypoint_manager import WaypointManager
from flight_control_dynamics import FlightControlDynamics

# --- 1. GLOBAL INITIALIZATION ---
# Initialize the engines globally so they are ready for any model
wp_manager = WaypointManager()
computer = FlightControlDynamics(mode="CIVILIAN")

# List of all primary engine modules to verify and load
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
            # Dynamically import the module
            loaded_modules[mod_name] = importlib.import_module(mod_name)
            print(f"✅ [LOADED] {mod_name}")
        except ImportError as e:
            print(f"❌ [FAILED] {mod_name} | Error: {e}")
    return loaded_modules

def run_flight_controller():
    # 1. Run the health check and load engines
    loaded_engines = verify_modules()
    
    while True:
        print("\n==================================================")
        print("✈️ Basic Aviation Knowledge - iOS Flight Controller")
        print("==================================================")
        
        # Display current navigation/safety state
        active_wp = wp_manager.get_active_waypoint(index=0)
        wp_name = active_wp.name if active_wp else 'None'
        print(f"📍 Active Waypoint: {wp_name}")
        print(f"⚙️ Dynamics Mode:   {computer.mode}")
        
        if active_wp:
            safety = computer.analyze_maneuver_safety(current_airspeed=110, target_bank_deg=30)
            margin_status = "⚠️ UNSAFE" if safety['is_unsafe'] else "✅ SAFE"
            print(f"🛡️ Stall Margin:    {safety['margin']} kts ({margin_status})")

        print("\n--- Available Execution Engines ---")
        
        # Create a dynamic menu based on successfully loaded modules
        available = list(loaded_engines.keys())
        for i, name in enumerate(available, 1):
            print(f"{i}. Run {name}")
            
        print("\n--- System Commands ---")
        print("E. Export Boeing Final Model JSON")
        print("Q. Quit Application")
        
        choice = input("\nEnter selection: ").strip().upper()
        
        if choice == 'Q':
            print("Shutting down flight controller. Fly safe.")
            sys.exit(0)
            
        elif choice == 'E':
            # Export the aggregated data bus directly to JSON
            print("\n📦 Generating Master Payload...")
            telemetry_link.export_final_model("final_model_output.json")
            
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    selected_mod_name = available[idx]
                    engine = loaded_engines[selected_mod_name]
                    
                    # We try to find the run function dynamically
                    func_name = next((attr for attr in dir(engine) if attr.startswith("run_")), None)
                    
                    if func_name:
                        print(f"\n🚀 Engaging {func_name} in {selected_mod_name}...\n")
                        
                        # Provide override context for UI-independent models
                        override_data = {
                            "lat": 47.6062, "lon": -122.3321, "elevation_m": 45.0, "year": 2026,
                            "temp_c": 15.0, "rh_pct": 0.85, "wind_mph": 15.0
                        }
                        
                        # Execute the engine
                        getattr(engine, func_name)(telemetry_override=override_data)
                    else:
                        print(f"⚠️ Error: Could not find a 'run_' orchestration function in {selected_mod_name}")
                else:
                    print("⚠️ Invalid numerical selection.")
            except ValueError:
                print("⚠️ Invalid input. Please select a number, 'E', or 'Q'.")

if __name__ == "__main__":
    try:
        run_flight_controller()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by pilot. Exiting.")
        sys.exit(0)
