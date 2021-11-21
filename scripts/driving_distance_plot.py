"""Plot driving distances to a location before and after  Cowley LTN installation.

The difficulty here is getting a rout-able map for the "before" state.

To add to the confusion, Google Maps appears to be ignoring the Littlemore Road filter (perhaps
because of mopeds driving through?) - as of 23 Nov 2021.

Therefore settled on using the following:

- BEFORE state: Google Directions API, in cycling mode
    - The only real traffic-free cycle route in this region is the ring road path which runs
    East-West, whereas these journeys are North-South.
    - After a bit of spot checking decided this was sufficiently good approximation to the "before"
    state
    - This requires a Google Directions API key to get this part to work, see
        https://developers.google.com/maps/documentation/directions/overview
- AFTER state: cannot use Google Directions API here because of the missing Littlemore Road filter
    - Use Open Source Routing Machine: http://project-osrm.org/
    - This API only works for driving (i.e. not cycling or walking) so annoyingly can't use for the
    "before" state too

You may get rate limited if you try to run this script too many times in quick succession. If
playing around with the graph I strongly recommend dumping the routing results to file first to
cut down on API calls (Google will start charging you and OSRM is an Open Source resource).

Setting environment variables
-----------------------------

You need two environment variables for this script to work:

- USER_EMAIL (for geo-coding)
- Google Directions API key

Set both by doing:

    export USER_EMAIL=[...]
    export GOOGLE_DIRECTIONS_API_KEY=[...]

before running this script.

Where to start
--------------

- If you only have street names: get postcodes from `postcode_lookup.py`
- If you have street names and postcodes: get (lat, long) using `get_lat_long_from_postcode`
- If you have street names, postcodes and (lat, long)
"""

import argparse
import json
import os
import pathlib
import typing

import geopy
import requests

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geopy.geocoders import Nominatim

USER_AGENT = os.environ['USER_EMAIL']
API_KEY = os.environ['GOOGLE_DIRECTIONS_API_KEY']
TEMPLARS_SHOPPING_PARK = (51.732612, -1.218179)

geolocator = Nominatim(user_agent=USER_AGENT)


def get_lat_long_from_postcode(postcode: str) -> typing.Tuple[float, float]:
    """Get lat-long of a postcode"""
    location = geolocator.geocode(postcode)
    return (location.latitude, location.longitude)


def get_distance_google_direcions_api(
    lat_from: float, lon_from: float, lat_to: float, lon_to: float, mode: str
) -> float:
    """Get driving distance (in meters) between two locations using Google Directions API.

    `mode` is mode of travel, one of `driving`, `walking`, `bicycling`, `transit`.
    See https://developers.google.com/maps/documentation/directions/get-directions#TravelModes
    """
    r = requests.get(
        f"https://maps.googleapis.com/maps/api/directions/json?origin={lat_from},+{lon_from}&destination={lat_to},+{lon_to}&mode={mode}&key={API_KEY}"
    )
    routes = json.loads(r.content)
    return routes.get("routes")[0]['legs'][0]['distance']['value']


def get_distance_osrm_api(lat_from: float, lon_from: float, lat_to: float, lon_to: float) -> float:
    """Get driving distance (in meters) between two locations using OSRM API.

    Note the unexpected order of the lat/long in the API call.
    """
    r = requests.get(
        f"http://router.project-osrm.org/route/v1/driving/{lon_from},{lat_from};{lon_to},{lat_to}?overview=false"
        ""
    )
    routes = json.loads(r.content)
    return routes.get("routes")[0]['distance']


def get_driving_distance_before_ltn(lat_from: float, lon_from: float, lat_to: float, lon_to: float) -> float:
    """Driving distance from `(lat_from, lon_from)` to `(lat_to, lon_to)` before LTN installation"""
    return get_distance_google_direcions_api(lat_from, lon_from, lat_to, lon_to, 'bicycling')


def get_driving_distance_after_ltn(lat_from: float, lon_from: float, lat_to: float, lon_to: float) -> float:
    """Driving distance from `(lat_from, lon_from)` to `(lat_to, lon_to)` after LTN installation"""
    return get_distance_osrm_api(lat_from, lon_from, lat_to, lon_to)


