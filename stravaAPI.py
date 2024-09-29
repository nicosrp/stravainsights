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

import requests
import os
import gpxpy
import polyline
import streamlit as st

def fetch_activities_and_gpx():
    # Create the GPX folder if it doesn't exist
    if not os.path.exists(gpx_folder):
        os.makedirs(gpx_folder)

    # Fetch activities using the Strava API (access token assumed to be fetched already)
    headers = {'Authorization': f'Bearer {access_token}'}
    activities_response = requests.get(
        'https://www.strava.com/api/v3/athlete/activities',
        headers=headers
    )

    if activities_response.status_code != 200:
        st.write(f"Error fetching activities: {activities_response.status_code}")
        return

    activities = activities_response.json()

    # Iterate through activities to generate GPX files
    for activity in activities:
        activity_id = activity['id']
        polyline_str = activity.get('map', {}).get('summary_polyline')

        # Skip if no polyline is found
        if not polyline_str:
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


# Testing function for debugging
if __name__ == "__main__":
    fetch_activities_and_gpx()