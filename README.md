# How accurate were old maps?

Eight maps across about 1,700 years, measured one way: Ptolemy's Geography (about AD 150), the Peutinger Table, al-Idrisi's world map (1154), the Carta Pisana (about 1275), the Hereford Mappa Mundi (about 1300), the Gough Map (about 1360), Saxton's general map of England and Wales (1579) and Ino Tadataka's survey of Japan (1821, through its 1878 compilation). A consolidation of eight earlier studies: the same 3,772 control points, re-fitted with one documented method, with distortion grids, bootstrap intervals and pre-specified checks.

Interactive page: https://maps.tristanhotham.com/map-accuracy/
Paper: https://doi.org/10.5281/zenodo.24104514
Blog post: https://blog.tristanhotham.com/2026/10/31/map-accuracy/
Code and data: https://github.com/Tristan-Hotham/map-accuracy

## Headline results

- Error as a share of the size of the area mapped (median Helmert error / root mean square distance of the places from their centre): from 1.7% (Ino, 1878 compilation) and 3.5% (Saxton) to 23.4% (Hereford) and 26.0% (Peutinger). In kilometres: 4.4 km (Saxton) to 526 km (Hereford).
- Date: rank correlation with relative error -0.71 (exact one-sided p = 0.029), carried by the two surveys. Before 1500: -0.31 (p = 0.28). Not significant with an equirectangular or Mercator ground (-0.52, p = 0.10). Significant in 5 of 8 checks.
- Purpose: medians of 2.6% (surveys), 8.0% (sea chart), 18.0% (route maps), 15.7% (world maps). Descriptive; one to three maps per group.
- Regional distortion: residuals spatially autocorrelated (Moran's I, p < 0.05) on 7 of 8 maps (not Ino 1878, 18 points).
- Centre and edge: error rises 35% per map-size step from home (pooled, map fixed effects, wild cluster bootstrap p = 0.048); rising on Ptolemy, Peutinger, al-Idrisi, Gough and the Catalan Atlas, falling on Hereford, no clear trend on the Carta Pisana, Saxton and Ino.
- Format: affine anisotropy 8.1 on the Peutinger Table (strip), 1.92 on Hereford, about 1.0 to 1.4 on the rest.
- Checks: the order of the eight maps holds under every check (rank correlation with the main order at least 0.95); shuffled map positions give 65% to 103%.

| Map | Date | Purpose | Places | Median km | Share of size % (95% CI) | Neighbourhood % |
|:-|:-|:-|-:|-:|-:|-:|
| Ptolemy's Geography | c. 150 | world map | 2,358 | 218.6 | 12.9 (12.2 to 13.7) | 41.7 |
| Peutinger Table | c. 300 (copy c. 1200) | route map | 465 | 348.6 | 26.0 (24.8 to 28.2) | 37.2 |
| al-Idrisi's world map | 1154 | world map | 431 | 328.3 | 15.7 (14.7 to 17.2) | 36.6 |
| Carta Pisana | c. 1275 | sea chart | 148 | 93.8 | 8.0 (6.8 to 9.6) | 17.8 |
| Hereford Mappa Mundi | c. 1300 | world map | 143 | 526.1 | 23.4 (20.1 to 29.3) | 47.6 |
| Gough Map | c. 1360 | route map | 163 | 17.5 | 10.0 (8.0 to 12.7) | 22.0 |
| Saxton's general map | 1579 | survey | 46 | 4.4 | 3.5 (2.6 to 4.2) | 10.2 |
| Ino's Japan (1878 compilation) | 1821 (compiled 1878) | survey | 18 | 8.3 | 1.7 (1.0 to 2.2) | 2.6 |
| Catalan Atlas chart | 1375 | sea chart | 201 | 117.1 | 8.6 (7.3 to 10.0) | 15.4 |
| Saxton's county sheets | 1574 to 1579 | survey | 811 | 1.4 | 4.9 (4.5 to 5.4) | 7.0 |
| Ino's large-scale sheets | 1821 | survey | 80 | 0.5 | 3.4 (2.0 to 5.1) | 4.5 |

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

- Control points from the author's earlier studies (CC BY 4.0): Ptolemy's Geography (doi:10.5281/zenodo.23882603), Peutinger Table (doi:10.5281/zenodo.23882605), al-Idrisi's world map (doi:10.5281/zenodo.23882607), Carta Pisana (doi:10.5281/zenodo.24044645), Hereford Mappa Mundi (doi:10.5281/zenodo.23878612), Gough Map (doi:10.5281/zenodo.24043678), Saxton's general map (doi:10.5281/zenodo.24052723), Ino's Japan (1878 compilation) (doi:10.5281/zenodo.23882609).
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

Hotham, T. (2026) How accurate were old maps? Eight maps across 1,700 years, measured one way. Zenodo. https://doi.org/10.5281/zenodo.24104514

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
