"""
routers/auth.py — Routes d'authentification

  POST /auth/connexion          → se connecter (tous)
  POST /auth/creer-premier-compte → créer le compte PDG initial (sans token)
  POST /auth/ajouter-vendeur    → directeur crée un vendeur pour sa boutique
  GET  /auth/moi                → voir son propre profil
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
    Retourne un token JWT à utiliser dans toutes les requêtes protégées.
    En-tête à envoyer :  Authorization: Bearer <token>
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
# Premier compte PDG — sans token, bloqué dès qu'un compte existe
# ------------------------------------------------------------------

@router.post(
    "/creer-premier-compte",
    response_model=schemas.ReponseUtilisateur,
    status_code=status.HTTP_201_CREATED,
    summary="Créer le compte PDG initial (aucun token requis)",
)
def creer_premier_compte(
    demande : schemas.DemandeCreationUtilisateur,
    db      : Session = Depends(get_db),
):
    """
    À utiliser une seule fois au démarrage pour créer le compte PDG.
    Automatiquement bloqué dès qu'un utilisateur existe.
    """
    if crud.get_nombre_utilisateurs(db) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un compte existe déjà. Connectez-vous en tant que PDG.",
        )

    if demande.role != "pdg":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le premier compte doit obligatoirement être un PDG.",
        )

    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ce nom est déjà utilisé.")

    return crud.creer_utilisateur(
        db=db,
        nom_utilisateur=demande.nom_utilisateur,
        mot_de_passe=demande.mot_de_passe,
        role="pdg",
        boutique_id=None,  # le PDG n'appartient à aucune boutique
    )


# ------------------------------------------------------------------
# Le directeur ajoute un vendeur à sa propre boutique
# ------------------------------------------------------------------

@router.post(
    "/ajouter-vendeur",
    response_model=schemas.ReponseUtilisateur,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un vendeur à sa boutique (directeur requis)",
)
def ajouter_vendeur(
    demande   : schemas.DemandeAjouterVendeur,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    """
    Le directeur crée un vendeur qui sera automatiquement
    assigné à la même boutique que le directeur.
    """
    if directeur.boutique_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce compte n'est pas associé à une boutique.",
        )

    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ce nom d'utilisateur est déjà pris.")

    return crud.creer_utilisateur(
        db=db,
        nom_utilisateur=demande.nom_utilisateur,
        mot_de_passe=demande.mot_de_passe,
        role="vendeur",
        boutique_id=directeur.boutique_id,  # même boutique que le directeur
    )


# ------------------------------------------------------------------
# Profil
# ------------------------------------------------------------------

@router.get(
    "/moi",
    response_model=schemas.ReponseUtilisateur,
    summary="Voir son propre profil",
)
def mon_profil(utilisateur=Depends(get_utilisateur_connecte)):
    return utilisateur
