import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
from typing import List, Callable

@dataclass
class WayPoint:
    lat: float
    lon: float
    elevation: float
    time: datetime
    name: str
    comment: str
    description: str

def process_waypoints(waypoints: List[WayPoint],
                     callback: Callable[[float, float, float, datetime], None],
                     min_time_diff: timedelta = timedelta(minutes=15)) -> None:
    last_processed_time = None

    for wp in waypoints:
        current_time = wp.time

        # Process first point or if enough time has passed
        if (last_processed_time is None or
            current_time - last_processed_time >= min_time_diff):
            callback(
                wp.lat,
                wp.lon,
                wp.elevation,
                current_time
            )
            last_processed_time = current_time

def parse_gpx_file(filepath: str) -> List[WayPoint]:
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

def process_point(lat: float, lon: float, alt: float, time: datetime) -> None:
    """Process a single GPX point.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        alt: Altitude in meters
        time: Timestamp of the point
    """
    print(f"Processing point: lat={lat:.6f}, lon={lon:.6f}, alt={alt:.1f}, time={time}")

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