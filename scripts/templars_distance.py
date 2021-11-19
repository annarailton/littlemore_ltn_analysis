"""Get the latitudes and longitudes of postcodes, and distances between places.

Have two ways of getting distances:

- Open Source Routing Machine: http://project-osrm.org/
    - this API only works for driving (i.e. not cycling or walking)
    - does have the Littlemore Road LTN filter in there
- Google Directions API (needs `GOOGLE_DIRECTIONS_API_KEY` added to environment variables)
    - no Littlemore Road LTN filter (!?!), but this does make it useful for "pre-LTN" distances

Done offline instead of in notebook to cut down on API calls.
"""

import csv
import json
import os
import pathlib
import requests
import typing

TEMPLARS_SHOPPING_PARK = (51.732612, -1.218179)
LITTLEMORE_ROAD_LTN_FILTER = (51.72890, -1.21867)  # from https://www.openstreetmap.org/node/8485497325

API_KEY = os.environ['GOOGLE_DIRECTIONS_API_KEY']


def get_distance_google_direcions_api(
    lat_from: float,
    lon_from: float,
    lat_to: float,
    lon_to: float,
) -> float:
    """Get driving distance (in meters) between two locations using Google Directions API.

    We use `mode=bicycling` as Google maps knows about some but not all of the LTN filters (?!) so
    this is the best approximation to `Before LTN`."""
    r = requests.get(
        f"https://maps.googleapis.com/maps/api/directions/json?origin={lat_from},+{lon_from}&destination={lat_to},+{lon_to}&mode=bicycling&key={API_KEY}"
    )

    routes = json.loads(r.content)
    return routes.get("routes")[0]['legs'][0]['distance']['value']


def get_distance_osrm_api(
    lat_from: float,
    lon_from: float,
    lat_to: float,
    lon_to: float,
) -> float:
    """Get driving distance (in meters) between two locations using OSRM API.

    Note the unexpected order of the lat/long in the API call.
    """
    r = requests.get(
        f"http://router.project-osrm.org/route/v1/driving/{lon_from},{lat_from};{lon_to},{lat_to}?overview=false"
        ""
    )

    routes = json.loads(r.content)
    return routes.get("routes")[0]['distance']


def update_street_data_with_distances_to_templars(csv_file: pathlib.Path) -> None:
    """Update street data CSV file with lat-long and LTN distance data"""
    data = []
    lat_to, lon_to = TEMPLARS_SHOPPING_PARK
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        header.extend([
            'driving_distance_to_templars_before',
            'driving_distance_to_templars_after',
        ])
        data.append(header)
        for row in reader:
            print(f'Processing {row[0]}')
            lat_from, lon_from = float(row[7]), float(row[8])
            distance_before = get_distance_google_direcions_api(lat_from, lon_from, lat_to, lon_to)
            distance_after = get_distance_osrm_api(lat_from, lon_from, lat_to, lon_to)
            row.extend([distance_before, distance_after])
            data.append(row)

    with open(csv_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(data)


if __name__ == '__main__':

    csv_file = pathlib.Path('.').absolute().parent.joinpath('data/street_data.csv')
    update_street_data_with_distances_to_templars(csv_file)
