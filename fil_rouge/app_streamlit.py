"""Exo 2 : l'appli Streamlit du fil rouge. Environ 1 h.

Question : l'appli que ce joueur ouvrirait chaque semaine pour savoir quoi travailler.
À produire : une barre latérale (cadence, période, couleur), trois st.metric, deux figures
en colonnes. Le titre de la page dit la question, pas « Dashboard ».
Colonnes utilisées : cadence (dont « aucune »), date_jeu (datetime), couleur (white ou black),
score, gaffes_joueur. Si votre load_data() ne les donne pas ainsi, corrigez-la.
Lancer : uv run streamlit run fil_rouge/app_streamlit.py --server.address 127.0.0.1
"""

import plotly.express as px
import streamlit as st

from data import familles, load_coups, load_data
from echiquier import NOMS_PIECES, figure_echiquier, piece

st.set_page_config(page_title="Mes parties d'échecs", page_icon="♟️", layout="wide")
print("relance")  # regardez le terminal à chaque clic

PLATEFORMES = {"lichess": "Lichess", "chesscom": "Chess.com", "imported": "Importées à la main"}
COULEURS = {"white": "Blancs", "black": "Noirs"}
NOMS_PHASES = {"opening": "Ouverture", "middlegame": "Milieu de partie", "endgame": "Finale"}
GRAVITES = {"blunder": "Gaffes", "mistake": "Erreurs", "inaccuracy": "Imprécisions"}
NATURES = {
    "allowed_tactic": "Tactique laissée à l'adversaire",
    "missed_tactic": "Tactique ratée",
    "positionnel": "Position (pas de tactique)",
}
MECANISMES = {"material": "Perte de matériel", "mate": "Mat", "promotion": "Promotion", "positional": "Position"}
VERT, ROUGE, ORANGE = "#769656", "#C0392B", "#E0A33A"
CONSEILS_PHASE = {
    "opening": "Révisez vos lignes d'ouverture et repérez le coup où vous quittez la théorie.",
    "middlegame": "Avant chaque coup du milieu de partie, demandez-vous : que menace l'adversaire après mon coup ?",
    "endgame": "Travaillez les finales de base (tour et pions, opposition) : elles se gagnent ou se perdent à un tempo.",
}


# 1. Chargement unique : la fonction ne s'exécute qu'au premier appel, ensuite Streamlit
#    rend le résultat en cache (les filtres sont appliqués dehors, ils sont bon marché)
@st.cache_data
def charger():
    print("chargement des données")  # n'apparaît qu'une fois dans le terminal
    return load_data(), load_coups()


def ecart(valeur: float, reference: float, unite: float = 1.0) -> float:
    """Écart arrondi à un zéro propre (Streamlit n'affiche alors ni flèche ni couleur)."""
    e = (valeur - reference) * unite
    return 0 if abs(e) < 0.05 else e


df, coups = charger()

# 2. Titre, puis barre latérale (un key= par widget)
st.title("♟️ Qu'est-ce que je devrais travailler pour progresser aux échecs ?")

with st.sidebar:
    st.header("Filtres")
    plateformes = [p for p in PLATEFORMES if p in set(df["plateforme"])]
    plateforme = st.multiselect(
        "Plateforme", plateformes, default=plateformes, format_func=PLATEFORMES.get, key="plateforme"
    )
    cadences = sorted(df["cadence"].unique())  # inclut « aucune »
    cadence = st.multiselect("Cadence", cadences, default=cadences, key="cadence")
    periode = st.date_input(
        "Période",
        value=(df["date_jeu"].min().date(), df["date_jeu"].max().date()),
        min_value=df["date_jeu"].min().date(),
        max_value=df["date_jeu"].max().date(),
        key="periode",
    )
    couleur = st.multiselect(
        "Couleur",
        list(COULEURS),
        default=list(COULEURS),
        format_func=COULEURS.get,
        key="couleur",
    )
    n_min = st.slider("Parties minimum par famille d'ouvertures", 5, 60, 30, step=5, key="n_min")

