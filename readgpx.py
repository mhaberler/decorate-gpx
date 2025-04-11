import sys
import gpxpy
from datetime import datetime, timedelta

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
    last_processed_time = None
    min_time_diff = timedelta(minutes=15)

    try:
        with open(gpx_file, 'r') as f:
            gpx = gpxpy.parse(f)

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    current_time = point.time

                    # Skip if we don't have time information
                    if not current_time:
                        continue

                    # Process first point or if enough time has passed
                    if (last_processed_time is None or
                        current_time - last_processed_time >= min_time_diff):
                        process_point(
                            point.latitude,
                            point.longitude,
                            point.elevation or 0.0,
                            current_time
                        )
                        last_processed_time = current_time

    except FileNotFoundError:
        print(f"Error: File '{gpx_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing GPX file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()