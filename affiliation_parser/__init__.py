from .utils import download_grid_data
from .parse import parse_affil, parse_email, parse_zipcode
from .matcher import match_affil
import re


def multiple_match_affil(text):
    email = parse_email(text)
    zip_code = parse_zipcode(text)
    text = re.sub(email, "", text)
    text = re.sub(zip_code, "", text)
    results = []
    for t in re.split('\;|\.', text):
        if t.strip() == "":
            continue
        result = parse_affil(t)
        results.append(result)
        # for af in result:
        #     results.append(af)
    # results = sorted(results, key=lambda x: x['score'], reverse=True)
    return results