"""
routers/auth.py — Routes d'authentification

  POST /auth/connexion          : se connecter et obtenir un token JWT
  POST /auth/creer-utilisateur  : créer le tout premier compte (sans token)
  POST /auth/ajouter-utilisateur: ajouter un compte (directeur requis)
  GET  /auth/moi                : voir son propre profil
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_utilisateur_connecte, exiger_directeur
from .. import crud, schemas
from ..auth import creer_token


router = APIRouter(prefix="/auth", tags=["Authentification"])


# ------------------------------------------------------------------
# Connexion — ouverte à tous
# ------------------------------------------------------------------

@router.post(
    "/connexion",
    response_model=schemas.ReponseToken,
    summary="Se connecter et obtenir un token JWT",
)
def connexion(demande: schemas.DemandeConnexion, db: Session = Depends(get_db)):
    """
    Envoie le nom d'utilisateur et le mot de passe.
    En retour : un token JWT à utiliser dans toutes les requêtes suivantes.

    Comment utiliser le token :
        En-tête HTTP → Authorization: Bearer <token>
    """
    utilisateur = crud.verifier_connexion(db, demande.nom_utilisateur, demande.mot_de_passe)

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect.",
        )

    token = creer_token(
        nom_utilisateur=utilisateur.nom_utilisateur,
        role=utilisateur.role,
    )

    return {"access_token": token, "type_token": "bearer"}


# ------------------------------------------------------------------
# Premier utilisateur — sans token (bootstrapping)
# Accessible UNIQUEMENT si aucun compte n'existe encore
# ------------------------------------------------------------------

@router.post(
    "/creer-premier-compte",
    response_model=schemas.ReponseUtilisateur,
    status_code=status.HTTP_201_CREATED,
    summary="Créer le tout premier compte directeur (aucun token requis)",
)
def creer_premier_compte(
    demande: schemas.DemandeCreationUtilisateur,
    db: Session = Depends(get_db),
):
    """
    Endpoint de démarrage : crée le premier compte directeur.
    Bloqué automatiquement dès qu'au moins un utilisateur existe.
    """
    # Bloquer si des utilisateurs existent déjà
    if crud.get_nombre_utilisateurs(db) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un compte existe déjà. Utilisez /auth/ajouter-utilisateur (token directeur requis).",
        )

    # Vérifier que le nom n'est pas déjà pris
    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le nom '{demande.nom_utilisateur}' est déjà utilisé.",
        )

    return crud.creer_utilisateur(
        db=db,
        nom_utilisateur=demande.nom_utilisateur,
        mot_de_passe=demande.mot_de_passe,
        role=demande.role,
    )


# ------------------------------------------------------------------
# Ajouter un utilisateur — réservé au directeur
# ------------------------------------------------------------------

@router.post(
    "/ajouter-utilisateur",
    response_model=schemas.ReponseUtilisateur,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un vendeur ou directeur (token directeur requis)",
)
def ajouter_utilisateur(
    demande: schemas.DemandeCreationUtilisateur,
    db: Session = Depends(get_db),
    _directeur=Depends(exiger_directeur),   # seul le directeur peut créer des comptes
):
    """
    Crée un nouveau compte vendeur ou directeur.
    Seul un directeur connecté peut utiliser cet endpoint.
    """
    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le nom '{demande.nom_utilisateur}' est déjà utilisé.",
        )

    return crud.creer_utilisateur(
        db=db,
        nom_utilisateur=demande.nom_utilisateur,
        mot_de_passe=demande.mot_de_passe,
        role=demande.role,
    )


# ------------------------------------------------------------------
# Profil de l'utilisateur connecté
# ------------------------------------------------------------------

@router.get(
    "/moi",
    response_model=schemas.ReponseUtilisateur,
    summary="Voir son propre profil",
)
def mon_profil(utilisateur=Depends(get_utilisateur_connecte)):
    """Retourne les informations du compte actuellement connecté."""
    return utilisateur
