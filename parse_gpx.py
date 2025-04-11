import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class WayPoint:
    lat: float
    lon: float
    elevation: float
    time: datetime
    name: str
    comment: str
    description: str

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

def main():
    gpx_file = "0826_15wcyrfz8_20250404-hilmar.gpx"
    waypoints = parse_gpx_file(gpx_file)

    print(f"Found {len(waypoints)} waypoints")

    # Print first few points as example
    for wp in waypoints[:5]:
        print(f"\nWaypoint at {wp.lat}, {wp.lon}")
        print(f"Time: {wp.time}")
        print(f"Elevation: {wp.elevation}m")
        print(f"Comment: {wp.comment}")

if __name__ == "__main__":
    main()