import os
import os.path as pa
import requests
import subprocess
import pandas as pd

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
        "proposal",
    ],
    "search": [
        ["instrument", "decam"],
        ["obs_type", "object"],
        ["proc_type", "instcal"],
        ["prod_type", "image"],
    ],
}

###############################################################################

##############################
###     Fetch/load df      ###
##############################

# Get archive images
PROJ_PATH = "/hildafs/project/phy220048p/tcabrera/decam_followup_O4/DECam_coverage"
ARCHIVE_IMAGES_PATH = f"{pa.dirname(__file__)}/archive_coverage.csv"
if pa.exists(ARCHIVE_IMAGES_PATH):
    df = pd.read_csv(ARCHIVE_IMAGES_PATH)
else:
    # Fetch
    apiurl = f"{ADSURL}/find/?limit=3000000"
    df = pd.DataFrame(requests.post(apiurl, json=JJ).json()[1:])

    # Reduce by filter
    df["ifilter"] = df["ifilter"].apply(lambda x: "NaN" if x == None else x[0])
    df = df[df["ifilter"].apply(lambda x: x in list("ugrizY"))]

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

# Initialize df_coverage with unique ra/dec of full df
df.set_index(["ra_center", "dec_center"], inplace=True)
df_coverage = pd.DataFrame(index=df.index.unique())
# Get filter truth columns
for f in list("ugrizY"):
    df_coverage[f] = df_coverage.index.isin(df.index[df["ifilter"] == f])
# Get proposal (propid) truth columns
for p in ["2012B-0001", "2014B-0404", "2019A-0305"]:
    df_coverage[p] = df_coverage.index.isin(df.index[df["proposal"] == p])
# Save
df_coverage.to_csv(f"{pa.dirname(__file__)}/archive_byfilter.csv")