# 3. Filtrer. Tant que la seconde date n'est pas choisie, periode n'a qu'un élément
if len(periode) != 2:
    st.info("Choisissez la date de fin de la période.")
    st.stop()

debut, fin = periode
jour = df["date_jeu"].dt.date
vue = df[df["plateforme"].isin(plateforme) & df["cadence"].isin(cadence) & df["couleur"].isin(couleur) & jour.between(debut, fin)]

if vue.empty:
    st.warning("Aucune partie ne correspond à ces filtres : élargissez la plateforme, la période, la cadence ou la couleur.")
    st.stop()

# Calculs sur les parties filtrées (servent à la conclusion, aux figures et au plan)
fam = familles(vue, min_n=n_min)
# coups_juges ne contient que mes coups jugés mauvais : on garde ceux des parties filtrées
coups_vue = coups[coups["partie_id"].isin(vue["partie_id"])]
gaffes = coups_vue[coups_vue["jugement"] == "blunder"]
par_phase = gaffes.groupby("phase").size().reindex(list(NOMS_PHASES), fill_value=0)

# La réponse à la question du titre, recalculée à chaque changement de filtre
if par_phase.sum() > 0:
    phase_max = par_phase.idxmax()
    conclusion = (
        f"**À travailler en premier : {NOMS_PHASES[phase_max].lower()}** "
        f"({par_phase[phase_max] / par_phase.sum():.0%} de mes gaffes)"
    )
    if not fam.empty:
        pire = fam.iloc[0]
        conclusion += f", puis **{pire['famille']}** (score {pire['score']:.0%} sur {pire['n']} parties)"
    st.success(conclusion + ".", icon=":material/target:")
else:
    st.info("Pas assez de gaffes dans ces parties pour dire quoi travailler.")

# 4. Trois chiffres, comparés à l'ensemble de mes parties
c1, c2, c3 = st.columns(3)
c1.metric(
    "Parties",
    f"{len(vue):,}".replace(",", " "),
    delta=f"{len(vue) / len(df):.0%} de toutes mes parties",
    delta_color="off",
    border=True,
)
c2.metric(
    "Score moyen",
    f"{vue['score'].mean():.0%}",
    delta=ecart(vue["score"].mean(), df["score"].mean(), 100),
    delta_description="pts vs toutes mes parties",
    help="1 = victoire, 0,5 = nulle, 0 = défaite",
    border=True,
)
c3.metric(
    "Gaffes par partie",
    f"{vue['gaffes_joueur'].mean():.1f}",
    delta=ecart(vue["gaffes_joueur"].mean(), df["gaffes_joueur"].mean()),
    delta_description="vs toutes mes parties",
    delta_color="inverse",  # moins de gaffes = bien
    border=True,
)

tab_synthese, tab_echiquier, tab_ouvertures, tab_fautes = st.tabs(
    [":material/dashboard: Synthèse", ":material/grid_on: Échiquier", ":material/menu_book: Ouvertures", ":material/search: Nature des fautes"]
)

