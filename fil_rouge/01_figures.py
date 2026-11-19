"""Exo 1 : trois figures. Environ 25 min.

Question : où ce joueur perd-il des points ?
À produire : trois figures Plotly dont le titre dit ce qu'elles montrent.
Lancer : uv run python fil_rouge/01_figures.py
"""

from pathlib import Path

import plotly.express as px

from data import familles, load_coups, load_data

DOSSIER = Path(__file__).resolve().parent

df, coups = load_data(), load_coups()
print(df.shape, coups.shape)


figures = []  # (figure, nom du fichier), affichées à la fin


def sauver(fig, nom):
    """Sauvegarde en HTML (plotly.js via CDN pour rester léger) et garde la figure."""
    fig.write_html(DOSSIER / nom, include_plotlyjs="cdn")
    print(fig.layout.title.text)
    figures.append((fig, nom))


# 1. Le score par famille d'ouvertures, la pire en haut (px.bar, familles(df))
fam = familles(df)  # déjà triée : la pire d'abord
pire = fam.iloc[0]
meilleure = fam.iloc[-1]
titre1 = (
    f"{pire['famille']} est ma pire ouverture : {pire['score']:.0%} de score "
    f"sur {pire['n']} parties, contre {meilleure['score']:.0%} pour {meilleure['famille']}"
)
# Dans un bar horizontal, la dernière ligne est en haut : on inverse pour mettre la pire en haut
fig1 = px.bar(
    fam.iloc[::-1], x="score", y="famille", orientation="h",
    hover_data=["n", "gaffes"], title=titre1,
    labels={"score": "Score moyen (1 = victoire, 0,5 = nulle)", "famille": "Famille d'ouvertures"},
)
fig1.add_vline(x=df["score"].mean(), line_dash="dash",
               annotation_text=f"moyenne {df['score'].mean():.0%}")
sauver(fig1, "figure_1_sans.html")

# 2. La phase de la partie où tombent ses gaffes : ouverture, milieu, finale (coups)
gaffes = coups[coups["jugement"] == "blunder"]  # seulement les gaffes (pas imprécisions/erreurs)
ordre = {"opening": "ouverture", "middlegame": "milieu de partie", "endgame": "finale"}
par_phase = gaffes["phase"].map(ordre).value_counts().reindex(list(ordre.values())).reset_index()
par_phase.columns = ["phase", "gaffes"]
par_phase["part"] = par_phase["gaffes"] / par_phase["gaffes"].sum()
top = par_phase.sort_values("gaffes").iloc[-1]
titre2 = (
    f"{top['part']:.0%} de mes {len(gaffes)} gaffes tombent en {top['phase']} "
    f"({top['gaffes']} gaffes)"
)
fig2 = px.bar(par_phase, x="phase", y="gaffes", text=par_phase["part"].map("{:.0%}".format),
              title=titre2, labels={"phase": "Phase de la partie", "gaffes": "Nombre de gaffes"})
sauver(fig2, "figure_2_sans.html")

# 3. Le score selon l'heure de la partie (heures UTC, au moins 30 parties par heure)
heures = df.groupby("heure").agg(n=("score", "count"), score=("score", "mean")).reset_index()
heures = heures[heures["n"] >= 30]  # sous 30 parties, la moyenne n'est pas fiable
bon = heures.loc[heures["score"].idxmax()]
mauvais = heures.loc[heures["score"].idxmin()]
titre3 = (
    f"Mon score varie de {mauvais['score']:.0%} à {mauvais['heure']:.0f} h UTC "
    f"({int(mauvais['n'])} parties) à {bon['score']:.0%} à {bon['heure']:.0f} h UTC ({int(bon['n'])} parties)"
)
fig3 = px.bar(heures, x="heure", y="score", hover_data=["n"], title=titre3,
              labels={"heure": "Heure (UTC)", "score": "Score moyen"})
fig3.add_hline(y=df["score"].mean(), line_dash="dash",
               annotation_text=f"moyenne {df['score'].mean():.0%}")
sauver(fig3, "figure_3_sans.html")

# Affichage à la fin (fig.show attend que le navigateur ait chargé la page)
for fig, nom in figures:
    try:
        fig.show()
    except MemoryError:  # machine à court de mémoire : le HTML est déjà sauvegardé
        print("fig.show() a échoué (mémoire), ouvrez", nom)
