# Trading — données de marché

Ce dépôt est la couche de données d'une veille de marché : un CSV quotidien par contrat et des graphiques hebdomadaires. La lecture se fait dans Notion, qui affiche les graphiques à partir de leurs liens publics. Il ne contient que des données de marché publiques.

## Contenu

| Chemin | Contenu |
| --- | --- |
| `actifs.json` | valeurs suivies, thème, contrat Hyperliquid ; valeurs sans contrat à part |
| `Données/<TICKER>.csv` | une ligne par jour et par contrat |
| `Graphiques/<AAAA-MM-JJ>/` | un graphique par contrat et `positionnement.png` (vue d'ensemble), générés le dimanche |
| `.outils/graphiques.py` | style des graphiques |
| `.outils/regenerer.py` | régénère les graphiques de la semaine à partir des CSV |

Lien public d'une image, à utiliser dans Notion :
`https://raw.githubusercontent.com/ErwanBaumann/Trading/main/Graphiques/<AAAA-MM-JJ>/<TICKER>.png`

## Colonnes des CSV

| Colonne | Définition |
| --- | --- |
| `date` | jour du relevé (UTC) |
| `cours` | prix de marque du contrat à 23 h UTC ; heure pleine la plus récente pour le relevé du jour |
| `oi_usd` | open interest : montant total des positions ouvertes, en USD |
| `apex_biais`, `sharps_biais`, `foule_biais` | biais net de chaque catégorie de traders, de −100 (tout vendeur) à +100 (tout acheteur) |
| `apex_portefeuilles` | nombre de portefeuilles Apex en position |
| `apex_engage_usd` | montant engagé par les Apex sur le contrat, en USD |
| `funding_h` | taux de financement horaire du contrat |

## Définitions

Source : Coinversa Pulse, contrats perpétuels Hyperliquid sur actions (marché `xyz`). Ce sont des contrats synthétiques échangés 24 h/24, surtout par des traders crypto avec levier : leur cours suit l'action mais peut s'en écarter, et leur positionnement ne reflète pas celui des investisseurs institutionnels.

Biais net = 100 × (montant acheteur − montant vendeur) / (montant acheteur + montant vendeur), calculé en montant et non en nombre de portefeuilles.

Catégories de rentabilité Coinversa, des plus rentables aux plus perdants : Apex (`money_printer`), Sharps (`smart_money`), Grinders (`grinder`), Scrapers (`humble_earner`), Foule (`exit_liquidity`), Bleeders (`semi_rekt`), Trapped (`full_rekt`), Blown Out (`giga_rekt`).

Seuils : acheteurs si biais ≥ +20, vendeurs si ≤ −20, partagés entre les deux. Bascule : changement de catégorie entre deux relevés. Mouvement net : écart d'au moins 20 points. Échantillon faible : moins de 5 M$ engagés par les Apex.

Limites : historique reconstitué le 4 octobre 2026 (cours et open interest depuis le 27 septembre, positionnement seulement le 27 septembre et le 4 octobre). Le week-end, les bourses sont fermées et les contrats bougent peu. Ces données ne sont pas des recommandations d'achat ou de vente.

## Mise à jour quotidienne

Instructions suivies par la tâche planifiée :

1. Pour chaque contrat de `actifs.json`, relever avec Coinversa Pulse le cours et l'open interest (`market_historical_oi` sur l'heure pleine la plus récente), le positionnement par catégorie (`live_cohort_bias` : Apex, Sharps, Foule, nombre de portefeuilles et montant engagés des Apex) et le taux de financement (`list_markets`).
2. Ajouter une ligne datée à chaque `Données/<TICKER>.csv` : une seule ligne par date, sans jamais réécrire les lignes passées.
3. Le dimanche : `python3 .outils/regenerer.py` depuis la racine du dépôt.
4. Valider avec le message « Relevé AAAA-MM-JJ » et pousser.
5. Mettre ensuite à jour l'espace Notion avec les mêmes chiffres et, le dimanche, les nouveaux liens d'images.
