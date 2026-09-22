# -*- coding: utf-8 -*-
"""
Created on Fri May  1 16:00:01 2026

@author: mehatam
"""

import streamlit as st
import pandas as pd
import requests
from io import StringIO

# ---------------------------------------------------------
# Function to download and parse AgriMet daily data
# ---------------------------------------------------------
def get_agrimet_daily(station, start_year, start_month, end_year, end_month, pcodes):
    all_data = []

    # Loop through each year
    for year in range(start_year, end_year + 1):

        # Determine month range for this year
        if year == start_year:
            m1 = start_month
        else:
            m1 = 1

        if year == end_year:
            m2 = end_month
        else:
            m2 = 12

        # Build URL
        url = (
            "https://www.usbr.gov/pn-bin/daily.pl?"
            f"station={station}"
            f"&year={year}&month={m1}&day=1"
            f"&year={year}&month={m2}&day=31"
        )

        # Add pcodes
        for p in pcodes:
            url += f"&pcode={p}"

        raw = requests.get(url).text

        # Clean lines
        lines = []
        for ln in raw.splitlines():
            if "</" in ln:
                continue
            if ln.startswith("#"):
                continue
            if not ln.strip():
                continue
            lines.append(ln)

        # Find header
        try:
            header_idx = next(i for i, ln in enumerate(lines) if "DATE" in ln)
        except StopIteration:
            continue

        header = lines[header_idx]
        data_lines = lines[header_idx + 1:]

        # Convert fixed-width → CSV-like
        clean_rows = []
        for ln in data_lines:
            parts = [p.strip() for p in ln.split(",")]
            clean_rows.append(",".join(parts))

        header_clean = ",".join([h.strip() for h in header.split(",")])
        csv_text = header_clean + "\n" + "\n".join(clean_rows)

        df = pd.read_csv(StringIO(csv_text))
        df = df[df["DATE"] != "END DATA"]

        all_data.append(df)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------

st.markdown("""
<style>
/* Increase general font size in the main content area */
html, body, [class*="css"]  {
    font-size: 18px !important;
}

/* Make Streamlit input labels larger */
label, .stTextInput label, .stNumberInput label {
    font-size: 20px !important;
    font-weight: 600 !important;
}

/* Adjust text inside input boxes */
input, textarea {
    font-size: 18px !important;
}

/* Increase button text size */
button, .stButton button {
    font-size: 18px !important;
    padding: 8px 16px !important;
}

/* Increase title font size */
h1 {
    font-size: 36px !important;
    font-weight: 700 !important;
}

/* Subheader style */
h2, h3 {
    font-size: 28px !important;
    font-weight: 650 !important;
}


/* Make sidebar expander headings bold */
.streamlit-expanderHeader {
    font-weight: 800 !important;
    font-size: 18px !important;
}

</style>
""", unsafe_allow_html=True)


################
st.title("AgriMet Daily Data Downloader (Multi-Year, Multi-Month)")

st.write("Download daily data from USBR AgriMet by station, date range, and variables (pcodes).")

station = st.text_input("Station ID (e.g., BOII)").upper()

col1, col2 = st.columns(2)
with col1:
    start_year = st.number_input("Start Year", min_value=1900, max_value=2100, value=2024)
    start_month = st.number_input("Start Month (1–12)", min_value=1, max_value=12, value=1)

with col2:
    end_year = st.number_input("End Year", min_value=1900, max_value=2100, value=2026)
    end_month = st.number_input("End Month (1–12)", min_value=1, max_value=12, value=12)

pcodes_input = st.text_input("PCODES (comma-separated, e.g., MN,MX,MM)").upper()
pcodes = [p.strip() for p in pcodes_input.split(",") if p.strip()]

if st.button("Download Data"):
    if not station or not pcodes:
        st.error("Please enter a station ID and at least one pcode.")
    else:
        st.write("Fetching data...")

        df = get_agrimet_daily(
            station,
            start_year,
            start_month,
            end_year,
            end_month,
            pcodes
        )

        if df.empty:
            st.error("No data returned. Check station or date range.")
        else:
            st.success("Data downloaded successfully!")
            st.dataframe(df.head())

            filename = f"{station}_{start_year}{start_month:02d}_{end_year}{end_month:02d}.csv"
            csv_bytes = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name=filename,
                mime="text/csv"
            )


#####

st.sidebar.title("AgriMet Weather Parameters")



