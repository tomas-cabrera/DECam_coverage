import os
import requests
import subprocess
import pandas as pd
import os.path as pa

GDIR = pa.dirname(pa.dirname(pa.dirname(pa.abspath(__file__))))

__last_modification_at_version__ = "v1.0.2p"
__last_modification_time__ = "2023-06-06"
__last_modification_author__ = "Cabrera"

# URLs
NATROOT = "https://astroarchive.noirlab.edu"
ADSURL = "/".join((NATROOT, "api/adv_search"))

JJ_TEMPLATE = {
    "outfields": [
        "instrument",
        "proposal",
        "obs_type",
        "caldat",
        "release_date",
        "proc_type",
        "prod_type",
        "md5sum",
        "archive_filename",
        "url",
        "ifilter",
        "ra_center",
        "dec_center",
        "AIRMASS",
        "EXPNUM",
        "OBJECT",
    ],
    "search": [
        ["instrument", "decam"],
        ["obs_type", "object"],
        ["proc_type", "instcal"],
    ],
}


###############################################################################


def verify_api_version():
    """! Checks if script is written to work with the current API.
    Copied from NOIRLab ADS Jupyter notebook example.
    """
    actual_api = float(requests.get("/".join((NATROOT, "api/version"))).content)
    expected_api = 6.0
    if int(actual_api) > int(expected_api):
        msg = f"This script needs to be updated to work with NOIRLAB archive API Version {actual_api}"
        print(msg)
    else:
        print(
            f"Current NOIRLAB archive API version ({actual_api}) is good for this script."
        )


def apiurl_limit(limit=1000):
    """! Composes API url with specified file limit.
    1000 is the default when no limit is specified in the apiurl
    3000000 should cover all available DECam images; HENON cannot handle this for the template-relevant fields.
    1000000 is a maximum verified number that HENON can handle.
    """
    return "/".join((ADSURL, "find/?limit=%d" % limit))


def query_archive(apiurl, jj):
    """! Simple function to query archive."""
    return pd.DataFrame(requests.post(apiurl, json=jj).json()[1:])
