"""
dependencies.py — Dépendances FastAPI réutilisables

  get_db()                   → session base de données
  get_utilisateur_connecte() → lit le token JWT
  exiger_vendeur()           → vendeur + directeur + pdg
  exiger_directeur()         → directeur + pdg
  exiger_pdg()               → pdg uniquement
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .data import SessionLocal
from .auth import lire_token
from . import crud

schema_bearer = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_utilisateur_connecte(
    credentials: HTTPAuthorizationCredentials = Depends(schema_bearer),
    db: Session = Depends(get_db),
):
    """
    Décode le token JWT et retourne l'utilisateur en base.
    Lève 401 si le token est absent, expiré ou invalide.
    """
    erreur_401 = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail      = "Token invalide ou expiré. Veuillez vous reconnecter.",
        headers     = {"WWW-Authenticate": "Bearer"},
    )
    contenu = lire_token(credentials.credentials)
    if contenu is None:
        raise erreur_401

    nom_utilisateur = contenu.get("sub")
    if not nom_utilisateur:
        raise erreur_401

    utilisateur = crud.get_utilisateur_par_nom(db, nom_utilisateur)
    if utilisateur is None:
        raise erreur_401

    return utilisateur


def exiger_vendeur(utilisateur=Depends(get_utilisateur_connecte)):
    """Autorise vendeur, directeur et PDG."""
    if utilisateur.role not in ["vendeur", "directeur", "pdg"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé.",
        )
    return utilisateur


def exiger_directeur(utilisateur=Depends(get_utilisateur_connecte)):
    """Autorise directeur et PDG (pas les vendeurs)."""
    if utilisateur.role not in ["directeur", "pdg"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Réservé au directeur ou au PDG.",
        )
    return utilisateur


def exiger_pdg(utilisateur=Depends(get_utilisateur_connecte)):
    """Réservé exclusivement au PDG."""
    if utilisateur.role != "pdg":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Réservé au PDG.",
        )
    return utilisateur
