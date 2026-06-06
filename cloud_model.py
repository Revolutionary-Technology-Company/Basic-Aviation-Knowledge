import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def run_cloud_layer():
    st.header("☁️ Planetary Cross-Country Cloud Corridor Predictor")
    st.markdown(r"### Mathematical Core Engine Vector Grid:")
    st.markdown(r"$$CC(\phi, \lambda, Y, d, h) = CC_{\text{base}} + \beta \cdot \Delta Y + \mathbf{\Phi}_{\text{ocean}}(Y) + \mathbf{\Gamma}_{\text{land}} + \mathbf{\Lambda}_{\text{lunar}}$$")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗺️ Spatiotemporal Target Parameters")
        target_date = st.date_input("Select Target Future Forecast Date", value=datetime(2050, 6, 6))
        target_time = st.time_input("Select Target Evaluation Time (UTC)", value=datetime.now().time())
        
        user_lat = st.number_input("Decimal GPS Latitude (🎚️ Φ)", value=41.8781, format="%.4f") # Default Chicago
        user_lon = st.number_input("Decimal GPS Longitude (🎚️ λ)", value=-87.6298, format="%.4f")
        
        st.markdown("### 🌲 Regional Boundary Conditions")
        region_type = st.selectbox(
            "Select Regional Surface Characterization Matrix:",
            ["Great Plains (High Evapotranspiration Pump)", "Rocky Mountains (High Orographic Lift Vector)", 
             "Industrial Northeast (High Aerosol Cloud Trap)", "Southwest Desert (Vaporization Void)"]
        )

    with col2:
        # Extract calendar time integers from user interface inputs
        year = target_date.year
        day_of_year = target_date.timetuple().tm_yday
        hour = target_time.hour
        
        # 1. Establish geographical baseline approximations from coordinate logic
        if user_lat > 40.0 and user_lon < -120.0:
            cc_base = 65.0  # Pacific Northwest Baseline
        elif user_lat < 35.0 and user_lon < -100.0:
            cc_base = 20.0  # Desert Southwest Baseline
        else:
            cc_base = 45.0  # Standard Central US Baseline
            
        # 2. Compute Long-Term Decadal Slope Vector (Beta Shift)
        delta_years = year - 2026
        beta = -0.08  # Historical macro-cloud trend decline coefficient per year
        climate_trend = beta * delta_years
        
        # 3. Solve Decadal Ocean Teleconnection Matrix Waves
        pdo_wave = 6.5 * np.cos((2 * np.pi / 20.0) * year)
        amo_wave = 4.2 * np.cos((2 * np.pi / 70.0) * year)
        ocean_matrix_sum = pdo_wave + amo_wave
        
        # 4. Inject Land-Use Parameterizations
        if region_type == "Great Plains (High Evapotranspiration Pump)":
            land_modifier = 8.5 * np.sin((2 * np.pi / 365.0) * day_of_year) # Peak summer crop moisture
        elif region_type == "Rocky Mountains (High Orographic Lift Vector)":
            land_modifier = 12.0 # High mechanical uplift constant
        elif region_type == "Industrial Northeast (High Aerosol Cloud Trap)":
            land_modifier = 14.5 # Heavy aerosol suspension locking matrix
        else:
            land_modifier = -25.0 # Desert void vaporization penalty
            
        # 5. Compute Hourly Topocentric Lunar Squeeze Term
        lunar_tide = 0.8 * np.cos((4 * np.pi / 24.0) * hour)
        
        # Run Matrix Composite Core Summation Engine
        final_cloud_cover = cc_base + climate_trend + ocean_matrix_sum + land_modifier + lunar_tide
        final_cloud_cover = max(0.0, min(100.0, final_cloud_cover)) # Clamp boundaries mathematically between 0-100%
        
        st.markdown("### 📊 Decadal Mathematical Forecast Projections")
        st.metric(label="Projected Total Cloud Cover Matrix ($CC$)", value=f"{final_cloud_cover:.1f} %")
        
        # Compile Metrics Dataframe Table
        df_metrics = pd.DataFrame({
            "Core Equation Variable Layer": ["Geographic Base Matrix ($CC_{base}$)", "Anthropogenic Trend Slope ($\\beta \\cdot \\Delta Y$)", "Ocean Coupling Matrix ($\\mathbf{\\Phi}_{ocean}$)", "Land Boundary Flux ($\\mathbf{\\Gamma}_{land}$)", "Lunar Tide Component ($\\mathbf{\\Lambda}_{lunar}$)", "Net Resulting Cloud Cover Calculation Value"],
            "Calculated Matrix Coefficient Value": [f"{cc_base:.1f} %", f"{climate_trend:.2f} %", f"{ocean_matrix_sum:.2f} %", f"{land_modifier:.1f} %", f"{lunar_tide:.2f} %", f"{final_cloud_cover:.1f} %"]
        })
        st.table(df_metrics)
        
        # Integrated Spreadsheet Downloader Engine Link
        st.download_button(
            label="💾 Export Future Generation Cloud Matrix Layout (.csv)",
            data=df_metrics.to_csv(index=False).encode('utf-8'),
            file_name=f"future_generation_cloud_prediction_{year}_{user_lat:.2f}.csv",
            mime="text/csv"
        )
