# cli_main.py
import os
import sys
import typer
import importlib
from typing import Optional
import telemetry_link
from waypoint_manager import WaypointManager
from flight_control_dynamics import FlightControlDynamics
from airport_data_manager import manager as airport_manager

# --- 1. SYSTEM CONFIGURATION ---
SRC_DIR = "src"
LOG_DIR = "logs"
CONFIG_FILE = "config.json"

# Physics Engines available for execution
PHYSICS_ENGINES = [
    "space_weather_engine", "radiation_model", "cloud_model", 
    "fog_thermodynamics", "aviation_icing", "wind_dynamics", 
    "lunar_model", "rossby_model"
]

@app.command()
def time(
    manual: bool = typer.Option(False, help="Set manual time"),
    year: int = 2026, month: int = 6, day: int = 8, hour: int = 12, minute: int = 0
):
    """Sync or override system time for planning."""
    if manual:
        telemetry_link.time_manager.set_manual_time(year, month, day, hour, minute)
    else:
        telemetry_link.time_manager.reset_to_system_time()
def initialize_avionics():
    """Boot sequence for the aviation knowledge system."""
    if not os.path.exists(SRC_DIR):
        typer.secho("CRITICAL FAILURE: /src data directory not found.", fg=typer.colors.RED)
        sys.exit(1)
    
    try:
        nav = WaypointManager(config_path=CONFIG_FILE, dso_catalog_path=os.path.join(SRC_DIR, "catalog-3.23.dat"))
        computer = FlightControlDynamics(mode="TACTICAL")
        return nav, computer
    except Exception as e:
        typer.secho(f"AVIONICS BOOT FAILURE: {e}", fg=typer.colors.RED)
        sys.exit(1)

# --- 2. CLI INTERFACE ---
app = typer.Typer(help="Basic Aviation Knowledge: Mission Control System")

@app.command()
def sequence():
    """Engage the Boeing Master Physics Sequence in strict order."""
    typer.secho("🚀 ENGAGING BOEING MASTER PHYSICS SEQUENCE...", fg=typer.colors.CYAN)
    
    override_data = {
        "lat": 47.6062, "lon": -122.3321, "elevation_m": 45.0, "temp_c": 15.0
    }
    
    # Execution sequence
    for mod_name in PHYSICS_ENGINES:
        try:
            engine = importlib.import_module(mod_name)
            func_name = next((attr for attr in dir(engine) if attr.startswith("run_")), None)
            if func_name:
                typer.echo(f"--- Running {mod_name} ---")
                getattr(engine, func_name)(telemetry_override=override_data)
        except ImportError:
            typer.secho(f"⚠️ Skipping {mod_name}: Module not found.", fg=typer.colors.YELLOW)
            
    typer.secho("✅ MASTER SEQUENCE COMPLETE.", fg=typer.colors.GREEN)

@app.command()
def airport(ident: str = typer.Argument(..., help="ICAO/IATA code (e.g., KSEA)")):
    """Query the airport database for infrastructure metadata."""
    data = airport_manager.get_airport(ident.upper())
    if data is not None:
        typer.echo(f"📍 Airport: {data['name']} ({ident.upper()})")
        typer.echo(f"   Elevation: {data['elevation_ft']} ft")
        freqs = airport_manager.get_frequencies(ident.upper())
        if freqs is not None:
            typer.echo(f"   Primary Freq: {freqs['frequency_mhz'].iloc[0]} MHz")
    else:
        typer.secho("⚠️ Airport code not found.", fg=typer.colors.RED)

@app.command()
def export():
    """Export the aggregated Global State to final_model_output.json."""
    typer.echo("📦 Generating Master Payload...")
    telemetry_link.export_final_model("final_model_output.json")
    typer.secho("✅ Payload saved to final_model_output.json", fg=typer.colors.GREEN)

@app.command()
def validate():
    """Run automated mission assurance and protocol integrity checks."""
    typer.echo("Executing Protocol Integrity Suite...")
    required_files = ["nasa_stream.bin", "oaam_topology_snapshot.json"]
    for f in required_files:
        if os.path.exists(os.path.join(LOG_DIR, f)):
            typer.echo(f"Protocol Check [{f}]: OK")
        else:
            typer.echo(f"Protocol Check [{f}]: FAILED")

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    app()
