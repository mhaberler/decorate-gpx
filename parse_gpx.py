#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
from typing import List, Callable
import requests
from time import sleep
import traceback
import geojson

every = 120 # minutes

pressure_levels = [
    # {"key": "10m", "alt": 10},
    {"key": "1000hPa", "alt": 110},
    {"key": "975hPa", "alt": 320},
    {"key": "950hPa", "alt": 500},
    {"key": "925hPa", "alt": 800},
    {"key": "900hPa", "alt": 1000},
    {"key": "850hPa", "alt": 1500},
    {"key": "700hPa", "alt": 3000},
    {"key": "600hPa", "alt": 4200},
    {"key": "500hPa", "alt": 5500},
]
features = []

@dataclass
class WayPoint:
    lat: float
    lon: float
    elevation: float
    time: datetime
    name: str
    comment: str
    description: str


# working query:
# https://api.open-meteo.com/v1/forecast?latitude=45.625896&longitude=11.305069&hourly=wind_speed_10m,wind_speed_925hPa,wind_speed_800hPa,wind_speed_975hPa,wind_speed_900hPa,wind_speed_700hPa,wind_speed_1000hPa,wind_speed_950hPa,wind_speed_850hPa,wind_speed_600hPa,wind_direction_1000hPa,wind_direction_925hPa,wind_direction_800hPa,wind_direction_975hPa,wind_direction_900hPa,wind_direction_700hPa,wind_direction_950hPa,wind_direction_850hPa,wind_direction_600hPa&models=icon_d2&timezone=GMT&start_date=2025-04-05&end_date=2025-04-05


def get_wind_data(lat: float, lon: float, time: datetime) -> object:
    """Get wind data from OpenMeteo API for given position and time."""
    wind_speed_params = [f"wind_speed_{level['key']}" for level in pressure_levels]
    wind_direction_params = [f"wind_direction_{level['key']}" for level in pressure_levels]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": wind_speed_params + wind_direction_params,
        "timeformat": "iso8601",
        "timezone": "UTC",
        "start_date": time.date().isoformat(),
        "end_date": time.date().isoformat(),
        "models": "icon_d2",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(traceback.format_exc())
        print(f"Warning: Failed to get wind data: {e}")
        return 0.0, 0.0


def process_waypoints(
    waypoints: List[WayPoint],
    callback: Callable[[float, float, float, datetime, float, float], None],
    min_time_diff: timedelta = timedelta(minutes=every),
) -> None:
    last_processed_time = None

    for wp in waypoints:
        current_time = wp.time

        # Process first point or if enough time has passed
        if (
            last_processed_time is None
            or current_time - last_processed_time >= min_time_diff
        ):

            # Get wind data from OpenMeteo
            forecast = get_wind_data(wp.lat, wp.lon, current_time)

            # Add small delay to avoid API rate limits
            sleep(0.5)

            callback(
                wp.lat, wp.lon, wp.elevation, current_time,forecast
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

    for wpt in root.findall("gpx:wpt", ns):
        try:
            # Get required attributes
            lat = float(wpt.get("lat", 0))
            lon = float(wpt.get("lon", 0))

            # Get child elements with null checks
            ele_elem = wpt.find("gpx:ele", ns)
            ele = float(ele_elem.text) if ele_elem is not None else 0.0

            time_elem = wpt.find("gpx:time", ns)
            if time_elem is None or not time_elem.text:
                continue  # Skip points without timestamp
            time = datetime.strptime(time_elem.text, "%Y-%m-%dT%H:%M:%SZ")

            name_elem = wpt.find("gpx:name", ns)
            name = name_elem.text if name_elem is not None else ""

            cmt_elem = wpt.find("gpx:cmt", ns)
            cmt = cmt_elem.text if cmt_elem is not None else ""

            desc_elem = wpt.find("gpx:desc", ns)
            desc = desc_elem.text if desc_elem is not None else ""

            waypoint = WayPoint(
                lat=lat,
                lon=lon,
                elevation=ele,
                time=time,
                name=name,
                comment=cmt,
                description=desc,
            )
            waypoints.append(waypoint)

        except (ValueError, AttributeError) as e:
            print(f"Warning: Skipping invalid waypoint: {e}")
            continue

    return waypoints


def process_point(
    lat: float,
    lon: float,
    alt: float,
    time: datetime,
    forecast: object,
) -> None:
    """Process a single GPX point with wind information.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        alt: Altitude in meters
        time: Timestamp of the point
        wind_speed: Wind speed in m/s
        wind_direction: Wind direction in degrees
    """

    geom = geojson.Point((lon, lat, alt))
    props = {"time": time.isoformat(), "forecast": forecast}
    feature = geojson.Feature(geometry=geom, properties=props)
    features.append(feature)

def main():
    if len(sys.argv) != 2:
        print("Usage: parse_gpx.py <gpx_file>")
        sys.exit(1)

    gpx_file = sys.argv[1]

    try:
        waypoints = parse_gpx_file(gpx_file)
        process_waypoints(waypoints, process_point)
        feature_collection = geojson.FeatureCollection(features)
        print(geojson.dumps(feature_collection, indent=2))

    except FileNotFoundError:
        print(f"Error: File '{gpx_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing GPX file: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
