# map-accuracy: working notes

Brief: /home/claude/work/new13/BRIEFS.md section A (+ shared rules new12, new11, new10, new9, new8 BRIEFS, house brief
/home/claude/newdata/BRIEF.md, GIF brief /home/claude/gifs/BRIEF.md). Format refs: fame-half-life, byelection-attention.
Scratch: /home/claude/scratch/map-accuracy (delete at the end, by exact path).

A consolidation paper: no new readings. Inputs are the control points of eight published studies (author's earlier
preprints), re-fitted with one common method.

## What was known before the plan was written

The headline numbers of the eight source studies (their READMEs) were known: each used its own fit (Ptolemy: Helmert on
his degree grid, 144 km; al-Idrisi: affine, 239 km; Hereford: bearing/distance from Jerusalem, no planar fit median;
Pisana: Mercator similarity 93 km; Gough: similarity 17.6 km; Saxton: per-sheet similarity 1.37 km, general map 4.2 km;
Ino: per-sheet coast fits, 1878 map 7.9 km). No re-fit with the common method below, no relative measure, no local
measure, no distortion grid and no date comparison had been run when this plan was written.

## Inputs (read in place, never modified)

| Map | Date used | Source file | Map frame | Points |
|---|---|---|---|---|
| Ptolemy, Geography (coordinates) | c. 150 | ptolemy/data/places.csv | Omega recension lon_o, lat_o in degrees; plane x = lon cos 36 deg, y = lat | 2,358 |
| Peutinger Table | c. 300 (original; surviving copy c. 1200) | peutinger/data/located.csv | Miller 1887 facsimile pixels x, y | 465 |
| al-Idrisi, Tabula Rogeriana | 1154 | idrisi/data/located.csv | Miller 1928 reconstruction pixels as drawn (x_as_drawn, y_as_drawn) | 431 |
| Hereford Mappa Mundi | c. 1300 | mappa-mundi/data/located.csv | Miller 1896 facsimile pixels (x_miller, y_miller); rows with lat/lon | 143 |
| Carta Pisana (portolan) | c. 1275 | portolan-charts/data/points.csv chart=pisana | scan pixels x, y | 148 |
| Gough Map | c. 1360 | gough-map/data/located.csv | photograph pixels x, y | 163 |
| Saxton, general map | 1579 | saxton-atlas/data/located.csv sheet p014 | scan pixels | 46 |
| Ino, via the 1878 Dai Nihon Zenzu | 1821 survey (1878 compilation) | ino-japan/data/national_fit.csv | 1878 map pixels | 18 |

Sheet sets (each sheet its own frame): Saxton county sheets 1574 to 1579 (34 sheets, 811 points); Ino large-scale sheets
1821 (ino-japan/data/control_fit.csv: 93 points on 16 sheets; sheets with at least 4 points used). Supplementary: the
Catalan Atlas chart, 1375 (201 points), the second portolan in the source study.

Image pixels have y down: map plane = (x, -y). Ptolemy's coordinates: (lon cos 36 deg, lat), his own ratio for the
parallel of Rhodes (sensitivity: ratio 1).

## Analysis plan (written before any re-fit was run)

Question: measured one way, how accurate are eight historical maps made between about AD 150 and 1821, in what sense,
and does accuracy follow date or purpose?

Unit: a control point (a real place identified on a map and located on the ground) within a frame (a map, or one sheet
of an atlas). Outcome: positional error in km on the ground after fitting the map to reality.

Common method (one frame at a time):
1. True positions projected to an azimuthal equidistant plane centred on the frame's control-point centroid (km).
2. Fits from the map plane to the ground plane by least squares: Helmert (similarity: shift, one scale, one rotation,
   4 parameters; MAIN) and affine (6 parameters). A reflection check: the map plane is fixed as above; never mirrored.
3. Residual of each point = great-circle distance between its true position and its fitted position (fitted plane
   point taken back to lon/lat by the inverse projection). In-sample residuals; leave-one-out residuals as a check.
4. Per frame: n; scale (km per map unit); rotation of map north against true north (degrees, anticlockwise positive);
   median, 90th percentile and RMS error (km); R = root mean square distance of the points from their centroid (km),
   the size of the mapped area; RELATIVE ERROR = 100 x median error / R (%) (MAIN comparable measure); affine
   anisotropy (ratio of singular values).
5. Local error: for each point, a Helmert fit on its k = 8 nearest neighbours in the same frame (true positions; k =
   min(8, n - 1) with at least 3), the point itself left out, predicts its position; local error (km) and LOCAL
   RELATIVE ERROR = local error / mean true distance to those neighbours (%). Median per frame. This measures shape at
   the scale of a neighbourhood and does not depend on how well the map holds together as a whole.
6. Distance from the map's home: pre-set home points: Ptolemy Alexandria; Peutinger Rome; al-Idrisi Palermo; Hereford
   Jerusalem; Pisana Genoa; Catalan Palma de Mallorca; Gough London; Saxton general map London; Ino 1878 Tokyo.
   Per frame Spearman correlation between error and distance from home; pooled point-level OLS of
   log(error / R) on (distance from home / R) with map fixed effects (whole-map frames), SE clustered by map with a
   wild cluster bootstrap (Webb weights, 9,999 draws) because there are only 9 clusters.
7. Distortion grids (display, not used in any statistic): residual vectors interpolated with Hardy's multiquadric
   (scipy RBFInterpolator, kernel multiquadric, epsilon = 1 / median nearest-neighbour distance, smoothing fixed at
   1e-3 x n in units of R) over a regular grid (spacing R / 4) inside the buffered convex hull of the points; grid and
   Natural Earth coast deformed by the field; local areal scale of each cell recorded.
