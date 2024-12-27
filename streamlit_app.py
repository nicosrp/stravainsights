import streamlit as st
import pandas as pd
import os
from stravaAPI import fetch_activities_and_gpx  # Function to fetch activities and generate GPX files
from stravaDash import * # Import the new function
#from update_strava_data import update_strava_data

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
def update_data(incremental=True):
    st.write("Fetching data from Strava and creating missing GPX files...")
    fetch_activities_and_gpx()
    st.success('Data fetched and GPX files updated. Regenerating statistics...')
    generate_map_and_statistics(incremental=incremental)  # Pass the incremental flag
    generate_runs_list_html()  # This function can be optimized similarly
    generate_summary_html()
    st.success('All files have been updated!')
    st.session_state['data_updated'] = True

# Set the page configuration
st.set_page_config(layout="wide", page_title="Strava Activity Analysis")

# Initialize session state for managing update process
if 'data_updated' not in st.session_state:
    st.session_state['data_updated'] = False
if 'initial_update_done' not in st.session_state:
    st.session_state['initial_update_done'] = False

# Streamlit app layout
st.title("My Strava Activities")

# Load existing data on page load
df = load_data(csv_file_path)

# Show the most up-to-date statistics if data is present
if df is not None:
    if os.path.exists('generated_summary.html'):
        with open('generated_summary.html', 'r', encoding='utf-8') as file:
            summary_content = file.read()
            st.write("### General Stats")
            st.components.v1.html(summary_content, height=300, scrolling=True)  # Adjust height as needed
        # Display city and country statistics
    if os.path.exists('generated_city_statistics_from_csv.html'):
        with open('generated_city_statistics_from_csv.html', 'r', encoding='utf-8') as file:
            stats_content = file.read()
            st.write("### Location Stats")
            st.components.v1.html(stats_content, height=800, scrolling=True)

    # Display the map
    if os.path.exists('activity_map.html'):
        with open('activity_map.html', 'r', encoding='utf-8') as file:
            map_content = file.read()
            st.write("### Spatial Distribution Map")
            st.text("This distribution map shows on which routes I have already been running around the world (zoomed into Copenhagen).")
            st.components.v1.html(map_content, height=600, scrolling=True)

    # Display the runs list
    if os.path.exists('runs_list.html'):
        with open('runs_list.html', 'r', encoding='utf-8') as file:
            runs_list_content = file.read()
            st.write("### List of All Runs")
            st.components.v1.html(runs_list_content, height=800, scrolling=True)

# Automatically update data if it's the first load and hasn't been updated
if not st.session_state['initial_update_done']:
    st.session_state['initial_update_done'] = True  # Set this to True to prevent repeated updates
    st.write("Performing initial data update...")
    update_data()  # Perform the initial update
    st.experimental_rerun()  # Rerun the app to reflect updated files

# Button to update the data
if st.button('Update Data'):
    update_data()
    st.experimental_set_query_params(updated=True)  # Reload the app to show updated files

# Handle the case where there is no existing data
if df is None:
    st.write("No existing data found. Please update the data to fetch the latest activities.")

# Sidebar for manual update
st.sidebar.header("Data Management")
if st.sidebar.button('Force Update Data from Strava'):
    update_data()
    st.experimental_set_query_params(updated=True)  # Reload the app to show updated files