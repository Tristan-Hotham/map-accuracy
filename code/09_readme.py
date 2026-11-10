"""Step 9: README.md from data/results.json. 10.5281/zenodo.24104514, https://doi.org/10.5281/zenodo.24104514 and https://blog.tristanhotham.com/2026/10/31/map-accuracy/ are left for the publisher."""
from common import *

R = jload(f"{DATA}/results.json"); q = R["q"]
MAIN = [m[0] for m in MAPS]


def m(k):
    return R["maps"].get(k) or R["sets"][k]


rows = "\n".join(f"| {m(k)['name']} | {m(k)['date']} | {m(k)['purpose']} | {m(k)['n']:,} | {m(k)['median_km']:.1f} | {m(k)['rel_pc']:.1f} ({m(k)['rel_pc_ci'][0]:.1f} to {m(k)['rel_pc_ci'][1]:.1f}) | {m(k)['local_rel_pc']:.1f} |"
                 for k in MAIN + ["catalan", "saxton_sheets", "ino_sheets"])
h1 = R["H1"]; pre = R["H1_checks"]["pre1500"]; hp = R["home"]["pooled"]
txt = f"""# How accurate were old maps?

Eight maps across about 1,700 years, measured one way: Ptolemy's Geography (about AD 150), the Peutinger Table, al-Idrisi's world map (1154), the Carta Pisana (about 1275), the Hereford Mappa Mundi (about 1300), the Gough Map (about 1360), Saxton's general map of England and Wales (1579) and Ino Tadataka's survey of Japan (1821, through its 1878 compilation). A consolidation of eight earlier studies: the same {R['n_points_whole']:,} control points, re-fitted with one documented method, with distortion grids, bootstrap intervals and pre-specified checks.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24104514}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/map-accuracy/}}
Code and data: {REPO}

## Headline results

- Error as a share of the size of the area mapped (median Helmert error / root mean square distance of the places from their centre): from {q['ino']['rel']:.1f}% (Ino, 1878 compilation) and {q['saxton']['rel']:.1f}% (Saxton) to {q['hereford']['rel']:.1f}% (Hereford) and {q['peutinger']['rel']:.1f}% (Peutinger). In kilometres: {q['saxton']['km']:.1f} km (Saxton) to {q['hereford']['km']:.0f} km (Hereford).
- Date: rank correlation with relative error {h1['rel']['rho']:.2f} (exact one-sided p = {h1['rel']['p_one_sided']:.3f}), carried by the two surveys. Before 1500: {pre['rho']:.2f} (p = {pre['p_one_sided']:.2f}). Not significant with an equirectangular or Mercator ground ({R['H1_checks']['R1_eqc']['rho']:.2f}, p = {R['H1_checks']['R1_eqc']['p_one_sided']:.2f}). Significant in {R['H1_n_sig']} of {R['H1_n_checks']} checks.
- Purpose: medians of {R['purpose']['survey']['median_rel']:.1f}% (surveys), {R['purpose']['sea chart']['median_rel']:.1f}% (sea chart), {R['purpose']['route map']['median_rel']:.1f}% (route maps), {R['purpose']['world map']['median_rel']:.1f}% (world maps). Descriptive; one to three maps per group.
- Regional distortion: residuals spatially autocorrelated (Moran's I, p < 0.05) on {R['H3']['maps_sig']} of 8 maps (not Ino 1878, 18 points).
- Centre and edge: error rises {hp['pct_per_R']:.0f}% per map-size step from home (pooled, map fixed effects, wild cluster bootstrap p = {hp['p_wild']:.3f}); rising on Ptolemy, Peutinger, al-Idrisi, Gough and the Catalan Atlas, falling on Hereford, no clear trend on the Carta Pisana, Saxton and Ino.
- Format: affine anisotropy {m('peutinger')['aniso']:.1f} on the Peutinger Table (strip), {m('hereford')['aniso']:.2f} on Hereford, about 1.0 to 1.4 on the rest.
- Checks: the order of the eight maps holds under every check (rank correlation with the main order at least {R['order_corr_min']:.2f}); shuffled map positions give {R['shuffle_range'][0]:.0f}% to {R['shuffle_range'][1]:.0f}%.

| Map | Date | Purpose | Places | Median km | Share of size % (95% CI) | Neighbourhood % |
|:-|:-|:-|-:|-:|-:|-:|
{rows}

## Files

| File | What it is |
|:-|:-|
| `index.html`, `js/page.js` | The interactive page (built by `code/06_build_site.py`): distortion grid explorer with a bend slider, layers, search and full-screen button; comparison chart and table. Loads `data/site.json`. |
| `header.png` | Social card, 1200 x 630. |
| `img/*.jpg` | Figures for the page. |
| `data/control_points.csv` | Input assembled from the eight studies: map, frame (sheet), place, region, true lat/lon, map-plane x, y, confidence. |
| `data/points_fit.csv` | One row per control point: fitted position, east and north error, Helmert, affine, robust, leave-one-out, equirectangular and Mercator errors, neighbourhood error, distance from home. |
| `data/frames.csv`, `data/maps.csv` | One row per frame; the comparison table. |
| `data/measures.json`, `data/grids.json`, `data/site.json`, `data/results.json` | All measures and checks; distortion grids; page data; every number quoted anywhere. |
| `code/` | Scripts, run in order (`fitlib.py` holds the common method), page, paper and blog templates, `qa.js`. |
| `release/` | Paper and cover note (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG), GIF and post text. |
| `NOTES.md` | Working notes with the analysis plan written before the re-fit. |

## Method in brief

- Frames: each whole map; Saxton's 34 county sheets and Ino's large-scale sheets (at least four points) as sheet sets; the Catalan Atlas chart as a supplementary row (sheets 7 and 8 shifted by the source study's join offset).
- Ground: azimuthal equidistant projection centred on each frame's points. Map plane: image pixels (x, -y); Ptolemy (lon cos 36, lat).
- Fit: Helmert (similarity) by least squares (affine as a check); error = great-circle distance from fitted to true position. Relative error = median / R, R the root mean square distance of the points from their centroid. Neighbourhood error: Helmert fit on the eight nearest neighbours, error / their mean distance.
- Distortion grids: multiquadric interpolation of the residual vectors (after Hardy 1971 and MapAnalyst), regular grid of spacing R/4 inside the buffered hull of the points. Display only.
- Uncertainty: 2,000 bootstrap resamples (points within a map; sheets for sheet sets). Hypotheses and checks in `NOTES.md`, written before the re-fit.
- Caveats: the places are those that could be identified; several maps are measured on reproductions (Miller's facsimiles and his reconstruction of al-Idrisi); Ino's whole-country frame is the 1878 compilation with 18 points; the projection of the ground moves the levels for large maps; eight maps cannot separate date from purpose.

## Sources and licences

- Control points from the author's earlier studies (CC BY 4.0): {', '.join(f"{INFO[k]['name']} (doi:{INFO[k]['doi']})" for k in MAIN)}.
- Ptolemy's coordinates: Grasshoff, G. and Defaux, O. (2019) Catalog of Ptolemy's Geography, doi:10.5281/zenodo.3585758, CC BY 4.0. Peutinger station positions: OmnesViae (René Voorburg).
- Natural Earth 1:50m land (public domain).
- Text, figures and data CC BY 4.0; code MIT (see `LICENSE`).

## How to rerun

Needs Python 3 with numpy, pandas, scipy, pyproj, shapely, matplotlib and Pillow, xelatex and pdftotext; node with Playwright for `code/qa.js`. Step 01 reads the eight source studies' `data/` folders (paths in `code/common.py`, `MA_STUDIES`); from step 02 on only `data/` is needed.

```
python3 code/01_points.py      # control points from the eight studies
python3 code/02_fit.py         # common method, checks, bootstrap (about 6 minutes)
python3 code/03_grids.py       # distortion grids
python3 code/04_results.py     # results.json, maps.csv, site.json
python3 code/05_figures.py     # figures and header
python3 code/06_build_site.py  # index.html
python3 code/07_paper.py       # paper PDF (DOI=10.5281/zenodo.N to fill the DOI)
python3 code/08_release.py     # blog post, Zenodo files
python3 code/09_readme.py      # this README
python3 reddit/collage.py      # Reddit collage
```

## Citation

Hotham, T. (2026) How accurate were old maps? Eight maps across 1,700 years, measured one way. Zenodo. {{https://doi.org/10.5281/zenodo.24104514}}

{AI}
"""
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in txt, bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(txt)
print("README", len(txt.split()), "words")
