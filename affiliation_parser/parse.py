import logging
import re
import string
from unidecode import unidecode
import numpy as np
from .keywords import *
from .data_processor import us_cities, us_state_cities_map, us_city_pop_map
from nltk.tokenize import WhitespaceTokenizer

w_tokenizer = WhitespaceTokenizer()
punct_re = re.compile("[{}]".format(re.escape(string.punctuation)))

US_CITIES = us_cities()
US_CITIES_SET = set(US_CITIES)
US_CITIES_TOP_2000 = set(US_CITIES[:1000])
US_CITIES_POP_MAP = us_city_pop_map()
US_STATE_CITY_MAP = us_state_cities_map()
MAX_WORDS = max(len(s.split()) for s in US_CITIES)


def string_steps(s: str, max_size=MAX_WORDS):
    string_words = s.upper().replace(',', '').replace('.', '').split()
    final_set = set([])
    for step in range(1, max_size+1):
        for start in range(len(string_words)):
            final_set.add(" ".join(string_words[start:start+step]))
            if start + step > len(string_words):
                break
        if step > len(string_words):
            break 


    return final_set

def preprocess(text: str):
    """
    Function to perform word tokenization
    """
    if isinstance(text, (type(None), float)):
        text_preprocess = ""
    else:
        text = unidecode(text).lower()
        text = punct_re.sub(" ", text)  # remove punctuation
        text_preprocess = " ".join(w_tokenizer.tokenize(text))
    return text_preprocess


def replace_institution_abbr(affil_text: str):
    """
    Replace abbreviation with full institution string
    """
    for university_list in UNIVERSITY_ABBR:
        for university in university_list:
            if university in affil_text:
                affil_text = re.sub(university, university_list[0], affil_text)
                return affil_text
    return affil_text


def append_institution_city(affil: str, location: str):
    """
    Append city to university that has multiple campuses if exist
    """
    for university_list in UNIVERSITY_MULTIPLE_CAMPUS:
        if university_list[0] in affil.lower():
            for city in university_list[1::]:
                if city in location.lower() and not city in affil.lower():
                    affil = affil + " " + city
                    return affil
    return affil


def clean_text(affil_text: str):
    """
    Given affiliation text with abbreviation, clean that text
    """
    affil_text = affil_text.strip()
    affil_text = re.sub("\t", " ", affil_text)
    affil_text = re.sub("Dept. ", "Department ", affil_text)
    affil_text = re.sub("Surg. ", "Surgery ", affil_text)
    affil_text = re.sub("Univ. ", "University ", affil_text)
    affil_text = affil_text[2:] if affil_text.startswith("2 ") else affil_text
    affil_text = affil_text[3:] if affil_text.startswith("2. ") else affil_text
    affil_text = re.sub(r"\*", " ", affil_text)
    affil_text = re.sub(";", "", affil_text)
    affil_text = re.sub("E-mail:", "", affil_text)
    affil_text = re.sub("email:", "", affil_text)
    affil_text = re.sub("P.O. Box", "", affil_text)
    affil_text = replace_institution_abbr(affil_text)
    return affil_text.strip()


def find_country(location: str):
    """
    Find country from string
    """
    location_lower = location.lower()
    for country in COUNTRY:
        for c in country:
            if c in location_lower:
                return country[0]
    return ""


def find_state(affil_text: str):
    """
    Get U.S. state info. 
    """
    for state in STATES:
        if state in affil_text: 
            stripped_state = state.strip()
            if len(stripped_state) == 2:
                return stripped_state
            else:
                return STATE_MAP[stripped_state]
    return ""


def find_cities(text: str, state = None):
    city = ""
    cities = US_CITIES_SET.intersection(string_steps(text))
    if state:
        city_ops = cities.intersection(US_STATE_CITY_MAP[state])
    else:
        city_ops = cities.intersection(US_CITIES_TOP_2000)

    if len(city_ops) > 1:
        logging.info(f"Extracted multiple city options={city_ops} for text={text}")
    
    if city_ops:
        city = max(city_ops, key=lambda x: (len(x.split()), US_CITIES_POP_MAP[x]))

    return city

    # for city in US_CITIES:
    #     if city in text.upper():
    #         if state and city not in US_STATE_CITY_MAP[state]:
    #             continue 

    #         return city 
    # return ""


