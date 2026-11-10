"""Step 2: the common method applied to every frame, with the pre-specified checks. Outputs:
data/points_fit.csv (one row per control point), data/frames.csv (one row per frame), data/measures.json (everything
the results step needs). Runtime a few minutes on 2 CPUs."""
import itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from fitlib import *
from common import *

rng = np.random.default_rng(SEED)
P = pd.read_csv(f"{DATA}/control_points.csv", keep_default_na=False, dtype={"pid": str, "frame": str, "region": str, "conf": str})
P["top"] = P.top.astype(str).eq("True")
WHOLE = [m[0] for m in MAPS] + [m[0] for m in SUPP]
SETS = [m[0] for m in SHEETS]


def ci(a):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]


def frame_of(g, kind="aeqd"):
    return Frame(g.lat.values, g.lon.values, g[["mx", "my"]].values, kind)


pts, frames, M = [], [], {}
for key in WHOLE + SETS:
    g_all = P[P["map"] == key]
    per_frame = []
    for fr, g in g_all.groupby("frame", sort=False):
        F = frame_of(g)
        p, r, Fit = F.run("helmert")
        pa, ra, _ = F.run("affine")
        rr = F.run("helmert", robust=True)[1]
        lo = F.loo("helmert")
        le, lrel = F.local(K_LOCAL)
        le6, lrel6 = F.local(6)
        le12, lrel12 = F.local(12)
        V = Fit - F.G
        lat_f, lon_f = F.g.ll(Fit)
        out = g[["map", "frame", "pid", "name", "region", "lat", "lon", "conf", "top"]].copy()
        out["fit_lat"], out["fit_lon"] = lat_f, lon_f
        out["gx"], out["gy"] = F.G[:, 0], F.G[:, 1]
        out["dE_km"], out["dN_km"] = V[:, 0], V[:, 1]
        out["err_km"], out["err_aff_km"], out["err_huber_km"], out["err_loo_km"] = r, ra, rr, lo
        out["local_km"], out["local_rel"], out["local_rel_k6"], out["local_rel_k12"] = le, lrel, lrel6, lrel12
        out["R_km"] = F.R
        out["rel"] = 100 * r / F.R
        info = INFO[key]
        if info["home"]:
            hn, hla, hlo = info["home"]
            out["home_km"] = km(g.lat.values, g.lon.values, hla, hlo)
        else:
            out["home_km"] = np.nan
        # other projections of the ground (R1)
        for kind in ("eqc", "merc"):
            F2 = frame_of(g, kind)
            out[f"err_{kind}_km"] = F2.run("helmert")[1]
        if key == "ptolemy":   # R8: aspect 1
            g8 = g.copy(); g8["mx"] = g8.mx / math.cos(math.radians(36))
            out["err_aspect1_km"] = frame_of(g8).run("helmert")[1]
        pts.append(out)
        I, pI = moran(F.G, V, 8, 999, rng) if F.n >= 10 else (np.nan, np.nan)
        hp = params(p); ap = params(pa, "affine")
        frames.append({"map": key, "frame": fr, "n": F.n, "R_km": F.R, "lat0": F.lat0, "lon0": F.lon0,
                       "km_per_unit": hp["scale"], "turn_deg": hp["turn_deg"], "aniso": ap["aniso"], "affine_det": ap["det_sign"],
                       "median_km": float(np.median(r)), "p90_km": float(np.percentile(r, 90)), "rms_km": float(np.sqrt(np.mean(r ** 2))),
                       "median_aff_km": float(np.median(ra)), "rel_pc": float(100 * np.median(r) / F.R),
                       "local_km": float(np.nanmedian(le)), "local_rel_pc": float(np.nanmedian(lrel)), "moran_I": I, "moran_p": pI,
                       "helmert": [float(x) for x in p], "affine": [float(x) for x in pa]})
        per_frame.append((fr, g, F))
    M[key] = per_frame
    print(key, len(per_frame), "frames", flush=True)

