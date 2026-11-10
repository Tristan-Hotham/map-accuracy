"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds the tables and compiles with xelatex.
Output: release/paper/Hotham_Map_Accuracy.pdf and .tex beside the f_*.pdf figures. The DOI stays a placeholder
(https://doi.org/10.5281/zenodo.24104514 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Map_Accuracy"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
MAIN = [m[0] for m in MAPS]; WHOLE = MAIN + ["catalan"]; SETS = [m[0] for m in SHEETS]


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    for k in ("f0", "f1", "f2", "f3"):
        if f == k: return f"{float(v):.{k[1]}f}".replace("-", "$-$")
    return tex(str(v))


def m(k):
    return R["maps"].get(k) or R["sets"][k]


def num(v, d=1):
    return f"{v:,.{d}f}".replace("-", "$-$") if v is not None else "n/a"


# inputs
FRAME = {"ptolemy": "Omega coordinates (degrees)", "peutinger": "Miller 1887 facsimile", "idrisi": "Miller 1928 reconstruction",
         "pisana": "scan", "hereford": "Miller 1896 facsimile", "gough": "photograph", "saxton": "BnF copy, scan", "ino": "1878 compilation",
         "catalan": "scan, sheets 5 to 8", "saxton_sheets": "BnF copy, 34 sheets", "ino_sheets": "LoC copy, sheets"}
POINTS = {"ptolemy": "identified places", "peutinger": "road stations", "idrisi": "towns", "pisana": "harbours, capes, mouths",
          "hereford": "inscriptions", "gough": "way stations", "saxton": "towns", "ino": "capes, islands", "catalan": "harbours, capes, mouths",
          "saxton_sheets": "towns", "ino_sheets": "coast points"}
rows = ""
for k in WHOLE + SETS:
    s = m(k)
    rows += (("\\midrule\n" if k in ("catalan",) else "") + f"{tex(s['name'])} & {tex(s['date'])} & {tex(s['purpose'])} & {tex(FRAME[k])} & {tex(POINTS[k])} & {s['n']:,} & {s['frames']} & \\footnotesize{{{s['doi'].split('zenodo.')[1]}}}\\\\\n")
TI = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Inputs. Control points from the author's earlier studies (Zenodo record numbers 10.5281/zenodo.N). Frames: the number of separately fitted images (sheets).}\\label{tab:inputs}"
      "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{p{2.9cm}p{1.9cm}p{1.2cm}p{2.5cm}p{2.3cm}rrr}\\toprule Map & Date & Purpose & Measured on & Points & $n$ & Frames & Zenodo\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for k in WHOLE + SETS:
    s = m(k)
    rows += (("\\midrule\n" if k == "catalan" else "") + f"{tex(s['short'])} & {s['n']:,} & {num(s['R_km'], 0)} & {num(s['median_km'], 1)} [{num(s['median_km_ci'][0], 1)}, {num(s['median_km_ci'][1], 1)}] & "
             f"{num(s['p90_km'], 0)} & {num(s['rel_pc'], 1)} [{num(s['rel_pc_ci'][0], 1)}, {num(s['rel_pc_ci'][1], 1)}] & {num(s['local_rel_pc'], 1)} [{num(s['local_rel_pc_ci'][0], 1)}, {num(s['local_rel_pc_ci'][1], 1)}] & "
             f"{num(s['turn_deg'], 0)} & {num(s['aniso'], 2)}\\\\\n")
TM = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{The common method. $R$: root mean square distance of the points from their centroid (km; median over sheets for sheet sets). Error: median great-circle error after the Helmert fit (km), 90th percentile, and median relative to $R$ (\\%). Neighbourhood: median error of a Helmert fit on each point's eight nearest neighbours, relative to their mean distance (\\%). 95\\% bootstrap intervals in brackets. Turn: degrees the map is turned anticlockwise from north. Aniso.: affine anisotropy.}\\label{tab:main}"
      "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lrrlrllrr}\\toprule Map & $n$ & $R$ & Median km [CI] & P90 & Relative \\% [CI] & Neighbourhood \\% [CI] & Turn & Aniso.\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
cols = [("rel_pc", "Main"), ("R1_eqc", "R1 eqc"), ("R1_merc", "R1 Merc."), ("R2_top", "R2 top"), ("R3_huber", "R3 Huber"), ("R4_loo", "R4 LOO"),
        ("R5_n40", "R5 $n=40$"), ("R7_k6", "R7 $k=6$"), ("R7_k12", "R7 $k=12$"), ("F1_shuffle", "F1 shuffled")]
rows = ""
for k in WHOLE + SETS:
    s = m(k); c = s["checks"]
    vals = [s["rel_pc"]] + [c.get(f) for f, _ in cols[1:]]
    rows += (("\\midrule\n" if k == "catalan" else "") + tex(s["short"]) + " & " + " & ".join(num(v, 1) for v in vals) + "\\\\\n")
h1 = R["H1_checks"]; r1 = R["H1"]
h1row = (f"\\midrule H1 $\\rho$ (date) & {num(r1['rel']['rho'], 2)} & {num(h1['R1_eqc']['rho'], 2)} & {num(h1['R1_merc']['rho'], 2)} & & {num(h1['R3_huber']['rho'], 2)} & {num(h1['R4_loo']['rho'], 2)} & & {num(h1['R7_k6']['rho'], 2)} & {num(h1['R7_k12']['rho'], 2)} & \\\\\n"
         f"H1 one-sided $p$ & {num(r1['rel']['p_one_sided'], 3)} & {num(h1['R1_eqc']['p_one_sided'], 3)} & {num(h1['R1_merc']['p_one_sided'], 3)} & & {num(h1['R3_huber']['p_one_sided'], 3)} & {num(h1['R4_loo']['p_one_sided'], 3)} & & {num(h1['R7_k6']['p_one_sided'], 3)} & {num(h1['R7_k12']['p_one_sided'], 3)} & \\\\\n")
TC = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Pre-specified checks: median relative error (\\%) of each map under each check (R7: neighbourhood error). n/a: fewer than ten top-confidence points per frame (R2) or fewer than 40 points (R5). Bottom rows: the H1 rank correlation between date and the column's measure across the eight maps, with its exact one-sided permutation $p$.}\\label{tab:checks}"
      "\\setlength{\\tabcolsep}{2.6pt}\\begin{tabular}{lrrrrrrrrrr}\\toprule Map & " + " & ".join(l for _, l in cols) + "\\\\\\midrule\n" + rows + h1row + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for k in WHOLE:
    h = R["home"][k]
    rows += f"{tex(m(k)['short'])} & {tex(h['home'])} & {num(h['rho'], 2)} [{num(h['ci'][0], 2)}, {num(h['ci'][1], 2)}] & {num(h['near_km'], 0)} & {num(h['far_km'], 0)}\\\\\n"
p = R["home"]["pooled"]
rows += (f"\\midrule Pooled (map FE) & & $b$ = {num(p['b'], 3)} (SE {num(p['se'], 3)}) & \\multicolumn{{2}}{{l}}{{wild bootstrap $p$ = {num(p['p_wild'], 3)}}}\\\\\n"
         f"\\quad leave one map out & & $b$ from {num(min(v['b'] for v in R['home']['pooled_lomo'].values()), 3)} to {num(max(v['b'] for v in R['home']['pooled_lomo'].values()), 3)} & \\multicolumn{{2}}{{l}}{{$n$ = {p['n']:,} points, {p['maps']} maps}}\\\\\n")
TH = ("\\begin{table}[tbp]\\centering\\small\\caption{Error and distance from home (H4). Spearman rank correlation between error and distance from the pre-set home, with 95\\% bootstrap interval; median error (km) of the nearest and farthest thirds of points. Pooled: OLS of $\\log(\\text{error}/R)$ on distance$/R$ with map fixed effects, standard errors clustered by map.}\\label{tab:home}"
      "\\begin{tabular}{llllr}\\toprule Map & Home & $\\rho$ [95\\% CI] & Near third & Far third\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for k in WHOLE:
    c = m(k)["checks"]; regs = c["R6_regions"]
    lo_k = min(regs, key=regs.get); hi_k = max(regs, key=regs.get)
    rows += f"{tex(m(k)['short'])} & {len(regs)} & {num(m(k)['rel_pc'], 1)} & {num(regs[lo_k], 1)} (without {tex(lo_k)}) & {num(regs[hi_k], 1)} (without {tex(hi_k)})\\\\\n"
TL = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Leave one region out (R6): the lowest and highest relative error when each region (or quadrant, for Saxton and Ino) is left out in turn.}\\label{tab:loro}"
      "\\begin{tabular}{lrrp{4.6cm}p{4.6cm}}\\toprule Map & Regions & Main \\% & Lowest \\% & Highest \\%\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for k in WHOLE + SETS:
    s = m(k); src = s["source"]
    if src["km"] is None:
        rows += f"{tex(s['short'])} & no planar median reported & & \\\\\n"; continue
    rows += f"{tex(s['short'])} & {tex(src['method'])} & {num(src['km'], 2 if src['km'] < 10 else 0)} & {num(src['here_km'], 2 if src['km'] < 10 else 0)}\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Consistency with the source studies (F2): each source study's own median error (km) and the comparable figure from the common method (same model where possible: affine for al-Idrisi, leave-one-out for the Ino sheets).}\\label{tab:src}"
      "\\begin{tabular}{llrr}\\toprule Map & Source study's method & Source km & Here km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_INPUTS", TI), ("TABLE_MAIN", TM), ("TABLE_CHECKS", TC), ("TABLE_HOME", TH), ("TABLE_LORO", TL), ("TABLE_SRC", TS)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda mm: tfmt(get(R, mm.group(1)), mm.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24104514", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("DSIT", "DCMS", "pre-registered", "preregistered"):
    assert bad not in t, bad
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
cites = set(re.findall(r"\\cite[pt]?\{([^}]+)\}", open(os.path.join(OUT, NAME + ".tex")).read()))
keys = {c.strip() for cc in cites for c in cc.split(",")}
bib = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", t))
print("uncited:", bib - keys, "missing:", keys - bib, "refs:", len(bib))
for lab in re.findall(r"\\label\{([^}]+)\}", t):
    assert f"\\ref{{{lab}}}" in t, ("unreferenced", lab)
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
