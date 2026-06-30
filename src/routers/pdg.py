"""
routers/pdg.py — Routes exclusives au PDG

  POST /pdg/boutiques                         → créer une boutique
  GET  /pdg/boutiques                         → lister toutes les boutiques
  PUT  /pdg/boutiques/{id}/archiver           → archiver une boutique
  POST /pdg/boutiques/{id}/ajouter-directeur  → créer le directeur d'une boutique
  POST /pdg/boutiques/{id}/ajouter-vendeur    → créer un vendeur dans une boutique
  GET  /pdg/dashboard                         → tableau de bord entreprise
  GET  /pdg/boutiques/{id}/stats              → stats détaillées d'une boutique
  GET  /pdg/evolution                         → courbe des ventes (30 derniers jours)
  GET  /pdg/classement                        → classement des boutiques par bénéfice
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, exiger_pdg
from .. import crud, schemas

router = APIRouter(prefix="/pdg", tags=["PDG — Direction générale"])


# ============================================================
# BOUTIQUES
# ============================================================

@router.post(
    "/boutiques",
    response_model=schemas.ReponseBoutique,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle boutique",
)
def creer_boutique(
    demande : schemas.DemandeCréerBoutique,
    db      : Session = Depends(get_db),
    _pdg    = Depends(exiger_pdg),
):
    return crud.creer_boutique(db, demande.nom, demande.ville, demande.adresse)


@router.get(
    "/boutiques",
    response_model=list[schemas.ReponseBoutique],
    summary="Lister toutes les boutiques",
)
def lister_boutiques(
    db   : Session = Depends(get_db),
    _pdg = Depends(exiger_pdg),
):
    return crud.get_boutiques(db)


@router.put(
    "/boutiques/{id}/archiver",
    response_model=schemas.ReponseBoutique,
    summary="Archiver une boutique (les données restent intactes)",
)
def archiver_boutique(
    id   : int,
    db   : Session = Depends(get_db),
    _pdg = Depends(exiger_pdg),
):
    boutique = crud.archiver_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return boutique


# ============================================================
# GESTION DES UTILISATEURS PAR BOUTIQUE
# ============================================================

@router.post(
    "/boutiques/{id}/ajouter-directeur",
    response_model=schemas.ReponseUtilisateur,
    status_code=status.HTTP_201_CREATED,
    summary="Assigner un directeur à une boutique",
)
def ajouter_directeur(
    id      : int,
    demande : schemas.DemandeAjouterDirecteur,
    db      : Session = Depends(get_db),
    _pdg    = Depends(exiger_pdg),
):
    """
    Crée un compte directeur et l'associe à la boutique.
    Une boutique ne peut avoir qu'un seul directeur.
    """
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")

    if not boutique.est_active:
        raise HTTPException(status_code=400, detail="Impossible d'assigner un directeur à une boutique archivée")

    # Vérifier que le nom n'est pas déjà pris
    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le nom '{demande.nom_utilisateur}' est déjà utilisé.",
        )

    return crud.creer_utilisateur(
        db              = db,
        nom_utilisateur = demande.nom_utilisateur,
        mot_de_passe    = demande.mot_de_passe,
        role            = "directeur",
        boutique_id     = id,
    )


@router.post(
    "/boutiques/{id}/ajouter-vendeur",
    response_model=schemas.ReponseUtilisateur,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un vendeur à une boutique",
)
def ajouter_vendeur(
    id      : int,
    demande : schemas.DemandeAjouterVendeur,
    db      : Session = Depends(get_db),
    _pdg    = Depends(exiger_pdg),
):
    """Le PDG peut aussi créer des vendeurs directement dans une boutique."""
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")

    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le nom '{demande.nom_utilisateur}' est déjà utilisé.",
        )

    return crud.creer_utilisateur(
        db              = db,
        nom_utilisateur = demande.nom_utilisateur,
        mot_de_passe    = demande.mot_de_passe,
        role            = "vendeur",
        boutique_id     = id,
    )


# ============================================================
# DASHBOARD PDG
# ============================================================

@router.get(
    "/dashboard",
    response_model=schemas.DashboardPDG,
    summary="Tableau de bord complet de l'entreprise",
)
def dashboard(
    db   : Session = Depends(get_db),
    _pdg = Depends(exiger_pdg),
):
    """
    Vue globale : bénéfice total, ventes du mois, alertes stock,
    classement des boutiques et activité récente.
    """
    boutiques       = crud.get_boutiques(db)
    boutiques_actives = [b for b in boutiques if b.est_active]

    # Statistiques par boutique
    classement = []
    for boutique in boutiques_actives:
        stats = schemas.StatsBoutique(
            boutique       = boutique,
            nb_articles    = crud.get_nb_articles_boutique(db, boutique.id),
            nb_vendeurs    = crud.get_vendeurs_de_boutique(db, boutique.id),
            benefice_total = crud.get_total_profit_boutique(db, boutique.id),
            ventes_du_mois = crud.get_ventes_du_mois_boutique(db, boutique.id),
        )
        classement.append(stats)

    # Trier du plus rentable au moins rentable
    classement.sort(key=lambda s: s.benefice_total, reverse=True)

    # Activité récente (tous types de mouvements)
    activite_brute = crud.get_activite_recente(db, limite=10)
    activite = [schemas.MouvementRecent(**m) for m in activite_brute]

    return schemas.DashboardPDG(
        nb_boutiques              = len(boutiques),
        nb_boutiques_actives      = len(boutiques_actives),
        benefice_total_entreprise = crud.get_benefice_total_entreprise(db),
        ventes_totales_du_mois    = crud.get_ventes_totales_du_mois(db),
        articles_en_alerte        = crud.get_nb_articles_en_alerte_total(db),
        classement_boutiques      = classement,
        activite_recente          = activite,
    )


@router.get(
    "/boutiques/{id}/stats",
    response_model=schemas.StatsBoutique,
    summary="Stats détaillées d'une boutique",
)
def stats_boutique(
    id   : int,
    db   : Session = Depends(get_db),
    _pdg = Depends(exiger_pdg),
):
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


@router.get(
    "/evolution",
    response_model=list[schemas.PointEvolution],
    summary="Évolution des ventes sur les 30 derniers jours (toutes boutiques)",
)
def evolution_ventes(
    nb_jours : int = Query(default=30, ge=7, le=365),
    db       : Session = Depends(get_db),
    _pdg     = Depends(exiger_pdg),
):
    """
    Retourne un point par jour : nombre de ventes et bénéfice.
    Utile pour afficher une courbe d'évolution dans le dashboard.
    """
    return crud.get_evolution_ventes(db, nb_jours)


@router.get(
    "/classement",
    response_model=list[schemas.StatsBoutique],
    summary="Classement des boutiques par bénéfice",
)
def classement_boutiques(
    db   : Session = Depends(get_db),
    _pdg = Depends(exiger_pdg),
):
    boutiques = [b for b in crud.get_boutiques(db) if b.est_active]
    stats_liste = [
        schemas.StatsBoutique(
            boutique       = b,
            nb_articles    = crud.get_nb_articles_boutique(db, b.id),
            nb_vendeurs    = crud.get_vendeurs_de_boutique(db, b.id),
            benefice_total = crud.get_total_profit_boutique(db, b.id),
            ventes_du_mois = crud.get_ventes_du_mois_boutique(db, b.id),
        )
        for b in boutiques
    ]
    stats_liste.sort(key=lambda s: s.benefice_total, reverse=True)
    return stats_liste