# ---------------------------------------------------------------- Synthèse
with tab_synthese:
    # 5. Deux figures côte à côte, calculées sur les parties filtrées
    gauche, droite = st.columns(2)

    with gauche, st.container(border=True):
        if fam.empty:
            st.info(f"Aucune famille d'ouvertures n'a {n_min} parties ou plus avec ces filtres : baissez le curseur.")
        else:
            pire, meilleure = fam.iloc[0], fam.iloc[-1]
            fig1 = px.bar(
                fam,
                x="score",
                y="famille",
                orientation="h",
                color="score",
                color_continuous_scale=[ROUGE, "#F4E7B0", VERT],
                range_color=(0.3, 0.7),
                hover_data=["n", "gaffes"],
                labels={"score": "Score moyen (1 = victoire, 0,5 = nulle, 0 = défaite)", "famille": "Famille d'ouvertures"},
                title=(
                    f"Le score va de {pire['score']:.0%} ({pire['famille']}) "
                    f"à {meilleure['score']:.0%} ({meilleure['famille']}) selon l'ouverture "
                    f"(familles de {n_min} parties ou plus)"
                ),
            )
            fig1.update_yaxes(autorange="reversed")  # la pire en haut
            fig1.update_coloraxes(showscale=False)
            st.plotly_chart(fig1, key="fig_familles")

    with droite, st.container(border=True):
        if gaffes.empty:
            st.info("Aucune gaffe dans ces parties.")
        else:
            phases = par_phase.rename(index=NOMS_PHASES).reset_index()
            phases.columns = ["phase", "gaffes"]
            total = par_phase.sum()
            fig2 = px.bar(
                phases,
                x="phase",
                y="gaffes",
                text="gaffes",
                labels={"phase": "Phase de la partie", "gaffes": "Nombre de gaffes"},
                title=(
                    f"{par_phase['middlegame'] / total:.0%} des gaffes tombent au milieu de partie et "
                    f"{par_phase['endgame'] / total:.0%} en finale ({total} gaffes au total)"
                ),
            )
            fig2.update_traces(marker_color=ROUGE)
            st.plotly_chart(fig2, key="fig_phases")

    # Est-ce que je stagne ? Le score par trimestre
    trimestres = (
        vue.assign(trimestre=vue["date_jeu"].dt.to_period("Q").astype(str))
        .groupby("trimestre")
        .agg(n=("score", "size"), score=("score", "mean"))
        .reset_index()
    )
    with st.container(border=True):
        if len(trimestres) < 2:
            st.info("Il faut au moins deux trimestres de parties pour voir une évolution : élargissez la période.")
        else:
            fig_t = px.line(
                trimestres,
                x="trimestre",
                y="score",
                markers=True,
                hover_data=["n"],
                labels={"trimestre": "Trimestre", "score": "Score moyen"},
                title=(
                    f"Mon score est passé de {trimestres['score'].iloc[0]:.0%} ({trimestres['trimestre'].iloc[0]}) "
                    f"à {trimestres['score'].iloc[-1]:.0%} ({trimestres['trimestre'].iloc[-1]})"
                ),
            )
            fig_t.update_traces(line_color=VERT)
            fig_t.add_hline(y=0.5, line_dash="dash", annotation_text="50 % : autant de points gagnés que perdus")
            fig_t.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_t, key="fig_trimestres")

    # Le plan : des pistes calculées sur ces parties
    st.subheader("Mon plan pour cette semaine")
    plan = st.columns(3, border=True)
    with plan[0]:
        st.markdown("**1. La phase**")
        if gaffes.empty:
            st.write("Pas assez de gaffes pour conclure.")
        else:
            st.write(f"{NOMS_PHASES[phase_max]} : {par_phase[phase_max] / par_phase.sum():.0%} de mes gaffes.")
            st.caption(CONSEILS_PHASE[phase_max])
    with plan[1]:
        st.markdown("**2. L'ouverture**")
        if fam.empty:
            st.write("Aucune famille assez jouée.")
        else:
            pire = fam.iloc[0]
            st.write(f"{pire['famille']} : {pire['score']:.0%} sur {pire['n']} parties.")
            st.caption("Rejouez ces parties et repérez le coup où l'évaluation bascule, puis préparez une réponse.")
    with plan[2]:
        st.markdown("**3. L'heure de jeu**")
        heures = vue.groupby("heure").agg(n=("score", "size"), score=("score", "mean")).reset_index()
        heures = heures[heures["n"] >= 20]
        if heures.empty:
            st.write("Pas assez de parties par heure.")
        else:
            bas = heures.loc[heures["score"].idxmin()]
            st.write(f"{int(bas['heure'])} h UTC : {bas['score']:.0%} sur {bas['n']} parties.")
            st.caption("Heures de 20 parties ou plus. À confirmer : l'écart peut venir du hasard.")

