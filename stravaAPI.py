import os
import requests
import pandas as pd
import gpxpy
import gpxpy.gpx
import polyline
import streamlit as st

# Accessing secrets using Streamlit
client_id = st.secrets["STRAVA_CLIENT_ID"]
client_secret = st.secrets["STRAVA_CLIENT_SECRET"]
refresh_token = st.secrets["STRAVA_REFRESH_TOKEN"]

# Directory to store GPX files
gpx_folder = 'API_GPX_FILES'

def fetch_activities_and_gpx():
    try:
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
        access_token = token_response.json().get('access_token')

        if not access_token:
            st.write(f"Failed to obtain access token. Response: {token_response.json()}")
            return

        # Step 2: Use the access token to fetch the activities
        headers = {'Authorization': f'Bearer {access_token}'}
        activities_response = requests.get(
            url='https://www.strava.com/api/v3/athlete/activities',
            headers=headers
        )
        activities_response.raise_for_status()
        activities = activities_response.json()

        # Process and save activities to CSV
        activities_data = []
        for activity in activities:
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
        df.to_csv('strava_activities.csv', index=False)
        st.write("Activities successfully fetched and saved to 'strava_activities.csv'.")

        # Step 3: Generate GPX files for activities
        if not os.path.exists(gpx_folder):
            os.makedirs(gpx_folder)

        for activity in activities:
            activity_id = activity['id']
            polyline_str = activity['map']['summary_polyline']
            if not polyline_str:
                st.write(f"No polyline found for activity {activity_id}")
                continue  # Skip activities without a polyline

            # Decode polyline and generate GPX file
            coordinates = polyline.decode(polyline_str)
            if not coordinates:
                st.write(f"No coordinates decoded for activity {activity_id}")
                continue

            gpx = gpxpy.gpx.GPX()
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(gpx_track)
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            for coord in coordinates:
                lat, lon = coord
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

            gpx_filename = f'{gpx_folder}/{activity_id}.gpx'
            with open(gpx_filename, 'w') as f:
                f.write(gpx.to_xml())
                st.write(f"GPX file saved as {gpx_filename}")

    except requests.exceptions.HTTPError as http_err:
        st.write(f"HTTP error occurred: {http_err}")
        st.write(f"Response: {token_response.text if 'token_response' in locals() else 'No response'}")
    except Exception as err:
        st.write(f"An error occurred: {err}")

# Testing function for debugging
if __name__ == "__main__":
    fetch_activities_and_gpx()