"""
routers/auth.py — Routes d'authentification

  POST /auth/connexion            → se connecter (tous)
  POST /auth/creer-premier-compte → créer le PDG initial
  POST /auth/ajouter-vendeur      → directeur crée un vendeur (permission gerer_vendeurs)
  GET  /auth/moi                  → voir son propre profil
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_utilisateur_connecte, exiger_directeur
from ..permissions import verifier_permission
from .. import crud, schemas
from ..auth import creer_token

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/connexion", response_model=schemas.ReponseToken,
             summary="Se connecter et obtenir un token JWT")
def connexion(demande: schemas.DemandeConnexion, db: Session = Depends(get_db)):
    resultat = crud.verifier_connexion(db, demande.nom_utilisateur, demande.mot_de_passe)
    if resultat is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect.",
        )
    if resultat == "suspendu":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte a été suspendu. Contactez le PDG pour le rétablir.",
        )
    # Journaliser la connexion
    boutique = crud.get_boutique(db, resultat.boutique_id) if resultat.boutique_id else None
    crud.journaliser(db, resultat, boutique.nom if boutique else None, "connexion", {
        "role": resultat.role,
    })
    token = creer_token(nom_utilisateur=resultat.nom_utilisateur, role=resultat.role)
    return {"access_token": token, "type_token": "bearer"}


@router.post("/creer-premier-compte", response_model=schemas.ReponseUtilisateur,
             status_code=status.HTTP_201_CREATED,
             summary="Créer le compte PDG initial (aucun token requis)")
def creer_premier_compte(
    demande : schemas.DemandeCreationUtilisateur,
    db      : Session = Depends(get_db),
):
    if crud.get_nombre_utilisateurs(db) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un compte existe déjà. Connectez-vous en tant que PDG.",
        )
    if demande.role != "pdg":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le premier compte doit être un PDG.",
        )
    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ce nom est déjà utilisé.")

    return crud.creer_utilisateur(
        db=db,
        nom_utilisateur     = demande.nom_utilisateur,
        mot_de_passe        = demande.mot_de_passe,
        role                = "pdg",
        prenom              = demande.prenom,
        nom_famille         = demande.nom_famille,
        telephone           = demande.telephone,
        adresse_personnelle = demande.adresse_personnelle,
        boutique_id         = None,
    )


@router.post("/ajouter-vendeur", response_model=schemas.ReponseUtilisateur,
             status_code=status.HTTP_201_CREATED,
             summary="Ajouter un vendeur à sa boutique (permission gerer_vendeurs)")
def ajouter_vendeur(
    demande   : schemas.DemandeAjouterVendeur,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    verifier_permission(directeur, "gerer_vendeurs")

    if directeur.boutique_id is None:
        raise HTTPException(status_code=400, detail="Compte non associé à une boutique.")
    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ce nom est déjà pris.")

    nouveau = crud.creer_utilisateur(
        db=db,
        nom_utilisateur     = demande.nom_utilisateur,
        mot_de_passe        = demande.mot_de_passe,
        role                = "vendeur",
        prenom              = demande.prenom,
        nom_famille         = demande.nom_famille,
        telephone           = demande.telephone,
        adresse_personnelle = demande.adresse_personnelle,
        boutique_id         = directeur.boutique_id,
    )

    boutique = crud.get_boutique(db, directeur.boutique_id)
    crud.journaliser(db, directeur, boutique.nom if boutique else None, "creation_vendeur", {
        "nouveau_vendeur_id"   : nouveau.id,
        "nouveau_nom_complet"  : f"{nouveau.prenom} {nouveau.nom_famille}",
        "nouveau_telephone"    : nouveau.telephone,
    })
    return nouveau


@router.get("/moi", response_model=schemas.ReponseUtilisateur, summary="Voir son propre profil")
def mon_profil(utilisateur=Depends(get_utilisateur_connecte)):
    return utilisateur
