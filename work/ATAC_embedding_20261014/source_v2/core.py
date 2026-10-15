"""Small sparse primitives shared by post-count stages; no AnnData dependency."""
import numpy as np
import pandas as pd
from scipy import sparse

BIOLOGICAL_COLUMNS = {"animal_id", "condition", "age_months", "sex", "genotype", "replicate_id"}

def require_counts(x, integer=True):
    if not sparse.issparse(x):
        raise ValueError("Counts must be sparse. Dense cell-by-feature matrices are refused.")
    x = x.tocsr(copy=False)
    values = x.data
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Counts must be finite and nonnegative.")
    if integer and not np.allclose(values, np.rint(values), rtol=0, atol=1e-6):
        raise ValueError("Integer raw counts required; normalized or expected fractional assignments are not molecule counts.")
    x.eliminate_zeros()
    return x

def validate_obs(obs, require_animals=True):
    needed = ["condition", "sex", "age_months", "library_id"]
    if require_animals: needed.append("animal_id")
    for field in needed:
        if field not in obs or obs[field].isna().any():
            raise ValueError(f"Missing or incomplete obs.{field}")
        if obs[field].astype(str).str.fullmatch(r"|UNRESOLVED|UNKNOWN|NA|None", case=False).any():
            raise ValueError(f"Unresolved obs.{field}")
    if not obs.index.is_unique: raise ValueError("Cell IDs must be unique.")
    if require_animals:
        for field in ["condition", "sex", "age_months"]:
            if (obs.groupby("animal_id", observed=True)[field].nunique() != 1).any():
                raise ValueError(f"Animal identity conflicts with {field}")

def validate_technical_batch(obs, batch_key):
    if batch_key in BIOLOGICAL_COLUMNS:
        raise ValueError(f"{batch_key} is biological; removing it as a batch can erase the signal of interest.")
    if batch_key not in obs or obs[batch_key].isna().any(): raise ValueError("Missing technical batch key")
    if obs[batch_key].astype(str).str.contains("UNRESOLVED|UNKNOWN", case=False).any():
        raise ValueError("Resolve technical batch provenance before integration.")
    tab = pd.crosstab(obs[batch_key], obs.condition)
    if len(tab) < 2: raise ValueError("Only one batch; correction is unnecessary.")
    # A conservative gate: each condition must occur in >=2 technical batches,
    # and every batch must span >=2 conditions. More complicated connected designs
    # need explicit scientific review instead of a silent bypass.
    if (tab.gt(0).sum(axis=0) < 2).any() or (tab.gt(0).sum(axis=1) < 2).any():
        raise ValueError("Technical batch and condition lack adequate overlap for this correction policy.")
    return tab

def qc_metrics(x, mt=None):
    x = require_counts(x)
    total = np.asarray(x.sum(axis=1)).ravel()
    detected = np.diff(x.indptr)
    result = {"total_counts": total, "detected_features": detected}
    if mt is not None:
        result["pct_mt"] = np.divide(np.asarray(x[:, mt].sum(axis=1)).ravel() * 100,
                                      total, out=np.zeros(len(total)), where=total > 0)
    return result

def sparse_tfidf(x):
    x = require_counts(x).astype(np.float32)
    rows = np.asarray(x.sum(axis=1)).ravel()
    present = np.asarray((x > 0).sum(axis=0)).ravel()
    inv = np.divide(1, rows, out=np.zeros_like(rows), where=rows > 0)
    idf = x.shape[0] / np.maximum(present, 1)
    x = sparse.diags(inv).dot(x).multiply(idf).tocsr()
    x.data = np.log1p(x.data * 1e4)
    return x

def aggregate_counts(x, obs, label_column, library_size, min_cells=30):
    x = require_counts(x)
    validate_obs(obs)
    if label_column not in obs: raise ValueError(f"Missing annotation field {label_column}")
    labels = obs[label_column].astype(str)
    valid = (~obs[label_column].isna()) & ~labels.str.lower().isin(["unknown", "ambiguous", "mixed", "unassigned", "nan"])
    selected = np.flatnonzero(valid.to_numpy())
    selected_obs = obs.iloc[selected]
    group_keys = pd.MultiIndex.from_frame(selected_obs[["animal_id", label_column]])
    codes, groups = pd.factorize(group_keys, sort=True)
    membership = sparse.csr_matrix((np.ones(len(codes), dtype=np.int64), (codes, np.arange(len(codes)))), shape=(len(groups), len(codes)))
    counts = membership @ x[selected]
    n_cells = np.asarray(membership.sum(axis=1)).ravel()
    libsize = np.asarray(membership @ np.asarray(library_size, dtype=float)[selected]).ravel()
    if not np.isfinite(libsize).all() or (libsize <= 0).any(): raise ValueError("Invalid full-assay library denominators")
    rows = []
    for i, (animal, label) in enumerate(groups):
        s = selected_obs.iloc[np.flatnonzero(codes == i)]
        row = {"sample_id": f"PB{i:05}", "animal_id": animal, "cell_type": label,
               "n_cells": n_cells[i], "library_size": libsize[i]}
        for field in ["condition", "sex", "age_months", "genotype", "technical_batch"]:
            if field in s:
                vals = s[field].dropna().unique()
                row[field] = vals[0] if len(vals) == 1 else "MIXED"
        rows.append(row)
    meta = pd.DataFrame(rows)
    keep = n_cells >= min_cells
    return counts[keep].tocsr(), meta.loc[keep].reset_index(drop=True), meta.loc[~keep].reset_index(drop=True)
