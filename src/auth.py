"""
auth.py — Utilitaires JWT et hachage de mot de passe

Contient :
  - hacher_mot_de_passe()   : transforme un mot de passe en hash sécurisé
  - verifier_mot_de_passe() : compare un mot de passe avec son hash
  - creer_token()           : génère un token JWT signé
  - lire_token()            : décode et vérifie un token JWT
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext


# ------------------------------------------------------------------
# Clé secrète utilisée pour signer les tokens JWT.
# En production, remplacez cette valeur par une vraie clé secrète
# stockée dans une variable d'environnement.
# ------------------------------------------------------------------
CLE_SECRETE = os.getenv("SECRET_KEY", "changez-cette-cle-en-production")

# Algorithme de signature du token
ALGORITHME = "HS256"

# Durée de vie d'un token : 8 heures
DUREE_TOKEN_HEURES = 8

# Contexte de hachage — utilise bcrypt, l'algorithme recommandé
contexte_hachage = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ------------------------------------------------------------------
# Mot de passe
# ------------------------------------------------------------------

def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """
    Transforme un mot de passe en texte clair en un hash bcrypt sécurisé.
    Le hash est différent à chaque appel même pour le même mot de passe.
    """
    return contexte_hachage.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond au hash stocké en base.
    Retourne True si correct, False sinon.
    """
    return contexte_hachage.verify(mot_de_passe, hash_stocke)


# ------------------------------------------------------------------
# Token JWT
# ------------------------------------------------------------------

def creer_token(nom_utilisateur: str, role: str) -> str:
    """
    Génère un token JWT signé contenant :
      - le nom d'utilisateur (sub)
      - le rôle (role)
      - la date d'expiration (exp)

    Le token est valable DUREE_TOKEN_HEURES heures.
    """
    expiration = datetime.now(timezone.utc) + timedelta(hours=DUREE_TOKEN_HEURES)

    contenu_token = {
        "sub"  : nom_utilisateur,   # subject — identifiant de l'utilisateur
        "role" : role,              # "vendeur" ou "directeur"
        "exp"  : expiration,        # date d'expiration automatique
    }

    token = jwt.encode(contenu_token, CLE_SECRETE, algorithm=ALGORITHME)
    return token


def lire_token(token: str) -> dict | None:
    """
    Décode un token JWT et retourne son contenu sous forme de dictionnaire.
    Retourne None si le token est invalide ou expiré.

    Le dictionnaire contient : "sub" (nom), "role", "exp"
    """
    try:
        contenu = jwt.decode(token, CLE_SECRETE, algorithms=[ALGORITHME])
        return contenu
    except jwt.ExpiredSignatureError:
        # Token expiré
        return None
    except jwt.InvalidTokenError:
        # Token falsifié ou mal formé
        return None
