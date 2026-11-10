"""Step 1: one table of control points from the eight source studies (plus the Catalan Atlas chart and the Saxton and
Ino sheet sets). Map positions are put in a right-handed map plane (image pixels: x, -y; Ptolemy: lon cos 36, lat).
Output: data/control_points.csv (map, frame, pid, name, region, lat, lon, mx, my, conf, top)."""
import numpy as np
import pandas as pd
from common import *

rows = []


def add(key, frame, df, pid, name, region, lat, lon, mx, my, conf, top):
    d = pd.DataFrame({"map": key, "frame": frame, "pid": df[pid].astype(str).values, "name": df[name].astype(str).values,
                      "region": (df[region].astype(str).values if region else ""), "lat": df[lat].astype(float).values,
                      "lon": df[lon].astype(float).values, "mx": np.asarray(mx, float), "my": np.asarray(my, float),
                      "conf": df[conf].astype(str).values, "top": df[conf].astype(str).isin(top).values})
    rows.append(d)


C36 = math.cos(math.radians(36))
d = pd.read_csv(f"{ST}/ptolemy/data/places.csv")
d = d[d.lon_o.notna() & d.lat_o.notna()]
d["nm"] = d.modern.fillna(d.locality)
add("ptolemy", "ptolemy", d, "id", "nm", "continent", "lat", "lon", d.lon_o * C36, d.lat_o, "confidence", ["high"])
# second plane for check R8 (aspect 1)
d = pd.read_csv(f"{ST}/peutinger/data/located.csv")
d["nm"] = [f"{a} ({b})" if isinstance(b, str) and b.strip() else a for a, b in zip(d.label, d.modern)]
add("peutinger", "peutinger", d, "tp_id", "nm", "region", "lat", "lon", d.x, -d.y, "conf", ["high"])
d = pd.read_csv(f"{ST}/idrisi/data/located.csv")
add("idrisi", "idrisi", d, "label", "identification", "region", "lat", "lon", d.x_as_drawn, -d.y_as_drawn, "conf", ["high"])
d = pd.read_csv(f"{ST}/mappa-mundi/data/located.csv")
d = d[d.lat.notna() & d.lon.notna() & d.x_miller.notna()]
d["nm"] = d.identification.fillna(d.name)
add("hereford", "hereford", d, "index_no", "nm", "region", "lat", "lon", d.x_miller, -d.y_miller, "pos_conf", ["high"])
d = pd.read_csv(f"{ST}/portolan-charts/data/points.csv")
# Catalan Atlas: sheets 7 and 8 shifted west by the join offset measured in the source study (fit.json "offsets", image
# pixels x, y-down); sheet 7 repeats the eastern strip of sheet 6.
OFF = jload(f"{ST}/portolan-charts/data/fit.json")["fits"]["catalan"]["offsets"]
for ch in ("pisana", "catalan"):
    g = d[d.chart == ch]
    ox = np.array([OFF.get(str(int(s)), (0, 0))[0] if s == s else 0 for s in g.sheet])
    oy = np.array([OFF.get(str(int(s)), (0, 0))[1] if s == s else 0 for s in g.sheet])
    add(ch, ch, g, "id", "identification", "basin", "lat", "lon", g.x - ox, -(g.y - oy), "conf", ["1"])
d = pd.read_csv(f"{ST}/gough-map/data/located.csv")
add("gough", "gough", d, "id", "name", "region", "lat", "lon", d.x, -d.y, "conf", ["high"])
d = pd.read_csv(f"{ST}/saxton-atlas/data/located.csv")
g = d[d.sheet == "p014"]
add("saxton", "saxton", g, "name", "name", "region", "lat", "lon", g.x, -g.y, "conf", ["1"])
g = d[d.sheet != "p014"].copy()
for sh, gg in g.groupby("sheet"):
    gg = gg.assign(pid=gg.sheet + ":" + gg.name, reg=gg.sheet_name)
    add("saxton_sheets", sh, gg, "pid", "name", "reg", "lat", "lon", gg.x, -gg.y, "conf", ["1"])
d = pd.read_csv(f"{ST}/ino-japan/data/national_fit.csv")
add("ino", "ino", d, "feature", "feature", None, "lat", "lon", d.x_1878, -d.y_1878, "conf", ["medium"])
d = pd.read_csv(f"{ST}/ino-japan/data/control_fit.csv")
d["nm"] = d.id
for sh, gg in d.groupby("sheet"):
    if len(gg) < 4:
        continue
    add("ino_sheets", f"sheet {sh}", gg, "id", "kind", None, "lat", "lon", gg.x, -gg.y, "conf", ["high"])

P = pd.concat(rows, ignore_index=True)
assert P[["lat", "lon", "mx", "my"]].notna().all().all()
assert P.lat.between(-60, 75).all() and P.lon.between(-30, 160).all()
# duplicates of the same real place within a frame are kept (a name drawn twice is two readings) but counted
dup = P.duplicated(["frame", "lat", "lon"], keep=False).groupby(P["map"]).sum()
P.to_csv(f"{DATA}/control_points.csv", index=False, float_format="%.6g")
summ = P.groupby("map").agg(n=("pid", "size"), frames=("frame", "nunique"), top=("top", "sum"))
summ["same_place_twice"] = dup
print(summ)
