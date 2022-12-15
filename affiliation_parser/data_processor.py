"""
Handle loading data files into dicts, other usable formats
"""
from collections import defaultdict
import csv
import logging
from typing import *
from .keywords import *
import os

logger = logging.getLogger(__name__)

TOP1000_CITIES = 'uscities_trimmed.csv'
fn = __file__
root_path = os.path.abspath(os.path.dirname(__file__))
logger.warning(root_path)

def us_cities():
    cities = []
    try:
        # Load city data
        with open(root_path + '/data/' + TOP1000_CITIES, encoding='utf-8') as fp:
            r = csv.reader(fp)
            next(r)
            for row in r:
                cities.append(row[0].upper().strip().replace(".", ""))
    except Exception as e:
        logger.error("Unable to load city information.")
        raise e

    return cities


def us_city_pop_map():
    city_pop_map = {}
    try:
        # Load city data
        with open(root_path + '/data/' + TOP1000_CITIES, encoding='utf-8') as fp:
            r = csv.reader(fp)
            next(r)
            for row in r:
                city_pop_map[row[0].upper().strip().replace(
                    ".", "")] = float(row[2])
    except Exception as e:
        logger.error("Unable to load city information.")

    return city_pop_map


def us_state_cities_map() -> Dict[str, Set[str]]:
    """
    Map state abbreviations to the cities within them.
    """
    cities_map = defaultdict(set)
    try:
        # Load city data
        with open(root_path + '/data/' + TOP1000_CITIES, encoding='utf-8') as fp:
            r=csv.reader(fp)
            next(r)
            for row in r:
                city=row[0].upper().strip().replace(".", "")
                state_id=row[1]
                if state_id not in STATE_MAP.values():
                    raise ValueError(
                        f"Unrecognized state abbreviation: {state_id}")
                cities_map[state_id].add(city)
    except Exception as e:
        logger.error("Unable to load city information.")

    return cities_map
