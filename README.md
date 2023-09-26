# DECam_coverage

This is some code used to piece together a tiling of the sky out of DECam images from the [NOIRLab Astro Data Archive](https://astroarchive.noirlab.edu/), that is, to assemble a tiling where template images are known.
The DES (NOIRLab propid [2012B-0001](https://time-allocation.noirlab.edu/#/proposal/details/2012B-0001)), DECaLS ([2014B-0404](https://time-allocation.noirlab.edu/#/proposal/details/2014B-0404)), and DELVE ([2019A-0305](https://time-allocation.noirlab.edu/#/proposal/details/2019A-0305)) survey tilings were used to define an all-sky tesselation, which was then cross-matched with the archive to determine the coverage.

The table of available DECam images was assembled from the archive by performing a simple exposure time cut (>= 30s for g-band, >= 50s otherwise); see [archive_coverage](https://github.com/tomas-cabrera/DECam_coverage/tree/main/archive_coverage).
The resulting `.csv` also contains information on which pointings are covered by which of the `ugrizY` filters.

[`decam-tiles_obstatus_DECaLS_2019.fits`](https://github.com/tomas-cabrera/DECam_coverage/blob/main/decam-tiles_obstatus_DECaLS_2019.fits) and [`decam-tiles-bliss-v1.fits`](https://github.com/tomas-cabrera/DECam_coverage/blob/main/decam-tiles-bliss-v1.fits) are fits tables of the DECaLS and DELVE all-sky tessellations, respectively.
The DELVE file also contains the columns `IN_DES` and `IN_DECALS`, which are boolean masks denoting which coordinates lie within the respective survey footprints.
The DES tessellation was directly assembled from the Archive by querying by propid and applying some cuts by inspecting the `OBJECT` field, including limiting our selection to tilings 1-3 (see [des_coverage](https://github.com/tomas-cabrera/DECam_coverage/tree/main/des_coverage);
[[decals](https://github.com/tomas-cabrera/DECam_coverage/tree/main/decals_coverage),[delve](https://github.com/tomas-cabrera/DECam_coverage/tree/main/delve_coverage)]_coverage do the same thing for the other two surveys, but were not used when assembling the tessellation in preference for the `.fits` files).

The three tessellations were combined into an all-sky tessellation in the following manner.
The `IN_*` columns in the DELVE fits file were used to generate equivalent columns for the other two files: the other two were crossmatched with the DELVE tiling, and the `IN_*` value for the nearest DELVE pointing determined whether the other pointing was within the respective survey
(yes, the DES pointings were checked if they were `IN_DES`; this eliminated "stray" pointings from supernova searches and the like).
Once all three tilings were labeled in such a way, the composite tiling was defined by taking the DES pointings `IN_DES`, the DECaLS pointings not `IN_DES` but `IN_DECALS`, and the DELVE pointings not `IN_DES` nor `IN_DECALS`
(see [assemble_tessellation](https://github.com/tomas-cabrera/DECam_coverage/tree/main/assemble_tessellation)).
In [`tiling.csv`](https://github.com/tomas-cabrera/DECam_coverage/blob/main/assemble_tessellation/tiling.csv), the `TILEID` column values denote which survey the pointing comes from, and also the survey tile id for that pointing
(the DES pointing "id" is simply the `pandas` id assigned after pulling the pointings from the archive; a future version could read the actual survey ids from the `OBJECT` field).
This composite tiling was then crossmatched with the available images for each filter (as fetched in [archive_coverage](https://github.com/tomas-cabrera/DECam_coverage/tree/main/archive_coverage)) to determine which pointings of the tiling are covered by archive images of the different filters.
[`tiling_coverage.csv`](https://github.com/tomas-cabrera/DECam_coverage/blob/main/assemble_tessellation/tiling_coverage.csv) is this filterwise coverage record.

Assembling the DES footprint from the archive had the side effect of including distinct rows for each unique ra/dec, which meant that any pointing errors led to practically duplicate rows, to factors from 5x to 1000x in the worst cases.
Fortunately, these pointing errors are an order of magnitude smaller than the distance between tiling pointings, so a clustering algorithm was used to identify groups and drop all but one member of the group (see [agglomerative_dendrogram](https://github.com/tomas-cabrera/DECam_coverage/tree/main/agglomerative_dendrogram)).
At this point a hard cut rejecting pointings with dec $\ge 35^\circ$ was also applied to further reduce the number of pointings, and the resulting list was saved as [`tiling_coverage.clustered.csv`](https://github.com/tomas-cabrera/DECam_coverage/blob/main/agglomerative_dendrogram/tiling_coverage.clustered.csv).
[coverage_to_gwemopt](https://github.com/tomas-cabrera/DECam_coverage/tree/main/coverage_to_gwemopt) then takes this mapping and casts it in the `DECam.tess` and `DECam.ref` files needed for `gwemopt`.

In `coverage_to_gwemopt.py`, the fields are assigned integer ids, as opposed to a `<survey>-<survey_index>`-style format.
All surveys have a number of pointing in the ten-thousands, and so to maintain a distinction among the surveys different millions intervals are reserved for each of the surveys: DES has ids 1000000-1099999, DECaLS has ids 2000000-2099999, and DELVE has ids 3000000-3499999.
DES and DELVE already assign unique ids to every pointing, but DELVE uses the same field id for all passes; accordingly, the different passes are allocated a separate hundred thousands interval, i.e. DELVE pass 1 is assigned ids 3100000-3199999, pass 2 is assigned DELVE ids 3200000-3299999, etc.
Altogether, the first digit of the custom field id encodes the survey the pointing is selected from, the second digit indicates the DELVE pass number (the other two surveys always have 0 as the second digit), and the last 5 digits carries forward the survey id number (except for DES, which as the pointings were taken from the NOIRLab Astro Data Archive simply were assigned indices; this could be improved to use the DES ids later).

The other folder here is [evaluate_coverage](https://github.com/tomas-cabrera/DECam_coverage/tree/main/evaluate_coverage), which was a first attempt at determining filterwise coverage, but only using the DECaLS tiling.
It should be considered deprecated.
