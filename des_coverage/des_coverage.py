import os
import os.path as pa
import requests
import subprocess
import pandas as pd

###############################################################################


def good_object(object):
    try:
        return ("hex" in object) and (int(object.split()[-1]) in [1, 2, 3])
    except:
        return False


###############################################################################

NATROOT = "https://astroarchive.noirlab.edu"
ADSURL = f"{NATROOT}/api/adv_search"

JJ = {
    "outfields": [
        "ra_center",
        "dec_center",
        "ifilter",
        "EXPNUM",
        "exposure",
        "OBJECT",
    ],
    "search": [
        ["instrument", "decam"],
        ["obs_type", "object"],
        ["proc_type", "instcal"],
        ["prod_type", "image"],
        ["proposal", "2012B-0001"],
    ],
}

###############################################################################

##############################
###     Fetch/load df      ###
##############################

# Get archive images
ARCHIVE_IMAGES_PATH = "./des_coverage.csv"
if False:  # pa.exists(ARCHIVE_IMAGES_PATH):
    df = pd.read_csv(ARCHIVE_IMAGES_PATH)
else:
    # Fetch
    apiurl = f"{ADSURL}/find/?limit=3000000"
    df = pd.DataFrame(requests.post(apiurl, json=JJ).json()[1:])

    # Reduce by filter
    df["ifilter"] = df["ifilter"].apply(lambda x: "NaN" if x == None else x[0])
    df = df[df["ifilter"].apply(lambda x: x in list("ugrizY"))]

    # Keep hex tilings, from passes 1, 2, and 3
    df = df[df["OBJECT"].apply(good_object)]

    # Reduce by exposure times
    df.drop(
        index=df.index[(df["ifilter"] == "g") & (df["exposure"] < 30)], inplace=True
    )
    df.drop(
        index=df.index[(df["ifilter"] != "g") & (df["exposure"] < 50)], inplace=True
    )

    # Drop duplicates
    df.drop_duplicates(inplace=True)

    # Save
    df.to_csv(ARCHIVE_IMAGES_PATH, index=False)

##############################
###  Generate coverage df  ###
##############################

df.set_index(["ra_center", "dec_center"], inplace=True)
df_coverage = []
for radec in df.index.unique():
    df_rd = df.loc[radec]
    row = dict(zip(["ra", "dec"], radec))
    for f in list("ugrizY"):
        if f in df_rd["ifilter"].values:
            row[f] = True
        else:
            row[f] = False
    df_coverage.append(row)
df_coverage = pd.DataFrame(df_coverage)
df_coverage.to_csv("./des_byfilter.csv")
