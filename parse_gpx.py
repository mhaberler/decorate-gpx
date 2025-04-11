import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
from typing import List, Callable
import requests
from time import sleep

@dataclass
class WayPoint:
    lat: float
    lon: float
    elevation: float
    time: datetime
    name: str
    comment: str
    description: str

def get_wind_data(lat: float, lon: float, time: datetime) -> tuple[float, float]:
    """Get wind data from OpenMeteo API for given position and time."""

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["windspeed_10m", "winddirection_10m"],
        "timeformat": "iso8601",
        "timezone": "UTC",
        "start_date": time.date().isoformat(),
        "end_date": time.date().isoformat(),
        "models": "icon-d2"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Find the closest hour in the returned data
        times = data["hourly"]["time"]
        target_hour = time.replace(minute=0, second=0, microsecond=0).isoformat()
        hour_index = times.index(target_hour)

        wind_speed = data["hourly"]["windspeed_10m"][hour_index]
        wind_direction = data["hourly"]["winddirection_10m"][hour_index]

        return wind_speed, wind_direction

    except Exception as e:
        print(f"Warning: Failed to get wind data: {e}")
        return 0.0, 0.0

def process_waypoints(waypoints: List[WayPoint],
                     callback: Callable[[float, float, float, datetime, float, float], None],
                     min_time_diff: timedelta = timedelta(minutes=120)) -> None:
    last_processed_time = None

    for wp in waypoints:
        current_time = wp.time

        # Process first point or if enough time has passed
        if (last_processed_time is None or
            current_time - last_processed_time >= min_time_diff):

            # Get wind data from OpenMeteo
            wind_speed, wind_direction = get_wind_data(wp.lat, wp.lon, current_time)

            # Add small delay to avoid API rate limits
            sleep(0.5)

            callback(
                wp.lat,
                wp.lon,
                wp.elevation,
                current_time,
                wind_speed,
                wind_direction
            )
            last_processed_time = current_time

def parse_gpx_file(filepath: str) -> List<WayPoint]:
    # Parse XML
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Define namespace
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}

    # Extract waypoints
    waypoints = []

    for wpt in root.findall('gpx:wpt', ns):
        # Get required attributes
        lat = float(wpt.get('lat'))
        lon = float(wpt.get('lon'))

        # Get child elements
        ele = float(wpt.find('gpx:ele', ns).text)
        time = datetime.strptime(wpt.find('gpx:time', ns).text, '%Y-%m-%dT%H:%M:%SZ')
        name = wpt.find('gpx:name', ns).text
        cmt = wpt.find('gpx:cmt', ns).text
        desc = wpt.find('gpx:desc', ns).text

        waypoint = WayPoint(
            lat=lat,
            lon=lon,
            elevation=ele,
            time=time,
            name=name,
            comment=cmt,
            description=desc
        )
        waypoints.append(waypoint)

    return waypoints

def process_point(lat: float, lon: float, alt: float, time: datetime,
                 wind_speed: float, wind_direction: float) -> None:
    """Process a single GPX point with wind information.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        alt: Altitude in meters
        time: Timestamp of the point
        wind_speed: Wind speed in m/s
        wind_direction: Wind direction in degrees
    """
    print(f"Processing point: lat={lat:.6f}, lon={lon:.6f}, alt={alt:.1f}, "
          f"time={time}, wind={wind_speed:.1f}m/s@{wind_direction:.0f}°")

def main():
    if len(sys.argv) != 2:
        print("Usage: script.py <gpx_file>")
        sys.exit(1)

    gpx_file = sys.argv[1]

    try:
        waypoints = parse_gpx_file(gpx_file)
        process_waypoints(waypoints, process_point)

    except FileNotFoundError:
        print(f"Error: File '{gpx_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing GPX file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()