---
type: theme
---
# IA

Ce qu'il faut regarder : Dépenses d'investissement en centres de données annoncées, nouvelles positions des grands fonds (13F).

## Valeurs avec données Hyperliquid
- [[Microsoft]]
- [[Alphabet]]
- [[Meta]]
- [[Palantir]]
- [[CoreWeave]]
- [[Nebius]]

## Valeurs sans données pour l'instant
- aucune

## Tableau vivant (plugin Dataview)

```dataview
TABLE cours AS "Cours", apex_biais AS "Apex", sharps_biais AS "Sharps", foule_biais AS "Foule", derniere_maj AS "Mis à jour"
FROM "Actifs"
WHERE contains(themes, this.file.link) AND cours
SORT apex_biais DESC
```
