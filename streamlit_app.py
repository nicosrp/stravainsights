import streamlit as st
import pandas as pd
import os
from stravaAPI import fetch_activities_and_gpx  # Imports function to fetch activities and generate GPX files
from stravaDash import generate_map_and_statistics, generate_runs_list_html  # Imports functions to create HTML files

# Set paths for data
gpx_folder = 'API_GPX_FILES'
csv_file_path = 'strava_activities.csv'

# Helper function to load CSV file
def load_data(file_path):
    return pd.read_csv(file_path)

# Streamlit app layout
st.title("Strava Activity Analysis")

# Sidebar for file upload and data fetching
st.sidebar.header("Data Management")
st.sidebar.write("You can either upload a new activities CSV file or fetch the latest data from Strava.")

# Option to fetch latest data from Strava
if st.sidebar.button('Fetch Latest Data from Strava'):
    st.write("Fetching data from Strava and creating missing GPX files...")
    fetch_activities_and_gpx()
    st.success('Latest data fetched and GPX files updated.')

# Option to upload a new activities CSV file
csv_upload = st.sidebar.file_uploader("Upload a Strava Activities CSV", type=['csv'])
if csv_upload:
    with open(csv_file_path, "wb") as f:
        f.write(csv_upload.getbuffer())
    st.success("CSV file uploaded successfully!")

# Main content: Load and display data
if os.path.exists(csv_file_path):
    df = load_data(csv_file_path)
    st.write("## Data Preview")
    st.dataframe(df.head())

    # Generate Statistics Section
    if st.button('Generate Statistics'):
        generate_map_and_statistics()
        st.success('Map and city/country statistics generated!')

        # Display the map
        with open('activity_map.html', 'r', encoding='utf-8') as file:
            map_content = file.read()
            st.write("### Activity Map")
            st.components.v1.html(map_content, height=600, scrolling=True)

        # Display the city and country statistics
        with open('generated_city_statistics_from_csv.html', 'r', encoding='utf-8') as file:
            stats_content = file.read()
            st.write("### City and Country Statistics")
            st.components.v1.html(stats_content, height=400, scrolling=True)

    # Generate Runs List Section
    if st.button('Generate Runs List'):
        generate_runs_list_html()
        st.success('Runs list generated!')

        # Display the runs list
        with open('runs_list.html', 'r', encoding='utf-8') as file:
            runs_list_content = file.read()
            st.write("### Runs List")
            st.components.v1.html(runs_list_content, height=400, scrolling=True)

else:
    st.write("Please upload a CSV file or fetch data from Strava to get started.")
