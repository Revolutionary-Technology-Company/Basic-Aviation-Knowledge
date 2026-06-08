Here is a comprehensive cheat sheet for the **Aviation Intelligence Engine** command-line interface.

Because we built this using `Typer`, every command is automatically documented. You can run `python cli_main.py --help` at any time to see a list, but this cheat sheet breaks down exactly how to use the specific modules we've constructed.

### 🚀 Core Flight & Navigation

Commands to initiate your primary simulation loops and TUI dashboard.

-   **Launch the Textual User Interface (TUI):**

    `python app.py start --mode TACTICAL --target Earth`

    *Initiates the interactive terminal dashboard for live monitoring and manual override injection.*

-   **Start the CLI Flight Loop:**

    `python cli_main.py flight --mode TACTICAL`

    *Triggers the Stellarium Universal GPS initialization, allowing you to lock your hardware dongle to a celestial reference frame (Earth, Mars, Luna, etc.) before flight.*

-   **Update Vehicle Configuration:**

    `python cli_main.py config MAX_CRUISE_ALT 45000`

    *Injects parameter overrides directly into the Pydantic schema validator.*

### 🌪️ Physics & Environmental Modeling

Commands to trigger the heavy mathematical arrays and meteorological models.

-   **Execute Boeing Master Sequence:**

    `python cli_main.py sequence`

    *Runs all physics engines (space weather, radiation, cloud, fog, icing, wind, lunar, rossby) in strict thermodynamic order without requiring manual sequencing.*

-   **Generate Synthetic Weather (AI-METAR/TAF):**

    `python cli_main.py weather KSEA`

    *Runs the physics matrix for a specific coordinate and generates an FAA-compliant METAR and 24-hour TAF report. (Replace `KSEA` with any valid IATA/ICAO code).*

-   **Time-Travel / Mission Planning Mode:**

    `python cli_main.py time --manual --year 2026 --month 12 --day 25 --hour 14 --minute 30`

    *Disconnects the physics engines from the system UTC clock and locks them to a future/past date for predictive mission planning.*

-   **Synchronize Time to Real-Time:**

    `python cli_main.py time`

    *Removes manual overrides and locks the physics engines back to your live system clock.*

### 📍 Infrastructure & Data Lookup

Commands to query your high-speed `src/` databases.

-   **Query Airport Infrastructure:**

    `python cli_main.py airport KSEA`

    *Performs an instant O(1) hash lookup to return station elevation, latitude, longitude, and primary radio frequencies.*

-   **Export Telemetry Payload:**

    `python cli_main.py export`

    *Aggregates the current global state from all physics engines and exports it to `final_model_output.json` for Boeing/NASA payload compliance.*

### ⚙️ System Diagnostics & Testing

Commands to verify hardware connections and protocol integrity.

-   **Hardware Telemetry Test:**

    `python live_telemetry.py`

    *Bypasses the orchestrator and directly tests your USB DGPS/RTK dongle, verifying satellite locks and testing the Mars/Earth reference frame transitions.*

-   **Stellarium Deep Space Catalog Test:**

    `python stellarium_parser.py`

    *Tests the binary/TSV extraction of the `catalog-3.23.dat` file to ensure celestial coordinates and magnitudes are loading properly.*

-   **Run Protocol Integrity Checks:**

    `python cli_main.py validate`

    *Scans the `/logs` directory to ensure all required output streams (Lockheed bus, Axiom ISS, NASA stream) are functioning correctly.*

-   **Regenerate Documentation:**

    `python cli_main.py regen-docs`

    *Scans the repository and auto-generates Markdown documentation from your code docstrings.*

**💡 Pro-Tip for Terminal Environments:**

If you chain your commands in a bash script (e.g., `test_flight.sh`), you can automate predictive planning. For example:

Bash

```
python cli_main.py time --manual --year 2027 --month 1 --day 1
python cli_main.py sequence
python cli_main.py weather KSEA
python cli_main.py export

```

