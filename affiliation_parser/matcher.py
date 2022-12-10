import os
import re
import csv
from pathlib import Path
import subprocess
import recordlinkage
from recordlinkage.index import Full

import numpy as np
import pandas as pd
from nltk.tokenize import WhitespaceTokenizer

from .utils import download_grid_data
from .parse import parse_affil, preprocess
from .parse import hospital_df


path = Path(os.getenv("~", '~/.affliation_parser')).expanduser()
grid_path = (path/"grid")
if not grid_path.exists():
    download_grid_data()
grid_df = pd.read_csv(grid_path/"grid.csv", header=0,
                      names=["grid_id", "institution", "city", "state", "country"])
grid_df = grid_df[grid_df['country'] == "United States"]
grid_df['institution'] = grid_df['institution'].str.replace(" (United States)", "", regex=False)
grid_df = pd.concat([grid_df, hospital_df], ignore_index=True)
grid_df["location"] = grid_df.city + " " + grid_df.state
grid_df['institution'] = grid_df['institution'].str.lower()
grid_df = grid_df.drop_duplicates(subset=['institution'])
del grid_df['Unnamed: 0']

# recordlinkage comparer
compare = recordlinkage.Compare()
compare.string("institution", "institution", method="levenshtein")
compare.string("location", "location", method="jarowinkler")
compare.string("country", "country", method="jarowinkler")

def match_affil(affiliation: str, k: int = 3):
    """
    Match affliation to GRID dataset.
    Return a da
    """
    parsed_affil = parse_affil(affiliation)
    df = pd.DataFrame([parsed_affil])

    indexer = recordlinkage.Index()
    indexer.add(Full())
    candidate_links = indexer.index(df, grid_df)

    features_df = compare.compute(candidate_links, df, grid_df)
    features_df["score"] = np.average(features_df, axis=1, weights=[0.3, 0.4, 0.4])

    topk_df = features_df[["score"]].reset_index().sort_values("score", ascending=False).head(k)
    topk_df = topk_df.merge(grid_df.reset_index(), left_on="level_1", right_on="index").\
        drop(labels=["level_0", "level_1", "location"], axis=1)

    return topk_df.to_dict(orient="records")
