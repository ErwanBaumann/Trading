# Méthode

## Ce que mesure le vault

Les données viennent de Coinversa Pulse, qui analyse les contrats perpétuels d'Hyperliquid sur actions (marché `xyz`). Ce sont des contrats synthétiques, échangés 24 h/24 surtout par des traders crypto avec levier : leur cours suit l'action mais peut s'en écarter, et leur positionnement ne reflète pas celui des investisseurs institutionnels.

| Mesure | Définition |
| --- | --- |
| Cours | prix de marque du contrat à 23 h UTC chaque jour ; heure pleine la plus récente pour le relevé du jour |
| Open interest | montant total des positions ouvertes sur le contrat, en USD |
| Biais net | 100 × (montant acheteur − montant vendeur) / (montant acheteur + montant vendeur), de −100 à +100, calculé en montant et non en nombre de portefeuilles |
| Apex, Sharps… | catégories de rentabilité de Coinversa, des plus rentables aux plus perdants : Apex, Sharps, Grinders, Scrapers, Foule, Bleeders, Trapped, Blown Out |

Noms techniques renvoyés par l'outil : money_printer = Apex, smart_money = Sharps, grinder = Grinders, humble_earner = Scrapers, exit_liquidity = Foule, semi_rekt = Bleeders, full_rekt = Trapped, giga_rekt = Blown Out.

## Seuils

- Acheteurs : biais ≥ +20 ; vendeurs : biais ≤ −20 ; entre les deux : partagés.
- Bascule : changement de catégorie entre deux relevés. Mouvement net : écart d'au moins 20 points.
- Échantillon faible (◦) : moins de 5 M$ engagés par les Apex sur le contrat ; ses mouvements reposent sur une poignée de portefeuilles.

## Limites

- Historique reconstitué le 4 octobre 2026 : cours et open interest quotidiens depuis le 27 septembre, positionnement seulement le 27 septembre (5 h UTC) et le 4 octobre. Ensuite, une ligne par jour.
- Le week-end, les bourses sont fermées et les contrats bougent peu.
- Rien dans ce vault n'est une recommandation d'achat ou de vente.

## Mise à jour automatique

Instructions suivies par la tâche planifiée, chaque matin :

1. Pour chaque fiche de `Actifs/` dont le champ `hyperliquid` n'est pas `aucun` : relever avec Coinversa Pulse le cours et l'open interest (market_historical_oi sur l'heure pleine la plus récente) et le positionnement par catégorie (live_cohort_bias). Ajouter une ligne datée à `Données/<ticker>.csv` ; une seule ligne par date, sans jamais réécrire les lignes passées.
2. Comparer à la veille et à 7 jours ; mettre à jour le frontmatter de la fiche (cours, biais, derniere_maj, echantillon_faible) et sa section « Dernier relevé ».
3. Ajouter une ligne en haut de « Signaux datés » seulement en cas de bascule, de mouvement net, ou de variation de l'open interest d'au moins 20 % sur 7 jours. Chaque ligne cite ses chiffres et renvoie au relevé du jour.
4. Écrire `Journal/AAAA-MM-JJ.md` : synthèse de 3 à 5 phrases, changements notables avec liens vers les fiches, tableau complet, champ `precedent` pointant vers le relevé de la veille.
5. Le dimanche : lancer `python3 .outils/regenerer.py` depuis la racine du vault. Il redessine un graphique par contrat dans `Graphiques/` à partir des CSV, et la vue d'ensemble du positionnement Apex dans `Graphiques/Journal/`, avec le même style.
6. Ne jamais modifier la section « Notes » d'une fiche, ni une note créée par Erwan.
7. Valider avec le message « Relevé AAAA-MM-JJ » et pousser sur GitHub.
