"""Exo 1 : lire mes parties d'échecs. Environ 25 min.

Question : je joue depuis 2023, je stagne, qu'est-ce que je devrais travailler ?
À produire : un DataFrame propre, prêt pour les figures de l'exo 1 et pour l'appli de l'exo 2.
Les colonnes et leurs pièges sont dans data/echecs/LISEZMOI.md : lisez-le d'abord.
Lancer : uv run python fil_rouge/data.py
"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "echecs"

# Colonnes dont le reste du code a besoin (les exos suivants les utilisent aussi)
COLONNES_ATTENDUES = [
    "partie_id", "date_jeu", "cadence", "resultat", "elo_joueur", "elo_adverse",
    "ouverture_famille", "gaffes_joueur",
]
# Colonnes qui doivent être des nombres (si pandas les lit en texte, le CSV est abîmé)
COLONNES_NUMERIQUES = ["elo_joueur", "elo_adverse", "gaffes_joueur"]
# Colonnes qui peuvent légitimement être vides en partie (ex. cadence : 48 parties)
# mais jamais en totalité : on vérifie seulement qu'elles ne sont pas 100 % vides.
RESULTATS_CONNUS = {"win", "draw", "lose"}


def valider(df: pd.DataFrame) -> pd.DataFrame:
    """Plan B : s'arrêter avec un message clair si le fichier n'a pas la forme attendue.

    Colonnes absentes, colonnes entièrement vides, nombres lus comme du texte,
    identifiant de partie en double, résultat inconnu.
    """
    # 1. Colonnes absentes
    manquantes = [c for c in COLONNES_ATTENDUES if c not in df.columns]
    if manquantes:
        raise ValueError(f"Colonnes absentes de parties.csv : {manquantes}")

    # 2. Colonnes entièrement vides (le fichier est probablement mal exporté)
    vides = [c for c in df.columns if df[c].isna().all()]
    if vides:
        raise ValueError(f"Colonnes entièrement vides : {vides}")

    # 3. Nombres lus comme du texte (ex. "1 664" ou "n/a" dans la colonne)
    textes = [c for c in COLONNES_NUMERIQUES if not pd.api.types.is_numeric_dtype(df[c])]
    if textes:
        raise ValueError(f"Colonnes numériques lues comme du texte : {textes}")

    # 4. Identifiants de partie en double
    doublons = df.loc[df["partie_id"].duplicated(), "partie_id"].unique()
    if len(doublons) > 0:
        raise ValueError(f"partie_id en double : {list(doublons[:5])}")

    # 5. Résultat inconnu (on accepte aussi les valeurs déjà traduites)
    connus = RESULTATS_CONNUS | {"victoire", "nulle", "défaite"}
    inconnus = set(df["resultat"].dropna().unique()) - connus
    if inconnus or df["resultat"].isna().any():
        raise ValueError(f"resultat inconnu ou vide : {inconnus}")

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

    # On vérifie le fichier brut AVANT de le transformer (résultats en anglais)
    valider(df)

    # Date en datetime : elle est en UTC, on la laisse « naïve » (sans fuseau)
    df["date_jeu"] = pd.to_datetime(df["date_jeu"])

    # Résultat traduit : attention, fin_partie == "checkmate" vaut aussi pour mes défaites,
    # c'est bien la colonne resultat qu'il faut utiliser
    df["resultat"] = df["resultat"].map(
        {"win": "victoire", "draw": "nulle", "lose": "défaite"}
    )

    # Score : 1 pour une victoire, 0,5 pour une nulle, 0 pour une défaite
    df["score"] = df["resultat"].map({"victoire": 1.0, "nulle": 0.5, "défaite": 0.0})

    # Année et heure (UTC) de la partie
    df["annee"] = df["date_jeu"].dt.year
    df["heure"] = df["date_jeu"].dt.hour

    # Écart d'Elo : positif = adversaire plus fort que moi (Elo « avant la partie »)
    df["ecart_elo"] = df["elo_adverse"] - df["elo_joueur"]

    # Cadence vide (correspondance, sans pendule...) -> "aucune", pour ne pas perdre ces
    # parties dans les groupby / filtres (les NaN y sont ignorés)
    df["cadence"] = df["cadence"].fillna("aucune")

    return valider(df)


def load_coups() -> pd.DataFrame:
    """Un de mes coups jugés mauvais par ligne (data/echecs/coups_juges.csv)."""
    # Attention : ce fichier ne contient QUE mes coups jugés mauvais (pas mes bons coups)
    return pd.read_csv(DATA / "coups_juges.csv")


def familles(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """Score moyen par famille d'ouvertures, la pire d'abord.

    Colonnes : famille, n (parties), score, gaffes (par partie).
    Sous min_n parties le chiffre ne dit rien : écartez la famille.
    """
    # Une ligne par partie : on peut compter les parties avec "count" directement.
    # Les 5 parties sans ouverture reconnue (famille vide) sont ignorées par groupby.
    res = (
        df.groupby("ouverture_famille")
        .agg(n=("partie_id", "count"), score=("score", "mean"), gaffes=("gaffes_joueur", "mean"))
        .reset_index()
        .rename(columns={"ouverture_famille": "famille"})
    )
    # On écarte les familles trop rares, puis la pire (score le plus bas) en premier
    res = res[res["n"] >= min_n]
    return res.sort_values("score").reset_index(drop=True)


if __name__ == "__main__":
    d = load_data()
    print(d.shape)
