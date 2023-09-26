import os.path as pa
import numpy as np
import pandas as pd
from astropy.table import Table

###############################################################################


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
    tid_split = tileid.split("-")
    if tid_split[0] == "DELVE":
        survey, n, passid = tid_split
        n = int(n) + int(passid) * 1e5
    else:
        survey, n = tid_split

    n = (survey_dict[survey] * 10**6) + int(n)

    return n


###############################################################################

# Load tiling coverage (tileid, ra, dec, des*)
# df = pd.read_csv("/hildafs/projects/phy220048p/tcabrera/decam_followup_O4/DECam_coverage/assemble_tessellation/tiling_coverage.csv")
df = pd.read_csv(
    "/hildafs/projects/phy220048p/tcabrera/decam_followup_O4/DECam_coverage/agglomerative_dendrogram/tiling_coverage.clustered.csv"
)

# Drop anythingwith dec >= 35 deg
df = df[df["DEC"] <= 35]

# Convert TILEID to index
df["TILEID"] = df["TILEID"].apply(tileid_to_float)
df[["TILEID", "RA", "DEC"]].to_csv(
    f"{pa.dirname(__file__)}/DECam.tess", index=False, header=False, sep=" "
)

# Iterate over filters
filters = list("ugrizY")
df_covered = []
for fi, f0 in enumerate(filters):
    # Get the covered tiles for each filter, rename TILEID > field
    print(f"# of matches for filter {f0}: {df[f'des{f0.lower()}'].sum()}")
    df_temp = df.loc[df[f"des{f0.lower()}"], ["TILEID"]]
    df_temp.rename(columns={"TILEID": "field"}, inplace=True)
    print(f"df_temp.shape: {df_temp.shape}")

    # Add column for filter id
    df_temp["fid"] = fi

    # Append to list
    df_covered.append(df_temp)

# Concat into large df
df_covered = pd.concat(df_covered)

# Convert to table and save
Table.from_pandas(df_covered).write(
    f"{pa.dirname(__file__)}/DECam.ref", format="ascii", overwrite=True
)
