import os
import gpxpy
import folium
import pandas as pd
from collections import defaultdict
from datetime import datetime
from geopy.geocoders import Nominatim

# Paths to GPX files and CSV file
gpx_folder = 'API_GPX_FILES'
csv_file_path = 'strava_activities.csv'

# Helper function to extract city and country names from location data
def get_city_and_country(location):
    city, country = None, None
    if location and location.raw and 'address' in location.raw:
        address = location.raw['address']
        city = address.get('city') or address.get('town') or address.get('village')
        country = address.get('country', 'Unknown')
    return city, country

# Function to update the map and statistics incrementally
def update_map_and_statistics():
    # Load the existing CSV data
    df = pd.read_csv(csv_file_path)
    df['start_date_local'] = pd.to_datetime(df['start_date_local'])
    
    # Load the list of GPX files already processed
    existing_gpx_files = set(os.listdir(gpx_folder))
    
    # Initialize map and statistics
    activity_map = folium.Map(location=[55.6761, 12.5683], zoom_start=11, tiles='cartodb positron')
    geolocator = Nominatim(user_agent="city_locator")
    city_distances = defaultdict(lambda: {'total_distance_km': 0, 'run_count': 0})
    country_distances = defaultdict(lambda: {'total_distance_km': 0, 'run_count': 0})
    new_tracks_data = []

    # Iterate over new GPX files to update statistics and map
    for file_name in existing_gpx_files:
        if file_name.endswith('.gpx'):
            activity_id = file_name.replace('.gpx', '')
            activity_data = df[df['id'] == int(activity_id)]
            if activity_data.empty:
                continue
            
            start_time = pd.to_datetime(activity_data['start_date_local'].values[0])
            file_path = os.path.join(gpx_folder, file_name)

            with open(file_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                if gpx.tracks and gpx.tracks[0].segments and gpx.tracks[0].segments[0].points:
                    track_points = [(point.latitude, point.longitude) for point in gpx.tracks[0].segments[0].points]
                    new_tracks_data.append((track_points, activity_id, start_time))

                    # Extract the first track point for location
                    point = gpx.tracks[0].segments[0].points[0]
                    latitude, longitude = point.latitude, point.longitude
                    
                    # Use geopy to get the city and country names
                    location = geolocator.reverse((latitude, longitude), exactly_one=True, timeout=10)
                    city, country = get_city_and_country(location)

                    total_distance_km = activity_data['distance'].values[0] / 1000
                    if city:
                        city_distances[city]['total_distance_km'] += total_distance_km
                        city_distances[city]['run_count'] += 1

                    if country:
                        country_distances[country]['total_distance_km'] += total_distance_km
                        country_distances[country]['run_count'] += 1

    # Add new tracks to the map
    for idx, (track_points, activity_id, start_time) in enumerate(new_tracks_data):
        activity_data = df[df['id'] == int(activity_id)]
        total_distance_km = activity_data['distance'].values[0] / 1000
        total_time_seconds = activity_data['moving_time'].values[0]
        avg_pace_seconds_per_km = total_time_seconds / total_distance_km if total_distance_km > 0 else 0
        avg_pace_minutes = int(avg_pace_seconds_per_km // 60)
        avg_pace_seconds = int(avg_pace_seconds_per_km % 60)
        run_date = start_time.strftime("%Y-%m-%d")
        
        # Popup text for the polyline
        popup_text = (f"Run ID: {activity_id}<br>"
                      f"Date: {run_date}<br>"
                      f"Total Distance: {total_distance_km:.3f} km<br>"
                      f"Pace: {avg_pace_minutes}:{avg_pace_seconds:02d} min/km")

        # Add polyline to the map
        points = [(point[0], point[1]) for point in track_points]
        folium.PolyLine(points, color='red', weight=2.5, opacity=1, tooltip=popup_text).add_to(activity_map)

    # Save the updated map
    activity_map.save('activity_map.html')

    # Update city and country statistics in the HTML
    stats_html_content = "<div class='city-stats'>\n<h2>City Statistics</h2>\n"
    for index, (city, stats) in enumerate(sorted(city_distances.items(), key=lambda x: x[1]['total_distance_km'], reverse=True)):
        stats_html_content += f"<p>{index + 1}. <strong>{city}</strong>: {stats['total_distance_km']:.3f} km ({stats['run_count']} Runs)</p>\n"
    
    stats_html_content += "<br><br><h2>Country Statistics</h2>\n"
    for index, (country, stats) in enumerate(sorted(country_distances.items(), key=lambda x: x[1]['total_distance_km'], reverse=True)):
        stats_html_content += f"<p>{index + 1}. <strong>{country}</strong>: {stats['total_distance_km']:.3f} km ({stats['run_count']} Runs)</p>\n"
    stats_html_content += "</div>"

    # Save the updated statistics HTML
    with open('generated_city_statistics_from_csv.html', 'w', encoding='utf-8') as file:
        file.write(stats_html_content)
    
    print(f"Updated city and country statistics.")

# Function to update the runs list incrementally
def update_runs_list_html():
    df = pd.read_csv(csv_file_path)
    df['start_date_local'] = pd.to_datetime(df['start_date_local'])

    runs_data = []

    # Iterate over GPX files
    for file_name in os.listdir(gpx_folder):
        if file_name.endswith('.gpx'):
            activity_id = file_name.replace('.gpx', '')
            activity_data = df[df['id'] == int(activity_id)]
            if activity_data.empty:
                continue

            start_time = pd.to_datetime(activity_data['start_date_local'].values[0])
            total_distance_km = activity_data['distance'].values[0] / 1000
            total_time_seconds = activity_data['moving_time'].values[0]

            # Calculate average pace
            avg_pace_seconds_per_km = total_time_seconds / total_distance_km if total_distance_km > 0 else 0
            avg_pace_minutes = int(avg_pace_seconds_per_km // 60)
            avg_pace_seconds = int(avg_pace_seconds_per_km % 60)

            # Generate time strings for the HTML table
            run_date = start_time.strftime("%Y-%m-%d")
            end_time = start_time + pd.to_timedelta(total_time_seconds, unit='s')
            time_str = f"{start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')} (Time: {pd.to_datetime(total_time_seconds, unit='s').strftime('%H:%M:%S')})"

            # Append to the runs_data list
            runs_data.append((activity_id, run_date, time_str, total_distance_km, f"{avg_pace_minutes}:{avg_pace_seconds:02d} min/km", start_time))

    # Sort runs by date in ascending order to assign correct run numbers
    runs_data.sort(key=lambda x: x[5])  # Sort by start_time

    # Assign run numbers
    for idx, run in enumerate(runs_data):
        runs_data[idx] = (idx + 1,) + run[1:]  # Insert the run number at the beginning

    # Sort runs by date in descending order for the HTML table
    runs_data.sort(key=lambda x: x[5], reverse=True)  # Sort by start_time in descending order

    # Generate the HTML content
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; color: #333; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #f4f4f4; cursor: pointer; }
            th.sort-asc::after { content: " \\2191"; }
            th.sort-desc::after { content: " \\2193"; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                                const comparer = (idx, asc, type) => (a, b) => {
                    let v1 = getCellValue(asc ? a : b, idx);
                    let v2 = getCellValue(asc ? b : a, idx);
                    if (type === 'date') {
                        v1 = new Date(v1);
                        v2 = new Date(v2);
                    } else if (type === 'pace') {
                        const [min1, sec1] = v1.split(':');
                        const [min2, sec2] = v2.split(':');
                        v1 = parseInt(min1) * 60 + parseInt(sec1);
                        v2 = parseInt(min2) * 60 + parseInt(sec2);
                    } else if (!isNaN(v1) && !isNaN(v2)) {
                        v1 = parseFloat(v1);
                        v2 = parseFloat(v2);
                    }
                    return v1 > v2 ? 1 : v1 < v2 ? -1 : 0;
                };

                document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {
                    const table = th.closest('table');
                    const type = th.getAttribute('data-type');
                    Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
                        .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc, type))
                        .forEach(tr => table.appendChild(tr));
                    th.classList.toggle('sort-asc', this.asc);
                    th.classList.toggle('sort-desc', !this.asc);
                })));
            });
        </script>
    </head>
    <body>
        <table>
            <tr>
                <th data-type="number">Run Number</th>
                <th data-type="date">Date</th>
                <th data-type="text">Time</th>
                <th data-type="number">Distance (km)</th>
                <th data-type="pace">Average Pace (min/km)</th>
            </tr>
    """

    # Add rows to the table
    for run in runs_data:
        run_number, run_date, time_str, distance_km, pace, _ = run
        html_content += f"""
            <tr>
                <td>{run_number}</td>
                <td>{run_date}</td>
                <td>{time_str}</td>
                <td>{distance_km:.3f}</td>
                <td>{pace}</td>
            </tr>
        """

    # Close the HTML content
    html_content += """
        </table>
    </body>
    </html>
    """

    # Save the generated HTML content to a file
    with open('runs_list.html', 'w', encoding='utf-8') as file:
        file.write(html_content)
    
    print("Updated runs list HTML.")

# Function to be called by the Streamlit app to perform incremental updates
def generate_statistics_html():
    # Call update functions to incrementally update files
    update_map_and_statistics()
    update_runs_list_html()

               
