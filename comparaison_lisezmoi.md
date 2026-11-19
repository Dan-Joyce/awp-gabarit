# Exo 1 : avec et sans LISEZMOI

Deux versions de `fil_rouge/data.py` et `fil_rouge/01_figures.py` :
- **avec** : branche `main` (commit `936485b`), faite après lecture de `LISEZMOI.md`, `conseils.md` et `plotly.com/llms.txt` ;
- **sans** : branche `sans-lisezmoi` (commit `09d2d08`), faite par un sous-agent neuf, qui n'a pas lu `LISEZMOI.md` ni `conseils.md` et n'a découvert les données qu'avec pandas.

## Tableau comparatif

| Point | Avec LISEZMOI (`main`) | Sans (`sans-lisezmoi`) |
|---|---|---|
| Cadences vides | Remplacées par `"aucune"` | Pareil (48 parties de correspondance) |
| Résultats | win/draw/lose traduits en victoire/nulle/défaite | Pareil |
| Heure UTC | `date_jeu` naïve, `heure` extraite | Pareil, mais « UTC » est une supposition non vérifiée |
| Score et `ecart_elo` | 1 / 0,5 / 0 et `elo_adverse − elo_joueur` | Pareil. `elo_joueur_apres` repéré comme « Elo d'après », mais `elo_avant_reconstruit` (1 779 parties) non vérifié |
| `valider` | 5 contrôles sur 8 colonnes, faits sur le fichier brut puis revalidés à la fin | 5 contrôles identiques sur 10 colonnes, faits une seule fois, avant les transformations |
| Phases des gaffes | `opening`, `middlegame`, `endgame` | Pareil, sans savoir que `opening_theory` chevauche `opening` (sans effet ici) |
| Figure 1 | 36 % (Hungarian Opening) à 66 % (Scotch Game) | Identique, avec « sur 36 parties » dans le titre et le score moyen tracé |
| Figure 2 | 53 % au milieu de partie, 34 % en finale, 7 030 gaffes | Mêmes chiffres, mais le titre ne cite que les 53 % du milieu de partie |
| Figure 3 | 46 % à 1 h UTC, 65 % à 18 h UTC | Identique |

Le DataFrame et les chiffres des trois figures sont les mêmes dans les deux versions.

## La question : où ce joueur perd-il des points ?

Réponse d'après les figures.

1. **Par phase (figure 2)** : 53 % des 7 030 gaffes tombent au milieu de partie et 34 % en finale. Il n'en reste que 13 % en ouverture (903 gaffes). Ce sont des comptes bruts, pas des gaffes par coup joué.
2. **Par ouverture (figure 1)** : le score moyen va de 36 % (Hungarian Opening, 36 parties) à 66 % (Scotch Game, 179 parties). Les pires familles (Hungarian, English, Philidor) sont à 36–41 % de score, avec environ 2,7 gaffes par partie. La Scotch Game est à 1,8 gaffe par partie.
3. **Par heure (figure 3)** : le score tombe à 46 % à 1 h UTC (100 parties) et monte à 65 % à 18 h UTC (126 parties), pour une moyenne de 52 %. Les heures du soir (20 h à 23 h UTC) sont à 49–53 %.

Le joueur perd donc surtout ses points au milieu de partie, dans quelques ouvertures précises, et plus la nuit. Les écarts par heure sont moins nets que ceux par ouverture, parce que certaines heures ne comptent que 30 à 60 parties.

## Ce que la documentation a apporté

La documentation n'a pas changé les chiffres : le sous-agent a retrouvé seul la plupart des pièges (cadence vide, `resultat` et non `fin_partie`, Elo d'avant la partie). Elle a transformé des suppositions en faits : les heures sont en UTC, l'Elo d'avant est reconstruit et fiable, les 5 parties sans ouverture sont attendues, et `coups_juges.csv` ne contient que les coups jugés mauvais. Elle donne aussi des garde-fous que l'IA ne pouvait pas deviner : les phases qui se chevauchent, le lien par `partie_id`, et le fait que la figure 2 compte des gaffes brutes.
