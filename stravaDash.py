import os
import gpxpy
import pandas as pd
import folium
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from collections import defaultdict
import streamlit as st
from datetime import datetime
import time
import json

# Paths to files and folders
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

def generate_map_and_statistics(incremental=True):
    # Load the CSV file for activities
    df = pd.read_csv(csv_file_path)
    
    # Ensure that only "Run" activities are processed
    df_runs = df[df['type'] == 'Run']
    
    # Check if existing map file is present
    map_file_path = 'activity_map.html'
    if incremental and os.path.exists(map_file_path):
        processed_activities = set()  # Set of already processed activity IDs
        with open(map_file_path, 'r', encoding='utf-8') as map_file:
            content = map_file.read()
            for activity_id in df_runs['id']:
                if f"Run Number: {activity_id}" in content:  # Simple heuristic to check if activity exists
                    processed_activities.add(activity_id)
    else:
        processed_activities = set()
    
    # Initialize folium map or load the existing one
    if incremental and os.path.exists(map_file_path):
        activity_map = folium.Map(location=[55.6761, 12.5683], zoom_start=11, tiles='cartodb positron')
    else:
        activity_map = folium.Map(location=[55.6761, 12.5683], zoom_start=11, tiles='cartodb positron')

    # Process new GPX files
    for file_name in os.listdir(gpx_folder):
        if file_name.endswith('.gpx'):
            activity_id = file_name.replace('.gpx', '')
            if activity_id in processed_activities:  # Skip already processed activities
                continue

            activity_data = df[df['id'] == int(activity_id)]
            if activity_data.empty:
                continue

            start_time = pd.to_datetime(activity_data['start_date_local'].values[0])
            file_path = os.path.join(gpx_folder, file_name)

            with open(file_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                if gpx.tracks and gpx.tracks[0].segments and gpx.tracks[0].segments[0].points:
                    track_points = [(point.latitude, point.longitude) for point in gpx.tracks[0].segments[0].points]

                    # Generate popup and polyline
                    total_distance_km = activity_data['distance'].values[0] / 1000
                    total_time_seconds = activity_data['moving_time'].values[0]
                    avg_pace_seconds_per_km = total_time_seconds / total_distance_km if total_distance_km > 0 else 0
                    avg_pace_minutes = int(avg_pace_seconds_per_km // 60)
                    avg_pace_seconds = int(avg_pace_seconds_per_km % 60)
                    run_date = start_time.to_pydatetime().strftime("%d.%m.%Y")
                    run_number = activity_data['run_number'].values[0]

                    popup_text = (f"Run Number: {run_number}<br>"
                                  f"Date: {run_date}<br>"
                                  f"Total Distance: {total_distance_km:.3f} km<br>"
                                  f"Pace: {avg_pace_minutes}:{avg_pace_seconds:02d} min/km")
                    points = [(point[0], point[1]) for point in track_points]
                    folium.PolyLine(points, color='red', weight=2.5, opacity=1, tooltip=popup_text).add_to(activity_map)

    # Save the updated map
    activity_map.save(map_file_path)

    st.write(f"Map updated with {len(processed_activities)} processed activities.")


# Generate the run list in a sortable HTML table
def generate_runs_list_html():
    # Load the CSV file for activities
    df = pd.read_csv(csv_file_path)
    
    # Ensure only run activities are processed
    df_runs = df[df['type'] == 'Run']
    
    runs_data = []
    for file_name in os.listdir(gpx_folder):
        if file_name.endswith('.gpx'):
            activity_id = file_name.replace('.gpx', '')
            activity_data = df_runs[df_runs['id'] == int(activity_id)]
            if activity_data.empty:
                continue

            start_time = pd.to_datetime(activity_data['start_date_local'].values[0])
            total_distance_km = activity_data['distance'].values[0] / 1000
            total_time_seconds = activity_data['moving_time'].values[0]
            run_number = activity_data['run_number'].values[0]

            # Calculate average pace
            avg_pace_seconds_per_km = total_time_seconds / total_distance_km if total_distance_km > 0 else 0
            avg_pace_minutes = int(avg_pace_seconds_per_km // 60)
            avg_pace_seconds = int(avg_pace_seconds_per_km % 60)

            # Generate time strings for the HTML table
            run_date = start_time.strftime("%d.%m.%Y")
            end_time = start_time + pd.to_timedelta(total_time_seconds, unit='s')
            time_str = f"{start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')} (Time: {pd.to_datetime(total_time_seconds, unit='s').strftime('%H:%M:%S')})"

            # Append to the runs_data list
            runs_data.append((run_number, run_date, time_str, total_distance_km, f"{avg_pace_minutes}:{avg_pace_seconds:02d} min/km", start_time))

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
    with open('runs_list.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

    print("Run list HTML file generated: runs_list.html")

def generate_city_statistics_html(incremental=True):
    """
    Generate HTML file with statistics about running activities grouped by city and country.
    
    Parameters:
    incremental (bool): If True, will only process new GPX files that haven't been processed before
    """
    print("Starting to generate city statistics...")
    
    # Load the CSV file for activities
    df = pd.read_csv(csv_file_path)
    
    # Ensure that only "Run" activities are processed
    df_runs = df[df['type'] == 'Run']
    
    # Initialize geocoder for reverse geocoding
    geolocator = Nominatim(user_agent="strava_city_stats")
    
    # Path to cache file for statistics
    stats_cache_file = 'city_stats_cache.json'
    
    # Load existing statistics if incremental and file exists
    if incremental and os.path.exists(stats_cache_file):
        try:
            with open(stats_cache_file, 'r') as f:
                cache_data = json.load(f)
                city_stats = defaultdict(lambda: {'distance': 0, 'count': 0})
                country_stats = defaultdict(lambda: {'distance': 0, 'count': 0})
                
                # Restore city stats from cache
                for city, stats in cache_data.get('cities', {}).items():
                    city_stats[city]['distance'] = stats['distance']
                    city_stats[city]['count'] = stats['count']
                
                # Restore country stats from cache
                for country, stats in cache_data.get('countries', {}).items():
                    country_stats[country]['distance'] = stats['distance']
                    country_stats[country]['count'] = stats['count']
                
                # Get the list of already processed activities
                processed_activities = set(cache_data.get('processed_activities', []))
                print(f"Loaded cache with {len(processed_activities)} previously processed activities")
        except Exception as e:
            print(f"Error loading cache: {e}")
            # If there's an error loading the cache, start fresh
            city_stats = defaultdict(lambda: {'distance': 0, 'count': 0})
            country_stats = defaultdict(lambda: {'distance': 0, 'count': 0})
            processed_activities = set()
    else:
        # Start with empty stats
        city_stats = defaultdict(lambda: {'distance': 0, 'count': 0})
        country_stats = defaultdict(lambda: {'distance': 0, 'count': 0})
        processed_activities = set()
    
    # Cache for geocoding results to avoid redundant API calls
    geocoding_cache = {}
    
    # List to track newly processed activities
    newly_processed = []
    
    # Count for tracking progress
    gpx_files = [f for f in os.listdir(gpx_folder) if f.endswith('.gpx')]
    total_files = len(gpx_files)
    processed_files = 0
    skipped_files = 0
    
    # Process GPX files to extract location data
    for file_name in gpx_files:
        activity_id = file_name.replace('.gpx', '')
        
        # Skip if already processed and we're doing incremental update
        if incremental and activity_id in processed_activities:
            skipped_files += 1
            continue
            
        processed_files += 1
        if processed_files % 10 == 0:
            print(f"Processed {processed_files} new GPX files, skipped {skipped_files}...")
            
        try:
            activity_id_int = int(activity_id)
            activity_data = df_runs[df_runs['id'] == activity_id_int]
            
            if activity_data.empty:
                continue
                
            file_path = os.path.join(gpx_folder, file_name)
            
            try:
                with open(file_path, 'r') as gpx_file:
                    gpx = gpxpy.parse(gpx_file)
                    if gpx.tracks and gpx.tracks[0].segments and gpx.tracks[0].segments[0].points:
                        # Get middle point of the track for location lookup
                        points = gpx.tracks[0].segments[0].points
                        mid_point = points[len(points) // 2]
                        
                        # Create a coordinate string for geocoding and caching
                        coord_str = f"{mid_point.latitude:.5f},{mid_point.longitude:.5f}"
                        
                        # Check if we already have this location in our cache
                        if coord_str in geocoding_cache:
                            city, country = geocoding_cache[coord_str]
                        else:
                            try:
                                # Add a delay to respect Nominatim's usage policy
                                time.sleep(1)
                                
                                # Reverse geocode to get city and country
                                location = geolocator.reverse(coord_str, exactly_one=True)
                                city, country = get_city_and_country(location)
                                
                                # Cache the result
                                geocoding_cache[coord_str] = (city, country)
                                
                            except Exception as e:
                                print(f"Geocoding error for activity {activity_id}: {e}")
                                continue
                        
                        # Get activity distance in km
                        distance_km = activity_data['distance'].values[0] / 1000
                        
                        # Update city statistics if city is available
                        if city:
                            city_stats[city]['distance'] += distance_km
                            city_stats[city]['count'] += 1
                        
                        # Update country statistics if country is available
                        if country:
                            country_stats[country]['distance'] += distance_km
                            country_stats[country]['count'] += 1
                        
                        # Mark as processed
                        newly_processed.append(activity_id)
            except Exception as e:
                print(f"Error parsing GPX file {file_name}: {e}")
                continue
        except Exception as e:
            print(f"Error processing file {file_name}: {e}")
            continue
    
    # Update processed activities list
    processed_activities.update(newly_processed)
    
    print(f"Completed processing {processed_files} new GPX files, skipped {skipped_files} already processed files.")
    
    # Save the updated cache
    try:
        cache_data = {
            'cities': {city: stats for city, stats in city_stats.items()},
            'countries': {country: stats for country, stats in country_stats.items()},
            'processed_activities': list(processed_activities)
        }
        
        with open(stats_cache_file, 'w') as f:
            json.dump(cache_data, f)
        print(f"Cache updated with {len(processed_activities)} total processed activities")
    except Exception as e:
        print(f"Error saving cache: {e}")
    
    # Sort cities and countries by total distance (descending)
    sorted_cities = sorted(city_stats.items(), key=lambda x: x[1]['distance'], reverse=True)
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1]['distance'], reverse=True)
    
    # Generate HTML content
    html_content = """<div class='city-stats'>
<h2>City Statistics</h2>
"""
    
    # Add city statistics
    for i, (city, stats) in enumerate(sorted_cities, 1):
        html_content += f"<p>{i}. <strong>{city}</strong>: {stats['distance']:.3f} km ({stats['count']} Runs)</p>\n"
    
    # Add country statistics
    html_content += "<br><br><h2>Country Statistics</h2>\n"
    for i, (country, stats) in enumerate(sorted_countries, 1):
        html_content += f"<p>{i}. <strong>{country}</strong>: {stats['distance']:.3f} km ({stats['count']} Runs)</p>\n"
    
    html_content += "</div>"
    
    print("Generating HTML file...")
    
    # Save the generated HTML content to a file
    with open('generated_city_statistics_from_csv.html', 'w', encoding='utf-8') as file:
        file.write(html_content)
    
    print("City statistics HTML file generated: generated_city_statistics_from_csv.html")

def generate_summary_html():
    # Load the CSV file for activities
    df = pd.read_csv(csv_file_path)

    # Ensure that only "Run" activities are processed
    df_runs = df[df['type'] == 'Run']
    
    # Basic statistics
    total_runs = len(df_runs)
    total_distance_km = df_runs['distance'].sum() / 1000  # Convert meters to kilometers
    avg_distance_per_run_km = total_distance_km / total_runs if total_runs > 0 else 0

    # Filter data for the current year
    current_year = datetime.now().year
    df_runs_current_year = df_runs[pd.to_datetime(df_runs['start_date_local']).dt.year == current_year]
    total_runs_current_year = len(df_runs_current_year)
    total_distance_current_year_km = df_runs_current_year['distance'].sum() / 1000  # Convert meters to kilometers
    avg_distance_per_run_current_year_km = total_distance_current_year_km / total_runs_current_year if total_runs_current_year > 0 else 0

    # Get the date of the last run
    if not df_runs.empty:
        last_run_date = pd.to_datetime(df_runs['start_date_local']).max().strftime('%d.%m.%Y')
    else:
        last_run_date = 'N/A'

    # Generate the HTML content
    summary_html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .summary-section {{ margin: 20px; }}
            p {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class='summary-section'>
            <p><strong>Total Runs:</strong> {total_runs}</p>
            <p><strong>Total Distance (km):</strong> {total_distance_km:.3f}</p>
            <p><strong>Average Distance per Run (km):</strong> {avg_distance_per_run_km:.3f}</p>
            <br>
            <p><strong>Total Runs, This Year:</strong> {total_runs_current_year}</p>
            <p><strong>Total Distance, This Year (km):</strong> {total_distance_current_year_km:.3f}</p>
            <p><strong>Average Distance per Run, This Year (km):</strong> {avg_distance_per_run_current_year_km:.3f}</p>
            <br>
            <p><strong>Date of Last Run:</strong> {last_run_date}</p>
        </div>
    </body>
    </html>
    """

    # Save the generated HTML content to a file
    with open('generated_summary.html', 'w', encoding='utf-8') as file:
        file.write(summary_html_content)

    print("Summary HTML file generated: generated_summary.html")