def check_country(affil_text: str):
    """
    Check if any states string from USA or UK
    """
    for country in ["UK"]:
        if country in affil_text:
            return "united kingdom"
    return ""


def parse_email(affil_text: str):
    """Find email from given string"""
    match = re.search(r"[\w\.-]+@[\w\.-]+", affil_text)
    if match is not None:
        email = match.group()
        if email[-1] == ".":
            email = email[:-1]
    else:
        email = ""
    return email


def parse_zipcode(affil_text: str):
    """
    Parse zip code from given affiliation text
    """
    zip_code_group = ""
    zip_code = re.search(r"(\d{5})([-])?(\d{4})?", affil_text)
    if zip_code is None:
        zip_code = re.search(r"(\d{3})([-])?(\d{4})?", affil_text)
    else:
        zip_code = ""

    if zip_code:
        zip_code_group = zip_code.groups()
        zip_code_group = [p for p in zip_code_group if p is not None]
        zip_code_group = "".join(zip_code_group)
    return zip_code_group


def parse_location(affil_text, location):
    """
    Parse location and country from affiliation string
    """
    location = re.sub(r"\.", "", location).strip()
    country = find_country(location)
    if not country:
        country = find_country(affil_text)

    # First try state from location, if no luck, try from full text
    state = find_state(location)
    if not state:
        state = find_state(affil_text)

    # If there's a state, try to find a city
    city = find_cities(location, state) 
    if not city:
        city = find_cities(affil_text, state)

    # If we extracted a state, then we're probably in the us
    if not country:
        if state or city in US_CITIES_TOP_2000:
            country = "united states of america"

    dict_location = {
        "location": location.strip(), 
        "country": country.strip(),
        "us_state": state,
        "us_city": city,
    }
    return dict_location


def parse_affil(affil_text):
    """
    Parse affiliation string to institution and department
    """
    affil_text = unidecode(affil_text)
    affil_text = clean_text(affil_text)
    email = parse_email(affil_text)
    zip_code = parse_zipcode(affil_text)
    affil_text = re.sub(email, "", affil_text)
    affil_text = re.sub(zip_code, "", affil_text)

    affil_list = affil_text.split(", ")
    affil = list()
    location = list()
    departments = list()

    for i, a in enumerate(affil_list):
        for ins in INSTITUTE:
            if ins in a.lower() and (not a in affil):
                affil.append(a)
                location = affil_list[i + 1 : :]

    # remove unwanted from affliation list and location list
    pop_index = list()
    for i, a in enumerate(affil):
        for rm in REMOVE_INSTITUE:
            if rm in a.lower() and (not "university" in a.lower()):
                pop_index.append(i)
    affil = np.delete(affil, list(set(pop_index))).tolist()

    pop_index = list()
    for i, l in enumerate(location):
        for rm in DEPARMENT:
            if rm in l.lower():
                pop_index.append(i)
    location = np.delete(location, list(set(pop_index))).tolist()

    affil = ", ".join(affil)
    location = ", ".join(location)
    if location == "":
        location = affil_text.split(", ")[-1]
    location = re.sub(r"\([^)]*\)", "", location).strip()

    for i, a in enumerate(affil_list):
        for dep in DEPARMENT:
            if dep in a.lower() and (not a in departments):
                departments.append(affil_list[i])
    department = ", ".join(departments)

    dict_location = parse_location(affil_text.strip(), location)
    affil = append_institution_city(affil, dict_location["location"])

    dict_out = {
        "full_text": affil_text.strip(),
        "department": department.strip(),
        "institution": affil.strip(),
        "email": email,
        "zipcode": zip_code,
    }
    dict_out.update(dict_location)
    if dict_out["country"] == "":
        dict_out["country"] = check_country(affil_text)  # check country
    return dict_out
