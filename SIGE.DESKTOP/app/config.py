"""
config.py — Constantes de configuration de l'application

L'URL de l'API est lue depuis le fichier .env (variable API_URL).
Tous les chemins de fichiers locaux (base SQLite, factures PDF) sont
définis ici pour rester cohérents dans toute l'application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# URL de l'API FastAPI (modifiable dans .env)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Dossier de travail de l'application (à côté du script)
DOSSIER_APP = Path(__file__).resolve().parent.parent

# Base de données locale (mode hors-ligne)
CHEMIN_BASE_LOCALE = DOSSIER_APP / "local_data.db"

# Dossier où sont sauvegardées les factures imprimées (copie texte)
DOSSIER_FACTURES = DOSSIER_APP / "factures"
DOSSIER_FACTURES.mkdir(exist_ok=True)

# Intervalle de vérification de la connexion internet (en millisecondes)
INTERVALLE_PING_MS = 10_000

# Couleurs du thème clair professionnel
COULEUR_PRIMAIRE      = "#1E3A5F"   # bleu marine
COULEUR_PRIMAIRE_CLAIR = "#2C5282"
COULEUR_FOND          = "#F5F7FA"   # gris très clair
COULEUR_CARTE         = "#FFFFFF"
COULEUR_TEXTE         = "#1A202C"
COULEUR_TEXTE_DOUX    = "#6B7280"
COULEUR_BORDURE       = "#E2E8F0"
COULEUR_SUCCES        = "#2F855A"
COULEUR_DANGER        = "#C53030"
COULEUR_ALERTE        = "#B7791F"
