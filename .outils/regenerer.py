"""Régénère tous les graphiques du vault à partir des CSV de Données/.
Usage, depuis la racine du vault : python3 .outils/regenerer.py
"""
import csv, glob, os, re, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from graphiques import asset_chart, overview_chart, fdate

def fm(path):
    txt = open(path, encoding="utf-8").read()
    head = txt.split("---")[1] if txt.startswith("---") else ""
    return {k.strip(): v.strip().strip('"') for k, v in re.findall(r"^(\w+):(.*)$", head, re.M)}

def num(v): return float(v) if v not in ("", None) else None

overview = []
for note in sorted(glob.glob("Actifs/*.md")):
    meta = fm(note); t = meta.get("ticker")
    if not t or not os.path.exists(f"Données/{t}.csv"): continue
    rows = [{k: (v if k == "date" else num(v)) for k, v in r.items()} for r in csv.DictReader(open(f"Données/{t}.csv"))]
    asset_chart(t, meta["nom"], rows, f"Graphiques/{t}.png")
    biased = [r for r in rows if r["apex_biais"] is not None]
    if len(biased) >= 2:
        last = biased[-1]; target = dt.date.fromisoformat(last["date"]) - dt.timedelta(days=7)
        ref = min(biased[:-1], key=lambda r: abs((dt.date.fromisoformat(r["date"]) - target).days))
        overview.append((meta["nom"], ref["apex_biais"], last["apex_biais"], meta.get("echantillon_faible") == "true",
                         ref["date"], last["date"]))

if overview:
    overview.sort(key=lambda it: -it[2])
    d_then, d_now = overview[0][4], overview[0][5]
    overview_chart([it[:4] for it in overview], fdate(d_now), fdate(d_then), f"Graphiques/Journal/{d_now}-positionnement.png")
print(f"{len(overview)} contrats, graphiques régénérés")
