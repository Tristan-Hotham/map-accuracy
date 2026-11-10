"""Step 4: data/results.json (every number quoted anywhere), data/maps.csv (the comparison table) and data/site.json
(page data). Reads data/measures.json, data/points_fit.csv, data/frames.csv, data/grids.json."""
import itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from common import *

Mz = jload(f"{DATA}/measures.json")
S, C, H, HOME = Mz["summary"], Mz["checks"], Mz["H1"], Mz["home"]
T = pd.read_csv(f"{DATA}/points_fit.csv", keep_default_na=False, dtype={"pid": str, "frame": str})
FR = pd.read_csv(f"{DATA}/frames.csv", keep_default_na=False, dtype={"frame": str})
MAIN = [m[0] for m in MAPS]; WHOLE = MAIN + [m[0] for m in SUPP]; SETS = [m[0] for m in SHEETS]
R = {"maps": {}, "sets": {}}

# source studies' own figures (F2), from their README/results, and the comparable number here
SRC = {"ptolemy": ("Helmert on his degree grid", 144, "median_km"), "peutinger": (None, None, None),
       "idrisi": ("affine", 239, "median_aff_km"), "pisana": ("Mercator similarity", 93, "median_km"),
       "hereford": ("similarity from Jerusalem", 516, "median_km"), "gough": ("similarity", 17.6, "median_km"),
       "saxton": ("similarity", 4.23, "median_km"), "ino": ("similarity", 7.9, "median_km"), "catalan": ("Mercator similarity", 88, "median_km"),
       "saxton_sheets": ("similarity per sheet", 1.37, "median_km"), "ino_sheets": ("similarity per sheet, leave one out", 0.508, None)}
for key in WHOLE + SETS:
    s = dict(S[key]); c = C[key]; info = INFO[key]
    s.update({"name": info["name"], "short": info["short"], "year": info["year"], "date": info["date"], "purpose": PURPOSE[info["purpose"]],
              "doi": info["doi"], "slug": info["slug"]})
    s["checks"] = {k: v for k, v in c.items() if k not in ("R6_regions",)}
    s["checks"]["R6_regions"] = c["R6_regions"]
    s["shuffle_ratio"] = c["F1_shuffle"] / s["rel_pc"]
    if key in HOME:
        s["home"] = HOME[key]
    src = SRC[key]
    s["source"] = {"method": src[0], "km": src[1], "here_km": (s[src[2]] if src[2] else (c["R4_loo_km"] if key == "ino_sheets" else None))}
    s["affine_gain_pc"] = 100 * (1 - s["median_aff_km"] / s["median_km"])
    s["best_proj_rel"] = min(s["rel_pc"], c["R1_eqc"], c["R1_merc"])
    s["best_proj"] = ["azimuthal equidistant", "equirectangular", "Mercator"][int(np.argmin([s["rel_pc"], c["R1_eqc"], c["R1_merc"]]))]
    (R["maps"] if key in WHOLE else R["sets"])[key] = s

# ranks
order = sorted(MAIN, key=lambda k: S[k]["rel_pc"])
R["rank_rel"] = order
R["rank_local"] = sorted(MAIN, key=lambda k: S[k]["local_rel_pc"])
R["rank_km"] = sorted(MAIN, key=lambda k: S[k]["median_km"])
R["best"], R["worst"] = order[0], order[-1]
R["H1"] = H
# H1 under each check
yrs = np.array([INFO[k]["year"] for k in MAIN], float)
allp = list(itertools.permutations(range(len(MAIN))))


PERM = np.array(allp)


def fast_perm(y, v):
    """Spearman rho for every permutation of v (no ties), vectorised."""
    ry = np.argsort(np.argsort(y)).astype(float); rv = np.argsort(np.argsort(v)).astype(float)
    n = len(y); P_ = np.array(list(itertools.permutations(range(n))))
    d = ry[None, :] - rv[P_]
    return 1 - 6 * (d ** 2).sum(1) / (n * (n * n - 1))


def sp(vals, y=yrs):
    v = np.array(vals, float); rho = spearmanr(y, v).statistic
    perms = fast_perm(y, v)
    return {"rho": float(rho), "p_one_sided": float((perms <= rho + 1e-12).mean())}


H1c = {}
for lab in ("R1_eqc", "R1_merc", "R3_huber", "R4_loo", "R7_k6", "R7_k12"):
    H1c[lab] = sp([C[k][lab] for k in MAIN])
