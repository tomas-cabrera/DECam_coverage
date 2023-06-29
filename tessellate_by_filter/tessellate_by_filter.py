import numpy as np
import pandas as pd
from astropy.table import Table

###############################################################################

# Load tiling coverage (tileid, ra, dec, des*)
df = pd.read_csv("../assemble_tessellation/tiling_coverage.csv")


# Save tesselation in gwemopt.tess format
# TILEID needs to be float-convertable
def tileid_to_float(tileid, survey_dict={"DES": 1, "DECaLS": 2, "DELVE": 3}):
    """Convert tileid to float

    Parameters
    ----------
    tileid : str
        _description_

    Returns
    -------
    float
        _description_
    """
    survey, n = tileid.split("-")

    n = (survey_dict[survey] * 10**6) + int(n)

    return n


df["TILEID"] = df["TILEID"].apply(tileid_to_float)
df[["TILEID", "RA", "DEC"]].to_csv("DECam.tess", index=False, header=False, sep=" ")

# Iterate over filters
filters = list("ugrizY")
df_covered = []
for fi, f0 in enumerate(filters):
    # Get the covered tiles for each filter, rename TILEID > field
    df_temp = df.loc[df[f"des{f0.lower()}"], ["TILEID"]]
    df_temp.rename(columns={"TILEID": "field"}, inplace=True)

    # Add column for filter id
    df_temp["fid"] = fi

    # Append to list
    df_covered.append(df_temp)

# Concat into large df
df_covered = pd.concat(df_covered)

# Convert to table and save
Table.from_pandas(df_covered).write("DECam.ref", format="ascii", overwrite=True)
