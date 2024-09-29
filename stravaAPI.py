import requests
import os
import gpxpy
import polyline
import streamlit as st

# Define your Strava API credentials (you can use Streamlit secrets here)
client_id = st.secrets["STRAVA_CLIENT_ID"]
client_secret = st.secrets["STRAVA_CLIENT_SECRET"]
refresh_token = st.secrets["STRAVA_REFRESH_TOKEN"]

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
        token_data = token_response.json()

        # Extract the access token
        access_token = token_data.get('access_token')
        
        # Debugging: Verify if access_token is successfully fetched
        if not access_token:
            st.write(f"Failed to obtain access token. Response: {token_data}")
            return

        # Print token data to debug
        st.write("Token Data:", token_data)

        # Step 2: Create GPX folder if it does not exist
        gpx_folder = 'API_GPX_FILES'
        if not os.path.exists(gpx_folder):
            os.makedirs(gpx_folder)

        # Step 3: Use the access token to fetch activities
        headers = {'Authorization': f'Bearer {access_token}'}
        activities_response = requests.get(
            url='https://www.strava.com/api/v3/athlete/activities',
            headers=headers
        )

        if activities_response.status_code != 200:
            st.write(f"Error fetching activities: {activities_response.status_code}")
            st.write(f"Response: {activities_response.text}")
            return

        activities = activities_response.json()

        # Process each activity and generate GPX files
        for activity in activities:
            activity_id = activity['id']
            polyline_str = activity.get('map', {}).get('summary_polyline')

            if not polyline_str:
                st.write(f"No polyline found for activity {activity_id}. Skipping...")
                continue

            # Decode polyline and generate GPX
            coordinates = polyline.decode(polyline_str)
            gpx = gpxpy.gpx.GPX()
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(gpx_track)
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            for coord in coordinates:
                lat, lon = coord
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

            # Save GPX file
            gpx_filename = os.path.join(gpx_folder, f'{activity_id}.gpx')
            with open(gpx_filename, 'w') as gpx_file:
                gpx_file.write(gpx.to_xml())
                st.write(f"Saved GPX file: {gpx_filename}")

    except requests.exceptions.HTTPError as http_err:
        st.write(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.write(f"An error occurred: {err}")
