"""Indicateurs de marché et règles d'alerte, calculés de façon déterministe.

Ce script ne contient aucune donnée personnelle et n'en écrit jamais dans le dépôt :
les fichiers de cours ou de portefeuille qu'on lui passe doivent rester HORS du dépôt
(dossier temporaire de la session), et rien de ce qu'il produit ne doit être validé.

Commandes (sortie JSON sur la sortie standard) :

  titre      indicateurs d'un titre à partir de ses clôtures quotidiennes, seuils par défaut,
             signaux de vigilance techniques, et taille selon la règle si l'enveloppe est donnée
  position   état d'une position face à ses seuils (plus-value, distances, règles franchies)
  contrat    semaine type d'un contrat Hyperliquid à partir de Données/<TICKER>.csv (jours ouvrés)
  lecture    écart d'une lecture à sa référence, en semaines types, et statut à l'échéance
  indice     indice base 100 du portefeuille hors versements, et recul depuis son plus haut
  fantome    valeur d'un portefeuille fantôme qui aurait investi les mêmes montants dans un ETF

Fichier de cours : CSV avec une colonne de date (date) et une colonne de clôture
(close, cours ou clôture), dans n'importe quel ordre ; les autres colonnes sont ignorées.

Exemples :
  python3 .outils/indicateurs.py titre --cours /tmp/s/NVDA.csv --ref /tmp/s/SMH.csv --type action
  python3 .outils/indicateurs.py titre --cours /tmp/s/X.csv --enveloppe 10000 --risque 2
  python3 .outils/indicateurs.py position --prix-revient 100 --cours-eur 91 --plus-haut-eur 104 \
          --stop-souple 10 --stop-ferme 16.8 --objectif 20 --suiveur 13.4
  python3 .outils/indicateurs.py contrat NVDA
  python3 .outils/indicateurs.py lecture --camp acheteurs --cours-ouverture 230 --cours 241 \
          --ref-ouverture 630 --ref 640 --semaine-type 6.7 --echeance
  python3 .outils/indicateurs.py indice --suivi /tmp/s/suivi.csv        (date,valeur,flux)
  python3 .outils/indicateurs.py fantome --mouvements /tmp/s/mv.csv --cours-etf 1234.5
                                                           (date,montant,cours_etf ; vente = montant négatif)
"""
import argparse, csv, datetime as dt, json, math, os, statistics, sys

# ---------------------------------------------------------------------------
# Paramètres des règles d'Erwan (page Méthode et page Portefeuille).
# Gelés jusqu'au 4 janvier 2027 : ne pas les modifier avant le bilan trimestriel.
# Les seuils modifiés à la main dans la base Positions priment toujours.
# ---------------------------------------------------------------------------
SEANCES_SIGMA = 60          # séances pour l'écart-type quotidien
MM = 50                     # moyenne mobile des clôtures
PENTE_RECUL = 10            # la MM50 est comparée à sa valeur d'il y a 10 séances
FORCE_SEANCES = 20          # force relative face à l'ETF de référence
FORCE_SEUIL = -1.0          # vigilance si retard d'au moins 1 semaine type
BRUSQUE_SIGMAS = 2.0        # mouvement brusque : variation d'au moins 2 écarts-types quotidiens
SOUPLE = (1.5, {"action": 8.0, "etf": 5.0})   # multiple de semaine type, plancher en %
FERME = (2.5, {"action": 12.0, "etf": 8.0})
SUIVEUR = 2.0               # écart au plus haut, en semaines types (au moins le stop souple)
SERIE = (4, {"action": 5.0, "etf": 3.0})       # 4 séances de baisse et au moins 1 semaine type
PLAFOND_LIGNE = 25.0        # % de l'enveloppe
LECTURE_SEUIL = 0.5         # écart à la référence, en semaines types, pour classer une lecture


def r(x, n=2):
    return None if x is None else round(x, n)


