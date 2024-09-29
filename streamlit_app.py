import streamlit as st
import pandas as pd
import os
from stravaDash import generate_statistics_html, generate_map_and_statistics, generate_runs_list_html
from stravaAPI import fetch_activities_and_gpx  # Updated function to fetch activities and GPX files

# Set paths for data
gpx_folder = 'API_GPX_FILES'
csv_file_path = 'strava_activities.csv'

# Streamlit app layout
st.title("Strava Activity Analysis Dashboard")

# Sidebar for data management
st.sidebar.header("Data Management")
fetch_data = st.sidebar.button("Fetch Latest Data and GPX Files from Strava")

# Helper function to load CSV file
def load_data(file_path):
    return pd.read_csv(file_path)

# Fetch data if the button is clicked
if fetch_data:
    # Fetch activities and generate GPX files
    st.info("Fetching data from Strava and creating missing GPX files...")
    try:
        fetch_activities_and_gpx()  # Call the updated function
        st.success("Successfully fetched the latest activities and created missing GPX files.")
    except Exception as e:
        st.error(f"Failed to fetch data or generate GPX files: {e}")

# Check if the CSV file exists
if os.path.exists(csv_file_path):
    # Load the CSV data
    df = load_data(csv_file_path)
    st.write("## Data Preview")
    st.dataframe(df.head())

    # Generate and display the latest statistics
    if st.button('Show Current Statistics'):
        # Generate all the HTML files using the current CSV data
        generate_statistics_html(df)
        generate_map_and_statistics(df, gpx_folder)
        generate_runs_list_html(df, gpx_folder)

        # Display Statistics
        with open('generated_statistics.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
            st.write("### Overall Statistics")
            st.components.v1.html(html_content, height=300, scrolling=True)

        # Display Map
        with open('activity_map.html', 'r', encoding='utf-8') as file:
            map_content = file.read()
            st.write("### Activity Map")
            st.components.v1.html(map_content, height=600, scrolling=True)

        # Display City and Country Statistics
        with open('generated_city_statistics_from_csv.html', 'r', encoding='utf-8') as file:
            stats_content = file.read()
            st.write("### City and Country Statistics")
            st.components.v1.html(stats_content, height=400, scrolling=True)

        # Display Runs List
        with open('runs_list.html', 'r', encoding='utf-8') as file:
            runs_list_content = file.read()
            st.write("### Runs List")
            st.components.v1.html(runs_list_content, height=400, scrolling=True)
else:
    st.write("Upload a CSV file to get started or fetch the latest data from Strava.")