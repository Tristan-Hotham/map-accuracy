"""Step 3: distortion grids (display only, not used in any statistic). For each whole-map frame, the residual vectors
of the Helmert fit (map position fitted to the ground minus true position) are interpolated with Hardy's multiquadric
(scipy RBFInterpolator, kernel multiquadric, linear polynomial, epsilon = 1 / median nearest-neighbour distance,
smoothing 1e-3 x n), in units of R (the root mean square distance of the points from their centroid). A regular grid
(spacing R / 4) and the Natural Earth coast inside the convex hull of the points (buffered by 0.15 R) are moved by the
field. Output: data/grids.json (page, figures, collage, GIF)."""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import numpy as np
import pandas as pd
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree
from shapely.geometry import shape, MultiPoint, LineString, Polygon, box
from shapely.ops import transform as stransform
from fitlib import Frame
from common import *

P = pd.read_csv(f"{DATA}/control_points.csv", keep_default_na=False, dtype={"pid": str, "frame": str})
T = pd.read_csv(f"{DATA}/points_fit.csv", keep_default_na=False, dtype={"pid": str, "frame": str})
LAND = jload(f"{GEO}/ne_50m_land.geojson")
land_polys = [shape(f["geometry"]) for f in LAND["features"]]
OUT = {}
SPACING = 0.25
for key in [m[0] for m in MAPS] + [m[0] for m in SUPP]:
    g = P[P["map"] == key]; t = T[T["map"] == key]
    F = Frame(g.lat.values, g.lon.values, g[["mx", "my"]].values)
    R = F.R
    X = F.G / R
    V = np.c_[t.dE_km.values, t.dN_km.values] / R
    nn = cKDTree(X).query(X, k=2)[0][:, 1]
    eps = 1.0 / max(np.median(nn), 1e-3)
    rbf = RBFInterpolator(X, V, kernel="multiquadric", epsilon=eps, smoothing=1e-3 * len(X), degree=1)
    hull = MultiPoint([tuple(p) for p in X]).convex_hull.buffer(0.15)
    x0, y0, x1, y1 = hull.bounds
    lines = []
    step = SPACING / 10
    for gx in np.arange(math.floor(x0 / SPACING) * SPACING, x1 + 1e-9, SPACING):
        ln = LineString([(gx, y0 - 1), (gx, y1 + 1)]).intersection(hull)
        for part in getattr(ln, "geoms", [ln]):
            if part.length > 0:
                pts = np.array([part.interpolate(s).coords[0] for s in np.arange(0, part.length + 1e-9, step)] + [part.coords[-1]])
                lines.append(pts)
    for gy in np.arange(math.floor(y0 / SPACING) * SPACING, y1 + 1e-9, SPACING):
        ln = LineString([(x0 - 1, gy), (x1 + 1, gy)]).intersection(hull)
        for part in getattr(ln, "geoms", [ln]):
            if part.length > 0:
                pts = np.array([part.interpolate(s).coords[0] for s in np.arange(0, part.length + 1e-9, step)] + [part.coords[-1]])
                lines.append(pts)
    # cells: areal scale of each full grid cell inside the hull
    cells = []
    for gx in np.arange(math.floor(x0 / SPACING) * SPACING, x1, SPACING):
        for gy in np.arange(math.floor(y0 / SPACING) * SPACING, y1, SPACING):
            c = np.array([(gx, gy), (gx + SPACING, gy), (gx + SPACING, gy + SPACING), (gx, gy + SPACING)])
            if not hull.contains(Polygon(c)):
                continue
            d = c + rbf(c)
            a0 = SPACING ** 2
            a1 = 0.5 * abs(np.dot(d[:, 0], np.roll(d[:, 1], 1)) - np.dot(d[:, 1], np.roll(d[:, 0], 1)))
            dd = (d - c).round(3).ravel().tolist()
            cells.append([round(gx, 3), round(gy, 3), round(math.log2(max(a1, 1e-6) / a0), 3)] + dd)
    # coast inside the hull, in the same plane
    lat0, lon0 = F.lat0, F.lon0
    hull_ll = None
    proj = lambda x, y, z=None: tuple(np.asarray(v) / R for v in F.g.fwd.transform(x, y))
    coast = []
    # quick lon/lat prefilter box around the points
    la_min, la_max = g.lat.min() - 15, g.lat.max() + 15
    lo_min, lo_max = g.lon.min() - 25, g.lon.max() + 25
    bb = box(lo_min, max(la_min, -80), lo_max, min(la_max, 85))
    for poly in land_polys:
        if not poly.intersects(bb):
            continue
        pc = poly.intersection(bb)
        for pg in getattr(pc, "geoms", [pc]):
            if pg.geom_type != "Polygon" or pg.is_empty:
                continue
            pp0 = stransform(proj, pg).simplify(0.004).buffer(0)
            for pp in getattr(pp0, "geoms", [pp0]):
                if pp.geom_type != "Polygon":
                    continue
                cl = pp.exterior.intersection(hull)
                for part in getattr(cl, "geoms", [cl]):
                    if part.geom_type == "LineString" and part.length > 0.02:
                        seg = part.segmentize(0.02)
                        coast.append(np.array(seg.coords))
    land_fill = []
    for poly in land_polys:
        if not poly.intersects(bb):
            continue
        pc = poly.intersection(bb)
        for pg in getattr(pc, "geoms", [pc]):
            if pg.geom_type != "Polygon" or pg.is_empty:
                continue
            pp = stransform(proj, pg).simplify(0.006).buffer(0).intersection(hull)
            for q in getattr(pp, "geoms", [pp]):
                if q.geom_type == "Polygon" and q.area > 1e-4:
                    land_fill.append(np.array(q.segmentize(0.02).exterior.coords))

    def pack(arr):
        d = rbf(arr)
        return [[round(float(a), 3), round(float(b), 3), round(float(c), 3), round(float(e), 3)] for (a, b), (c, e) in zip(arr, d)]
    hp = np.array(hull.exterior.coords)
    info = INFO[key]
    home = info["home"]; hxy = F.g.xy([home[1]], [home[2]])[0] / R
    OUT[key] = {"R_km": round(R, 1), "n": int(len(X)), "eps": round(float(eps), 2), "home": [home[0], round(float(hxy[0]), 3), round(float(hxy[1]), 3)] + [round(float(v), 3) for v in rbf(hxy[None, :])[0]],
                "pts": [[round(float(a), 3), round(float(b), 3), round(float(c), 3), round(float(e), 3), round(float(k), 1), nm, rg]
                        for (a, b), (c, e), k, nm, rg in zip(X, V, t.err_km.values, t.name.values, t.region.values)],
                "grid": [pack(l) for l in lines], "cells": cells, "coast": [pack(c) for c in coast], "land": [pack(c) for c in land_fill],
                "hull": [[round(float(a), 3), round(float(b), 3)] for a, b in hp],
                "scale_range": [float(np.percentile([c[2] for c in cells], 5)), float(np.percentile([c[2] for c in cells], 95))] if cells else None}
    print(key, len(lines), "lines", len(cells), "cells", len(coast), "coast parts", len(land_fill), "land parts", flush=True)
jsave(OUT, f"{DATA}/grids.json")
print(os.path.getsize(f"{DATA}/grids.json") // 1024, "KB")
