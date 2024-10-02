import streamlit as st
import pandas as pd
import os
from stravaAPI import fetch_activities_and_gpx  # Function to fetch activities and generate GPX files
from stravaDash import generate_map_and_statistics, generate_runs_list_html  # Functions to create HTML files
from update_strava_data import update_strava_data

# Set paths for data
gpx_folder = 'API_GPX_FILES'
csv_file_path = 'strava_activities.csv'

# Ensure the GPX folder exists
if not os.path.exists(gpx_folder):
    os.makedirs(gpx_folder)

# Helper function to load data
@st.cache_data
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return None

# Function to update data from Strava and regenerate files
def update_data():
    st.write("Fetching data from Strava and creating missing GPX files...")
    fetch_activities_and_gpx()
    st.success('Data fetched and GPX files updated. Regenerating statistics...')
    generate_map_and_statistics()
    generate_runs_list_html()
    st.success('All files have been updated!')

# Set the page configuration
st.set_page_config(layout="wide", page_title="Strava Activity Analysis")

# Streamlit app layout
st.title("Strava Activity Analysis")

# Automatically load existing data on page load
df = load_data(csv_file_path)

# Show the most up-to-date statistics if data is present
if df is not None:
    st.write("## Current Statistics")

    # Display city and country statistics
    if os.path.exists('generated_city_statistics_from_csv.html'):
        with open('generated_city_statistics_from_csv.html', 'r', encoding='utf-8') as file:
            stats_content = file.read()
            st.write("### City and Country Statistics")
            st.components.v1.html(stats_content, height=800, scrolling=True)

    # Display the map
    if os.path.exists('activity_map.html'):
        with open('activity_map.html', 'r', encoding='utf-8') as file:
            map_content = file.read()
            st.write("### Activity Map")
            st.components.v1.html(map_content, height=600, scrolling=True)

    # Display the runs list
    if os.path.exists('runs_list.html'):
        with open('runs_list.html', 'r', encoding='utf-8') as file:
            runs_list_content = file.read()
            st.write("### Runs List")
            st.components.v1.html(runs_list_content, height=800, scrolling=True)

# Button to update the data
if st.button('Update Data'):
    update_data()
    # Use query params to force a rerun
    st.experimental_set_query_params(rerun=True)

# Handle the case where there is no existing data
if df is None:
    st.write("No existing data found. Please update the data to fetch the latest activities.")

# Sidebar for manual update
st.sidebar.header("Data Management")
if st.sidebar.button('Force Update Data from Strava'):
    update_data()
    # Use query params to force a rerun
    st.experimental_set_query_params(rerun=True)