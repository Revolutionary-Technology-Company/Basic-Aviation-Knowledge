import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_calendar_arc_layer():
    st.header("📅 12-Month Climatological Cloud Arc Engine")
    st.markdown(r"Plots the annual wave transformation of cloud liquid water path ($\Delta LWP$) across a full calendar year cycle based on IPCC tracks.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎛️ Long-Range Timeline Constraints")
        target_century_year = st.number_input(
            "Select Evaluation Target Year (Century Horizon)", 
            min_value=2026, max_value=2126, value=2075, step=1
        )
        
        # --- NEW IPCC CARBON EMISSION SCENARIO SELECTOR ---
        st.markdown("### 🏭 Global Carbon-Emission Scenario Matrix")
        ssp_track = st.selectbox(
            "Select IPCC Scenario Track (Alters Long-Term Beta Coefficient):",
            [
                "SSP1-2.6 (Low Emissions / Green Growth Track)",
                "SSP2-4.5 (Middle of the Road / Moderate Track)",
                "SSP3-7.0 (High Emissions / Regional Rivalry Track)",
                "SSP5-8.5 (Extreme Emissions / Fossil-Fueled Track)"
            ]
        )
        
        st.markdown("### 🌲 Boundary Driver Properties")
        regional_forcing = st.selectbox(
            "Select Regional Boundary Driver Forcing For Arc Analysis:",
            ["Midwest Agricultural Belt (Summer Stomatal Surge)", 
             "Great Lakes Basin (Winter Convective Instability Engine)", 
             "Standard Continental Background Matrix"]
        )
        
    with col2:
        # Define dynamic long-term cloud decay rates (Beta Coefficients) based on IPCC tracks
        if "SSP1-2.6" in ssp_track:
            beta_decay = -0.012  # Stabilized, minimal cloud coverage loss
            ssp_label = "SSP1-2.6 (Low)"
        elif "SSP2-4.5" in ssp_track:
            beta_decay = -0.045  # Moderate, ongoing structural decline
            ssp_label = "SSP2-4.5 (Mod)"
        elif "SSP3-7.0" in ssp_track:
            beta_decay = -0.085  # Severe cloud degradation from high warming
            ssp_label = "SSP3-7.0 (High)"
        else:  # SSP5-8.5
            beta_decay = -0.140  # Extreme cloud dissolution due to intense thermal feedback loops
            ssp_label = "SSP5-8.5 (Extreme)"

        # Build vector array mapping 365 sequential days of the calendar year
        days_in_year = np.arange(1, 366)
        
        # 1. Evaluate Carbon Scenario Decadal Baseline Decay Trend (Beta Vector Shift)
        delta_years = target_century_year - 2026
        base_climatology_offset = beta_decay * delta_years
        
        # 2. Extract Structural Multi-Decadal Ocean Matrix Waves
        pdo_index_wave = 5.2 * np.cos((2 * np.pi / 20.0) * target_century_year)
        amo_index_wave = 3.8 * np.sin((2 * np.pi / 70.0) * target_century_year)
        ocean_forcing_constant = pdo_index_wave + amo_index_wave
        
        # 3. Process High-Resolution Regional Boundary Curve Loops
        if regional_forcing == "Midwest Agricultural Belt (Summer Stomatal Surge)":
            seasonal_profile = 15.0 * np.sin((2 * np.pi / 365.0) * (days_in_year - 110))
        elif regional_forcing == "Great Lakes Basin (Winter Convective Instability Engine)":
            seasonal_profile = 18.0 * np.cos((2 * np.pi / 365.0) * days_in_year)
        else:
            seasonal_profile = 4.0 * np.sin((2 * np.pi / 365.0) * days_in_year)
            
        # 4. Sum System Matrices: Base (50%) + Carbon Trend + Ocean + Seasonal Forcing Loop
        modeled_lwp_arc = 50.0 + base_climatology_offset + ocean_forcing_constant + seasonal_profile
        
        # Apply strict physical system ceiling boundaries (Clamp matrix between 0% and 100%)
        modeled_lwp_arc = np.clip(modeled_lwp_arc, 0.0, 100.0)
        
        # --- GENERATE MATPLOTLIB INTERACTIVE ALIGNMENT PLOT ---
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(days_in_year, modeled_lwp_arc, color="royalblue", linewidth=2.5, label=f"Cloud Density Arc ({ssp_label})")
        ax.axhline(50.0, color="gray", linestyle=":", alpha=0.5, label="Historical Century Median")
        
        # Configure calendar month markings along the x-axis grid line arrays
        month_days = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        ax.set_xticks(month_days)
        ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        
        ax.set_title(f"12-Month Predicted Cloud Cover Trajectory Matrix for Year {target_century_year}")
        ax.set_xlabel("Calendar Time Steps (Day of Year)")
        ax.set_ylabel("Calculated Cloud Density Metrics (%)")
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.legend(loc="lower left")
        
        # Render visual component to dashboard layout window
        st.pyplot(fig)
        
        # --- CALCULATED STATISTICAL SUMMARY METRICS ---
        st.markdown("### 📈 Scenario Climatological Matrix Extents")
        max_idx = np.argmax(modeled_lwp_arc)
        min_idx = np.argmin(modeled_lwp_arc)
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("Assigned Beta Value ($\\beta$)", f"{beta_decay:.3f} % / yr")
        stat_col2.metric("Annual Peak Coverage", f"{modeled_lwp_arc[max_idx]:.1f} %", f"Day {days_in_year[max_idx]}")
        stat_col3.metric("Annual Minimum Coverage", f"{modeled_lwp_arc[min_idx]:.1f} %", f"Day {days_in_year[min_idx]}")
        
        # --- COMPILE SPREADSHEET STRUCTURAL DATA LOG ---
        df_calendar_log = pd.DataFrame({
            "Day_Of_Year": days_in_year,
            "IPCC_Scenario_Track": ssp_track,
            "Decadal_Beta_Trend_Pct": base_climatology_offset,
            "Ocean_Basin_Coupling_Forcing_Pct": ocean_forcing_constant,
            "Regional_Boundary_Seasonal_Forcing_Pct": seasonal_profile,
            "Final_Composite_Cloud_Density_Pct": modeled_lwp_arc
        })
        
        # Export Spreadsheet Link Configuration Block
        st.download_button(
            label="💾 Download Scenario-Linked Data Matrix (.csv)",
            data=df_calendar_log.to_csv(index=False).encode('utf-8'),
            file_name=f"cloud_calendar_{ssp_label.replace(' ', '_')}_{target_century_year}.csv",
            mime="text/csv"
        )
