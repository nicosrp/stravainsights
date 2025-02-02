import requests
import os
import gpxpy
import polyline
import pandas as pd
import streamlit as st

# Paths to files and folders
csv_file_path = 'strava_activities.csv'
gpx_folder = 'API_GPX_FILES'
os.makedirs(gpx_folder, exist_ok=True)  # Ensure the GPX folder exists

def update_strava_data():
    # Fetching secrets using Streamlit's secrets management
    client_id = st.secrets["STRAVA_CLIENT_ID"]
    client_secret = st.secrets["STRAVA_CLIENT_SECRET"]
    refresh_token = st.secrets["STRAVA_REFRESH_TOKEN"]

    # Step 1: Obtain an access token using the refresh token
    token_url = 'https://www.strava.com/oauth/token'
    response = requests.post(
        token_url,
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
    )

    if response.status_code != 200:
        print(f"Error fetching access token: {response.status_code}")
        print(f"Response: {response.json()}")
        return

    # Extract access token from the response
    access_token = response.json().get('access_token')

    if not access_token:
        print("Access token not found in the response.")
        return

    # Strava API base URL
    api_base_url = 'https://www.strava.com/api/v3/'

    # Headers for API requests
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Pagination parameters
    page = 1
    per_page = 200  # Fetch up to 200 activities per page
    all_activities = []

    # Fetch activities with pagination
    while True:
        response = requests.get(
            f"{api_base_url}athlete/activities",
            headers=headers,
            params={'page': page, 'per_page': per_page}
        )

        if response.status_code != 200:
            print(f"Error fetching activities: {response.status_code}")
            print(f"Response: {response.text}")
            break

        activities = response.json()
        if not activities:
            break  # No more activities to fetch

        all_activities.extend(activities)
        page += 1

    # Check if activities were fetched
    if not all_activities:
        print("No activities fetched from Strava. CSV will not be updated.")
        return

    # Convert activities to DataFrame
    activities_data = []
    for activity in all_activities:
        activities_data.append({
            'id': activity['id'],
            'name': activity['name'],
            'type': activity['type'],
            'start_date_local': activity['start_date_local'],
            'distance': activity['distance'],
            'moving_time': activity['moving_time'],
            'elapsed_time': activity['elapsed_time'],
            'total_elevation_gain': activity['total_elevation_gain']
        })

    df = pd.DataFrame(activities_data)
    if df.empty:
        print("Warning: DataFrame is empty. No data to write to CSV.")
        return

    # Save DataFrame to CSV
    df.to_csv(csv_file_path, index=False)
    print(f"Activities successfully saved to '{csv_file_path}'.")

    # Get existing GPX files in the folder
    existing_gpx_files = {f.replace('.gpx', '') for f in os.listdir(gpx_folder)}

    # Download missing GPX files
    for activity in all_activities:
        activity_id = str(activity['id'])

        # Skip if the GPX file already exists
        if activity_id in existing_gpx_files:
            continue

        # Fetch GPX data using Strava's API
        response = requests.get(f"{api_base_url}activities/{activity_id}", headers=headers)
        if response.status_code != 200:
            print(f"Failed to get activity data for {activity_id}: {response.status_code}")
            continue

        activity_data = response.json()
        if 'map' not in activity_data or 'summary_polyline' not in activity_data['map']:
            print(f"No polyline data for activity {activity_id}")
            continue

        polyline_str = activity_data['map']['summary_polyline']
        coordinates = polyline.decode(polyline_str)

        # Create GPX file
        gpx = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for coord in coordinates:
            lat, lon = coord
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

        # Save the GPX file
        gpx_file_path = os.path.join(gpx_folder, f'{activity_id}.gpx')
        with open(gpx_file_path, 'w') as f:
            f.write(gpx.to_xml())

        print(f'Saved GPX file: {gpx_file_path}')

    print("Successfully fetched the latest activities and created missing GPX files.")

if __name__ == "__main__":
    update_strava_data()

