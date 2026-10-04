# Marchés

Veille des marchés d'Erwan : un relevé par jour dans `Journal/`, une fiche par valeur dans `Actifs/`, reliées par thème. Chaque fiche garde l'historique de ses signaux, ce qui permet de voir si une tendance tient dans la durée ou se retourne.

Dernier relevé : [[2026-10-04]] · Thèmes : [[Puces et mémoire]] · [[IA]] · [[Robotique et actionneurs]] · [[Défense]] · Construction et limites : [[Méthode]]

## Derniers relevés

```dataview
LIST FROM "Journal" SORT file.name DESC LIMIT 10
```

## Positionnement Apex du jour (échantillons fiables)

```dataview
TABLE cours AS "Cours", apex_biais AS "Apex", sharps_biais AS "Sharps", foule_biais AS "Foule", derniere_maj AS "Mis à jour"
FROM "Actifs"
WHERE cours AND echantillon_faible = false
SORT apex_biais DESC
```

## Organisation

| Dossier | Contenu | Qui écrit |
| --- | --- | --- |
| `Journal/` | un relevé par jour, avec liens vers les fiches | tâche automatique |
| `Actifs/` | une fiche par valeur : dernier relevé, graphique, signaux datés, notes | tâche automatique, sauf la section Notes |
| `Thèmes/` | une page par thème, avec un tableau vivant | à la création |
| `Données/` | un CSV par contrat, une ligne par jour | tâche automatique |
| `Graphiques/` | un graphique par contrat, régénéré le dimanche | tâche automatique |

## Plugins

Git (obligatoire) récupère les relevés depuis GitHub : active la récupération au démarrage d'Obsidian. Dataview (optionnel) affiche les tableaux vivants de cette page et des thèmes ; sans lui, les blocs restent visibles en texte brut et rien d'autre ne change.