def update_street_data_with_distances_to_location(
    csv_file: pathlib.Path, loc_to_name_short: str, lat_to: float, lon_to: float
) -> None:
    """Update street data CSV file with lat-long and LTN distance data.

    Overwrites the existing file to help with unnecessary API spamming.
    """
    df = pd.read_csv(csv_file)

    if 'street' not in df.columns:
        raise ValueError('Missing `street` column, required for graph label')

    if 'postcode' not in df.columns:
        raise ValueError('Missing `postcode` column, please run script `postcode_lookup.py')

    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        df[['latitude', 'longitude']] = df['postcode'].apply(get_lat_long_from_postcode).tolist()

    before_column_name = f'driving_distance_to_{loc_to_name_short}_before'
    after_column_name = f'driving_distance_to_{loc_to_name_short}_after'

    if before_column_name in df.columns and after_column_name in df.columns:
        print(f'Columns {before_column_name} and {after_column_name} already exist, no action taken')
        return

    df[before_column_name] = df.apply(
        lambda x: get_driving_distance_before_ltn(x.latitude, x.longitude, lat_to, lon_to), axis=1
    ).astype('float64')
    df[after_column_name] = df.apply(
        lambda x: get_driving_distance_after_ltn(x.latitude, x.longitude, lat_to, lon_to), axis=1
    ).astype('float64')

    df.to_csv(csv_file)  # overwrite existing file


def plot_stacked_distances_graph(
    csv_file: pathlib.Path, output_png: pathlib.Path, loc_to_name_short: str, loc_to_name_full: str,
    loc_from_name_full: str
) -> None:
    """Create a nice stacked bar chart of the driving distances before and after LTN installation.

    Bars in order of increasing distance before LTN.

    Args:
        csv_file (pathlib.Path): Location of data CSV file
        output_png (pathlib.Path): Location of output PNG file
        loc_to_name_short (str): short location to name, used in column name
        loc_to_name_full (str): long location to name, used in graph title
        loc_from_name_full (str): long location from name, used in graph title

    """

    MILES_CONVERSION = 0.000621371  # meters to miles

    df = pd.read_csv(csv_file)
    before_column_name = f'driving_distance_to_{loc_to_name_short}_before'
    after_column_name = f'driving_distance_to_{loc_to_name_short}_after'
    df['diff'] = df[after_column_name] - df[before_column_name]

    # Normalise some of the distances as routing can be a bit out
    NORM_DISTANCE = 50  # meters
    df.loc[df["diff"] <= NORM_DISTANCE, "diff"] = 0.0
    df.loc[df["diff"] == 0.0, after_column_name] = df[before_column_name]
    df = df.sort_values(before_column_name)

    # Plot graph
    before = df["driving_distance_to_templars_before"] * MILES_CONVERSION
    diff = df["diff"] * MILES_CONVERSION
    average_distance_increase = diff.mean()
    width = 0.5

    _, ax = plt.subplots(figsize=(12, 8))
    ax.bar(df['street'], before, label="Before LTN", width=width)
    ax.bar(df['street'], diff, label="After LTN", width=width, bottom=before)
    plt.legend(loc="best")
    plt.xticks(rotation=270)
    plt.gca().set_ylim(bottom=0)  # set bottom y limit to 0
    plt.xlabel('Streets')
    plt.ylabel('Driving distance (miles)')
    plt.text(-2.5, 1.9, f'Average distance increase: {average_distance_increase:0.2f} miles', fontsize=12)
    plt.title(f'Driving distance to {loc_to_name_full} from {loc_from_name_full}')
    plt.savefig(output_png, bbox_inches="tight")
    print(f'Plot written to {output_png}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--data', help='location of CSV street data', default='data/street_data.csv')
    parser.add_argument('--output', help='location of output PNG file', default='distances_barchart.png')

    args = parser.parse_args()

    csv_file = pathlib.Path(args.data)
    png_file = pathlib.Path(args.output)

    assert csv_file.is_file()

    update_street_data_with_distances_to_location(csv_file, 'templars', *TEMPLARS_SHOPPING_PARK)
    plot_stacked_distances_graph(csv_file, png_file, 'templars', 'Templars Shopping Park', 'Littlemore streets')