8. Uncertainty: 95% bootstrap intervals (2,000 draws) for median error, relative error and local relative error:
   points resampled within a single frame (refitting each time); sheets resampled for sheet sets.

Hypotheses and what would count against them:
- H1 progress: relative error falls with date across the eight maps (Spearman correlation between date and relative
  error < 0, exact permutation test over 8! orderings, one-sided). Against: p > 0.05 or a correlation near 0. I expect
  this to fail in the strong form: purpose and the kind of source matter more.
- H2 purpose: grouped a priori as world maps (Ptolemy, al-Idrisi, Hereford), route maps (Peutinger, Gough), sea charts
  (Pisana; Catalan supplementary), surveys (Saxton, Ino). Expect relative error: surveys < sea charts < route maps and
  world maps, and Hereford worst. Descriptive only (n = 8 maps; no test claimed).
- H3 regional distortion: residuals are spatially autocorrelated (Moran's I of the east and north residual components,
  8-nearest-neighbour weights, permutation test with 999 draws) on every map; local relative error well below the
  whole-map relative error. Against: I near 0.
- H4 centre and edge: error grows with distance from the map's home (pooled slope > 0). Against: pooled CI including 0.
- H5 stretch: the affine fit improves most on the Peutinger Table (strip format), reported as anisotropy and the
  affine/Helmert ratio. Descriptive.

Pre-specified checks:
- R1 projection of the ground: equirectangular at the centroid latitude and Mercator instead of azimuthal equidistant.
- R2 only the highest-confidence points (each source's top code).
- R3 robust Helmert (iteratively reweighted least squares, Huber weights, c = 1.345 MAD-scaled).
- R4 leave-one-out residuals instead of in-sample.
- R5 equal size: 40 points drawn per frame (500 draws), median relative error (frames with at least 40 points).
- R6 leave one region out (source regions; quadrants about the centroid where a frame has none): range of relative error.
- R7 k = 6 and 12 for the local error.
- R8 Ptolemy aspect ratio 1 instead of cos 36 deg.
- F1 falsification: map positions shuffled among the control points within each frame (200 draws): relative error of
  a map carrying no information; every real map must be far below it.
- F2 consistency: the common-method errors set beside each source study's own published figure.

Robustness language rule: a result is called robust only if it holds in every check above.

## Running log
- 01_points: 4,864 control points in 53 frames (8 whole maps 3,772 points; Catalan 201; Saxton sheets 811 on 34 sheets;
  Ino sheets 80 on 10 sheets). Catalan sheets 7 and 8 shifted by the source study's join offset (first run without it
  gave 156 km against the source's 88 km; fixed before any comparison was written up). Peutinger names cleaned after
  the main run; points_fit.csv names patched in fit order (numbers unchanged; a full rerun of 02 is identical).
- Sanity (F2): Gough 17.5 vs 17.6 km, Saxton 4.4 vs 4.23, Pisana 93.8 vs 93 (Mercator in source), Hereford 526 vs 516,
  Ino 1878 8.3 vs 7.9. Ptolemy 219 vs 144 (source fitted on his degree grid; equirectangular ground here gives 8.7%
  instead of 12.9%). Rotation signs agree with the sources (Pisana +9, Saxton sheets +8, Gough +95).
- Results as planned: H1 rho -0.71, exact one-sided p 0.029 (main), significant in 5 of 8 checks, NOT with an
  equirectangular/Mercator ground (p 0.098); pre-1500 maps rho -0.31 (exploratory). Reported as "weak, not robust".
- H3 second clause (neighbourhood relative error below whole-map relative error) fails on every map; the denominators
  differ, reported honestly in the paper. Moran's I significant on 7 of 8 (not Ino 1878).
- H4 pooled +35% per R, wild cluster bootstrap p 0.048; per map: positive on 5, negative on Hereford, null on 3.
- H5 holds (Peutinger anisotropy 8.1).

## References (all checked online during the build: title, authors, year, venue, volume, pages)
Verified via publisher/library/bibliography pages: Jenny and Hurni 2011 (PDF first page); Jenny et al. 2007,
Boutoura and Livieratos 2006, Balletti 2006, Livieratos 2006a/b, Forstner and Oehrli 1998, Beineke 2001 (MapAnalyst
literature list); Tobler 1966 (Deep Blue, abstract); Tobler 1994, Hardy 1971, Boutoura and Livieratos 1986 (Jenny and
Hurni reference list); Lloyd and Lilley 2009 (QUB, abstract); Lilley et al. 2009, Delano-Smith et al. 2017,
Solopova 2012, Smallwood 2010 (abstract read), Parsons 1958 (Historia Cartarum bibliography); Claeys Bouuaert et al.
2016 (researchr bibtex, abstract); Harley and Woodward 1987, 1992, 1994 and chapter pages (Chicago front matter);
Talbert 2010 (BMCR review: original c. 300, copy c. 1200); Nicolai 2016, Harvey 1996, Berggren and Jones 2000,
Stückelberger and Grasshoff 2006, Efron and Tibshirani 1993 (library catalogues); Edney 2019 (USM, description);
Woodward 1985 (abstract); Moran 1950 (OUP); Cameron et al. 2008 (RePEc, abstract); Webb 2023 (RePEc, abstract);
Huber 1964 (Encyclopedia of Mathematics reference); Evans and Lawrence 1979 (library catalogues); Westrem 2001
(Brepols); Bevan and Phillott 1873, Grasshoff and Defaux 2019 (source studies). Not checked: journal word limits
(search allowance exhausted), so the cover note says so.
