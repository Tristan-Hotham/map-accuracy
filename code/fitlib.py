"""The common method: projection of the ground, Helmert and affine fits, residuals as great-circle distances, local
error, Moran's I. Used by 02_fit.py, 03_grids.py and the checks."""
import numpy as np
from pyproj import CRS, Transformer
from scipy.spatial import cKDTree
from common import km


def centroid(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    v = np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)].mean(0)
    return float(np.degrees(np.arctan2(v[2], np.hypot(v[0], v[1])))), float(np.degrees(np.arctan2(v[1], v[0])))


class Ground:
    """Ground plane in km about (lat0, lon0): 'aeqd' (main), 'eqc' (equirectangular, true scale at lat0) or 'merc'."""
    def __init__(self, lat0, lon0, kind="aeqd"):
        self.lat0, self.lon0, self.kind = lat0, lon0, kind
        if kind == "aeqd":
            p = f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +R=6371008.8 +units=km"
        elif kind == "eqc":
            p = f"+proj=eqc +lat_ts={lat0} +lat_0=0 +lon_0={lon0} +R=6371008.8 +units=km"
        elif kind == "merc":
            p = f"+proj=merc +lat_ts={lat0} +lon_0={lon0} +R=6371008.8 +units=km"
        else:
            raise ValueError(kind)
        crs = CRS.from_proj4(p)
        self.fwd = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        self.inv = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    def xy(self, lat, lon):
        x, y = self.fwd.transform(np.asarray(lon, float), np.asarray(lat, float))
        return np.c_[x, y]

    def ll(self, XY):
        lon, lat = self.inv.transform(XY[:, 0], XY[:, 1])
        return np.asarray(lat), np.asarray(lon)


def design(M, model):
    x, y = M[:, 0], M[:, 1]
    n = len(x); o, z = np.ones(n), np.zeros(n)
    if model == "helmert":   # X = a x - b y + tx ; Y = b x + a y + ty
        A = np.r_[np.c_[x, -y, o, z], np.c_[y, x, z, o]]
    else:                    # affine
        A = np.r_[np.c_[x, y, o, z, z, z], np.c_[z, z, z, x, y, o]]
    return A


def fit(M, G, model="helmert", w=None):
    A = design(M, model); b = np.r_[G[:, 0], G[:, 1]]
    if w is not None:
        ww = np.sqrt(np.r_[w, w]); A, b = A * ww[:, None], b * ww
    p, *_ = np.linalg.lstsq(A, b, rcond=None)
    return p


def apply(p, M, model="helmert"):
    A = design(M, model); n = len(M)
    v = A @ p
    return np.c_[v[:n], v[n:]]


def params(p, model="helmert"):
    if model == "helmert":
        a, b = p[0], p[1]
        return {"scale": float(np.hypot(a, b)), "turn_deg": float(-np.degrees(np.arctan2(b, a)))}
    L = np.array([[p[0], p[1]], [p[3], p[4]]])
    s = np.linalg.svd(L, compute_uv=False)
    return {"aniso": float(s[0] / s[1]), "det_sign": float(np.sign(np.linalg.det(L)))}


def huber_fit(M, G, model="helmert", c=1.345, it=50):
    w = np.ones(len(M)); p = fit(M, G, model)
    for _ in range(it):
        r = np.hypot(*(apply(p, M, model) - G).T)
        s = np.median(np.abs(r)) / 0.6745 + 1e-12
        u = r / (c * s)
        w_new = np.where(u <= 1, 1.0, 1.0 / u)
        p_new = fit(M, G, model, w_new)
        if np.allclose(p_new, p, rtol=1e-9, atol=1e-9):
            break
        p, w = p_new, w_new
    return p


class Frame:
    """One map or sheet: lat, lon, map plane M (n x 2)."""
    def __init__(self, lat, lon, M, kind="aeqd"):
        self.lat, self.lon, self.M = np.asarray(lat, float), np.asarray(lon, float), np.asarray(M, float)
        self.lat0, self.lon0 = centroid(self.lat, self.lon)
        self.g = Ground(self.lat0, self.lon0, kind)
        self.G = self.g.xy(self.lat, self.lon)
        d = km(self.lat, self.lon, self.lat0, self.lon0)
        self.R = float(np.sqrt(np.mean(d ** 2)))
        self.n = len(self.lat)

    def resid(self, p, model="helmert", idx=None):
        idx = np.arange(self.n) if idx is None else idx
        F = apply(p, self.M[idx], model)
        la, lo = self.g.ll(F)
        return km(self.lat[idx], self.lon[idx], la, lo), F

    def run(self, model="helmert", robust=False, idx=None):
        idx = np.arange(self.n) if idx is None else idx
        p = (huber_fit if robust else fit)(self.M[idx], self.G[idx], model)
        r, F = self.resid(p, model, idx)
        return p, r, F

    def loo(self, model="helmert"):
        out = np.empty(self.n)
        allidx = np.arange(self.n)
        for i in range(self.n):
            keep = allidx != i
            p = fit(self.M[keep], self.G[keep], model)
            out[i] = self.resid(p, model, np.array([i]))[0][0]
        return out

    def local(self, k=8):
        k = min(k, self.n - 1)
        if k < 3:
            return np.full(self.n, np.nan), np.full(self.n, np.nan)
        tree = cKDTree(self.G)
        _, nb = tree.query(self.G, k=k + 1)
        err = np.empty(self.n); rel = np.empty(self.n)
        for i in range(self.n):
            j = [q for q in nb[i] if q != i][:k]
            p = fit(self.M[j], self.G[j], "helmert")
            e = self.resid(p, "helmert", np.array([i]))[0][0]
            dn = km(self.lat[i], self.lon[i], self.lat[j], self.lon[j]).mean()
            err[i] = e; rel[i] = 100 * e / dn
        return err, rel


def moran(G, V, k=8, perms=999, rng=None):
    """Moran's I of the residual vectors (mean of the I of the two components), kNN row-standardised weights."""
    rng = rng or np.random.default_rng(0)
    n = len(G); k = min(k, n - 1)
    _, nb = cKDTree(G).query(G, k=k + 1)
    nb = nb[:, 1:]

    def I(V):
        out = []
        for c in range(2):
            z = V[:, c] - V[:, c].mean()
            out.append((z * z[nb].mean(1)).sum() / (z * z).sum())
        return float(np.mean(out))
    i0 = I(V)
    sims = np.array([I(V[rng.permutation(n)]) for _ in range(perms)])
    return i0, float((1 + (sims >= i0).sum()) / (perms + 1))
