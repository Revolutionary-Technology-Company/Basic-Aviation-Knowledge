Contributing to Basic Aviation Knowledge
========================================

Thank you for your interest in contributing to the Basic Aviation Knowledge repository. Our mission is to maintain a high-fidelity aerospace simulation, navigation, and telemetry suite.

To ensure the system remains stable and FAA-compliant, please follow these guidelines when adding new models or features.

1\. Protecting the "Pro" Kernel
-------------------------------

The core physics kernels (e.g., `aviation_physics.py`, `flight_control_dynamics.py`, `atmospheric_entry_controller.py`) are strictly optimized and validated.

**Guideline:** * **Do not modify the core kernels** unless you are submitting a documented optimization or bug fix.

-   **Expand by Extension:** If you are adding a new planetary climate model or a new aircraft performance profile, create a *new module* (e.g., `mars_model.py`) rather than overwriting existing physics files.

2\. How to Add a New Model
--------------------------

If you are developing a new model (e.g., a climate model or a trajectory engine), please adhere to the following standards:

### A. Pattern & Structure

-   **File Naming:** Use the `[name]_model.py` convention (e.g., `rossby_model.py`, `sfo_model.py`).

-   **Imports:** Always import the foundational math and performance modules:

    Python

    ```
    import numpy as np
    from numba import njit
    import aviation_physics
    import schema_validator

    ```

### B. High-Performance Requirements

-   **NJIT Acceleration:** If your model performs time-stepped thermodynamics or iterative physics calculations, use the `@njit(fastmath=True)` decorator. Our system relies on Numba to keep flight-loop latency under strict limits.

-   **Schema Enforcement:** Every new model must support validation. If your model introduces new parameters, add them to `schema_validator.py` or implement a local `validate()` function that ensures all inputs (mass, G-loads, etc.) are strictly typed and within physical bounds.

### C. Telemetry Compliance

All new models must integrate with the existing telemetry pipeline:

-   **Data Flow:** Ensure your model outputs data compatible with `export_telemetry.py`.

-   **Atomic Writing:** If your model generates logs or performance matrices, use the file-locking patterns found in `aviation_matrix_export.py` (`fcntl.flock`) to prevent telemetry corruption.

3\. Workflow for Contributors
-----------------------------

1.  **Environment Setup:** Ensure you have the full development stack installed. Use the provided `install.sh` and `requirements.txt` to align your environment with our local runtime dependencies.

2.  **Implementation:** Develop your new model in the root directory. Use existing modules (like `aviation_telemetry.py` or `aerodynamic_matrix.py`) as templates for your logic.

3.  **Validation:** * Before submitting, run the model through the `cli_main.py` validation suite to ensure it doesn't break the mission control system.

    -   Use `audit_physics.py` (if available in your local branch) to verify your new model is correctly recognized by the repository core.

4.  **Documentation:** Add a docstring to the top of your new file. Run `python cli_main.py regen-docs` to ensure your new model is automatically captured in the project documentation.

4\. Code Standards
------------------

-   **No Hard-Coded Configurations:** Do not hard-code flight parameters. All environmental and vehicle constants must be referenced via the `config.json` loader to ensure FAA compliance.

-   **Safety First:** Wrap all file I/O or external sensor calls in the `avionics_safety_wrapper` (see `aviation_matrix_export.py`) to prevent system crashes during flight simulation.

*For technical questions or to request a code review of a new physics kernel, please open an Issue with the prefix `[PROPOSAL]` followed by the name of the model you intend to implement.*
