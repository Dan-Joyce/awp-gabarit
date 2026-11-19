"""Exo 1 : trois figures. Environ 25 min.

Question : où ce joueur perd-il des points ?
À produire : trois figures Plotly dont le titre dit ce qu'elles montrent.
Lancer : uv run python fil_rouge/01_figures.py
"""

from pathlib import Path

import plotly.express as px

from data import familles, load_coups, load_data

DOSSIER = Path(__file__).resolve().parent  # les fichiers HTML sont sauvegardés ici

df, coups = load_data(), load_coups()
print(df.shape, coups.shape)

# 1. Le score par famille d'ouvertures, la pire en haut (px.bar, familles(df))
fam = familles(df)  # déjà triée : la pire famille en premier
pire, meilleure = fam.iloc[0], fam.iloc[-1]
fig1 = px.bar(
    fam,
    x="score",
    y="famille",
    orientation="h",  # barres horizontales
    hover_data=["n", "gaffes"],
    labels={"score": "Score moyen (1 = victoire, 0,5 = nulle, 0 = défaite)", "famille": "Famille d'ouvertures"},
    title=(
        f"Le score va de {pire['score']:.0%} ({pire['famille']}) "
        f"à {meilleure['score']:.0%} ({meilleure['famille']}) selon l'ouverture "
        f"(familles de 30 parties ou plus)"
    ),
)
# Les barres sont dessinées de bas en haut : on inverse l'axe pour avoir la pire en haut
fig1.update_yaxes(autorange="reversed")
fig1.show()
fig1.write_html(DOSSIER / "figure_1.html", include_plotlyjs="cdn")  # "cdn" : fichier léger, plotly.js chargé depuis internet

# 2. La phase de la partie où tombent ses gaffes : ouverture, milieu, finale (coups)
# On ne garde que les gaffes (jugement == "blunder") puis on compte par phase
gaffes = coups[coups["jugement"] == "blunder"]
par_phase = gaffes.groupby("phase").size()
# Ordre logique d'une partie, avec les noms en français
ordre = ["opening", "middlegame", "endgame"]
noms = {"opening": "Ouverture", "middlegame": "Milieu de partie", "endgame": "Finale"}
phases = par_phase.reindex(ordre).rename(index=noms).reset_index()
phases.columns = ["phase", "gaffes"]
part_milieu = par_phase["middlegame"] / par_phase.sum()
part_finale = par_phase["endgame"] / par_phase.sum()
fig2 = px.bar(
    phases,
    x="phase",
    y="gaffes",
    text="gaffes",
    labels={"phase": "Phase de la partie", "gaffes": "Nombre de gaffes"},
    title=(
        f"{part_milieu:.0%} des gaffes tombent au milieu de partie et "
        f"{part_finale:.0%} en finale ({par_phase.sum()} gaffes au total)"
    ),
)
fig2.show()
fig2.write_html(DOSSIER / "figure_2.html", include_plotlyjs="cdn")  # "cdn" : fichier léger, plotly.js chargé depuis internet

# 3. Le score selon l'heure de la partie (heures UTC, au moins 30 parties par heure)
heures = df.groupby("heure").agg(n=("score", "size"), score=("score", "mean")).reset_index()
heures = heures[heures["n"] >= 30]  # en dessous, la moyenne ne dit rien
bas = heures.loc[heures["score"].idxmin()]
haut = heures.loc[heures["score"].idxmax()]
fig3 = px.bar(
    heures,
    x="heure",
    y="score",
    hover_data=["n"],
    labels={"heure": "Heure de début de la partie (UTC)", "score": "Score moyen"},
    title=(
        f"Le score moyen varie de {bas['score']:.0%} à {int(bas['heure'])} h UTC "
        f"à {haut['score']:.0%} à {int(haut['heure'])} h UTC (heures de 30 parties ou plus)"
    ),
)
# Ligne de repère : le score moyen sur toutes les parties
fig3.add_hline(y=df["score"].mean(), line_dash="dash", annotation_text="moyenne générale")
fig3.update_xaxes(dtick=1)  # une graduation par heure
fig3.show()
fig3.write_html(DOSSIER / "figure_3.html", include_plotlyjs="cdn")  # "cdn" : fichier léger, plotly.js chargé depuis internet
