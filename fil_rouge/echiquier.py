"""Outils pour dessiner mes fautes sur un échiquier (utilisés par app_streamlit.py).

coups_juges.csv ne donne que le coup en notation algébrique (« Nf3 », « exd5 », « Qh4xe1+ ») :
on en tire la case d'arrivée (la dernière case écrite) et la pièce jouée (la majuscule du début).
"""

import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go

FICHIERS = list("abcdefgh")
CLAIR, FONCE = "#EEEED2", "#769656"  # les couleurs d'un échiquier classique
ROUGE = "#C0392B"
NOMS_PIECES = {"P": "Pion", "N": "Cavalier", "B": "Fou", "R": "Tour", "Q": "Dame", "K": "Roi"}


def case_arrivee(coup: str) -> str | None:
    """« Qh4xe1+ » -> « e1 ». Les roques (O-O) n'ont pas de case : None."""
    cases = re.findall(r"[a-h][1-8]", str(coup))
    return cases[-1] if cases else None


def piece(coup: str) -> str:
    """Lettre de la pièce : N, B, R, Q, K ; un pion si le coup commence par une minuscule."""
    coup = str(coup)
    if coup.startswith("O-O"):
        return "K"  # le roque est un coup de roi
    return coup[0] if coup[0] in "NBRQK" else "P"


def compter_cases(coups: pd.DataFrame) -> np.ndarray:
    """Matrice 8x8 (ligne = rangée 1..8, colonne = colonne a..h) du nombre de coups par case d'arrivée."""
    grille = np.zeros((8, 8), dtype=int)
    for case in coups["coup"].map(case_arrivee).dropna():
        grille[int(case[1]) - 1, FICHIERS.index(case[0])] += 1
    return grille


def figure_echiquier(coups: pd.DataFrame, titre: str, couleur_fautes: str = ROUGE) -> go.Figure:
    """Un échiquier vu du côté des Blancs, avec un rond par case : plus il est gros, plus j'y ai fauté."""
    grille = compter_cases(coups)
    # Fond : cases foncées quand (colonne + rangée) est paire (a1 est foncée)
    fond = np.fromfunction(lambda r, c: ((r + c) % 2 == 0).astype(int), (8, 8))
    fig = go.Figure(
        go.Heatmap(
            z=fond,
            x=FICHIERS,
            y=list(range(1, 9)),
            colorscale=[[0, CLAIR], [1, FONCE]],
            showscale=False,
            hoverinfo="skip",
            xgap=0,
            ygap=0,
        )
    )
    rangs, cols = np.nonzero(grille)
    nombres = grille[rangs, cols]
    if len(nombres):
        fig.add_trace(
            go.Scatter(
                x=[FICHIERS[c] for c in cols],
                y=rangs + 1,
                mode="markers+text",
                text=nombres,
                textfont=dict(color="white", size=11),
                marker=dict(
                    size=nombres,
                    sizemode="area",
                    sizeref=2.0 * nombres.max() / (46.0**2),
                    sizemin=12,
                    color=couleur_fautes,
                    opacity=0.85,
                    line=dict(color="white", width=1),
                ),
                customdata=[f"{FICHIERS[c]}{r + 1}" for r, c in zip(rangs, cols)],
                hovertemplate="Case %{customdata} : %{text} coups<extra></extra>",
                showlegend=False,
            )
        )
    fig.update_layout(
        title=titre,
        height=560,
        margin=dict(l=10, r=10, t=70, b=10),
        xaxis=dict(side="bottom", showgrid=False, zeroline=False, fixedrange=True, constrain="domain"),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 9)),
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            scaleanchor="x",
            constrain="domain",
        ),
    )
    return fig