H1c["best_proj"] = sp([R["maps"][k]["best_proj_rel"] for k in MAIN])
H1c["affine"] = sp([S[k]["rel_aff_pc"] for k in MAIN])
# exploratory: the six maps before 1500 only
pre = [k for k in MAIN if INFO[k]["year"] < 1500]
yp = np.array([INFO[k]["year"] for k in pre], float); vp = np.array([S[k]["rel_pc"] for k in pre])
rho = spearmanr(yp, vp).statistic
perms = fast_perm(yp, vp)
H1c["pre1500"] = {"rho": float(rho), "p_one_sided": float((perms <= rho + 1e-12).mean()), "n": len(pre)}
vl = np.array([S[k]["local_rel_pc"] for k in pre]); rho = spearmanr(yp, vl).statistic
perms = fast_perm(yp, vl)
H1c["pre1500_local"] = {"rho": float(rho), "p_one_sided": float((perms <= rho + 1e-12).mean())}
R["H1_checks"] = H1c
R["H1_n_sig"] = int(sum(v["p_one_sided"] < 0.05 for k, v in H1c.items() if not k.startswith("pre1500")))
R["H1_n_checks"] = int(sum(1 for k in H1c if not k.startswith("pre1500")))
# purpose groups
grp = {}
for k in MAIN:
    grp.setdefault(PURPOSE[INFO[k]["purpose"]], []).append(k)
R["purpose"] = {g: {"maps": ks, "median_rel": float(np.median([S[k]["rel_pc"] for k in ks])),
                    "median_local": float(np.median([S[k]["local_rel_pc"] for k in ks]))} for g, ks in grp.items()}
# H3
R["H3"] = {"maps_sig": int(sum(S[k]["frames_moran_sig"] for k in MAIN)), "maps": len(MAIN),
           "not_sig": [k for k in MAIN if S[k]["frames_moran_sig"] == 0],
           "local_over_global": {k: S[k]["local_rel_pc"] / S[k]["rel_pc"] for k in MAIN}}
R["H3"]["local_km_smaller"] = [k for k in MAIN if S[k]["local_km"] < S[k]["median_km"]]
R["H3"]["n_local_km_smaller"] = len(R["H3"]["local_km_smaller"])
R["H3"]["moran_range"] = [min(S[k]["moran_I"] for k in MAIN if S[k]["frames_moran_sig"]), max(S[k]["moran_I"] for k in MAIN)]
R["saxton_sheets_moran_sig"] = int(S["saxton_sheets"]["frames_moran_sig"]); R["saxton_sheets_moran_n"] = int(S["saxton_sheets"]["frames_moran"])
# H4
R["home"] = HOME
R["H4_positive"] = [k for k in WHOLE if HOME[k]["ci"][0] > 0]
R["H4_negative"] = [k for k in WHOLE if HOME[k]["ci"][1] < 0]
R["H4_null"] = [k for k in WHOLE if HOME[k]["ci"][0] <= 0 <= HOME[k]["ci"][1]]
# H5
R["H5"] = {k: {"aniso": S[k]["aniso"], "affine_gain_pc": R["maps"][k]["affine_gain_pc"]} for k in WHOLE}
R["H5_max"] = max(WHOLE, key=lambda k: S[k]["aniso"])
# totals
R["n_points_whole"] = int(sum(S[k]["n"] for k in MAIN))
R["n_points_all"] = int(sum(S[k]["n"] for k in WHOLE + SETS))
R["n_frames_all"] = int(sum(S[k]["frames"] for k in WHOLE + SETS))
R["span_years"] = INFO["ino"]["year"] - INFO["ptolemy"]["year"]
R["ratio_worst_best_rel"] = S[R["worst"]]["rel_pc"] / S[R["best"]]["rel_pc"]
R["ratio_hereford_pisana"] = S["hereford"]["rel_pc"] / S["pisana"]["rel_pc"]
R["shuffle_min_ratio"] = min(R["maps"][k]["shuffle_ratio"] for k in MAIN)
R["shuffle_range"] = [min(C[k]["F1_shuffle"] for k in MAIN), max(C[k]["F1_shuffle"] for k in MAIN)]
# leave one region out: does the ranking change?
rk = []
for k in MAIN:
    rk.append((k, C[k]["R6_min"], C[k]["R6_max"]))
R["R6"] = {k: [a, b] for k, a, b in rk}
# checks: does the order of the eight change under each check (Spearman between main and check across maps)
ordc = {}
for lab in ("R1_eqc", "R1_merc", "R3_huber", "R4_loo"):
    ordc[lab] = float(spearmanr([S[k]["rel_pc"] for k in MAIN], [C[k][lab] for k in MAIN]).statistic)
ordc["R7_k6"] = float(spearmanr([S[k]["local_rel_pc"] for k in MAIN], [C[k]["R7_k6"] for k in MAIN]).statistic)
ordc["R7_k12"] = float(spearmanr([S[k]["local_rel_pc"] for k in MAIN], [C[k]["R7_k12"] for k in MAIN]).statistic)
R["order_corr"] = ordc
R["order_corr_min"] = min(ordc.values())
R["proj_change"] = {k: [S[k]["rel_pc"], C[k]["R1_eqc"], C[k]["R1_merc"]] for k in WHOLE}
R["proj_max_drop_pc"] = max(100 * (1 - min(C[k]["R1_eqc"], C[k]["R1_merc"]) / S[k]["rel_pc"]) for k in WHOLE)
R["proj_max_drop_map"] = max(WHOLE, key=lambda k: 1 - min(C[k]["R1_eqc"], C[k]["R1_merc"]) / S[k]["rel_pc"])

