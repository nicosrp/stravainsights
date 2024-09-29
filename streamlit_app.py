import streamlit as st
import pandas as pd
import os
from stravaAPI import fetch_activities_and_gpx  # Assuming stravaAPI.py has this function
from stravaDash import update_map_and_statistics, update_runs_list_html, generate_map_and_statistics, generate_runs_list_html

# Set paths for data
gpx_folder = 'API_GPX_FILES'
csv_file_path = 'strava_activities.csv'

# Helper function to load data
@st.cache_data
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return None

# Function to update data from Strava and regenerate files
def update_data(incremental=True):
    st.write("Updating data from Strava and creating missing GPX files...")
    fetch_activities_and_gpx()
    if incremental:
        st.write("Performing incremental update...")
        update_map_and_statistics()
        update_runs_list_html()
    else:
        st.write("Performing full rebuild...")
        generate_map_and_statistics()
        generate_runs_list_html()
    st.success('All files have been updated!')

# Streamlit app layout
st.title("Strava Activity Analysis")

# Automatically load existing data on page load
df = load_data(csv_file_path)

# Show the most up-to-date statistics if data is present
if df is not None:
    st.write("## Current Statistics")

    # Display the map
    with open('activity_map.html', 'r', encoding='utf-8') as file:
        map_content = file.read()
        st.write("### Activity Map")
        st.components.v1.html(map_content, height=600, scrolling=True)

    # Display city and country statistics
    with open('generated_city_statistics_from_csv.html', 'r', encoding='utf-8') as file:
        stats_content = file.read()
        st.write("### City and Country Statistics")
        st.components.v1.html(stats_content, height=400, scrolling=True)

    # Display the runs list
    with open('runs_list.html', 'r', encoding='utf-8') as file:
        runs_list_content = file.read()
        st.write("### Runs List")
        st.components.v1.html(runs_list_content, height=400, scrolling=True)

    # Button to update the data
    if st.button('Incremental Update'):
        update_data(incremental=True)

    # Button to force a full rebuild
    if st.button('Full Rebuild'):
        update_data(incremental=False)

else:
    st.write("No existing data found. Please update the data to fetch the latest activities.")

# Optionally, allow user to update data if a new run was uploaded on Strava
st.sidebar.header("Data Management")
if st.sidebar.button('Force Update Data from Strava'):
    update_data()
