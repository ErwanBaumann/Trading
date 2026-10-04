"""Régénère les graphiques à partir des CSV de Données/, dans Graphiques/<date du dernier relevé>/.

Usage, depuis la racine du dépôt : python3 .outils/regenerer.py
Chaque semaine a son propre dossier daté : les liens déjà intégrés dans Notion ne changent jamais
(Notion garde les images externes en cache, un nom de fichier neuf garantit l'affichage à jour).
"""
import csv, json, os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from graphiques import asset_chart, overview_chart, fdate

WEAK_USD = 5e6  # en dessous : échantillon faible (cercle vide sur la vue d'ensemble)

def num(v): return float(v) if v not in ("", None) else None

reg = json.load(open("actifs.json", encoding="utf-8"))
overview, last_date = [], None
for a in reg["contrats"]:
    t, name = a["ticker"], a["nom"]
    path = f"Données/{t}.csv"
    if not os.path.exists(path): continue
    rows = [{k: (v if k == "date" else num(v)) for k, v in r.items()} for r in csv.DictReader(open(path))]
    last_date = max(last_date or rows[-1]["date"], rows[-1]["date"])
    out_dir = f"Graphiques/{rows[-1]['date']}"
    os.makedirs(out_dir, exist_ok=True)
    asset_chart(t, name, rows, f"{out_dir}/{t}.png")
    biased = [r for r in rows if r["apex_biais"] is not None]
    if len(biased) >= 2:
        last = biased[-1]; target = dt.date.fromisoformat(last["date"]) - dt.timedelta(days=7)
        ref = min(biased[:-1], key=lambda r: abs((dt.date.fromisoformat(r["date"]) - target).days))
        weak = (last.get("apex_engage_usd") or 0) < WEAK_USD
        overview.append((name, ref["apex_biais"], last["apex_biais"], weak, ref["date"], last["date"]))

if overview:
    overview.sort(key=lambda it: -it[2])
    d_then, d_now = overview[0][4], overview[0][5]
    overview_chart([it[:4] for it in overview], fdate(d_now), fdate(d_then), f"Graphiques/{d_now}/positionnement.png")
print(f"{len(overview)} contrats · graphiques écrits dans Graphiques/{last_date}/")
