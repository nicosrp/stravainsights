import os
import gpxpy
import pandas as pd
import folium
import numpy as np
from datetime import datetime
from geopy.geocoders import Nominatim
from collections import defaultdict

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

# Generate statistics and save to HTML
def generate_statistics_html(df, output_file='generated_statistics.html'):
    # Filter only "Run" activities
    df_runs = df[df['type'] == 'Run']

    # Calculate total runs and distance
    total_runs = len(df_runs)
    total_distance_km = df_runs['distance'].sum() / 1000
    average_distance_per_run_km = total_distance_km / total_runs

    # Extract activities for the current year
    current_year = datetime.now().year
    df_runs['start_date'] = pd.to_datetime(df_runs['start_date_local'], errors='coerce')
    df_current_year = df_runs[df_runs['start_date'].dt.year == current_year]

    # Calculate runs and distance for the current year
    total_runs_current_year = len(df_current_year)
    total_distance_current_year_km = df_current_year['distance'].sum() / 1000
    average_distance_per_run_current_year_km = (
        total_distance_current_year_km / total_runs_current_year if total_runs_current_year > 0 else 0
    )

    # Date of the last run
    last_run_date = df_runs['start_date'].max().strftime('%d.%m.%Y')

    # Generate HTML content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
        </style>
    </head>
    <body>
        <p><strong>Total Runs:</strong> {total_runs}</p>
        <p><strong>Total Distance (km):</strong> {total_distance_km:.3f}</p>
        <p><strong>Average Distance per Run (km):</strong> {average_distance_per_run_km:.3f}</p>
        <br>
        <p><strong>Total Runs, This Year:</strong> {total_runs_current_year}</p>
        <p><strong>Total Distance, This Year (km):</strong> {total_distance_current_year_km:.3f}</p>
        <p><strong>Average Distance per Run, This Year (km):</strong> {average_distance_per_run_current_year_km:.3f}</p>
        <br>
        <p><strong>Date of Last Run:</strong> {last_run_date}</p>
    </body>
    </html>
    """
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)

# Create map and city/country statistics
def generate_map_and_statistics(df, gpx_folder, output_map='activity_map.html', output_stats='generated_city_statistics_from_csv.html'):
    geolocator = Nominatim(user_agent="city_locator")
    city_distances = defaultdict(lambda: {'total_distance_km': 0, 'run_count': 0})
    country_distances = defaultdict(lambda: {'total_distance_km': 0, 'run_count': 0})
    activity_map = folium.Map(location=[55.6761, 12.5683], zoom_start=11, tiles='cartodb positron')
    tracks_data = []

    # Iterate over GPX files
    for file_name in os.listdir(gpx_folder):
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
                    track_points = [(point.latitude, point.longitude, point.elevation, point.time) 
                                    for point in gpx.tracks[0].segments[0].points]
                    tracks_data.append((track_points, activity_id, start_time))

                    point = gpx.tracks[0].segments[0].points[0]
                    latitude, longitude = point.latitude, point.longitude

                    location = geolocator.reverse((latitude, longitude), exactly_one=True, timeout=10)
                    city, country = get_city_and_country(location)

                    total_distance_km = activity_data['distance'].values[0] / 1000
                    if city:
                        city_distances[city]['total_distance_km'] += total_distance_km
                        city_distances[city]['run_count'] += 1
                    if country:
                        country_distances[country]['total_distance_km'] += total_distance_km
                        country_distances[country]['run_count'] += 1

    # Sort tracks and create map
    tracks_data.sort(key=lambda x: x[2])
    for idx, (track_points, activity_id, start_time) in enumerate(tracks_data):
        activity_data = df[df['id'] == int(activity_id)]
        total_distance_km = activity_data['distance'].values[0] / 1000
        total_time_seconds = activity_data['moving_time'].values[0]
        avg_pace_seconds_per_km = total_time_seconds / total_distance_km if total_distance_km > 0 else 0
        avg_pace_minutes = int(avg_pace_seconds_per_km // 60)
        avg_pace_seconds = int(avg_pace_seconds_per_km % 60)
        run_date = start_time.to_pydatetime().strftime("%Y-%m-%d")
        run_number = idx + 1

        popup_text = (f"Run Number: {run_number}<br>"
                      f"Date: {run_date}<br>"
                      f"Total Distance: {total_distance_km:.3f} km<br>"
                      f"Pace: {avg_pace_minutes}:{avg_pace_seconds:02d} min/km")
        points = [(point[0], point[1]) for point in track_points]
        folium.PolyLine(points, color='red', weight=2.5, opacity=1, tooltip=popup_text).add_to(activity_map)

    activity_map.save(output_map)

    # Generate city and country statistics HTML
    stats_html_content = "<div class='city-stats'>\n<h2>City Statistics</h2>\n"
    for index, (city, stats) in enumerate(sorted(city_distances.items(), key=lambda x: x[1]['total_distance_km'], reverse=True)):
        stats_html_content += f"<p>{index + 1}. <strong>{city}</strong>: {stats['total_distance_km']:.3f} km ({stats['run_count']} Runs)</p>\n"

    stats_html_content += "<br><br><h2>Country Statistics</h2>\n"
    for index, (country, stats) in enumerate(sorted(country_distances.items(), key=lambda x: x[1]['total_distance_km'], reverse=True)):
        stats_html_content += f"<p>{index + 1}. <strong>{country}</strong>: {stats['total_distance_km']:.3f} km ({stats['run_count']} Runs)</p>\n"
    stats_html_content += "</div>"

    with open(output_stats, 'w', encoding='utf-8') as file:
        file.write(stats_html_content)

# Generate the run list in a sortable HTML table
def generate_runs_list_html(df, gpx_folder, output_file='runs_list.html'):
    runs_data = []
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
                const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
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
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)