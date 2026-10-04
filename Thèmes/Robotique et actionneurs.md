---
type: theme
---
# Robotique et actionneurs

Ce qu'il faut regarder : Commandes et chiffre d'affaires réellement liés aux humanoïdes dans les résultats des fournisseurs de composants.

## Valeurs avec données Hyperliquid
- [[Tesla]]
- [[Unitree]]
- [[Hyundai Motor]]

## Valeurs sans données pour l'instant
- [[Harmonic Drive Systems]]
- [[Nabtesco]]
- [[THK]]
- [[Schaeffler]]

## Tableau vivant (plugin Dataview)

```dataview
TABLE cours AS "Cours", apex_biais AS "Apex", sharps_biais AS "Sharps", foule_biais AS "Foule", derniere_maj AS "Mis à jour"
FROM "Actifs"
WHERE contains(themes, this.file.link) AND cours
SORT apex_biais DESC
```
