import os.path as pa

import numpy as np
import pandas as pd
from joblib import dump, load
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram
from sklearn.cluster import AgglomerativeClustering

# from sklearn.datasets import load_iris


def plot_dendrogram(model, **kwargs):
    # Create linkage matrix and then plot the dendrogram

    # create the counts of samples under each node
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # leaf node
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)

    # Plot the corresponding dendrogram
    dendrogram(linkage_matrix, **kwargs)


# iris = load_iris()
# X = iris.data
df = pd.read_csv(
    f"{pa.dirname(pa.dirname(__file__))}/assemble_tessellation/tiling_coverage.csv"
)
df = df[df["DEC"] <= 35]
X = df[["RA", "DEC"]].to_numpy()

# Define model; 0.1 degrees = 6 arcminutes
model_path = "ad.fit.joblib"
if pa.exists(model_path):
    print("Loading model...", end="")
    model = load(model_path)
    print("done.")
else:
    # Initialize model
    model = AgglomerativeClustering(
        distance_threshold=0.1,
        n_clusters=None,
        compute_full_tree=True,
        memory="/hildafs/home/tcabrera/HIPAL/decam_followup_O4/DECam_coverage/agglomerative_dendrogram/cache",
    )

    # Fit model
    print("Fitting...", end="")
    model = model.fit(X)
    print("done.")

    # Dump model for later loading
    dump(model, model_path)

# Save cluster membership
df["clus_id"] = model.labels_
df.drop_duplicates(subset=["clus_id"], inplace=True)
df.to_csv(f"{pa.dirname(__file__)}/tiling_coverage.clustered.csv", index=False)

# Plot
plt.title("Hierarchical Clustering Dendrogram")
# plot the top three levels of the dendrogram
plot_dendrogram(model, truncate_mode="level", p=5)
plt.xlabel("Number of points in node (or index of point if no parenthesis).")
plt.savefig(f"{pa.dirname(__file__)}/agglomerative_dendrogram.png")