T = pd.concat(pts, ignore_index=True)
FR = pd.DataFrame(frames)


def summary(key, col="err_km"):
    d = T[T["map"] == key]
    rel = 100 * d[col] / d.R_km
    return {"n": int(len(d)), "frames": int(d.frame.nunique()), "median_km": float(d[col].median()),
            "p90_km": float(d[col].quantile(.9)), "rel_pc": float(rel.median()), "p90_rel_pc": float(rel.quantile(.9))}


S = {}
for key in WHOLE + SETS:
    d = T[T["map"] == key]
    s = summary(key)
    s.update({"median_aff_km": float(d.err_aff_km.median()), "rel_aff_pc": float((100 * d.err_aff_km / d.R_km).median()),
              "local_km": float(d.local_km.median()), "local_rel_pc": float(d.local_rel.median()),
              "R_km": float(d.groupby("frame").R_km.first().median()), "top_n": int(d.top.sum())})
    f = FR[FR["map"] == key]
    s.update({"turn_deg": float(f.turn_deg.median()), "aniso": float(f.aniso.median()), "km_per_unit": float(f.km_per_unit.median()),
              "moran_I": float(f.moran_I.median()), "moran_p_max": float(f.moran_p.max()), "frames_moran_sig": int((f.moran_p < 0.05).sum()),
              "frames_moran": int(f.moran_p.notna().sum())})
    # bootstrap
    B = B_BOOT
    if key in WHOLE:
        fr, g, F = M[key][0]
        bm, br, bl = [], [], []
        for _ in range(B):
            idx = rng.integers(0, F.n, F.n)
            p_ = fit(F.M[idx], F.G[idx], "helmert")
            r_ = F.resid(p_, "helmert", idx)[0]
            # R of the resample (size of the resampled set)
            la0, lo0 = centroid(F.lat[idx], F.lon[idx])
            R_ = np.sqrt(np.mean(km(F.lat[idx], F.lon[idx], la0, lo0) ** 2))
            bm.append(np.median(r_)); br.append(100 * np.median(r_) / R_)
            bl.append(np.nanmedian(d.local_rel.values[idx]))
    else:
        frs = d.frame.unique(); groups = {f_: d[d.frame == f_] for f_ in frs}
        bm, br, bl = [], [], []
        for _ in range(B):
            pick = rng.choice(frs, len(frs))
            dd = pd.concat([groups[f_] for f_ in pick])
            bm.append(dd.err_km.median()); br.append((100 * dd.err_km / dd.R_km).median()); bl.append(dd.local_rel.median())
    s["median_km_ci"], s["rel_pc_ci"], s["local_rel_pc_ci"] = ci(bm), ci(br), ci(bl)
    S[key] = s

