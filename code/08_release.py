"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24104514, https://doi.org/10.5281/zenodo.24104514 and https://blog.tristanhotham.com/2026/10/31/map-accuracy/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Map_Accuracy"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
q = R["q"]
meta = {"title": "How accurate were old maps?",
        "slug": "map-accuracy",
        "excerpt": f"Eight old maps, from Ptolemy to Ino's survey of Japan, measured one way. Errors run from {q['ino']['rel']:.1f}% to {q['peutinger']['rel']:.1f}% of the area mapped, and they follow what a map was for more than when it was made.",
        "seo_description": "Ptolemy, the Peutinger Table, al-Idrisi, Hereford, a portolan chart, Gough, Saxton and Ino measured one way. Accuracy follows purpose, not date.",
        "tags": ["maps", "data visualisation", "history of cartography", "old maps", "map accuracy", "Ptolemy", "Mappa Mundi", "portolan charts"],
        "header_alt": "Title card on cream paper reading 'How accurate were old maps?' beside six bent grids showing how Ptolemy, the Hereford map, the Carta Pisana, the Gough Map, Saxton and al-Idrisi distort the real world."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("control_points.csv", "points_fit.csv", "frames.csv", "maps.csv", "measures.json", "grids.json", "results.json"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = re.sub(r"\\textit\{([^}]*)\}", r"\1", ab).replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("\\rho", "rho").replace("``", "\"").replace("''", "\"")
srcs = "".join(f"<li>{INFO[k]['name']}: doi:{INFO[k]['doi']}</li>" for k in [m[0] for m in MAPS])
zmeta = {"title": "How Accurate Were Old Maps? Eight Maps Across 1,700 Years, Measured One Way",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/map-accuracy/}}.</p><p>Control points from the author's earlier studies:</p><ul>{srcs}</ul><p>Ptolemy coordinates from Grasshoff and Defaux, Catalog of Ptolemy's Geography (doi:10.5281/zenodo.3585758, CC BY 4.0); coastlines Natural Earth (public domain). Text, figures and data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["history of cartography", "cartometric analysis", "map accuracy", "distortion grids", "Helmert transformation", "MapAnalyst", "Ptolemy", "portolan charts", "mappae mundi"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}] +
                                [{"identifier": INFO[k]["doi"], "relation": "isDerivedFrom", "resource_type": "publication"} for k in [m[0] for m in MAPS]],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
