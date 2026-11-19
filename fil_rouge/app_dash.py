"""Exo 4 : la même appli en Dash, avec un drill-down. Environ 25 min.

Question : quelles ouvertures coûtent des points, et dans quelles parties ?
À produire : un curseur (parties minimum) et le graphique des familles ; un clic sur une barre
liste les parties, un clic sur une partie liste les coups jugés mauvais, dans deux AG Grid.
Lancer : uv run python fil_rouge/app_dash.py   (http://127.0.0.1:8050)
"""

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Dash, Input, Output, callback, ctx, dcc, html

from data import familles, load_coups, load_data

VERT, ROUGE = "#769656", "#C0392B"

app = Dash(
    __name__,
    title="Mes parties d'échecs",
    external_stylesheets=[dbc.themes.BOOTSTRAP],  # grille Bootstrap : les colonnes s'empilent sur téléphone
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # Dash tourne sur Flask

# Réglages imposés pour tout AgGrid du projet (voir AGENTS.md)
OPTIONS_GRILLE = {"theme": "themeBalham", "animateRows": True, "pagination": True, "paginationPageSize": 10}
# minWidth : sur un petit écran la grille défile au lieu d'écraser les colonnes
COLONNE_PAR_DEFAUT = {"filter": True, "sortable": True, "minWidth": 110}

COLONNES_PARTIES = [
    {"field": "partie_id", "headerName": "Partie"},
    {"field": "date", "headerName": "Date"},
    {"field": "plateforme", "headerName": "Plateforme"},
    {"field": "cadence", "headerName": "Cadence"},
    {"field": "couleur", "headerName": "Couleur"},
    {"field": "resultat", "headerName": "Résultat"},
    {"field": "elo_joueur", "headerName": "Mon Elo"},
    {"field": "elo_adverse", "headerName": "Elo adverse"},
    {"field": "gaffes_joueur", "headerName": "Gaffes"},
    {"field": "precision_joueur", "headerName": "Précision"},
]
COLONNES_COUPS = [
    {"field": "numero_coup", "headerName": "Coup n°"},
    {"field": "coup", "headerName": "Mon coup"},
    {"field": "meilleur_coup", "headerName": "Meilleur coup"},
    {"field": "jugement", "headerName": "Gravité"},
    {"field": "phase", "headerName": "Phase"},
    {"field": "variation_eval_cp", "headerName": "Perte (cp)"},
    {"field": "categorie", "headerName": "Catégorie"},
    {"field": "sous_type", "headerName": "Tactique"},
    {"field": "mecanisme", "headerName": "Mécanisme"},
    {"field": "temps_restant_s", "headerName": "Temps restant (s)"},
]


def vers_lignes(df, colonnes):
    """DataFrame -> liste de dicts pour AgGrid (les valeurs vides deviennent None, sinon le JSON casse)."""
    champs = [c["field"] for c in colonnes]
    return df[champs].astype(object).where(df[champs].notna(), None).to_dict("records")


app.layout = dbc.Container(
    [
        html.H2("Quelles ouvertures me coûtent des points ? Cliquez une barre", className="my-3"),
        dbc.Card(
            dbc.CardBody(
                [
                    html.Label("Parties minimum par famille d'ouvertures", htmlFor="n-min"),
                    dcc.Slider(30, 60, 10, value=30, id="n-min"),
                    dcc.Loading(dcc.Graph(id="familles", config={"displayModeBar": False})),
                ]
            ),
            className="mb-3",
        ),
        dbc.Row(
            [
                # xs=12 : une colonne sur téléphone ; xl=6 : deux grilles côte à côte sur grand écran
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Cliquez une barre pour voir ses parties", id="parties-titre"),
                                dag.AgGrid(
                                    id="parties",
                                    rowData=[],
                                    columnDefs=COLONNES_PARTIES,
                                    dashGridOptions={
                                        **OPTIONS_GRILLE,
                                        "rowSelection": {"mode": "singleRow", "enableClickSelection": True},
                                    },
                                    columnSize="responsiveSizeToFit",
                                    defaultColDef=COLONNE_PAR_DEFAUT,
                                ),
                            ]
                        )
                    ),
                    xs=12,
                    xl=6,
                    className="mb-3",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Cliquez une partie pour voir mes coups jugés mauvais", id="coups-titre"),
                                dag.AgGrid(
                                    id="coups",
                                    rowData=[],
                                    columnDefs=COLONNES_COUPS,
                                    dashGridOptions=OPTIONS_GRILLE,
                                    columnSize="responsiveSizeToFit",
                                    defaultColDef=COLONNE_PAR_DEFAUT,
                                ),
                            ]
                        )
                    ),
                    xs=12,
                    xl=6,
                    className="mb-3",
                ),
            ]
        ),
    ],
    className="pb-4",
)


# Le curseur redessine le graphique des familles, la pire en haut
@callback(Output("familles", "figure"), Input("n-min", "value"))
def maj_familles(n_min):
    fam = familles(load_data(), min_n=n_min)  # données lues ici, pas à l'import : toujours à jour
    if fam.empty:
        return px.bar(title=f"Aucune famille d'ouvertures n'a {n_min} parties ou plus")
    pire, meilleure = fam.iloc[0], fam.iloc[-1]
    fig = px.bar(
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
            f"{pire['famille']} : {pire['score']:.1%} de score sur {pire['n']} parties "
            f"(meilleure : {meilleure['famille']}, {meilleure['score']:.1%})"
        ),
    )
    fig.update_yaxes(autorange="reversed")  # la pire en haut
    fig.update_coloraxes(showscale=False)
    # Téléphone : titre plus petit, marges serrées, noms de familles qui ne sont pas coupés
    fig.update_layout(title_font_size=14, margin={"l": 10, "r": 10, "t": 60, "b": 10})
    fig.update_yaxes(automargin=True, title_text=None)
    return fig


# Un clic sur une barre liste les parties de la famille (le curseur remet la liste à zéro)
@callback(
    Output("parties", "rowData"),
    Output("parties-titre", "children"),
    Input("familles", "clickData"),
    Input("n-min", "value"),
    prevent_initial_call=True,
)
def maj_parties(click, _n_min):
    if ctx.triggered_id == "n-min" or not click:
        return [], "Cliquez une barre pour voir ses parties"
    famille = click["points"][0]["y"]  # barres horizontales : le nom de la famille est sur l'axe y
    df = load_data()
    parties = df[df["ouverture_famille"] == famille].sort_values("date_jeu").copy()
    parties["date"] = parties["date_jeu"].dt.strftime("%Y-%m-%d %H:%M")
    return vers_lignes(parties, COLONNES_PARTIES), f"{len(parties)} parties en {famille}"


# Un clic sur une partie liste mes coups jugés mauvais dans cette partie
@callback(
    Output("coups", "rowData"),
    Output("coups-titre", "children"),
    Input("parties", "selectedRows"),
)
def maj_coups(lignes):
    if not lignes:
        return [], "Cliquez une partie pour voir mes coups jugés mauvais"
    partie_id = lignes[0]["partie_id"]
    coups = load_coups()
    coups = coups[coups["partie_id"] == partie_id].sort_values("ply")
    titre = f"{len(coups)} coups jugés mauvais dans la partie {partie_id}"
    if coups.empty:
        titre = f"Aucun coup jugé mauvais dans la partie {partie_id}"
    return vers_lignes(coups, COLONNES_COUPS), titre


if __name__ == "__main__":
    # debug=True : bouton « Callbacks » en bas à droite, le graphe des callbacks
    app.run(debug=False, port=8050)