# ---------- checks ----------
CHK = {k: {} for k in WHOLE + SETS}
for key in WHOLE + SETS:
    d = T[T["map"] == key]
    for lab, col in (("R1_eqc", "err_eqc_km"), ("R1_merc", "err_merc_km"), ("R3_huber", "err_huber_km"), ("R4_loo", "err_loo_km")):
        CHK[key][lab] = float((100 * d[col] / d.R_km).median())
    CHK[key]["R4_loo_km"] = float(d.err_loo_km.median())
    CHK[key]["R7_k6"] = float(d.local_rel_k6.median()); CHK[key]["R7_k12"] = float(d.local_rel_k12.median())
    if key == "ptolemy":
        CHK[key]["R8_aspect1"] = float((100 * d.err_aspect1_km / d.R_km).median())
    # R2 top confidence only (refit on the top points; frames with at least 10)
    vals = []
    for fr, g, F in M[key]:
        gt = g[g.top.values]
        if len(gt) >= 10:
            Ft = frame_of(gt); r_ = Ft.run()[1]; vals.extend(100 * r_ / Ft.R)
    CHK[key]["R2_top"] = float(np.median(vals)) if vals else None
    CHK[key]["R2_top_n"] = len(vals)
    # R5 equal size 40
    if key in WHOLE and M[key][0][2].n >= 40:
        fr, g, F = M[key][0]; v = []
        for _ in range(500):
            idx = rng.choice(F.n, 40, replace=False)
            sub = Frame(F.lat[idx], F.lon[idx], F.M[idx]); v.append(100 * np.median(sub.run()[1]) / sub.R)
        CHK[key]["R5_n40"] = float(np.median(v)); CHK[key]["R5_n40_ci"] = ci(v)
    # R6 leave one region out
    if key in WHOLE:
        fr, g, F = M[key][0]
        reg = g.region.values.copy()
        if len(set(reg)) < 2 or key in ("saxton", "ino"):
            G0 = F.G
            reg = np.where(G0[:, 0] >= 0, "E", "W").astype(object) + np.where(G0[:, 1] >= 0, "N", "S")
        v = {}
        for rg in sorted(set(reg)):
            keep = reg != rg
            if keep.sum() < 10 or (~keep).sum() < 3:
                continue
            sub = Frame(F.lat[keep], F.lon[keep], F.M[keep]); v[str(rg)] = float(100 * np.median(sub.run()[1]) / sub.R)
        CHK[key]["R6_regions"] = v
        CHK[key]["R6_min"], CHK[key]["R6_max"] = (min(v.values()), max(v.values())) if v else (None, None)
    else:
        v = {}
        for fr in d.frame.unique():
            dd = d[d.frame != fr]; v[fr] = float((100 * dd.err_km / dd.R_km).median())
        CHK[key]["R6_regions"] = v; CHK[key]["R6_min"], CHK[key]["R6_max"] = min(v.values()), max(v.values())
    # F1 shuffled map positions
    v = []; vl = []
    for _ in range(200):
        vv = []
        for fr, g, F in M[key]:
            perm = rng.permutation(F.n)
            Fs = Frame(F.lat, F.lon, F.M[perm]); vv.extend(100 * Fs.run()[1] / Fs.R)
        v.append(np.median(vv))
    CHK[key]["F1_shuffle"] = float(np.median(v)); CHK[key]["F1_shuffle_ci"] = ci(v)
    print("checks", key, flush=True)

# shuffled local error (one draw set, 20 draws, for the local measure)
for key in WHOLE + SETS:
    v = []
    for _ in range(20):
        vv = []
        for fr, g, F in M[key]:
            Fs = Frame(F.lat, F.lon, F.M[rng.permutation(F.n)]); vv.extend(Fs.local(K_LOCAL)[1])
        v.append(np.nanmedian(vv))
    CHK[key]["F1_shuffle_local"] = float(np.median(v))

# ---------- H1: date against relative error (8 maps) ----------
main = [m[0] for m in MAPS]
yrs = np.array([INFO[k]["year"] for k in main], float)
H = {}
for lab, field in (("rel", "rel_pc"), ("local", "local_rel_pc"), ("km", "median_km")):
    v = np.array([S[k][field] for k in main])
    rho = spearmanr(yrs, v).statistic
    perms = [spearmanr(yrs, v[list(q)]).statistic for q in itertools.permutations(range(len(main)))]
    perms = np.array(perms)
    H[lab] = {"rho": float(rho), "p_one_sided": float((perms <= rho + 1e-12).mean()), "n_perm": int(len(perms))}
# with the Peutinger copy date (c. 1200) instead
y2 = yrs.copy(); y2[main.index("peutinger")] = 1200
v = np.array([S[k]["rel_pc"] for k in main]); rho2 = spearmanr(y2, v).statistic
perms = np.array([spearmanr(y2, v[list(q)]).statistic for q in itertools.permutations(range(len(main)))])
H["rel_copydate"] = {"rho": float(rho2), "p_one_sided": float((perms <= rho2 + 1e-12).mean())}