def lire_cours(chemin):
    """Retourne [(date, clôture)] trié, sans doublons, et une liste d'avertissements."""
    avert = []
    with open(chemin, encoding="utf-8-sig") as f:
        lignes = list(csv.DictReader(f))
    if not lignes:
        sys.exit(f"{chemin} : fichier vide")
    cles = {k.lower().strip(): k for k in lignes[0].keys() if k}
    cd = cles.get("date")
    cc = next((cles[k] for k in ("close", "cours", "clôture", "cloture", "adj close", "prix") if k in cles), None)
    if not cd or not cc:
        sys.exit(f"{chemin} : colonnes date et close (ou cours) introuvables, trouvé {list(cles)}")
    vus = {}
    for l in lignes:
        d, c = (l.get(cd) or "").strip(), (l.get(cc) or "").replace(",", "").replace("$", "").replace("€", "").strip()
        if not d or not c:
            continue
        try:
            jour = dt.date.fromisoformat(d[:10])
            val = float(c)
        except ValueError:
            avert.append(f"ligne ignorée : {d} {c}")
            continue
        if val <= 0:
            avert.append(f"cours non positif ignoré le {jour}")
            continue
        if jour in vus and vus[jour] != val:
            avert.append(f"doublon le {jour} : {vus[jour]} et {val}, dernière valeur gardée")
        vus[jour] = val
    serie = sorted(vus.items())
    for (d0, c0), (d1, c1) in zip(serie, serie[1:]):
        if (d1 - d0).days > 6:
            avert.append(f"trou de {(d1 - d0).days} jours entre {d0} et {d1}")
        if abs(c1 / c0 - 1) > 0.30:
            avert.append(f"variation suspecte de {100 * (c1 / c0 - 1):+.1f} % le {d1} (division d'actions ? erreur de saisie ?)")
    return serie, avert


def rendements(cl):
    return [b / a - 1 for a, b in zip(cl, cl[1:])]


def mm(cl, n, decalage=0):
    fin = len(cl) - decalage
    return statistics.fmean(cl[fin - n:fin]) if fin >= n else None


def seuils(sw, typ, etf_large=False):
    """Seuils par défaut en %, à partir de la semaine type (en %)."""
    souple = max(SOUPLE[0] * sw, SOUPLE[1][typ])
    ferme = max(FERME[0] * sw, FERME[1][typ])
    return {
        "stop_souple_pct": r(souple),
        "stop_ferme_pct": r(ferme),
        "objectif_pct": None if etf_large else r(2 * souple),
        "stop_suiveur_ecart_pct": r(max(SUIVEUR * sw, souple)),
        "stop_suiveur_active_a_pct": r(souple),
        "serie_seances": SERIE[0],
        "serie_baisse_min_pct": r(max(sw, SERIE[1][typ])),
    }


