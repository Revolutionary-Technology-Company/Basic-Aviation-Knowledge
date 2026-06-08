Basic Aviation Knowledge: Mission Control & Flight Dynamics Kernel
==================================================================

Overview
--------

This repository provides a high-fidelity aerospace simulation, navigation, and telemetry suite. Designed for modularity, it allows for high-precision orbital pathing, adaptive atmospheric entry control, and multi-contractor telemetry dispatch (NASA, Lockheed, Northrop, etc.).

Mission-Critical Capabilities
-----------------------------

### 1\. High-Fidelity Physics & Dynamics

-   **Advanced Entry Engine:** Atmospheric entry management utilizing Sutton-Graves stagnation heat flux models and PID-controlled bank-angle correction for storm drift.

-   **Energy Management:** Automated S-Turn maneuver injection to dissipate kinetic energy during high-angle or "too hot" arrivals.

-   **Performance Kernels:** Hot-path physics calculations (Rossby dynamics, icing models, thermodynamics) are accelerated via **Numba (`njit`)** and integrated multicore processing for near-real-time throughput.

### 2\. Mission Assurance & Compliance

-   **Config Validation:** Enforces strict Pydantic schema validation for all inputs (mass, area, G-loads). Rejects malformed configuration files before simulation start.

-   **Atomic Telemetry:** Utilizes file-locking (`fcntl`) for all binary telemetry exports (Lockheed 1553B, NASA HDF5), ensuring data integrity during high-throughput flight loops.

-   **Protocol Integrity:** Automated pre-flight checklists via `cli_main.py` verify that all six aerospace export protocols (Boeing, NASA, Lockheed, Axiom, Northrop, OAAM) are live and writing valid data.

### 3\. Integrated Interfaces

-   **Tactical CLI (`cli_main.py`):** Professionalized Typer-based command-line interface for mission control, protocol validation, and automated documentation generation.

-   **Cockpit TUI (`app.py`):** Asynchronous Textual dashboard for real-time flight monitoring, featuring non-blocking logging and parameter overriding.

Architecture & Integrity Note
-----------------------------

*To our operators:* The repository utilizes a **Modular Open Systems Approach (MOSA)**.

-   Your **High-Fidelity Math Kernels** (e.g., `aviation_physics.py`, `rossby_model.py`, `atmospheric_entry_controller.py`) remain in their standalone, deep-logic form.

-   The **Orchestration Shells** (`cli_main.py`, `app.py`) are strictly non-invasive wrappers. They import and execute your physics logic but do not alter or simplify the underlying computational fidelity.

Quick Start / Mission Commands
------------------------------

### Validation & Readiness

Verify all protocol channels and configurations:

Bash

```
python cli_main.py validate

```

### Launch Mission Control

Start the cockpit TUI with tactical profile:

Bash

```
python app.py --mode TACTICAL --target Earth

```

### Performance Reporting

Export high-fidelity trajectory data for FAA/Mission Review:

Bash

```
python aviation_matrix_export.py

```

### Auto-Documentation

Generate/Refresh documentation from current code docstrings:

Bash

```
python cli_main.py regen-docs

```

Requirements
------------

Ensure your environment is set for high-performance aviation computation:

Bash

```
pip install -r requirements.txt
# Requirements include: numpy, pandas, numba, textual, typer, pydantic

```

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
