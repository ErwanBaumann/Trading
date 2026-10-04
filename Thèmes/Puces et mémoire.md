---
type: theme
---
# Puces et mémoire

Ce qu'il faut regarder : Résultats et prévisions trimestriels, prix de la mémoire, positionnement des traders.

## Valeurs avec données Hyperliquid
- [[Nvidia]]
- [[AMD]]
- [[SanDisk]]
- [[Micron]]
- [[Samsung Electronics]]
- [[TSMC]]
- [[ASML]]
- [[Broadcom]]

## Valeurs sans données pour l'instant
- [[SK Hynix]]

## Tableau vivant (plugin Dataview)

```dataview
TABLE cours AS "Cours", apex_biais AS "Apex", sharps_biais AS "Sharps", foule_biais AS "Foule", derniere_maj AS "Mis à jour"
FROM "Actifs"
WHERE contains(themes, this.file.link) AND cours
SORT apex_biais DESC
```