with st.sidebar.expander("Weather Parameters at Most AgriMet Stations"):
    st.markdown("""
ET = Evapotranspiration Kimberly-Penman (in)  
ETrs = Evapotranspiration ASCE-EWRI Alfalfa (in)  
ETos = Evapotranspiration ASCE-EWRI Grass (in)  
MN = Minimum Daily Air Temperature (F)  
MX = Maximum Daily Air Temperature (F)  
MM = Mean Daily Air Temperature (F)  
PC = Accumulated Precipitation Since Recharge/Reset (in)  
PP = Daily (24 hour) Precipitation (in)  
PU = Accumulated Water Year Precipitation (in)  
SR = Daily Global Solar Radiation (langleys)  
TA = Mean Daily Humidity (%)  
TG = Growing Degree Days (base 50F)  
YM = Mean Daily Dewpoint Temperature (F)  
UA = Daily Average Wind Speed (mph)  
UD = Daily Average Wind Direction (deg az)  
WG = Daily Peak Wind Gust (mph)  
WR = Daily Wind Run (miles)  
""")

with st.sidebar.expander("Weather Parameters at Specific Stations"):
    st.markdown("""
BN = Minimum Daily Barometric Pressure (in. Hg)  
BP = Average Daily Barometric Pressure (in. Hg)  
BX = Maximum Daily Barometric Pressure (in. Hg)  
SR2 = Daily Diffuse Solar Radiation  
RHN = Minimum Daily Humidity (%)  
PE = 24 Hour Pan Evaporation (in)  
""")

with st.sidebar.expander("Special Parameters at Specific Stations"):
    st.markdown("""
XB = Minimum Daily 1" Soil Temperature (F)  
XF = Maximum Daily 1" Soil Temperature (F)  
YL = Mean Daily 1" Soil Temperature (F)  
ZL = Minimum Daily 2" Soil Temperature (F)  
ZK = Maximum Daily 2" Soil Temperature (F)  
ZM = Mean Daily 2" Soil Temperature (F)  
XC = Minimum Daily 4" Soil Temperature (F)  
XG = Maximum Daily 4" Soil Temperature (F)  
YW = Mean Daily 4" Soil Temperature (F)  
XD = Minimum Daily 8" Soil Temperature (F)  
XH = Maximum Daily 8" Soil Temperature (F)  
XJ = Mean Daily 8" Soil Temperature (F)  
ZG = Minimum Daily 20" Soil Temperature (F)  
ZH = Maximum Daily 20" Soil Temperature (F)  
ZCN = Minimum Daily 40" Soil Temperature (F)  
ZCX = Maximum Daily 40" Soil Temperature (F)  
ZCM = Mean Daily 40" Soil Temperature (F)  
YA = Maximum Daily Canopy Air Temperature (F)  
YB = Minimum Daily Canopy Air Temperature (F)  
Z1 = Minimum Daily Canopy Air Temperature (F)  
Z2 = Maximum Daily Canopy Air Temperature (F)  
Z3 = Average Daily Canopy Air Temperature (F)  
YC = Maximum Daily Shelter Temperature (F)  
YD = Minimum Daily Shelter Temperature (F)  
SP = Snow Water Content (in)  
""")

with st.sidebar.expander("AgriMet Station Links"):
    st.markdown("""
https://www.usbr.gov/pn/agrimet/location.html  
https://www.usbr.gov/pn/agrimet/agrimetmap/agrimap.html  
""")

## instruction for users how to download data

st.sidebar.title("Intrsuctions: Download Agrimet Data")

with st.sidebar.expander("How to Download AgriMet Data"):
    st.markdown("""
***Follow these steps to download daily AgriMet weather data:***

***1. Enter a Station ID***  
Type the AgriMet station code (e.g., BOII, FTMO, COVM).  
Station IDs are available under *AgriMet Station Links*.

***2. Select Start Year and End Year***  
Choose the year range you want to download.  
Example: 2024 to 2026.

***3. Select Start Month and End Month***  
Choose the month range within those years.  
Example: 1 (January) to 12 (December).

***4. Enter PCODES***  
PCODES are weather parameter codes.  
Enter them as a comma-separated list, such as:  
- MN, MX, MM  
- ET, ETrs, ETos  
- PP  
- SR  
(Full lists available in other sidebar sections.)

Example: `ET, MN, PP`

***5. Click "Download Data"***  
The app will fetch the data and display a preview.

***6. Download the CSV***  
Click the “Download CSV” button to save the dataset to your computer.

***If no data appears:***  
- Check the station ID spelling  
- Confirm the date range  
- Ensure PCODES are valid  
""")