import streamlit as st
import pandas as pd
import os
from stravaAPI import fetch_activities_and_gpx  # Function to fetch activities and generate GPX files
from stravaDash import generate_map_and_statistics, generate_runs_list_html  # Functions to create HTML files

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
    # Debugging: Add print statements to track function calls
    print("Running fetch_activities_and_gpx...")
    fetch_activities_and_gpx()
    print("Finished fetching activities and updating GPX files.")
    
    st.success('Data fetched and GPX files updated. Regenerating statistics...')
    
    # Generate map and statistics
    generate_map_and_statistics()
    generate_runs_list_html()
    
    st.success('All files have been updated!')

# Automatically update data when the app starts
if 'data_updated' not in st.session_state:
    st.write("Updating data on app startup...")
    update_data()  # Call the update_data function
    st.session_state['data_updated'] = True  # Set flag to avoid repeating updates during the same session

# Streamlit app layout
st.title("Strava Activity Analysis")

# Automatically load existing data on page load
df = load_data(csv_file_path)

# Show the most up-to-date statistics if data is present
if df is not None:
    st.write("## Current Statistics")

    # Display the map
    if os.path.exists('activity_map.html'):
        with open('activity_map.html', 'r', encoding='utf-8') as file:
            map_content = file.read()
            st.write("### Activity Map")
            st.components.v1.html(map_content, height=600, scrolling=True)

    # Display city and country statistics
    if os.path.exists('generated_city_statistics_from_csv.html'):
        with open('generated_city_statistics_from_csv.html', 'r', encoding='utf-8') as file:
            stats_content = file.read()
            st.write("### City and Country Statistics")
            st.components.v1.html(stats_content, height=400, scrolling=True)

    # Display the runs list
    if os.path.exists('runs_list.html'):
        with open('runs_list.html', 'r', encoding='utf-8') as file:
            runs_list_content = file.read()
            st.write("### Runs List")
            st.components.v1.html(runs_list_content, height=400, scrolling=True)

    # Button to update the data
    if st.button('Update Data'):
        update_data()
else:
    st.write("No existing data found. Please update the data to fetch the latest activities.")

# Optionally, allow user to update data if a new run was uploaded on Strava
st.sidebar.header("Data Management")
if st.sidebar.button('Force Update Data from Strava'):
    update_data()