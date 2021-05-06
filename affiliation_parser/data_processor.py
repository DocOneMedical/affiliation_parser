"""
Handle loading data files into dicts, other usable formats
"""
from collections import defaultdict
import csv
from importlib.resources import open_text
import logging
from typing import *

import affiliation_parser.data as data
from .keywords import * 


logger = logging.getLogger(__name__)

TOP1000_CITIES = 'uscities_trimmed.csv'


def us_cities():
    cities = []
    try:
        # Load city data
        with open_text(data, TOP1000_CITIES) as fp:
            r = csv.reader(fp)
            next(r)
            for row in r:
                cities.append(row[0].upper().strip().replace(".", ""))
    except Exception as e:
        logger.error("Unable to load city information.")

    return cities


def us_state_cities_map() -> Dict[str, Set[str]]:
    """
    Map state abbreviations to the cities within them.
    """
    cities_map = defaultdict(set)
    try:
        # Load city data
        with open_text(data, TOP1000_CITIES) as fp:
            r = csv.reader(fp)
            next(r)
            for row in r:
                city = row[0].upper().strip().replace(".", "")
                state_id = row[1]
                if state_id not in STATE_MAP.values():
                    raise ValueError(f"Unrecognized state abbreviation: {state_id}")
                cities_map[state_id].add(city)
    except Exception as e:
        logger.error("Unable to load city information.")

    return cities_map

