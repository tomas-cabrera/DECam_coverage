import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates import Angle
from copy import copy
import matplotlib.pyplot as plt

###############################################################################

### Reference image info
# Here, the reference image is used for information about the CCD corner coordinates.
# The ra and dec of the image should be specified as noted; due to the equatorial mount of the 4m Blanco telescope, this is sufficient information.
c1_corners = pd.read_csv("ccds/cornerCoords_SN-C1.dat", delim_whitespace=True)
c1_field_center_ra = 54.2743
c1_field_center_dec = -27.1116

### SISPI telemetry viewer exposure info
# https://des-ops.fnal.gov:8082/TV/app/Q/index
# SELECT id, exptime, seeing, filter, ra, declination, qc_done, qc_accept, qc_fwhm, qc_sky, qc_cloud, qc_teff, qc_eps FROM exposure WHERE POW(ra - 79.7583, 2) + POW(declination + 47.8869, 2) <= POW(0.5, 2) ORDER BY filterSELECT id, exptime, seeing, filter, ra, declination, qc_done, qc_accept, qc_fwhm, qc_sky, qc_cloud, qc_teff, qc_eps FROM exposure WHERE POW(ra - 79.7583, 2) + POW(declination + 47.8869, 2) <= POW(0.75, 2) ORDER BY ra, declination
path_to_templates = "ccds/GRB230906A/GRB230906A_DECamcrossmatch_r-1.0.csv"
df_templates = pd.read_csv(path_to_templates)
df_templates.sort_values(by=["ra", "declination", "filter"], inplace=True)

### Localization box info
RAcorners = np.array(
    [
        Angle("5h18m50s").deg,
        Angle("5h19m00s").deg,
        Angle("5h19m13s").deg,
        Angle("5h19m04s").deg,
    ]
)
DECcorners = np.array(
    [
        Angle("-47d56m41s").deg,
        Angle("-47d59m08s").deg,
        Angle("-47d49m45s").deg,
        Angle("-47d47m17s").deg,
    ]
)

for ccdid in c1_corners["CCD"].unique():
    df_temp = c1_corners[c1_corners["CCD"] == ccdid].copy()
    df_temp = df_temp.iloc[[0, 1, 3, 2, 0]]
    plt.plot(df_temp["RA"], df_temp["Dec"])
plt.gca().set_aspect("equal")
plt.savefig("ccds.pdf")
plt.close()

###############################################################################


def is_on_silicon(
    RApoints,
    DECpoints,
    RAcands,
    DECcands,
):
    """Given the exposure and candidate pointings, returns the index for each CCD the candidate is on, along with the ra and dec offsets of the candidate from the CCD edge.

    Parameters
    ----------
    RApoints : list-like
        List-like of RAs for exposure pointings.
        Must include 1 RA for each candidate.
    DECpoints : list-like
        List-like of DECs for exposure pointings
        Must include 1 DEC for each candidate.
    RAcands : list-like
        List-like of RAs for candidates.
    DECcands : list-like
        List-like of DECs for candidates.

    Returns
    -------
    3 x np.array
        Returns three np.arrays, of the CCD indices, RA offsets from the CCD edges, and DEC offsets.
    """
    ccds = []
    raminarcsecs = []
    decminarcsecs = []
    for RApoint, DECpoint, RAcand, DECcand in zip(
        RApoints, DECpoints, RAcands, DECcands
    ):
        found = np.nan
        raminarcsec = np.nan
        decminarcsec = np.nan
        for ccd in range(1, 63):
            ww = c1_corners["CCD"] == ccd
            maxra = (
                np.max(c1_corners["RA"][ww].to_numpy()) + RApoint - c1_field_center_ra
            )
            minra = (
                np.min(c1_corners["RA"][ww].to_numpy()) + RApoint - c1_field_center_ra
            )
            maxdec = (
                np.max(c1_corners["Dec"][ww].to_numpy())
                + DECpoint
                - c1_field_center_dec
            )
            mindec = (
                np.min(c1_corners["Dec"][ww].to_numpy())
                + DECpoint
                - c1_field_center_dec
            )
            if (
                (RAcand < maxra)
                & (RAcand > minra)
                & (DECcand < maxdec)
                & (DECcand > mindec)
            ):
                found = copy(ccd)
                raminarcsec = min([maxra - RAcand, RAcand - minra]) * 3600
                decminarcsec = min([maxdec - DECcand, DECcand - mindec]) * 3600

        ccds.append(found)
        raminarcsecs.append(raminarcsec)
        decminarcsecs.append(decminarcsec)
    return np.array(ccds), np.array(raminarcsecs), np.array(decminarcsecs)


###############################################################################

# Average teff
print(df_templates.groupby(["ra"])["qc_teff"].median())
print(df_templates.groupby(["ra"])["qc_teff"].mean())

# Iterate over filters
for f in df_templates["filter"].unique()[-1:]:
    print(f"Checking templates for {f}-band")

    # Iterate over templates
    for ti, t in df_templates[df_templates["filter"] == f].iterrows():
        print(
            f"Exposure {t['id']}: (ra, declination) = ({t['ra']}, {t['declination']})"
        )
        print(
            f"Exposure {t['id']}: (exptime*teff, exptime) = ({t['exptime'] * t['qc_teff']}, {t['exptime']})"
        )

        # Compose exposure ra/dec arrays
        RAexp = np.array([t["ra"]] * 4)
        DECexp = np.array([t["declination"]] * 4)

        # Find corner ccds
        ccds, raoffset, decoffset = is_on_silicon(RAcorners, DECcorners, RAexp, DECexp)

        # Save the # of ccds
        Nccds = len(np.unique(ccds[~np.isnan(ccds)]))
        df_templates.loc[df_templates["id"] == t["id"], "Nccds"] = Nccds
        Nisnan = np.isnan(ccds).sum()
        df_templates.loc[df_templates["id"] == t["id"], "Nisnan"] = Nisnan

        # If everything is on the same ccd
        if np.all(ccds == ccds[0]):
            print(
                f"Exposure {t['id']}: All corners are on the same CCD! (minraoffset, mindecoffset) = ({raoffset.min()}, {decoffset.min()}) [arcsec]"
            )
        else:
            print(
                f"Exposure {t['id']}: {Nccds} CCDs cover the localization box; ccds = {ccds}"
            )

        print(raoffset)
        print(decoffset)

        path_to_figure = path_to_templates.replace(
            ".csv", f".{t['ra']}{t['declination']}.pdf"
        )
        # Plot ccds
        for ccdid in c1_corners["CCD"].unique():
            df_temp = c1_corners[c1_corners["CCD"] == ccdid].copy()
            df_temp = df_temp.iloc[[0, 1, 3, 2, 0]]
            plt.plot(
                df_temp["RA"] + t["ra"] - c1_field_center_ra,
                df_temp["Dec"] + t["declination"] - c1_field_center_dec,
                c="k",
                lw=0.5,
            )
        # Plot localization
        plt.plot(
            RAcorners[[0, 1, 2, 3, 0]],
            DECcorners[[0, 1, 2, 3, 0]],
            c="r",
        )
        # Plot XRT source
        plt.scatter(
            [79.7533],
            [-47.8930],
            c="b",
            marker="+",
        )
        plt.title(f"RA: {t['ra']} Dec: {t['declination']}")
        plt.gca().set_aspect("equal")
        plt.savefig(path_to_figure)
        plt.close()

df_templates.to_csv(path_to_templates.replace(".csv", ".plus.csv"))
