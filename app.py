import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="Solar Resource Monitoring Dashboard", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; color: #2E86C1; }
    .main { background-color: #fcfcfc; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    files = glob.glob("data/*.csv")
    if not files:
        return pd.DataFrame()
    
    combined_list = []
    for f in files:
        df_temp = pd.read_csv(f, sep='\t')
        # Use the filename as the year label
        df_temp['Year_Label'] = os.path.basename(f).replace('.csv', '')
        time_col = 'time (US/Pacific)'
        if time_col in df_temp.columns:
            df_temp[time_col] = pd.to_datetime(df_temp[time_col])
        combined_list.append(df_temp)
    
    full_df = pd.concat(combined_list, ignore_index=True)
    return full_df.sort_values('time (US/Pacific)')

# --- LOAD DATA ---
df = load_data()

weather_metrics = {
    "Temperature (°C)": "E_BaseMet_Air Temperature (°C)",
    "Humidity (%)": "E_BaseMet_Relative Humidity (%RH)",
    "Barometric Pressure (Hpa)": "E_BaseMet_Barometric_Pressure (Hpa)",
    "Wind Speed (m/s)": "E_BaseMet_Wind_Speed (m/s)",
    "Wind Direction (°)": "E_BaseMet_Wind_Direction (Degrees)",
    "Back of Module Temp (°C)": "E_BOM_Temp_1 (°C)"
}

if df.empty:
    st.error("No data found in 'data/' folder. Please ensure your CSV files are there.")
    st.stop()

# --- SIDEBAR CONTROLS ---
st.sidebar.title("Dashboard Controls")

# Year Selector
all_years = sorted(df['Year_Label'].unique())
selected_years = st.sidebar.multiselect("Select Years", options=all_years, default=all_years)

# Time Period Picker (Date Range)
min_date = df['time (US/Pacific)'].min().date()
max_date = df['time (US/Pacific)'].max().date()

st.sidebar.subheader("Select Time Period")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# --- DATA FILTERING ---
# Filter by Year
filtered_df = df[df['Year_Label'].isin(selected_years)]

# Filter by Date Range (Checking if range is complete)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['time (US/Pacific)'].dt.date >= start_date) & 
        (filtered_df['time (US/Pacific)'].dt.date <= end_date)
    ]

# --- HEADER SECTION ---
st.title("Solar Resource Monitoring Dashboard")

# Format coverage as MM/DD/YYYY
start_str = filtered_df['time (US/Pacific)'].min().strftime('%m/%d/%Y')
end_str = filtered_df['time (US/Pacific)'].max().strftime('%m/%d/%Y')
st.markdown(f"**Data Coverage:** {start_str} - {end_str}")

# --- METRIC BOXES ---
m1, m2, m3, m4 = st.columns(4)
if not filtered_df.empty:
    latest = filtered_df.iloc[-1]
    m1.metric("Latest Temp", f"{latest[weather_metrics['Temperature (°C)']]:.1f} °C")
    m2.metric("Latest Humidity", f"{latest[weather_metrics['Humidity (%)']]:.0f}%")
    m3.metric("Wind Speed", f"{latest[weather_metrics['Wind Speed (m/s)']]:.1f} m/s")
    m4.metric("Pressure", f"{latest[weather_metrics['Barometric Pressure (Hpa)']]:.0f} hPa")

st.divider()

# --- INTERACTIVE WEATHER TRENDS ---
st.subheader("Interactive Weather Trends")

# Metric Selection
selected_metric_label = st.selectbox(
    "Select Weather Metric to Visualize:", 
    options=list(weather_metrics.keys())
)
selected_column = weather_metrics[selected_metric_label]

if not filtered_df.empty:
    fig_weather = px.line(
        filtered_df, 
        x='time (US/Pacific)', 
        y=selected_column, 
        color='Year_Label',
        title=f"{selected_metric_label} Over Selected Period",
        template="plotly_white",
        labels={selected_column: selected_metric_label, 'time (US/Pacific)': 'Date'}
    )
    fig_weather.update_layout(hovermode="x unified", height=600)
    st.plotly_chart(fig_weather, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

# --- RAW DATA FOOTER ---
with st.expander("View Data Table"):
    st.dataframe(filtered_df.tail(500), use_container_width=True)