def cmd_titre(a):
    serie, avert = lire_cours(a.cours)
    dates = [d for d, _ in serie]
    cl = [c for _, c in serie]
    n = len(cl)
    if n < 21:
        sys.exit(json.dumps({"erreur": f"seulement {n} clôtures, il en faut au moins 21 (idéalement 61)",
                             "avertissements": avert}, ensure_ascii=False))
    if n < SEANCES_SIGMA + 1:
        avert.append(f"historique court ({n} clôtures) : écart-type sur {n - 1} séances")
    if n < MM + PENTE_RECUL:
        avert.append(f"historique court ({n} clôtures) : MM{MM} ou sa pente indisponible")
    rd = rendements(cl)[-SEANCES_SIGMA:]
    sigma = statistics.stdev(rd) * 100
    sw = sigma * math.sqrt(5)
    var_jour = rd[-1] * 100
    m50, m50_avant = mm(cl, MM), mm(cl, MM, PENTE_RECUL)

    k = 0
    while k < len(rd) and rd[-1 - k] < 0:
        k += 1
    baisse_serie = (cl[-1] / cl[-1 - k] - 1) * 100 if k else 0.0

    perf20 = (cl[-1] / cl[-1 - FORCE_SEANCES] - 1) * 100 if n > FORCE_SEANCES else None
    out = {
        "derniere_date": dates[-1].isoformat(),
        "derniere_cloture": cl[-1],
        "seances": n,
        "variation_jour_pct": r(var_jour),
        "sigma_jour_pct": r(sigma),
        "semaine_type_pct": r(sw),
        "mm50": r(m50, 4),
        "ecart_mm50_pct": r((cl[-1] / m50 - 1) * 100) if m50 else None,
        "pente_mm50_10s_pct": r((m50 / m50_avant - 1) * 100) if m50 and m50_avant else None,
        "perf_20s_pct": r(perf20),
        "seances_baisse_affilee": k,
        "baisse_serie_pct": r(baisse_serie),
        "mouvement_brusque": abs(var_jour) >= BRUSQUE_SIGMAS * sigma,
        "variation_jour_en_sigmas": r(var_jour / sigma) if sigma else None,
        "seuils_par_defaut": seuils(sw, a.type, a.etf_large),
    }

    vig = {
        "T1_cloture_sous_mm50": (cl[-1] < m50) if m50 else None,
        "T2_mm50_en_baisse": (m50 < m50_avant) if m50 and m50_avant else None,
        "T3_retard_sur_reference": None,
        "S1_reference_sous_sa_mm50": None,
    }
    if a.ref:
        rs, ra = lire_cours(a.ref)
        avert += [f"référence : {x}" for x in ra]
        rmap = dict(rs)
        communs = [d for d in dates if d in rmap]
        rcl = [c for _, c in rs]
        rm50 = mm(rcl, MM)
        out["reference"] = {"derniere_date": rs[-1][0].isoformat(), "derniere_cloture": rs[-1][1],
                            "mm50": r(rm50, 4), "variation_jour_pct": r((rcl[-1] / rcl[-2] - 1) * 100) if len(rcl) > 1 else None}
        if rs[-1][0] != dates[-1]:
            avert.append(f"dernière date différente : titre {dates[-1]}, référence {rs[-1][0]}")
        if len(communs) > FORCE_SEANCES:
            d1, d0 = communs[-1], communs[-1 - FORCE_SEANCES]
            pt = (dict(serie)[d1] / dict(serie)[d0] - 1) * 100
            pr = (rmap[d1] / rmap[d0] - 1) * 100
            fr = (pt - pr) / sw
            out["force_relative_20s"] = {"titre_pct": r(pt), "reference_pct": r(pr), "ecart_semaines_types": r(fr)}
            vig["T3_retard_sur_reference"] = fr <= FORCE_SEUIL
        else:
            avert.append("pas assez de dates communes avec la référence pour la force relative")
        if rm50:
            vig["S1_reference_sous_sa_mm50"] = rcl[-1] < rm50
    out["vigilance_technique"] = vig
    out["vigilance_technique_vrais"] = sum(1 for v in vig.values() if v)
    out["vigilance_note"] = ("Signaux techniques sur 4 ; la tâche y ajoute F1 (consensus des analystes en baisse) "
                             "et F2 (mauvaise nouvelle propre à l'entreprise sur 7 jours) pour un score sur 6.")

    if a.enveloppe:
        ferme = out["seuils_par_defaut"]["stop_ferme_pct"]
        brut = a.enveloppe * (a.risque / 100) / (ferme / 100)
        plafond = a.enveloppe * PLAFOND_LIGNE / 100
        out["taille_selon_la_regle"] = {
            "montant_eur": r(min(brut, plafond), 0),
            "perte_au_stop_ferme_eur": r(min(brut, plafond) * ferme / 100, 0),
            "limitee_par_le_plafond_de_ligne": brut > plafond,
            "calcul": f"{a.enveloppe:g} € × {a.risque:g} % / {ferme:g} % de stop ferme, plafonné à {PLAFOND_LIGNE:g} % de l'enveloppe",
        }
    out["avertissements"] = avert
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_position(a):
    pv = (a.cours_eur / a.prix_revient - 1) * 100
    haut = max(a.plus_haut_eur or a.cours_eur, a.cours_eur)
    recul = (a.cours_eur / haut - 1) * 100
    gain_max = (haut / a.prix_revient - 1) * 100
    regles = []
    if pv <= -a.stop_ferme:
        regles.append({"regle": "Stop", "detail": "stop ferme franchi", "prevoit": "Vendre"})
    elif pv <= -a.stop_souple:
        regles.append({"regle": "Stop", "detail": "stop souple franchi", "prevoit": "Vendre"})
    if a.objectif is not None and pv >= a.objectif:
        regles.append({"regle": "Objectif", "detail": "objectif atteint", "prevoit": "Alléger"})
    suiveur_actif = gain_max >= a.stop_souple
    niveau_suiveur = None
    if suiveur_actif and a.suiveur:
        niveau_suiveur = max(haut * (1 - a.suiveur / 100), a.prix_revient)
        if a.cours_eur <= niveau_suiveur:
            regles.append({"regle": "Stop suiveur", "detail": "stop suiveur franchi", "prevoit": "Vendre"})
    out = {
        "plus_value_pct": r(pv),
        "plus_haut_eur": r(haut, 4),
        "recul_depuis_plus_haut_pct": r(recul),
        "niveau_stop_souple_eur": r(a.prix_revient * (1 - a.stop_souple / 100), 4),
        "niveau_stop_ferme_eur": r(a.prix_revient * (1 - a.stop_ferme / 100), 4),
        "niveau_objectif_eur": r(a.prix_revient * (1 + a.objectif / 100), 4) if a.objectif is not None else None,
        "stop_suiveur_active": suiveur_actif,
        "niveau_stop_suiveur_eur": r(niveau_suiveur, 4),
        "distance_stop_souple_pct": r(pv + a.stop_souple),
        "distance_stop_ferme_pct": r(pv + a.stop_ferme),
        "regles_franchies": regles,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_contrat(a):
    chemin = os.path.join(a.depot, "Données", f"{a.ticker}.csv")
    with open(chemin, encoding="utf-8") as f:
        lignes = [l for l in csv.DictReader(f) if l.get("cours")]
    jours = [(dt.date.fromisoformat(l["date"]), float(l["cours"])) for l in lignes]
    ouvres = [(d, c) for d, c in jours if d.weekday() < 5]
    cl = [c for _, c in ouvres][-(SEANCES_SIGMA + 1):]
    if len(cl) < 16:
        print(json.dumps({"ticker": a.ticker, "semaine_type_pct": None,
                          "note": f"seulement {len(cl)} relevés en jours ouvrés, il en faut 16"}, ensure_ascii=False))
        return
    s = statistics.stdev(rendements(cl)) * 100
    print(json.dumps({"ticker": a.ticker, "releves_ouvres": len(cl), "sigma_jour_pct": r(s),
                      "semaine_type_pct": r(s * math.sqrt(5))}, ensure_ascii=False))


def cmd_lecture(a):
    pt = (a.cours / a.cours_ouverture - 1) * 100
    pr = (a.ref / a.ref_ouverture - 1) * 100
    sens = 1 if a.camp == "acheteurs" else -1
    ecart = (pt - pr) / a.semaine_type
    dans_le_sens = sens * ecart
    out = {"variation_titre_pct": r(pt), "variation_reference_pct": r(pr),
           "ecart_semaines_types": r(ecart), "ecart_dans_le_sens_du_camp": r(dans_le_sens)}
    if a.echeance:
        out["statut"] = ("Dans leur sens" if dans_le_sens >= LECTURE_SEUIL
                         else "Contre eux" if dans_le_sens <= -LECTURE_SEUIL else "Sans effet")
    print(json.dumps(out, ensure_ascii=False))


def cmd_indice(a):
    with open(a.suivi, encoding="utf-8-sig") as f:
        lignes = sorted(csv.DictReader(f), key=lambda l: l["date"])
    ind, haut, prec = 100.0, 100.0, None
    for l in lignes:
        v, flux = float(l["valeur"]), float(l.get("flux") or 0)
        if prec:
            ind *= (v - flux) / prec
        prec = v
        haut = max(haut, ind)
    print(json.dumps({"date": lignes[-1]["date"], "indice": r(ind), "plus_haut_indice": r(haut),
                      "recul_depuis_plus_haut_pct": r((ind / haut - 1) * 100)}, ensure_ascii=False))


def cmd_fantome(a):
    with open(a.mouvements, encoding="utf-8-sig") as f:
        lignes = sorted(csv.DictReader(f), key=lambda l: l["date"])
    parts = 0.0
    for l in lignes:
        parts += float(l["montant"]) / float(l["cours_etf"])
    print(json.dumps({"parts": r(parts, 6), "valeur_fantome_eur": r(parts * a.cours_etf)}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    t = sp.add_parser("titre")
    t.add_argument("--cours", required=True)
    t.add_argument("--ref")
    t.add_argument("--type", choices=["action", "etf"], default="action")
    t.add_argument("--etf-large", action="store_true", help="ETF monde ou S&P 500 : pas d'objectif")
    t.add_argument("--enveloppe", type=float)
    t.add_argument("--risque", type=float, default=2.0, help="perte au stop ferme, en %% de l'enveloppe")
    t.set_defaults(f=cmd_titre)

    q = sp.add_parser("position")
    q.add_argument("--prix-revient", type=float, required=True)
    q.add_argument("--cours-eur", type=float, required=True)
    q.add_argument("--plus-haut-eur", type=float)
    q.add_argument("--stop-souple", type=float, required=True)
    q.add_argument("--stop-ferme", type=float, required=True)
    q.add_argument("--objectif", type=float)
    q.add_argument("--suiveur", type=float)
    q.set_defaults(f=cmd_position)

    c = sp.add_parser("contrat")
    c.add_argument("ticker")
    c.add_argument("--depot", default=".")
    c.set_defaults(f=cmd_contrat)

    l = sp.add_parser("lecture")
    l.add_argument("--camp", choices=["acheteurs", "vendeurs"], required=True)
    for nom in ("--cours-ouverture", "--cours", "--ref-ouverture", "--ref", "--semaine-type"):
        l.add_argument(nom, type=float, required=True)
    l.add_argument("--echeance", action="store_true", help="donne le statut final (30 jours)")
    l.set_defaults(f=cmd_lecture)

    i = sp.add_parser("indice")
    i.add_argument("--suivi", required=True)
    i.set_defaults(f=cmd_indice)

    g = sp.add_parser("fantome")
    g.add_argument("--mouvements", required=True)
    g.add_argument("--cours-etf", type=float, required=True)
    g.set_defaults(f=cmd_fantome)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
