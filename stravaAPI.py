import os
import requests
import pandas as pd
import gpxpy
import gpxpy.gpx
import polyline
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client_id = os.getenv('STRAVA_CLIENT_ID')
client_secret = os.getenv('STRAVA_CLIENT_SECRET')
refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')

# Fetch activities and create missing GPX files
def fetch_activities_and_gpx():
    # Step 1: Get an access token using the refresh token
    try:
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
            print(f"Failed to obtain access token. Response: {token_response.json()}")
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

        # Step 3: Check for missing GPX files and create them
        gpx_folder = 'API_GPX_FILES'
        os.makedirs(gpx_folder, exist_ok=True)
        included_activity_ids = [os.path.splitext(filename)[0] for filename in os.listdir(gpx_folder)]

        for activity_id in df['id']:
            if str(activity_id) not in included_activity_ids:
                # Fetch the activity details to get the polyline
                url = f"https://www.strava.com/api/v3/activities/{activity_id}"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    activity_data = response.json()
                    polyline_str = activity_data['map']['summary_polyline']
                    
                    # Decode polyline to get coordinates
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

                    # Save GPX file
                    with open(f'{gpx_folder}/{activity_id}.gpx', 'w') as f:
                        f.write(gpx.to_xml())
                    
                    print(f'GPX file saved as {activity_id}.gpx')
                else:
                    print(f"Failed to get activity data for {activity_id}: {response.status_code}")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

# Call the function (for testing, this can be removed when used in Streamlit)
if __name__ == "__main__":
    fetch_activities_and_gpx()