# ------- quoted convenience values -------
q = {}
for k in WHOLE + SETS:
    s = R["maps"].get(k) or R["sets"][k]
    q[k] = {"rel": s["rel_pc"], "rel_lo": s["rel_pc_ci"][0], "rel_hi": s["rel_pc_ci"][1], "km": s["median_km"], "km_lo": s["median_km_ci"][0],
            "km_hi": s["median_km_ci"][1], "loc": s["local_rel_pc"], "loc_lo": s["local_rel_pc_ci"][0], "loc_hi": s["local_rel_pc_ci"][1],
            "n": s["n"], "R": s["R_km"], "turn": s["turn_deg"], "aniso": s["aniso"], "p90": s["p90_km"], "shuffle": s["checks"]["F1_shuffle"]}
R["q"] = q
R["n_maps"] = len(MAIN)

# comparison table
rows = []
for k in WHOLE + SETS:
    s = R["maps"].get(k) or R["sets"][k]
    rows.append({"key": k, "map": s["name"], "date": s["date"], "year": s["year"], "purpose": s["purpose"], "frames": s["frames"], "points": s["n"],
                 "size_R_km": round(s["R_km"], 1), "median_km": round(s["median_km"], 2), "median_km_lo": round(s["median_km_ci"][0], 2),
                 "median_km_hi": round(s["median_km_ci"][1], 2), "p90_km": round(s["p90_km"], 2), "relative_pc": round(s["rel_pc"], 2),
                 "relative_lo": round(s["rel_pc_ci"][0], 2), "relative_hi": round(s["rel_pc_ci"][1], 2), "local_pc": round(s["local_rel_pc"], 1),
                 "local_lo": round(s["local_rel_pc_ci"][0], 1), "local_hi": round(s["local_rel_pc_ci"][1], 1), "turn_deg": round(s["turn_deg"], 1),
                 "anisotropy": round(s["aniso"], 2), "affine_median_km": round(s["median_aff_km"], 2), "moran_I": round(s["moran_I"], 2),
                 "shuffled_pc": round(s["checks"]["F1_shuffle"], 1), "source_doi": s["doi"]})
pd.DataFrame(rows).to_csv(f"{DATA}/maps.csv", index=False)
jsave(R, f"{DATA}/results.json", indent=1)

# ------- site.json (page data) -------
G = jload(f"{DATA}/grids.json")
site = {"maps": [], "sets": []}
for k in WHOLE:
    s = R["maps"][k]; g = G[k]
    site["maps"].append({"k": k, "name": s["name"], "short": s["short"], "year": s["year"], "date": s["date"], "purpose": s["purpose"],
                         "n": s["n"], "R": round(s["R_km"]), "km": round(s["median_km"], 1), "kmlo": round(s["median_km_ci"][0], 1), "kmhi": round(s["median_km_ci"][1], 1),
                         "rel": round(s["rel_pc"], 1), "rello": round(s["rel_pc_ci"][0], 1), "relhi": round(s["rel_pc_ci"][1], 1),
                         "loc": round(s["local_rel_pc"], 1), "loclo": round(s["local_rel_pc_ci"][0], 1), "lochi": round(s["local_rel_pc_ci"][1], 1),
                         "turn": round(s["turn_deg"], 1), "aniso": round(s["aniso"], 2), "home": g["home"], "slug": s["slug"], "supp": k in [m[0] for m in SUPP],
                         "pts": g["pts"], "grid": g["grid"], "cells": g["cells"], "coast": g["coast"], "land": g["land"], "hull": g["hull"]})
for k in SETS:
    s = R["sets"][k]
    site["sets"].append({"k": k, "name": s["name"], "short": s["short"], "year": s["year"], "date": s["date"], "n": s["n"], "frames": s["frames"],
                         "R": round(s["R_km"], 1), "km": round(s["median_km"], 2), "rel": round(s["rel_pc"], 1), "rello": round(s["rel_pc_ci"][0], 1),
                         "relhi": round(s["rel_pc_ci"][1], 1), "loc": round(s["local_rel_pc"], 1), "loclo": round(s["local_rel_pc_ci"][0], 1),
                         "lochi": round(s["local_rel_pc_ci"][1], 1)})
jsave(site, f"{DATA}/site.json")
print("results.json", os.path.getsize(f"{DATA}/results.json") // 1024, "KB; site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
print(order, R["rank_local"]); print(H1c); print(R["order_corr"]); print(R["H4_positive"], R["H4_negative"], R["H4_null"])
print({k: round(v, 2) for k, v in R["H3"]["local_over_global"].items()}, R["proj_max_drop_map"], R["proj_max_drop_pc"])