# ---------------------------------------------------------------- Échiquier
with tab_echiquier:
    st.markdown("Chaque rond est une case où j'ai joué un coup jugé mauvais : plus il est gros, plus j'y ai fauté.")
    gravite = st.segmented_control(
        "Gravité", list(GRAVITES), default="blunder", format_func=GRAVITES.get, key="gravite"
    ) or "blunder"
    fautes = coups_vue[coups_vue["jugement"] == gravite].copy()
    if fautes.empty:
        st.info("Aucune faute de ce type dans ces parties.")
    else:
        fautes["piece"] = fautes["coup"].map(piece).map(NOMS_PIECES)
        col_board, col_pieces = st.columns([3, 2])
        with col_board, st.container(border=True):
            st.plotly_chart(
                figure_echiquier(fautes, f"{len(fautes)} {GRAVITES[gravite].lower()} par case d'arrivée (vue des Blancs)"),
                key="fig_echiquier",
            )
            st.caption("Les roques n'ont pas de case : ils ne sont pas dessinés.")
        with col_pieces, st.container(border=True):
            par_piece = fautes["piece"].value_counts().rename_axis("piece").reset_index(name="fautes")
            top = par_piece.iloc[0]
            fig_p = px.bar(
                par_piece,
                x="fautes",
                y="piece",
                orientation="h",
                text="fautes",
                labels={"fautes": "Nombre de coups", "piece": "Pièce jouée"},
                title=f"Le coup fautif est le plus souvent un coup de {top['piece'].lower()} ({top['fautes'] / len(fautes):.0%})",
            )
            fig_p.update_traces(marker_color=ROUGE)
            fig_p.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_p, key="fig_pieces")

# ---------------------------------------------------------------- Ouvertures
with tab_ouvertures:
    if fam.empty:
        st.info(f"Aucune famille d'ouvertures n'a {n_min} parties ou plus avec ces filtres : baissez le curseur.")
    else:
        st.markdown(f"Familles d'ouvertures jouées au moins {n_min} fois, de la plus faible à la plus solide.")
        st.dataframe(
            fam.rename(columns={"famille": "Famille", "n": "Parties", "score": "Score", "gaffes": "Gaffes par partie"}),
            column_config={
                "Score": st.column_config.ProgressColumn("Score", min_value=0.0, max_value=1.0, format="percent"),
                "Gaffes par partie": st.column_config.NumberColumn(format="%.1f"),
            },
            hide_index=True,
            alt="Score et gaffes par famille d'ouvertures",
        )
        st.caption("Un petit nombre de parties donne un score fragile : fiez-vous d'abord aux familles les plus jouées.")

# ---------------------------------------------------------------- Nature des fautes
with tab_fautes:
    if gaffes.empty:
        st.info("Aucune gaffe dans ces parties.")
    else:
        g1, g2 = st.columns(2)
        nature = gaffes["sous_type"].fillna("positionnel").map(NATURES).value_counts().rename_axis("nature").reset_index(name="gaffes")
        with g1, st.container(border=True):
            fig_n = px.bar(
                nature,
                x="gaffes",
                y="nature",
                orientation="h",
                text="gaffes",
                labels={"gaffes": "Nombre de gaffes", "nature": ""},
                title=f"{nature['nature'].iloc[0]} : {nature['gaffes'].iloc[0] / len(gaffes):.0%} de mes gaffes",
            )
            fig_n.update_traces(marker_color=ORANGE)
            fig_n.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_n, key="fig_nature")
        meca = gaffes["mecanisme"].map(MECANISMES).value_counts().rename_axis("mecanisme").reset_index(name="gaffes")
        with g2, st.container(border=True):
            fig_m = px.bar(
                meca,
                x="gaffes",
                y="mecanisme",
                orientation="h",
                text="gaffes",
                labels={"gaffes": "Nombre de gaffes", "mecanisme": ""},
                title=f"Ce que la gaffe coûte : {meca['mecanisme'].iloc[0].lower()} ({meca['gaffes'].iloc[0] / len(gaffes):.0%})",
            )
            fig_m.update_traces(marker_color=ORANGE)
            fig_m.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_m, key="fig_meca")
        st.caption(
            "« Laissée » : j'ai permis une tactique à l'adversaire. « Ratée » : j'ai laissé passer la mienne. "
            "Une tactique laissée se corrige en vérifiant les menaces adverses avant de jouer."
        )
