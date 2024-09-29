import os
import requests
import gpxpy
import polyline
import streamlit as st
import pandas as pd

# Set paths for GPX folder and CSV file
gpx_folder = 'API_GPX_FILES'
csv_file_path = 'strava_activities.csv'

# Define your Strava API credentials
client_id = st.secrets["STRAVA_CLIENT_ID"]
client_secret = st.secrets["STRAVA_CLIENT_SECRET"]
refresh_token = st.secrets["STRAVA_REFRESH_TOKEN"]

def fetch_activities_and_gpx():
    try:
        st.write("Fetching data from Strava and creating missing GPX files...")

        # Step 1: Get an access token using the refresh token
        token_response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )

        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get('access_token')

        # Debug: Ensure access token is retrieved
        if not access_token:
            st.write(f"Failed to obtain access token. Response: {token_data}")
            return

        # Step 2: Create the GPX folder if it does not exist
        if not os.path.exists(gpx_folder):
            os.makedirs(gpx_folder)

        # Step 3: Identify missing GPX files
        existing_gpx_files = set(f.replace('.gpx', '') for f in os.listdir(gpx_folder) if f.endswith('.gpx'))

        # Step 4: Fetch activities from Strava with pagination
        headers = {'Authorization': f'Bearer {access_token}'}
        page = 1
        activities = []

        while True:
            activities_response = requests.get(
                url='https://www.strava.com/api/v3/athlete/activities',
                headers=headers,
                params={'page': page, 'per_page': 200}  # Adjust 'per_page' to your preference (max 200)
            )

            if activities_response.status_code != 200:
                st.write(f"Error fetching activities: {activities_response.status_code}")
                st.write(f"Response: {activities_response.text}")
                break

            new_activities = activities_response.json()
            if not new_activities:
                # Break if there are no more activities to fetch
                break

            activities.extend(new_activities)
            page += 1

        updated_gpx_files = 0
        activities_data = []

        # Step 5: Generate GPX files for missing activities
        for activity in activities:
            activity_id = str(activity['id'])
            activities_data.append({
                'id': activity_id,
                'name': activity['name'],
                'type': activity['type'],
                'start_date_local': activity['start_date_local'],
                'distance': activity['distance'],
                'moving_time': activity['moving_time'],
                'elapsed_time': activity['elapsed_time'],
                'total_elevation_gain': activity['total_elevation_gain']
            })

            # Check if the GPX file for this activity already exists
            if activity_id in existing_gpx_files:
                continue

            polyline_str = activity.get('map', {}).get('summary_polyline')
            if not polyline_str:
                st.write(f"No polyline found for activity {activity_id}. Skipping...")
                continue

            # Decode polyline and create GPX file
            coordinates = polyline.decode(polyline_str)
            gpx = gpxpy.gpx.GPX()
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(gpx_track)
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            for coord in coordinates:
                lat, lon = coord
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

            # Save the GPX file
            gpx_filename = os.path.join(gpx_folder, f'{activity_id}.gpx')
            with open(gpx_filename, 'w') as gpx_file:
                gpx_file.write(gpx.to_xml())
                st.write(f"Saved GPX file: {gpx_filename}")
                updated_gpx_files += 1

        # Step 6: Save activities to CSV
        df = pd.DataFrame(activities_data)
        df.to_csv(csv_file_path, index=False)
        st.write(f"Updated '{csv_file_path}' with the latest activities.")

        if updated_gpx_files == 0:
            st.write("No new GPX files were created. The folder is up to date.")
        else:
            st.write(f"Updated GPX folder with {updated_gpx_files} new GPX files.")

    except requests.exceptions.HTTPError as http_err:
        st.write(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.write(f"An error occurred: {err}")