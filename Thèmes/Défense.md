---
type: theme
---
# Défense

Ce qu'il faut regarder : Contrats publics attribués (Quiver), budgets de défense, carnets de commandes. Presque aucun contrat Hyperliquid : Quiver est la source principale.

## Valeurs avec données Hyperliquid
- [[Palantir]]

## Valeurs sans données pour l'instant
- [[Rheinmetall]]
- [[Hensoldt]]
- [[Renk]]
- [[Thales]]
- [[Safran]]
- [[BAE Systems]]
- [[Leonardo]]
- [[Saab]]
- [[Lockheed Martin]]
- [[RTX]]

## Tableau vivant (plugin Dataview)

```dataview
TABLE cours AS "Cours", apex_biais AS "Apex", sharps_biais AS "Sharps", foule_biais AS "Foule", derniere_maj AS "Mis à jour"
FROM "Actifs"
WHERE contains(themes, this.file.link) AND cours
SORT apex_biais DESC
```
