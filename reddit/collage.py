"""Reddit collage (r/dataisbeautiful style): light paper, the comparison chart on the left, the eight distortion grids on
the right, legend and source footer. Reads data/results.json and data/grids.json. Output: reddit/map_accuracy_collage.png"""
import os, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.environ.get("MA_FONTS", "/home/claude/ref/fonts")
for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
PAPER, INK, MUT, RULE, LAND = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3", "#E6D8B6"
COL = {"world map": "#B4442E", "route map": "#C98A2B", "sea chart": "#2F6A9E", "survey": "#3E7D5A"}
plt.rcParams.update({"font.family": "Source Serif 4", "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.edgecolor": MUT,
                     "xtick.color": MUT, "ytick.color": MUT, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = json.load(open(f"{ROOT}/data/results.json")); G = json.load(open(f"{ROOT}/data/grids.json"))
MAIN = ["ptolemy", "peutinger", "idrisi", "pisana", "hereford", "gough", "saxton", "ino"]

fig = plt.figure(figsize=(24, 13.5), dpi=110)
fig.text(0.03, 0.955, "How accurate were old maps?", family=DISP, fontweight="bold", fontsize=46, color=INK, va="top")
fig.text(0.03, 0.885, "Eight maps from AD 150 to 1821, each fitted to the real world with one scale, shift and turn, measured the same way.",
         fontsize=21, color=MUT, va="top")
# chart
ax = fig.add_axes([0.06, 0.16, 0.41, 0.64])
OFF = {"ptolemy": (12, 4, "left"), "peutinger": (12, 4, "left"), "idrisi": (-12, 6, "right"), "pisana": (-12, -14, "right"),
       "hereford": (12, 4, "left"), "gough": (12, -2, "left"), "saxton": (-12, 4, "right"), "ino": (-12, 4, "right")}
for k in MAIN:
    s = R["maps"][k]; c = COL[s["purpose"]]
    ax.plot([s["year"]] * 2, s["rel_pc_ci"], color=c, lw=3, alpha=.7)
    ax.plot(s["year"], s["rel_pc"], "o", ms=17, color=c, mec="white", mew=2)
    dx, dy, ha = OFF[k]
    ax.annotate(f"{s['short']} {s['rel_pc']:.1f}%", (s["year"], s["rel_pc"]), xytext=(dx, dy), textcoords="offset points",
                fontsize=17, ha=ha, color=INK, path_effects=HALO)
ax.set_yscale("log"); ax.set_ylim(0.8, 40); ax.set_xlim(50, 1950)
ax.set_yticks([1, 2, 5, 10, 20, 40]); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.tick_params(labelsize=15); ax.grid(axis="y", color=RULE, lw=.8)
ax.set_ylabel("Typical error, as a share of the area mapped (log scale)", fontsize=16, color=INK)
ax.set_xlabel("Year the map was made", fontsize=16, color=INK)
ax.set_title("Lower is more accurate. Bars: 95% intervals.", loc="left", fontsize=16, color=MUT)
h = [Line2D([], [], marker="o", ls="", ms=14, mfc=c, mec="white", label=p) for p, c in COL.items()]
ax.legend(handles=h, loc="lower left", frameon=True, facecolor=PAPER, edgecolor=RULE, fontsize=15, title="Made as a", title_fontsize=15)
# grids
for i, k in enumerate(MAIN):
    g = G[k]; s = R["maps"][k]; c = COL[s["purpose"]]
    a = fig.add_axes([0.52 + (i % 4) * 0.12, 0.47 - (i // 4) * 0.335, 0.11, 0.24])
    for l in g["land"]:
        q = np.array(l); a.fill(q[:, 0], q[:, 1], color=LAND, lw=0)
    for l in g["grid"]:
        q = np.array(l); a.plot(q[:, 0], q[:, 1], color="#CDBF9F", lw=.5); a.plot(q[:, 0] + q[:, 2], q[:, 1] + q[:, 3], color=c, lw=1.1)
    hb = np.array(g["hull"]); a.set_xlim(hb[:, 0].min(), hb[:, 0].max()); a.set_ylim(hb[:, 1].min(), hb[:, 1].max())
    a.set_aspect("equal"); a.axis("off")
    fig.text(0.52 + (i % 4) * 0.12 + 0.055, 0.47 - (i // 4) * 0.335 + 0.25, f"{s['short']}, {s['date'].split(' (')[0]}", fontsize=16,
             fontweight="semibold", ha="center", va="bottom", color=INK)
    fig.text(0.52 + (i % 4) * 0.12 + 0.055, 0.47 - (i // 4) * 0.335 - 0.008, f"{s['median_km']:,.0f} km typical error" if s["median_km"] >= 10 else f"{s['median_km']:.1f} km typical error",
             fontsize=13.5, ha="center", va="top", color=MUT, family="IBM Plex Mono")
fig.text(0.52, 0.83, "Beige: real land. Grey: a regular grid on the real ground. Colour: the same grid as each map draws it.", fontsize=16, color=MUT, va="top")
fig.text(0.03, 0.035, "Data: control points from eight published studies by the author (Zenodo, CC BY 4.0); Ptolemy coordinates from Grasshoff and Defaux (CC BY 4.0); "
         "\ncoast Natural Earth. Method after MapAnalyst (Jenny and Hurni 2011).   Dr Tristan Hotham · maps.tristanhotham.com/map-accuracy",
         fontsize=13.5, color=MUT, family="IBM Plex Mono", va="bottom", linespacing=1.5)
out = f"{ROOT}/reddit/map_accuracy_collage.png"
fig.savefig(out, facecolor=PAPER)
print(out)
