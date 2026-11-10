"""Step 5: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and header.png (1200 x 630). Light paper background; colour = what the map was made for."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
import numpy as np, pandas as pd
from PIL import Image
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE, LAND = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3", "#E6D8B6"
COL = {"world map": "#B4442E", "route map": "#C98A2B", "sea chart": "#2F6A9E", "survey": "#3E7D5A"}
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3.2, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
G = jload(f"{DATA}/grids.json")
MAIN = [m[0] for m in MAPS]; WHOLE = MAIN + ["catalan"]
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD, SCR):
    os.makedirs(d_, exist_ok=True)
SRC = "Data: control points from eight published studies by the author (Zenodo, CC BY 4.0); Natural Earth (public domain)\nmaps.tristanhotham.com/map-accuracy"


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.05, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8.3, family=MONO, color=MUT, va="bottom", linespacing=1.4)


def m(k):
    return R["maps"].get(k) or R["sets"][k]


def legend_purpose(ax, loc="upper right", extra=()):
    h = [Line2D([], [], marker="o", ls="", ms=9, mfc=c, mec="white", label=p) for p, c in COL.items()]
    h += list(extra)
    ax.legend(handles=h, loc=loc, frameon=False, fontsize=10.5)


# ---------- 1. accuracy against date ----------
LABOFF = {"ptolemy": (8, 6), "peutinger": (8, 4), "idrisi": (-8, 8), "pisana": (-10, -16), "hereford": (8, 6), "gough": (10, -2),
          "saxton": (-8, 9), "ino": (-6, 9), "catalan": (8, -12), "saxton_sheets": (8, -12), "ino_sheets": (8, -10)}
fig, axs = plt.subplots(1, 2, figsize=(14, 7.2))
fig.subplots_adjust(left=0.07, right=0.98, top=0.79, bottom=0.17, wspace=0.22)
for ax, (fld, lo, hi, lab) in zip(axs, (("rel_pc", "rel_pc_ci", None, "Whole-map error, % of the mapped area's size"),
                                        ("local_rel_pc", "local_rel_pc_ci", None, "Neighbourhood error, % of the distance to neighbours"))):
    for k in WHOLE + ["saxton_sheets", "ino_sheets"]:
        s = m(k); c = COL[s["purpose"]]
        x = s["year"]; y = s[fld]; ci = s[lo]
        hollow = k in ("catalan", "saxton_sheets", "ino_sheets")
        ax.plot([x, x], ci, color=c, lw=2, alpha=.55 if hollow else .9, solid_capstyle="round")
        ax.plot(x, y, "o", ms=10 if not hollow else 8, mfc=PAPER if hollow else c, mec=c, mew=2)
        dx, dy = LABOFF[k]
        ax.annotate(s["short"], (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=10.5, color=INK,
                    ha="left" if dx > 0 else "right", path_effects=HALO)
    ax.set_yscale("log")
    ax.set_xlim(50, 1950); ax.set_ylabel(lab, fontsize=11.5)
    ax.set_xlabel("Date of the map (Peutinger: the lost original; copy about 1200)", fontsize=10.5)
    ax.grid(axis="y", color=RULE, lw=.6)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
axs[0].set_ylim(1, 40); axs[1].set_ylim(2, 70)
axs[0].set_yticks([1, 2, 5, 10, 20, 40]); axs[1].set_yticks([2, 5, 10, 20, 50])
for a_ in axs:
    a_.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a_.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
axs[0].set_title("A. The whole map after one scale and one turn", loc="left", fontsize=12.5, color=INK)
axs[1].set_title("B. Each place against its eight nearest neighbours", loc="left", fontsize=12.5, color=INK)
legend_purpose(axs[1], "lower left", [Line2D([], [], marker="o", ls="", ms=8, mfc=PAPER, mec=MUT, mew=2, label="sheet sets, second portolan")])
title(fig, "How accurate were old maps?", f"Median error of {R['n_maps']} maps measured one way, with 95% bootstrap intervals. Lower is better; log scale.", 0.965)
foot(fig)
out(fig, "compare")

# ---------- 2. distortion grids, small multiples ----------
fig, axs = plt.subplots(3, 3, figsize=(14, 14.6))
fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.075, wspace=0.06, hspace=0.18)
for ax, k in zip(axs.flat, WHOLE):
    g = G[k]; s = m(k); c = COL[s["purpose"]]
    for l in g["land"]:
        a = np.array(l); ax.fill(a[:, 0], a[:, 1], color=LAND, lw=0, zorder=0)
    for l in g["grid"]:
        a = np.array(l); ax.plot(a[:, 0], a[:, 1], color="#C9BC9C", lw=.5, zorder=1)
        ax.plot(a[:, 0] + a[:, 2], a[:, 1] + a[:, 3], color=c, lw=.9, zorder=2)
    p = np.array([x[:4] for x in g["pts"]])
    ax.scatter(p[:, 0], p[:, 1], s=2.5 if len(p) > 1000 else 5, c=INK, lw=0, zorder=3, rasterized=True)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{s['short']}, {s['date'].split(' (')[0]}", loc="left", fontsize=13, color=INK, family=DISP, fontweight="bold")
    ax.text(0.0, -0.02, f"{s['n']:,} places · error {s['rel_pc']:.1f}% · {s['median_km']:.0f} km", transform=ax.transAxes, fontsize=9.5,
            family=MONO, color=MUT, va="top")
title(fig, "Eight old maps, bent to fit the real world",
      "Grey: a regular grid on the real ground. Colour: the same grid as each map draws it, after one best scale, shift and turn.\nDots: the places measured. North is up on every panel; each panel at its own scale.", 0.975)
foot(fig)
out(fig, "grids")

# ---------- 3. absolute error against size ----------
fig, ax = plt.subplots(figsize=(11, 7.6))
fig.subplots_adjust(left=0.1, right=0.97, top=0.82, bottom=0.15)
xs = np.array([3, 4000])
for pc in (1, 3, 10, 30):
    ax.plot(xs, xs * pc / 100, color=RULE, lw=1, zorder=0)
    xl = 0.15 * 100 / pc * 1.15 if pc > 1 else 16
    ax.text(max(xl, 5.6), max(xl, 5.6) * pc / 100 * 1.08, f"{pc}%", fontsize=10.5, color=MUT, ha="left", va="bottom", rotation=27, path_effects=HALO)
for k in WHOLE + ["saxton_sheets", "ino_sheets"]:
    s = m(k); c = COL[s["purpose"]]; hollow = k in ("catalan", "saxton_sheets", "ino_sheets")
    ax.plot(s["R_km"], s["median_km"], "o", ms=11, mfc=PAPER if hollow else c, mec=c, mew=2)
    ax.plot([s["R_km"]] * 2, s["median_km_ci"], color=c, lw=2, alpha=.7)
    off = {"idrisi": (9, -8), "ptolemy": (-10, -6), "peutinger": (-10, 6), "catalan": (9, 2), "pisana": (9, -12)}.get(k, (9, -4))
    ax.annotate(s["short"], (s["R_km"], s["median_km"]), xytext=off, textcoords="offset points", fontsize=10.5, path_effects=HALO,
                ha="right" if off[0] < 0 else "left")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(5, 4000); ax.set_ylim(0.15, 900)
ax.set_xlabel("Size of the mapped area (root mean square distance of the places from their centre, km)")
ax.set_ylabel("Median error after the fit, km")
for a_ in (ax.xaxis, ax.yaxis):
    a_.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax.grid(color=RULE, lw=.4)
legend_purpose(ax, "upper left")
title(fig, "Kilometres of error grow with the size of the map", "Median error against the size of the area mapped. Grey lines: error as a share of size.")
foot(fig)
out(fig, "size")

# ---------- 4. error against distance from the map's home ----------
T = pd.read_csv(f"{DATA}/points_fit.csv", dtype={"pid": str, "frame": str})
fig, axs = plt.subplots(3, 3, figsize=(14, 11.5), sharex=False)
fig.subplots_adjust(left=0.07, right=0.98, top=0.86, bottom=0.1, wspace=0.25, hspace=0.42)
for ax, k in zip(axs.flat, WHOLE):
    d = T[T["map"] == k]; s = m(k); c = COL[s["purpose"]]; h = R["home"][k]
    ax.scatter(d.home_km, d.err_km, s=4, color=c, alpha=.35, lw=0, rasterized=True)
    qs = np.quantile(d.home_km, np.linspace(0, 1, 7))
    mid = [(qs[i] + qs[i + 1]) / 2 for i in range(6)]
    med = [d[(d.home_km >= qs[i]) & (d.home_km <= qs[i + 1])].err_km.median() for i in range(6)]
    ax.plot(mid, med, color=INK, lw=2)
    ax.set_title(f"{s['short']}: from {h['home']}", loc="left", fontsize=12, color=INK)
    ax.text(0.98, 0.95, f"rank corr. {h['rho']:+.2f}", transform=ax.transAxes, ha="right", va="top", fontsize=9.5, family=MONO, color=MUT)
    ax.set_xlabel("km from home", fontsize=9.5); ax.set_ylabel("error, km", fontsize=9.5)
    ax.set_ylim(0, np.percentile(d.err_km, 97) * 1.15)
title(fig, "Do maps get worse away from home?", "Each dot is a place: its error against its distance from the map's centre of knowledge. Line: medians of six distance bands.", 0.97)
foot(fig)
out(fig, "home")

# ---------- 5. checks ----------
labels = [("rel_pc", "Main: azimuthal equidistant, Helmert"), ("R1_eqc", "Equirectangular ground"), ("R1_merc", "Mercator ground"),
          ("R2_top", "Highest-confidence places only"), ("R3_huber", "Robust (Huber) fit"), ("R4_loo", "Leave-one-out errors"),
          ("R5_n40", "40 places per map"), ("F1_shuffle", "Shuffled map positions (no information)")]
fig, ax = plt.subplots(figsize=(13, 8.2))
fig.subplots_adjust(left=0.2, right=0.97, top=0.83, bottom=0.15)
order = R["rank_rel"]
mk = ["o", "s", "D", "^", "v", "P", "X", "*"]
cols = ["#2B2119", "#2F6A9E", "#5B8DB8", "#3E7D5A", "#C98A2B", "#8A6FB0", "#B4442E", "#9C9384"]
for j, (fld, lab) in enumerate(labels):
    for i, k in enumerate(order):
        s = m(k)
        v = s["rel_pc"] if fld == "rel_pc" else s["checks"].get(fld)
        if v is None:
            continue
        ax.plot(v, i + (j - 3.5) * 0.08, mk[j], color=cols[j], ms=8 if j == 0 else 6.5, mec="white", mew=.6)
    if fld == "rel_pc":
        for i, k in enumerate(order):
            s = m(k); ax.plot(s["rel_pc_ci"], [i - 0.28] * 2, color=INK, lw=1.4)
ax.set_yticks(range(len(order))); ax.set_yticklabels([f"{m(k)['short']} ({m(k)['date'].split(' (')[0]})" for k in order])
ax.set_xscale("log"); ax.set_xlim(1, 130)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
ax.set_xlabel("Whole-map error, % of the mapped area's size")
ax.invert_yaxis(); ax.grid(axis="x", color=RULE, lw=.5)
ax.legend(handles=[Line2D([], [], marker=mk[j], ls="", color=cols[j], ms=7, mec="white", label=lab) for j, (f_, lab) in enumerate(labels)],
          loc="lower right", fontsize=9.5, frameon=True, facecolor=PAPER, edgecolor=RULE)
title(fig, "The order holds; the shuffled maps show what no skill looks like", "Each map's error under the main method and every planned check. Bar: 95% bootstrap interval of the main estimate.")
foot(fig)
out(fig, "checks")

# ---------- 6. which way is up ----------
fig, axs = plt.subplots(2, 4, figsize=(14, 7.6))
fig.subplots_adjust(left=0.03, right=0.97, top=0.8, bottom=0.1, wspace=0.15, hspace=0.35)
for ax, k in zip(axs.flat, MAIN):
    s = m(k); c = COL[s["purpose"]]; t = math.radians(s["turn_deg"])
    circ = plt.Circle((0, 0), 1, fill=False, color=RULE, lw=1.5); ax.add_patch(circ)
    ax.annotate("", (0, 0.95), (0, 0), arrowprops=dict(arrowstyle="-|>", color=MUT, lw=1.6, mutation_scale=14))
    ax.text(0, 1.08, "N", ha="center", va="bottom", fontsize=10, color=MUT, family=MONO)
    # true north as the map draws it: the map is turned anticlockwise by t, so north points at angle t anticlockwise from up
    nx, ny = -math.sin(t) * 0.95, math.cos(t) * 0.95
    ax.annotate("", (nx, ny), (0, 0), arrowprops=dict(arrowstyle="-|>", color=c, lw=3, mutation_scale=20))
    ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.35, 1.35); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{s['short']}", fontsize=13, color=INK, family=DISP, fontweight="bold")
    ax.text(0, -1.3, ("south at the top" if abs(s['turn_deg']) > 170 else f"turned {abs(s['turn_deg']):.0f}° {'anticlockwise' if s['turn_deg'] > 0 else 'clockwise'}") if abs(s['turn_deg']) >= 0.5 else "north up",
            ha="center", va="top", fontsize=10, family=MONO, color=MUT)
title(fig, "Which way is up?", "Grey: the top of each map. Colour: where true north points on the map, from the best fit.", 0.96)
foot(fig)
out(fig, "turns")

# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.text(0.045, 0.86, "How accurate", fontsize=40, family=DISP, fontweight="bold", color=INK, va="top")
fig.text(0.045, 0.74, "were old maps?", fontsize=40, family=DISP, fontweight="bold", color=COL["world map"], va="top")
fig.text(0.045, 0.57, f"Eight maps across {round(R['span_years'], -2):,} years,\nmeasured one way", fontsize=17, color=INK, va="top", linespacing=1.3)
fig.text(0.045, 0.08, "Dr Tristan Hotham · Independent researcher · 2026", fontsize=11, family=MONO, color=MUT)
picks = ["ptolemy", "hereford", "pisana", "gough", "saxton", "idrisi"]
for i, k in enumerate(picks):
    ax = fig.add_axes([0.47 + (i % 3) * 0.175, 0.52 - (i // 3) * 0.44, 0.17, 0.4])
    g = G[k]; c = COL[m(k)["purpose"]]
    for l in g["land"]:
        a = np.array(l); ax.fill(a[:, 0] + a[:, 2], a[:, 1] + a[:, 3], color=LAND, lw=0)
    for l in g["grid"]:
        a = np.array(l); ax.plot(a[:, 0] + a[:, 2], a[:, 1] + a[:, 3], color=c, lw=.7)
    ax.set_aspect("equal"); ax.axis("off")
    ax.text(0.5, -0.02, m(k)["short"], transform=ax.transAxes, ha="center", va="top", fontsize=10, family=MONO, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
