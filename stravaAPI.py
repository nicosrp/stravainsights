import requests
import os
import gpxpy
import polyline
import pandas as pd

# Paths to files and folders
csv_file_path = 'strava_activities.csv'
gpx_folder = 'API_GPX_FILES'
os.makedirs(gpx_folder, exist_ok=True)  # Ensure the GPX folder exists

def fetch_activities_and_gpx():
    # Use your environment or secrets for tokens
    access_token = os.getenv('STRAVA_ACCESS_TOKEN')  # Adjust to retrieve access token securely

    if not access_token:
        print("Access token is missing.")
        return

    # Strava API base URL
    api_base_url = 'https://www.strava.com/api/v3/'

    # Headers for API requests
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Pagination parameters
    page = 1
    per_page = 200  # Max number of activities per page
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
            break  # Exit loop if no more activities

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