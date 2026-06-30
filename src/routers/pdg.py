"""
routers/pdg.py — Routes exclusives au PDG

Boutiques :
  POST   /pdg/boutiques                          → créer une boutique
  GET    /pdg/boutiques                          → lister toutes les boutiques
  PUT    /pdg/boutiques/{id}/archiver            → archiver

Équipes :
  POST   /pdg/boutiques/{id}/ajouter-directeur   → créer le directeur
  POST   /pdg/boutiques/{id}/ajouter-vendeur     → créer un vendeur

Permissions des directeurs :
  GET    /pdg/directeurs/{id}/permissions        → voir les droits d'un directeur
  PUT    /pdg/directeurs/{id}/permissions        → modifier ses droits
  PUT    /pdg/directeurs/{id}/suspendre          → bloquer l'accès
  PUT    /pdg/directeurs/{id}/reactiver          → rétablir l'accès

Dashboard :
  GET    /pdg/dashboard                          → vue globale entreprise
  GET    /pdg/boutiques/{id}/stats               → stats d'une boutique
  GET    /pdg/evolution                          → courbe des ventes
  GET    /pdg/classement                         → classement boutiques
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, exiger_pdg
from ..permissions import TOUTES_LES_PERMISSIONS, LABELS_PERMISSIONS
from .. import crud, schemas

router = APIRouter(prefix="/pdg", tags=["PDG — Direction générale"])


# ============================================================
# BOUTIQUES
# ============================================================

@router.post("/boutiques", response_model=schemas.ReponseBoutique,
             status_code=status.HTTP_201_CREATED, summary="Créer une boutique")
def creer_boutique(
    demande : schemas.DemandeCréerBoutique,
    db      : Session = Depends(get_db),
    _pdg    = Depends(exiger_pdg),
):
    return crud.creer_boutique(db, demande.nom, demande.ville, demande.adresse)


@router.get("/boutiques", response_model=list[schemas.ReponseBoutique],
            summary="Lister toutes les boutiques")
def lister_boutiques(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    return crud.get_boutiques(db)


@router.put("/boutiques/{id}/archiver", response_model=schemas.ReponseBoutique,
            summary="Archiver une boutique (données conservées)")
def archiver_boutique(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutique = crud.archiver_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return boutique


# ============================================================
# GESTION DES ÉQUIPES
# ============================================================

@router.post("/boutiques/{id}/ajouter-directeur",
             response_model=schemas.ReponseUtilisateur,
             status_code=status.HTTP_201_CREATED,
             summary="Créer le directeur d'une boutique")
def ajouter_directeur(
    id      : int,
    demande : schemas.DemandeAjouterDirecteur,
    db      : Session = Depends(get_db),
    _pdg    = Depends(exiger_pdg),
):
    """
    Crée un compte directeur et l'associe à la boutique.
    Le directeur démarre sans aucune permission — le PDG les accordera ensuite.
    """
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    if not boutique.est_active:
        raise HTTPException(status_code=400, detail="Boutique archivée — impossible d'y affecter un directeur")

    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Le nom '{demande.nom_utilisateur}' est déjà utilisé.")

    return crud.creer_utilisateur(
        db              = db,
        nom_utilisateur = demande.nom_utilisateur,
        mot_de_passe    = demande.mot_de_passe,
        role            = "directeur",
        boutique_id     = id,
    )


@router.post("/boutiques/{id}/ajouter-vendeur",
             response_model=schemas.ReponseUtilisateur,
             status_code=status.HTTP_201_CREATED,
             summary="Ajouter un vendeur à une boutique")
def ajouter_vendeur(
    id      : int,
    demande : schemas.DemandeAjouterVendeur,
    db      : Session = Depends(get_db),
    _pdg    = Depends(exiger_pdg),
):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")

    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Le nom '{demande.nom_utilisateur}' est déjà utilisé.")

    return crud.creer_utilisateur(
        db              = db,
        nom_utilisateur = demande.nom_utilisateur,
        mot_de_passe    = demande.mot_de_passe,
        role            = "vendeur",
        boutique_id     = id,
    )


# ============================================================
# PERMISSIONS DES DIRECTEURS
# ============================================================

@router.get("/directeurs/{id}/permissions",
            response_model=schemas.ReponsePermissions,
            summary="Voir les droits d'un directeur")
def voir_permissions(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    """
    Affiche les droits actuels du directeur et ceux qui lui manquent.
    """
    directeur = crud.get_utilisateur_par_id(db, id)
    if not directeur or directeur.role != "directeur":
        raise HTTPException(status_code=404, detail="Directeur introuvable")

    permissions_actuelles  = directeur.permissions or []
    permissions_manquantes = [p for p in TOUTES_LES_PERMISSIONS if p not in permissions_actuelles]

    return schemas.ReponsePermissions(
        directeur_id           = directeur.id,
        nom_utilisateur        = directeur.nom_utilisateur,
        boutique_id            = directeur.boutique_id,
        est_actif              = directeur.est_actif,
        permissions            = permissions_actuelles,
        permissions_manquantes = permissions_manquantes,
    )


@router.put("/directeurs/{id}/permissions",
            response_model=schemas.ReponsePermissions,
            summary="Modifier les droits d'un directeur")
def modifier_permissions(
    id      : int,
    demande : schemas.DemandeModifierPermissions,
    db      : Session = Depends(get_db),
    _pdg    = Depends(exiger_pdg),
):
    """
    Remplace entièrement la liste des permissions du directeur.

    Exemple pour tout accorder :
      ["voir_profits", "faire_achats", "creer_articles", "voir_alertes", "gerer_vendeurs"]

    Exemple pour tout bloquer :
      []
    """
    directeur = crud.modifier_permissions(db, id, demande.permissions)
    if not directeur:
        raise HTTPException(status_code=404, detail="Directeur introuvable")

    permissions_manquantes = [p for p in TOUTES_LES_PERMISSIONS if p not in (directeur.permissions or [])]

    return schemas.ReponsePermissions(
        directeur_id           = directeur.id,
        nom_utilisateur        = directeur.nom_utilisateur,
        boutique_id            = directeur.boutique_id,
        est_actif              = directeur.est_actif,
        permissions            = directeur.permissions or [],
        permissions_manquantes = permissions_manquantes,
    )


@router.put("/directeurs/{id}/suspendre",
            response_model=schemas.ReponseUtilisateur,
            summary="Suspendre un compte (directeur ou vendeur)")
def suspendre(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    """
    Désactive le compte — l'utilisateur ne peut plus se connecter
    et reçoit un message explicite lui indiquant de contacter le PDG.
    """
    utilisateur = crud.suspendre_utilisateur(db, id)
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return utilisateur


@router.put("/directeurs/{id}/reactiver",
            response_model=schemas.ReponseUtilisateur,
            summary="Réactiver un compte suspendu")
def reactiver(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    utilisateur = crud.reactiver_utilisateur(db, id)
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return utilisateur


# ============================================================
# DASHBOARD PDG
# ============================================================

@router.get("/dashboard", response_model=schemas.DashboardPDG,
            summary="Tableau de bord complet de l'entreprise")
def dashboard(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutiques         = crud.get_boutiques(db)
    boutiques_actives = [b for b in boutiques if b.est_active]

    classement = sorted(
        [
            schemas.StatsBoutique(
                boutique       = b,
                nb_articles    = crud.get_nb_articles_boutique(db, b.id),
                nb_vendeurs    = crud.get_vendeurs_de_boutique(db, b.id),
                benefice_total = crud.get_total_profit_boutique(db, b.id),
                ventes_du_mois = crud.get_ventes_du_mois_boutique(db, b.id),
            )
            for b in boutiques_actives
        ],
        key     = lambda s: s.benefice_total,
        reverse = True,
    )

    activite = [
        schemas.MouvementRecent(**m)
        for m in crud.get_activite_recente(db, limite=10)
    ]

    return schemas.DashboardPDG(
        nb_boutiques              = len(boutiques),
        nb_boutiques_actives      = len(boutiques_actives),
        benefice_total_entreprise = crud.get_benefice_total_entreprise(db),
        ventes_totales_du_mois    = crud.get_ventes_totales_du_mois(db),
        articles_en_alerte        = crud.get_nb_articles_en_alerte_total(db),
        classement_boutiques      = classement,
        activite_recente          = activite,
    )


@router.get("/boutiques/{id}/stats", response_model=schemas.StatsBoutique,
            summary="Stats détaillées d'une boutique")
def stats_boutique(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return schemas.StatsBoutique(
        boutique       = boutique,
        nb_articles    = crud.get_nb_articles_boutique(db, id),
        nb_vendeurs    = crud.get_vendeurs_de_boutique(db, id),
        benefice_total = crud.get_total_profit_boutique(db, id),
        ventes_du_mois = crud.get_ventes_du_mois_boutique(db, id),
    )


@router.get("/evolution", response_model=list[schemas.PointEvolution],
            summary="Évolution des ventes (toutes boutiques)")
def evolution_ventes(
    nb_jours : int = Query(default=30, ge=7, le=365),
    db       : Session = Depends(get_db),
    _pdg     = Depends(exiger_pdg),
):
    return crud.get_evolution_ventes(db, nb_jours)


@router.get("/classement", response_model=list[schemas.StatsBoutique],
            summary="Classement des boutiques par bénéfice")
def classement_boutiques(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutiques = [b for b in crud.get_boutiques(db) if b.est_active]
    return sorted(
        [
            schemas.StatsBoutique(
                boutique       = b,
                nb_articles    = crud.get_nb_articles_boutique(db, b.id),
                nb_vendeurs    = crud.get_vendeurs_de_boutique(db, b.id),
                benefice_total = crud.get_total_profit_boutique(db, b.id),
                ventes_du_mois = crud.get_ventes_du_mois_boutique(db, b.id),
            )
            for b in boutiques
        ],
        key     = lambda s: s.benefice_total,
        reverse = True,
    )
