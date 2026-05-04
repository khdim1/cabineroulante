import sqlite3

DB_NAME = "fauteuils.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fauteuils (
        id INTEGER PRIMARY KEY,
        nom TEXT,
        largeur_assise_min REAL,   -- cm
        largeur_assise_max REAL,
        profondeur_assise_min REAL,
        profondeur_assise_max REAL,
        hauteur_dossier REAL,       -- hauteur du dossier (cm) (valeur typique, réglable)
        charge_max REAL,            -- kg
        hauteur_assise_min REAL,    -- hauteur sol‑assise min (cm)
        hauteur_assise_max REAL,    -- hauteur sol‑assise max (cm)
        image TEXT
    )''')

    # Nettoyage et insertion de modèles réels
    c.execute("DELETE FROM fauteuils")
    modeles = [
        # Modèle, larg_min, larg_max, prof_min, prof_max, haut_dossier, charge_max, haut_assise_min, haut_assise_max, image
        ("Quickie Q7 (Sunrise Medical)", 36, 56, 40, 51, 42, 113, 38, 48, "q7.png"),
        ("Top End Crossfire T6", 30, 56, 38, 48, 43, 113, 37, 47, "crossfire.png"),
        ("Kuschall Compact SA", 34, 46, 39, 49, 40, 130, 40, 50, "compact_sa.png"),
        ("Ottobock Boma", 38, 50, 42, 50, 45, 140, 42, 52, "boma.png"),
        ("Drive Titan HD (Heavy Duty)", 51, 71, 46, 56, 48, 204, 45, 55, "titan_hd.png"),
        ("Invacare R2 Basic", 34, 46, 38, 48, 40, 100, 38, 48, "r2basic.png"),
        ("Progeo Joker X", 32, 44, 36, 46, 38, 110, 36, 46, "jokerx.png"),
        ("Motion Composites Helio C2", 36, 48, 40, 50, 42, 125, 40, 50, "helio_c2.png"),
    ]
    c.executemany("INSERT INTO fauteuils VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", modeles)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de données initialisée avec modèles réels.")