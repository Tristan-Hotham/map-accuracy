"""Shared paths, constants and helpers for the map-accuracy study ("How accurate were old maps?").

Inputs (read in place, never modified): the control points of eight published studies by the author, each with a
real place identified on an old map, its position on the map (pixels or the map's own coordinates) and its true
position (WGS84). See README.md and NOTES.md for the files and columns.

  ST/ptolemy/data/places.csv            Ptolemy's Geography (Grasshoff and Defaux catalogue, CC BY 4.0) matched to places
  ST/peutinger/data/located.csv         Peutinger Table, Miller 1887 facsimile pixels; OmnesViae positions
  ST/idrisi/data/located.csv            al-Idrisi, Miller 1928 reconstruction pixels
  ST/mappa-mundi/data/located.csv       Hereford Mappa Mundi, Miller 1896 facsimile pixels
  ST/portolan-charts/data/points.csv    Carta Pisana and Catalan Atlas chart, scan pixels
  ST/gough-map/data/located.csv         Gough Map, photograph pixels
  ST/saxton-atlas/data/located.csv      Saxton's atlas, 35 sheets, scan pixels
  ST/ino-japan/data/control_fit.csv     Ino's large-scale sheets, sheet pixels
  ST/ino-japan/data/national_fit.csv    the 1878 Dai Nihon Zenzu compiled from Ino's survey, map pixels
  GEO/ne_50m_land.geojson               Natural Earth land 1:50m (public domain), for the distortion grids
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.environ.get("MA_STUDIES", "/home/claude/studies")
GEO = os.environ.get("MA_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("MA_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("MA_SCRATCH", "/home/claude/scratch/map-accuracy")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG):
    os.makedirs(d, exist_ok=True)

SLUG = "map-accuracy"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
SEED = 20261

# The whole-map frames, in date order. key: (label, short, date used, date shown, purpose group, home (name, lat, lon),
# source study slug, source DOI)
MAPS = [
    ("ptolemy", "Ptolemy's Geography", "Ptolemy", 150, "c. 150", "world", ("Alexandria", 31.2, 29.92), "ptolemy", "10.5281/zenodo.23882603"),
    ("peutinger", "Peutinger Table", "Peutinger", 300, "c. 300 (copy c. 1200)", "route", ("Rome", 41.893, 12.483), "peutinger", "10.5281/zenodo.23882605"),
    ("idrisi", "al-Idrisi's world map", "al-Idrisi", 1154, "1154", "world", ("Palermo", 38.116, 13.361), "idrisi", "10.5281/zenodo.23882607"),
    ("pisana", "Carta Pisana", "Carta Pisana", 1275, "c. 1275", "sea", ("Genoa", 44.407, 8.934), "portolan-charts", "10.5281/zenodo.24044645"),
    ("hereford", "Hereford Mappa Mundi", "Hereford", 1300, "c. 1300", "world", ("Jerusalem", 31.778, 35.235), "mappa-mundi", "10.5281/zenodo.23878612"),
    ("gough", "Gough Map", "Gough", 1360, "c. 1360", "route", ("London", 51.507, -0.128), "gough-map", "10.5281/zenodo.24043678"),
    ("saxton", "Saxton's general map", "Saxton", 1579, "1579", "survey", ("London", 51.507, -0.128), "saxton-atlas", "10.5281/zenodo.24052723"),
    ("ino", "Ino's Japan (1878 compilation)", "Ino", 1821, "1821 (compiled 1878)", "survey", ("Tokyo", 35.681, 139.767), "ino-japan", "10.5281/zenodo.23882609"),
]
SUPP = [("catalan", "Catalan Atlas chart", "Catalan Atlas", 1375, "1375", "sea", ("Palma", 39.570, 2.650), "portolan-charts", "10.5281/zenodo.24044645")]
SHEETS = [("saxton_sheets", "Saxton's county sheets", "Saxton sheets", 1576, "1574 to 1579", "survey", None, "saxton-atlas", "10.5281/zenodo.24052723"),
          ("ino_sheets", "Ino's large-scale sheets", "Ino sheets", 1821, "1821", "survey", None, "ino-japan", "10.5281/zenodo.23882609")]
ALL = MAPS + SUPP + SHEETS
INFO = {m[0]: dict(zip(("key", "name", "short", "year", "date", "purpose", "home", "slug", "doi"), m)) for m in ALL}
PURPOSE = {"world": "world map", "route": "route map", "sea": "sea chart", "survey": "survey"}
K_LOCAL = 8
B_BOOT = 2000


def km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(np.asarray(lon2) - np.asarray(lon1)) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    raise ValueError(f)
