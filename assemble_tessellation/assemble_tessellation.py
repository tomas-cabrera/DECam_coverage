import numpy as np
import os
import pandas as pd
import sqlite3
import multiprocessing as mp
import parmap
import astropy.units as u
from astropy.table import Table
from astropy.coordinates import SkyCoord, match_coordinates_sky

###############################################################################

ARCHIVE_PATH = "../archive_coverage/archive_byfilter.csv"
DES_PATH = "../des_coverage/des_byfilter.csv"
DECALS_PATH = "../decam-tiles_obstatus_DECaLS_2019.fits"
DELVE_PATH = "../decam-tiles-bliss-v1.fits"

###############################################################################

##############################
###         Setup          ###
##############################

# Read in archive data
df_archive = pd.read_csv(ARCHIVE_PATH)
df_archive.rename(columns={"ra_center": "RA", "dec_center": "DEC"}, inplace=True)
df_archive.dropna(subset=["RA", "DEC"], inplace=True)

# Load DES data
df_des = pd.read_csv(DES_PATH)
df_des.rename(columns={"ra": "RA", "dec": "DEC"}, inplace=True)
df_des.dropna(subset=["RA", "DEC"], inplace=True)
df_des["TILEID"] = [f"DES-{x}" for x in df_des.index]

# Read in DECaLS data
df_decals = Table.read(DECALS_PATH)
df_decals = df_decals.to_pandas()
df_decals.dropna(subset=["RA", "DEC"], inplace=True)
df_decals["TILEID"] = df_decals["TILEID"].apply(lambda x: f"DECaLS-{x}")

# Read in DELVE data
df_delve = Table.read(DELVE_PATH)
df_delve = df_delve.to_pandas()
df_delve.dropna(subset=["RA", "DEC"], inplace=True)
df_delve["TILEID"] = df_delve["TILEID"].apply(lambda x: f"DELVE-{x}")

print("df_archive:", df_archive, sep="\n")
print("df_des:", df_des, sep="\n")
print("df_decals:", df_decals, sep="\n")
print("df_delve:", df_delve, sep="\n")

##############################
### Map to DELVE pointings ###
##############################

# Setup DELVE coords
coords_delve = SkyCoord(ra=df_delve["RA"], dec=df_delve["DEC"], unit=u.deg)
print("coords_delve:", coords_delve)

### Map DES to DELVE coords ###
# Setup DES coords
coords_des = SkyCoord(ra=df_des["RA"], dec=df_des["DEC"], unit=u.deg)
print("coords_des:", coords_des)
# Crossmatch with DELVE
xm_des = match_coordinates_sky(coords_des, coords_delve)
# Add DELVE index, separation to df_des
df_des["id_delve"] = df_delve.index[xm_des[0]]
df_des["sep_delve"] = xm_des[1].value
df_des["IN_DES"] = df_delve["IN_DES"].to_numpy()[xm_des[0]]
df_des["IN_DECALS"] = df_delve["IN_DECALS"].to_numpy()[xm_des[0]]

### Map DECaLS to DELVE coords ###
# Setup DECaLS coords
coords_decals = SkyCoord(ra=df_decals["RA"], dec=df_decals["DEC"], unit=u.deg)
# Crossmatch with DELVE
xm_decals = match_coordinates_sky(coords_decals, coords_delve)
# Add DELVE index, separation, IN_[DES,DECALS] to df_decals
df_decals["id_delve"] = df_delve.index[xm_decals[0]]
df_decals["sep_delve"] = xm_decals[1].value
df_decals["IN_DES"] = df_delve["IN_DES"].to_numpy()[xm_decals[0]]
df_decals["IN_DECALS"] = df_delve["IN_DECALS"].to_numpy()[xm_decals[0]]

print("df_des:", df_des, sep="\n")
print("df_decals:", df_decals, sep="\n")

##############################
###  Assemble tesselation  ###
##############################

df_tiling = pd.concat(
    [
        df_des.loc[df_des["IN_DES"], ["TILEID", "RA", "DEC"]],
        df_decals.loc[
            ~df_decals["IN_DES"] & df_decals["IN_DECALS"], ["TILEID", "RA", "DEC"]
        ],
        df_delve.loc[
            ~df_delve["IN_DES"] & ~df_delve["IN_DECALS"], ["TILEID", "RA", "DEC"]
        ],
    ]
)

print("df_tiling:", df_tiling, sep="\n")
df_tiling.to_csv("tiling.csv")

##############################
###   Evaluate_coverage    ###
##############################

# Setup tiling coords
coords_tiling = SkyCoord(ra=df_tiling["RA"], dec=df_tiling["DEC"], unit=u.deg)

# Iterate over search radii
for sr in [0.05, 0.1, 0.25]:
    search_radius = 0.05
    # Iterate over filters
    for f in list("ugrizY"):
        coords_archive = SkyCoord(
            ra=df_archive.loc[df_archive[f], "RA"],
            dec=df_archive.loc[df_archive[f], "DEC"],
            unit=u.deg,
        )
        # Crossmatch
        xm_tiling = match_coordinates_sky(coords_tiling, coords_archive)
        # Add to df_tiling
        df_tiling[f"des{f.lower()}"] = xm_tiling[1].deg <= search_radius

    # Save
    df_tiling.to_csv("tiling_coverage.csv")
