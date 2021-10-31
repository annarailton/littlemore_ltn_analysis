"""Get the latitudes and longitudes of postcodes.

Also get (driving) distances from postcodes to Littlemore Road LTN filter using
Open Source Routing Machine: http://project-osrm.org/

Done offline instead of in notebook to cut down on API calls.
"""

import csv
import json
import pathlib
import requests
import typing

import geopy

from geopy.geocoders import Nominatim


geolocator = Nominatim(user_agent="anna.railton@gmail.com")

def get_lat_long(postcode: str) -> typing.Tuple[float, float]:
    """Get lat-long of a postcode"""
    location = geolocator.geocode(postcode)
    return (location.latitude, location.longitude)


def get_distance_to_ltn(lat: float, lon:float) -> float:
    """Get distance (in meters) to southern side of Littlemore Road LTN filter"""

    littlemore_ltn_filter = (51.72890, -1.21867)  # from https://www.openstreetmap.org/node/8485497325
    lat_ltn, lon_ltn = littlemore_ltn_filter

    r = requests.get(f"http://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon_ltn},{lat_ltn}?overview=false""")

    routes = json.loads(r.content)
    return routes.get("routes")[0]['distance']


def update_street_data_with_lat_long_ltn_distance(csv_file: pathlib.Path) -> None:
    """Update street data CSV file with lat-long and LTN distance data"""
    data = []
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        header.extend(['latitude', 'longitude', 'driving_distance_to_ltn_meters'])
        data.append(header)
        for row in reader:
            postcode = row[6]
            print(f'Processing: {postcode}')
            lat, lon = get_lat_long(postcode)
            distance_to_ltn = get_distance_to_ltn(lat, lon)
            if postcode == "OX4 3ST":  # Littlemore Road, don't want wrong side of filter!
                distance_to_ltn = 0.0
            row.extend([lat, lon, distance_to_ltn])
            data.append(row)

    with open(csv_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(data)


if __name__ == '__main__':

    # postcode = "OX4 4PU"
    # lat, lon = get_lat_long(postcode)
    # distance = get_distance_to_ltn(lat, lon)
    # print(postcode, distance)
    csv_file = pathlib.Path('.').absolute().parent.joinpath('data/street_data.csv')

    update_street_data_with_lat_long_ltn_distance(csv_file)
