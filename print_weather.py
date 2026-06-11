import socket
from datetime import datetime
import streamlit as st
import pandas as pd

def format_pirep_entry(index, row_text):
    if pd.isna(row_text):
        return ""
    
    clean_text = str(row_text).strip()
    if not clean_text:
        return ""
        
    return f"Report {index}:\n{clean_text}\n------------------------------"

def build_pirep_section(pireps_df):
    if pireps_df.empty:
        return "NO ACTIVE PIREPS REPORTED FOR THIS AREA."
        
    entries = []
    for idx, row in pireps_df.iterrows():
        entry = format_pirep_entry(idx + 1, row['PIREP Text'])
        if not entry:
            continue
        entries.append(entry)
        
    if not entries:
        return "NO ACTIVE PIREPS REPORTED FOR THIS AREA."
        
    return "\n".join(entries)

def format_aviation_printout(icao_station, metar_data, taf_data, pireps_df):
    if not icao_station:
        icao_station = "UNKNOWN"
        
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    print_job = [
        "==========================================",
        "          AVIATION WEATHER BRIEF          ",
        f"          STATION: {icao_station.upper()}              ",
        f"          PRINTED: {timestamp}        ",
        "==========================================",
        "\n[CURRENT METAR]",
        metar_data,
        "\n[WEATHER PREDICTIONS / TAF]"
    ]
    
    for line in taf_data.split('\n'):
        print_job.append(line)
        
    print_job.append("\n[PILOT REPORTS / PIREPS]")
    print_job.append(build_pirep_section(pireps_df))
        
    print_job.extend([
        "\n\n==========================================",
        "             END OF BRIEFING              ",
        "==========================================\n\n\n\n"
    ])
    
    return "\n".join(print_job)

def send_to_network_printer(ip_address, text_payload):
    if not ip_address:
        return False, "Invalid IP Address"
        
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((ip_address, 9100))
            s.sendall(text_payload.encode('utf-8'))
        return True, "Weather briefing dispatched to printer successfully."
    except Exception as e:
        return False, f"Printing failed: {e}"

def execute_print_job(ip_addr, station, metar, taf, pireps):
    if not ip_addr:
        st.warning("A valid Printer IP Address is required to dispatch.")
        return

    formatted_briefing = format_aviation_printout(station, metar, taf, pireps)
    
    with st.spinner(f"Connecting to Printer at {ip_addr}:9100..."):
        success, msg = send_to_network_printer(ip_addr, formatted_briefing)
        
    if not success:
        st.error(msg)
        return
        
    st.success(msg)
    with st.expander("View Print Spool Payload"):
        st.code(formatted_briefing, language="text")

st.set_page_config(page_title="Standalone Printer Node", layout="centered")

st.title("Printer Node")
st.markdown("Launch weather briefing print jobs directly to network-attached printers over port 9100.")

col1, col2 = st.columns(2)
with col1:
    station_input = st.text_input("Station ICAO", value="KJFK")
with col2:
    printer_ip = st.text_input("Printer IP Address", value="192.168.1.150")

metar_input = st.text_area("METAR Data", value="KJFK 070851Z 11006KT 10SM FEW045 BKN250 18/14 A3002 RMK AO2 SLP164")
taf_input = st.text_area("TAF Data", value="KJFK 070550Z 0706/0812 13007KT P6SM SKC\nFM071400 16011KT P6SM FEW050\nFM080100 17008KT P6SM BKN060", height=100)

st.subheader("Live PIREPs")

default_pireps = pd.DataFrame({
    "PIREP Text": [
        "UA /OV JFK045015 /TM 0830 /FL060 /TP B738 /TA M02 /WV 12015KT /TB LGT",
        "UUA /OV LGA /TM 0842 /FL020 /TP A320 /LLWS -15KT SFC-020 BY ARRIVING ACFT"
    ]
})

edited_pireps_df = st.data_editor(default_pireps, num_rows="dynamic", use_container_width=True)

if st.button("Dispatch Print Job", type="primary"):
    execute_print_job(printer_ip, station_input, metar_input, taf_input, edited_pireps_df)
