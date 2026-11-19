"""Exo 1 : lire mes parties d'échecs. Environ 25 min.

Question : je joue depuis 2023, je stagne, qu'est-ce que je devrais travailler ?
À produire : un DataFrame propre, prêt pour les figures de l'exo 1 et pour l'appli de l'exo 2.
Les colonnes et leurs pièges sont dans data/echecs/LISEZMOI.md : lisez-le d'abord.
Lancer : uv run python fil_rouge/data.py
"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "echecs"


COLONNES_OBLIGATOIRES = [
    "partie_id", "date_jeu", "cadence", "resultat", "couleur", "elo_joueur",
    "elo_adverse", "ouverture_famille", "gaffes_joueur", "nb_coups",
]
COLONNES_NOMBRES = ["elo_joueur", "elo_adverse", "gaffes_joueur", "nb_coups"]
RESULTATS = {"win": "victoire", "draw": "nulle", "lose": "défaite"}
SCORES = {"victoire": 1.0, "nulle": 0.5, "défaite": 0.0}


def valider(df: pd.DataFrame) -> pd.DataFrame:
    """Plan B : s'arrêter avec un message clair si le fichier n'a pas la forme attendue.

    Colonnes absentes, colonnes entièrement vides, nombres lus comme du texte,
    identifiant de partie en double, résultat inconnu.
    """
    # 1. Colonnes absentes
    manquantes = [c for c in COLONNES_OBLIGATOIRES if c not in df.columns]
    if manquantes:
        raise ValueError(f"Colonnes absentes : {manquantes}")
    # 2. Colonnes entièrement vides
    vides = [c for c in COLONNES_OBLIGATOIRES if df[c].isna().all()]
    if vides:
        raise ValueError(f"Colonnes entièrement vides : {vides}")
    # 3. Nombres lus comme du texte
    for c in COLONNES_NOMBRES:
        if not pd.api.types.is_numeric_dtype(df[c]):
            raise ValueError(f"La colonne {c} devrait être numérique (type lu : {df[c].dtype})")
    # 4. Identifiants de partie en double
    nb_doublons = df["partie_id"].duplicated().sum()
    if nb_doublons:
        raise ValueError(f"{nb_doublons} identifiants de partie en double")
    # 5. Résultats inconnus
    inconnus = set(df["resultat"].dropna().unique()) - set(RESULTATS)
    if inconnus or df["resultat"].isna().any():
        raise ValueError(f"Résultats inconnus ou vides : {inconnus}")
    return df


def load_data() -> pd.DataFrame:
    """Une ligne par partie (data/echecs/parties.csv), validée.

    Ajoutez : le résultat de mon point de vue en français, un score (1, 0,5 ou 0),
    l'année, l'heure, et l'écart d'Elo avec l'adversaire. Une cadence vide veut dire
    « aucune » : ne la laissez pas disparaître des filtres.
    Les exos suivants lisent ces colonnes, gardez ces noms : date_jeu (en datetime),
    resultat (victoire, nulle, défaite), score, annee, heure (UTC), ecart_elo
    (Elo de l'adversaire moins le mien), cadence.
    """
    df = pd.read_csv(DATA / "parties.csv")
    df = valider(df)

    # Date en vrai datetime (les heures du fichier sont déjà en UTC, on ne convertit rien)
    df["date_jeu"] = pd.to_datetime(df["date_jeu"])
    df["annee"] = df["date_jeu"].dt.year
    df["heure"] = df["date_jeu"].dt.hour

    # Résultat traduit (win/draw/lose -> victoire/nulle/défaite) et score associé
    df["resultat"] = df["resultat"].map(RESULTATS)
    df["score"] = df["resultat"].map(SCORES)

    # Écart d'Elo : Elo de l'adversaire moins le mien (Elo d'avant la partie)
    df["ecart_elo"] = df["elo_adverse"] - df["elo_joueur"]

    # Cadence vide = parties par correspondance sans cadence : on la nomme « aucune »
    # pour que les groupby / filtres ne la perdent pas
    df["cadence"] = df["cadence"].fillna("aucune")
    return df


def load_coups() -> pd.DataFrame:
    """Un de mes coups jugés mauvais par ligne (data/echecs/coups_juges.csv)."""
    return pd.read_csv(DATA / "coups_juges.csv")


def familles(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """Score moyen par famille d'ouvertures, la pire d'abord.

    Colonnes : famille, n (parties), score, gaffes (par partie).
    Sous min_n parties le chiffre ne dit rien : écartez la famille.
    """
    # Les parties sans ouverture connue n'ont pas de famille : groupby les ignore
    res = (
        df.groupby("ouverture_famille")
        .agg(n=("partie_id", "count"), score=("score", "mean"), gaffes=("gaffes_joueur", "mean"))
        .reset_index()
        .rename(columns={"ouverture_famille": "famille"})
    )
    res = res[res["n"] >= min_n]
    return res.sort_values("score").reset_index(drop=True)


if __name__ == "__main__":
    d = load_data()
    print(d.shape)
