"""
dependencies.py — Dépendances FastAPI réutilisables

Contient :
  - get_db()                  : session base de données
  - get_utilisateur_connecte(): lit le token JWT et retourne l'utilisateur
  - exiger_vendeur()          : autorise vendeur ET directeur
  - exiger_directeur()        : autorise seulement le directeur
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .data import SessionLocal
from .auth import lire_token
from . import crud


# ------------------------------------------------------------------
# Base de données
# ------------------------------------------------------------------

def get_db():
    """
    Fournit une session base de données à chaque requête.
    La session est toujours fermée proprement après usage.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------
# Lecture du token JWT
# ------------------------------------------------------------------

# HTTPBearer lit automatiquement l'en-tête : Authorization: Bearer <token>
schema_bearer = HTTPBearer()


def get_utilisateur_connecte(
    credentials: HTTPAuthorizationCredentials = Depends(schema_bearer),
    db: Session = Depends(get_db),
):
    """
    Lit le token JWT envoyé dans l'en-tête Authorization.
    Vérifie qu'il est valide et retourne l'utilisateur correspondant en base.

    Lève une erreur 401 si :
      - le token est absent, expiré ou invalide
      - l'utilisateur n'existe plus en base
    """
    erreur_401 = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail      = "Token invalide ou expiré. Veuillez vous reconnecter.",
        headers     = {"WWW-Authenticate": "Bearer"},
    )

    # Décodage du token
    contenu = lire_token(credentials.credentials)
    if contenu is None:
        raise erreur_401

    # Récupération du nom d'utilisateur dans le token
    nom_utilisateur = contenu.get("sub")
    if not nom_utilisateur:
        raise erreur_401

    # Vérification que l'utilisateur existe toujours en base
    utilisateur = crud.get_utilisateur_par_nom(db, nom_utilisateur)
    if utilisateur is None:
        raise erreur_401

    return utilisateur


# ------------------------------------------------------------------
# Gardes de rôle
# ------------------------------------------------------------------

def exiger_vendeur(utilisateur=Depends(get_utilisateur_connecte)):
    """
    Autorise les vendeurs ET les directeurs.
    Lève une erreur 403 si l'utilisateur n'a aucun de ces rôles.
    """
    roles_autorises = ["vendeur", "directeur"]

    if utilisateur.role not in roles_autorises:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Accès refusé. Rôle requis : vendeur ou directeur.",
        )
    return utilisateur


def exiger_directeur(utilisateur=Depends(get_utilisateur_connecte)):
    """
    Autorise seulement le directeur général.
    Lève une erreur 403 si l'utilisateur est un simple vendeur.
    """
    if utilisateur.role != "directeur":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Accès refusé. Réservé au directeur général.",
        )
    return utilisateur
