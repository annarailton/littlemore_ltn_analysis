import requests

from bs4 import BeautifulSoup


def zoopla_postcode_search(street_name: str, location_name: str) -> str:
    """Scrape Zoopla for postcodes.

    Args:
        street_name (str): street name
        location_name (str): either `littlemore` or `oxford`, top level search location

    Returns:
        str: postcode
    """
    street_squashed = street_name.lower().replace(' ', '-')
    url = f'https://www.zoopla.co.uk/house-prices/{location_name}/{street_squashed}'
    results = requests.get(url)
    soup = BeautifulSoup(results.text, 'html.parser')
    try:
        # Select postcode from first result
        postcode = soup.select(".hp-card__title")[0].text.strip().split(',')[1].strip()
        return postcode
    except IndexError:
        return ''


if __name__ == '__main__':

    for street_name in ["Chapel Lane", "College Lane", "Compass Close"]:

        postcode = zoopla_postcode_search(street_name, 'littlemore')
        if not postcode:
            postcode = zoopla_postcode_search(street_name, 'oxford')

        if postcode:
            print(street_name, postcode)
        else:
            print(f'Could not find postcode for {street_name}')
