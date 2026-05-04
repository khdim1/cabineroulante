import sqlite3
from database import DB_NAME
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

TOL_LARGEUR = config["recommandations"]["tolerance_largeur_assise_cm"]
TOL_PROFONDEUR = config["recommandations"]["tolerance_profondeur_assise_cm"]
TOL_HAUTEUR_DOSSIER = config["recommandations"]["tolerance_hauteur_dossier_cm"]
MARGE_HAUTEUR_ASSISE = config["recommandations"]["marge_hauteur_assise_cm"]

def recommander(mesures):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    hanches = mesures.get("hanches", 0)
    prof = mesures.get("profondeur_assise", 0)
    h_dossier = mesures.get("hauteur_dossier", 0)
    poids = mesures.get("poids", 0)
    h_poplitee = mesures.get("hauteur_poplitee", 0)

    meilleur = None
    meilleur_score = -1

    for row in c.execute("SELECT * FROM fauteuils"):
        # 1. Vérifier la charge max
        if poids > row["charge_max"]:
            continue

        # 2. Largeur d'assise : hanches + tolérance dans l'intervalle
        if not (row["largeur_assise_min"] <= hanches + TOL_LARGEUR <= row["largeur_assise_max"]):
            continue

        # 3. Profondeur d'assise
        if not (row["profondeur_assise_min"] <= prof + TOL_PROFONDEUR <= row["profondeur_assise_max"]):
            continue

        # 4. Hauteur du dossier (tolérance)
        if abs(h_dossier - row["hauteur_dossier"]) > TOL_HAUTEUR_DOSSIER:
            continue

        # 5. Hauteur d'assise : hauteur poplitée - marge doit être dans la plage réglable
        hauteur_ideale = h_poplitee - MARGE_HAUTEUR_ASSISE
        if not (row["hauteur_assise_min"] <= hauteur_ideale <= row["hauteur_assise_max"]):
            continue

        # Score : privilégier la largeur la plus proche du milieu de l'intervalle
        centre_largeur = (row["largeur_assise_min"] + row["largeur_assise_max"]) / 2
        score = 100 - abs(hanches + TOL_LARGEUR - centre_largeur)
        if score > meilleur_score:
            meilleur_score = score
            meilleur = dict(row)

    conn.close()
    return meilleur