# ---------- H4: distance from home ----------
HOME = {}
W = T[T["map"].isin(WHOLE)].copy()
W["dh"] = W.home_km / W.R_km
W["ly"] = np.log(np.maximum(W.err_km, 0.01) / W.R_km)
for key in WHOLE:
    d = W[W["map"] == key]
    rho = spearmanr(d.home_km, d.err_km).statistic
    bs = []
    for _ in range(1000):
        idx = rng.integers(0, len(d), len(d)); bs.append(spearmanr(d.home_km.values[idx], d.err_km.values[idx]).statistic)
    q = d.home_km.quantile([1 / 3, 2 / 3]).values
    HOME[key] = {"rho": float(rho), "ci": ci(bs), "home": INFO[key]["home"][0],
                 "near_km": float(d[d.home_km <= q[0]].err_km.median()), "far_km": float(d[d.home_km > q[1]].err_km.median()),
                 "near_cut_km": float(q[0]), "far_cut_km": float(q[1])}


def within(df, cols):
    return df[cols] - df.groupby("map")[cols].transform("mean")


def ols_cluster(df):
    Z = within(df, ["ly", "dh"])
    x, y = Z.dh.values, Z.ly.values
    b = (x * y).sum() / (x * x).sum()
    u = y - b * x
    G = df["map"].values; gs = np.unique(G); nG = len(gs)
    meat = sum(((x[G == g_] * u[G == g_]).sum()) ** 2 for g_ in gs)
    n = len(x); k = 1 + nG
    se = math.sqrt(meat / (x * x).sum() ** 2 * nG / (nG - 1) * (n - 1) / (n - k))
    return b, se, x, y, u, G, gs


b, se, x, y, u, G, gs = ols_cluster(W)
webb = np.array([-math.sqrt(1.5), -1, -math.sqrt(.5), math.sqrt(.5), 1, math.sqrt(1.5)])
t0 = b / se
# restricted (null b = 0): y* = u_r * w_g with u_r = y (within-transformed y under the null)
cnt = 0; bs_b = []
NB = 9999
for _ in range(NB):
    w = dict(zip(gs, rng.choice(webb, len(gs))))
    wv = np.array([w[g_] for g_ in G])
    ys = y * wv
    bb = (x * ys).sum() / (x * x).sum(); uu = ys - bb * x
    meat = sum(((x[G == g_] * uu[G == g_]).sum()) ** 2 for g_ in gs)
    sb = math.sqrt(meat / (x * x).sum() ** 2 * len(gs) / (len(gs) - 1))
    cnt += abs(bb / sb) >= abs(t0)
    yu = b * x + u * wv; bs_b.append((x * yu).sum() / (x * x).sum())
HOME["pooled"] = {"b": float(b), "se": float(se), "t": float(t0), "p_wild": float((cnt + 1) / (NB + 1)), "ci_wild": ci(bs_b),
                  "n": int(len(W)), "maps": int(len(gs)), "pct_per_R": float(100 * (math.exp(b) - 1))}
# leave one map out
HOME["pooled_lomo"] = {}
for key in WHOLE:
    bb, ss, *_ = ols_cluster(W[W["map"] != key]); HOME["pooled_lomo"][key] = {"b": float(bb), "se": float(ss)}

T.to_csv(f"{DATA}/points_fit.csv", index=False, float_format="%.5g")
FR.drop(columns=["helmert", "affine"]).to_csv(f"{DATA}/frames.csv", index=False, float_format="%.5g")
jsave({"summary": S, "checks": CHK, "H1": H, "home": HOME, "frames": frames}, f"{DATA}/measures.json", indent=1)
print(pd.DataFrame(S).T[["n", "median_km", "rel_pc", "rel_pc_ci", "local_rel_pc", "local_rel_pc_ci", "turn_deg", "aniso"]])
print(H); print(HOME["pooled"])