This automatically jumps to New Year's Day 2027, runs the global physics engine, prints the Seattle weather prediction, and exports the JSON payload without any manual interaction.

### 🌪️ Synthetic Weather & Meteorology

These commands utilize your physics engines to generate FAA-compliant METAR and TAF reports.

-   **Generate Current Station Weather:**

    `python cli_main.py weather KSEA`

    *Calculates the current physical state for Seattle-Tacoma and outputs the AI-METAR and 24-hour AI-TAF.*

-   **Generate High-Altitude / Mountain Weather:**

    `python cli_main.py weather KDEN`

    *Tests the physics engine against a high-elevation station (Denver), which will automatically adjust the barometric pressure and cloud base temperature matrices.*

-   **Coastal / Marine Fog Test:**

    `python cli_main.py weather KSFO`

    *Tests the fog thermodynamics engine for San Francisco, ideal for checking visibility (SM) degradation in your METAR.*

### ⏰ Predictive Mission Planning (Time Manipulation)

By combining the time-bridge with your weather and physics models, you can forecast future conditions.

-   **Jump to a Future Date:**

    `python cli_main.py time --manual --year 2026 --month 11 --day 15 --hour 14 --minute 0`

    *Locks the global telemetry bus to November 15, 2026, at 14:00 UTC.*

-   **Generate Future Forecast:**

    `python cli_main.py weather KSEA` *(Run immediately after setting the time)*

    *Because the time bus is locked to November, this command now generates a predictive AI-METAR for that specific future date, rather than today.*

-   **Synchronize Back to Live UTC:**

    `python cli_main.py time`

    *Clears the manual override and locks all physics engines back to the real-time system clock.*

### 🚀 Extraterrestrial & Flight Operations

Commands for initiating your Universal GPS and planetary physics.

-   **Launch Flight Computer (Tactical):**

    `python cli_main.py flight --mode TACTICAL`

    *Initializes the Stellarium Universal GPS prompt. Allows you to lock your USB dongle to Mars, Earth, or Luna, and loads aggressive stall-margin matrices.*

-   **Launch Flight Computer (Civilian):**

    `python cli_main.py flight --mode CIVILIAN`

    *Loads the flight computer with standard civilian safety buffers and fuel-efficiency parameters.*

-   **Run Master Physics Pipeline:**

    `python cli_main.py sequence`

    *Executes the Boeing Master Sequence. Runs space weather, radiation, cloud thermodynamics, fog, icing, and wind models in strict cascading order.*

### 📍 Infrastructure & Waypoint Database

Commands to instantly query your O(1) hash-mapped CSV databases.

-   **Query Major Hub Infrastructure:**

    `python cli_main.py airport KORD`

    *Returns elevation, latitude, longitude, and primary radio frequencies for Chicago O'Hare.*

-   **Query Remote/Small Airfields:**

    `python cli_main.py airport PAJN`

    *Returns infrastructure data for Juneau, Alaska, demonstrating the global reach of your database.*

### ⚙️ System Administration & Output

Commands for managing the software state and exporting data to external partners.

-   **Export Global State Payload:**

    `python cli_main.py export`

    *Dumps the aggregated results of all active physics engines into `final_model_output.json` for Boeing/NASA protocol ingestion.*

-   **Hot-Swap Configuration Variables:**

    `python cli_main.py config MAX_GS 450.5`

    *Injects a strict float value (450.5) into the Pydantic schema validator for the maximum ground speed parameter.*

-   **Run Protocol Assurance:**

    `python cli_main.py validate`

    *Scans the `/logs` directory to ensure data streams for Lockheed, Northrop, Axiom, and NASA are active and uncorrupted.*

-   **Generate Technical Documentation:**

    `python cli_main.py regen-docs`

    *Parses your Python docstrings and updates the Markdown files in your `/docs` repository.*
