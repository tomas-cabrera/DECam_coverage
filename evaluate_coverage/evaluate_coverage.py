import sys
import os
import sqlite3
import multiprocessing as mp
import parmap

from astropy.io import fits
from astropy.table import Table

###############################################################################

PATH_TO_TILING = "/hildafs/projects/phy220048p/tcabrera/decam_followup_O4/coverage_map/decam-tiles_obstatus_DECaLS_2019.fits"
PATH_TO_DB = "/hildafs/projects/phy220048p/share/decam_pipeline/DECAM_FOLLOWUP/misc/database/PipelineDB.db"


def check_template_availability(
    tile,
    dbpath,
    search_radius=0.25,
    filters=list("ugrizY"),
    minexptimes={
        "u": 50,
        "g": 30,
        "r": 50,
        "i": 50,
        "z": 50,
        "Y": 50,
    },
):
    """_summary_

    Parameters
    ----------
    tile : _type_
        _description_
    conn : _type_
        _description_
    """
    return_dict = {
        "field": tile["TILEID"],
        "ra": tile["RA"],
        "dec": tile["DEC"],
    }
    with sqlite3.connect(dbpath) as conn:
        for filter in filters:
            query_results = conn.execute(
                """SELECT * FROM noirlab
                WHERE ((POW(ra_center - ?, 2) + POW(dec_center - ?, 2)) <= POW(?, 2)) 
                    AND SUBSTR(ifilter, 1, 1) = ?
                    AND prod_type = "image"
                    AND EXPTIME > ?
                LIMIT 1
                """,
                # Add this above LIMIT 1 if actually searching for the best template
                # ORDER BY
                #     (EXPTIME / POW(seeing, 2)) DESC,
                #     EXPTIME DESC
                [tile["RA"], tile["DEC"], search_radius, filter, minexptimes[filter]],
            ).fetchone()
            # print(type(query_results))

            # Record existence of template
            filterkey = f"des{filter.lower()}"
            if query_results == None:
                return_dict[filterkey] = False
            else:
                return_dict[filterkey] = True

    return return_dict


###############################################################################

search_radius = 0.1

# Open fits file, get exposure info
with fits.open(PATH_TO_TILING) as tiling_hdul:
    tiling_data = tiling_hdul[1].data
    print(tiling_hdul[1].header.cards)
    with sqlite3.connect(PATH_TO_DB) as conn:
        with mp.Pool(os.cpu_count()) as pm_pool:
            availability = parmap.map(
                check_template_availability,
                tiling_data,
                PATH_TO_DB,
                search_radius=search_radius,
                pm_pool=pm_pool,
                pm_pbar=True,
            )

        avail_table = Table(availability)
        avail_table.write(
            f"./DECaLS_coverage_DECam_searchradius-{search_radius}.fits",
            format="fits",
            overwrite=True,
        )
