**Title:** [OC] How accurate were old maps? I measured eight maps from AD 150 to 1821 the same way: errors run from 1.7% of the area mapped (Ino's Japan) to 26.0% (the Peutinger Table), and they follow what a map was for more than when it was made

**Body:**

I took the places I had identified on eight old maps in earlier studies (3,772 in all) and fitted every map to the real world the same way: one best scale, shift and turn, then the distance on the globe from where the map puts each place to where it really is. Because a map of Britain will always be out by fewer kilometres than a map of the world, the main yardstick is the typical error as a share of the size of the area mapped.

- Ino's survey of Japan (1821, as compiled in 1878): 1.7%. Saxton's England and Wales (1579): 3.5%.
- Carta Pisana, a sea chart of about 1275: 8.0%. Gough Map of Britain: 10.0%.
- Ptolemy (about AD 150): 12.9%. al-Idrisi (1154): 15.7%. Hereford Mappa Mundi: 23.4%. Peutinger Table: 26.0%.
- Later maps are better overall, but that rests on the two surveys, which come last. Among the six maps before 1500 there is no clear trend with date, and the date trend holds in only 5 of 8 planned checks. Accuracy here is not progress.
- The coloured grids show how each map bends the real world: the Peutinger Table squeezes it into a ribbon, the Hereford map folds it round Jerusalem.

Interactive version (bend the world into each map's shape): https://maps.tristanhotham.com/map-accuracy/

**Source comment:**

Data: control points from eight earlier studies of mine (Zenodo, CC BY 4.0), Ptolemy's coordinates from Grasshoff and Defaux's catalogue (CC BY 4.0), coastlines from Natural Earth. Method: Helmert (similarity) fits on an azimuthal equidistant projection, bootstrap intervals, distortion grids from a multiquadric surface as in MapAnalyst; method and checks pre-specified in a written plan before the re-fit. Tools: Python (numpy, scipy, pyproj, matplotlib). Paper, data and code: https://github.com/Tristan-Hotham/map-accuracy
