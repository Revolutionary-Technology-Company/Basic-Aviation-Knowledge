import numpy as np


def calculate_icing_accretion(
    temp_c, rh_pct, rainfall_mm_hr, elevation_m, wind_mph=30.0
):
    """Solves the coupled mass collection and thermodynamic freezing equations

    to predict structural ice accumulation rates at specific station coordinates.
    """
    # 1. Core Physical Constants
    L_f = 3.34e5  # Latent heat of fusion for water (J/kg)
    sigma = 5.670374e-8  # Stefan-Boltzmann constant

    # 2. Elevation Pressure Shift Correction
    # Barometric equation mapping pressure drops across altitude changes
    P_pascals = 101325.0 * (1.0 - 2.25577e-5 * elevation_m) ** 5.25588

    # 3. Derive Airborne Liquid Water Content (LWC) from Ground Rainfall Metrics
    if rainfall_mm_hr > 0 and temp_c <= 2.0:
        # Marshall-Palmer size distribution derivation to find g/m³ in air column
        lwc_g_m3 = 0.072 * (rainfall_mm_hr**0.88)
    else:
        lwc_g_m3 = 0.0

    # Convert values to kinematic standard imperial/metric frameworks
    v_m_s = wind_mph * 0.44704
    lwc_kg_m3 = lwc_g_m3 / 1000.0

    # 4. Thermodynamic Freezing Fraction Matrix (n_freezing)
    if temp_c < 0.0 and lwc_g_m3 > 0.0:
        # Simplified mess balance tracking thermal extraction rates
        # Evaporative cooling suppression constant scaling with humidity deficit
        q_evap_loss = (1.0 - rh_pct) * 15.0
        # Convective thermal extraction profile
        q_convective_loss = 12.5 * np.sqrt(v_m_s) * (0.0 - temp_c)

        total_cooling_energy = q_convective_loss + q_evap_loss
        latent_heat_available = lwc_kg_m3 * v_m_s * L_f

        n_freezing = total_cooling_energy / latent_heat_available
        n_freezing = max(0.0, min(1.0, n_freezing))  # Clamp bounds between 0-1
    else:
        n_freezing = 0.0

    # 5. Execute Mass Collection Accumulation Equation
    # Assume standard airfoil collection efficiency constant of 0.65
    e_collection = 0.65 if temp_c <= 0.0 else 0.0

    # Accretion mass = E * n * LWC * V (kg per square meter per second)
    mass_accretion_rate_sec = e_collection * n_freezing * lwc_kg_m3 * v_m_s
    mass_accretion_hr_kg = mass_accretion_rate_sec * 3600.0

    return P_pascals / 100.0, lwc_g_m3, n_freezing, mass_accretion_hr_kg


if __name__ == "__main__":
    print("=================================================================")
    print("        METEOROLOGICAL STRUCTURAL ICING MATRIX ENGINE            ")
    print("=================================================================")
    print("Evaluating ice accumulation metrics across station constraints:\n")

    # Parallel Scenarios: Testing the clashing effects of Elevation vs Humidity
    icing_scenarios = {
        "Low-Altitude Freezing Rain (SFO Coast Setup)": {
            "t": -1.5,
            "rh": 0.98,
            "rain": 4.5,
            "elev": 10.0,
        },
        "High-Altitude Pass (Denver Ridge Runway Setup)": {
            "t": -6.0,
            "rh": 0.95,
            "rain": 2.5,
            "elev": 1600.0,
        },
        "Sub-Saturated Cold Air Column (Dry Cold Outflow)": {
            "t": -4.0,
            "rh": 0.40,
            "rain": 1.5,
            "elev": 500.0,
        },
    }

    for label, p in icing_scenarios.items():
        mb_press, lwc, f_frac, ice_mass = calculate_icing_accretion(
            temp_c=p["t"],
            rh_pct=p["rh"],
            rainfall_mm_hr=p["rain"],
            elevation_m=p["elev"],
        )

        print(f"❄️  Scenario Matrix: {label}")
        print(f"   -> Pressure at Elevation:   {mb_press:.1f} hPa")
        print(f"   -> Computed Liquid Water:   {lwc:.4f} g/m³ in air column")
        print(f"   -> Freezing Rate Fraction:  {f_frac * 100.0:.1f} % of drops freeze")
        print(f"   -> CRITICAL ICE ACCRETION:   {ice_mass:.2f} kg / m² per hour")
        print("-" * 65)
