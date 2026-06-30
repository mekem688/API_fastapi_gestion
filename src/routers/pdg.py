"""
routers/pdg.py — Routes exclusives au PDG

Boutiques, équipes, permissions, dashboard, crédits entreprise, journal global.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, exiger_pdg
from ..permissions import TOUTES_LES_PERMISSIONS
from ..models import VenteCredit, AchatCredit
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
    pdg     = Depends(exiger_pdg),
):
    boutique = crud.creer_boutique(db, demande.nom, demande.ville, demande.adresse)
    crud.journaliser(db, pdg, None, "creation_boutique", {"boutique_nom": boutique.nom})
    return boutique


@router.get("/boutiques", response_model=list[schemas.ReponseBoutique])
def lister_boutiques(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    return crud.get_boutiques(db)


@router.put("/boutiques/{id}/archiver", response_model=schemas.ReponseBoutique)
def archiver_boutique(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutique = crud.archiver_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return boutique


# ============================================================
# ÉQUIPES
# ============================================================

@router.post("/boutiques/{id}/ajouter-directeur",
             response_model=schemas.ReponseUtilisateur,
             status_code=status.HTTP_201_CREATED)
def ajouter_directeur(
    id      : int,
    demande : schemas.DemandeAjouterDirecteur,
    db      : Session = Depends(get_db),
    pdg     = Depends(exiger_pdg),
):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    if not boutique.est_active:
        raise HTTPException(status_code=400, detail="Boutique archivée")
    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=409, detail="Nom déjà utilisé")

    directeur = crud.creer_utilisateur(
        db=db,
        nom_utilisateur     = demande.nom_utilisateur,
        mot_de_passe        = demande.mot_de_passe,
        role                = "directeur",
        prenom              = demande.prenom,
        nom_famille         = demande.nom_famille,
        telephone           = demande.telephone,
        adresse_personnelle = demande.adresse_personnelle,
        boutique_id         = id,
    )
    crud.journaliser(db, pdg, boutique.nom, "creation_directeur", {
        "directeur_id"    : directeur.id,
        "directeur_nom"   : f"{directeur.prenom} {directeur.nom_famille}",
        "directeur_tel"   : directeur.telephone,
        "boutique_id"     : id,
    })
    return directeur


@router.post("/boutiques/{id}/ajouter-vendeur",
             response_model=schemas.ReponseUtilisateur,
             status_code=status.HTTP_201_CREATED)
def ajouter_vendeur(
    id      : int,
    demande : schemas.DemandeAjouterVendeur,
    db      : Session = Depends(get_db),
    pdg     = Depends(exiger_pdg),
):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    if crud.get_utilisateur_par_nom(db, demande.nom_utilisateur):
        raise HTTPException(status_code=409, detail="Nom déjà utilisé")

    vendeur = crud.creer_utilisateur(
        db=db,
        nom_utilisateur     = demande.nom_utilisateur,
        mot_de_passe        = demande.mot_de_passe,
        role                = "vendeur",
        prenom              = demande.prenom,
        nom_famille         = demande.nom_famille,
        telephone           = demande.telephone,
        adresse_personnelle = demande.adresse_personnelle,
        boutique_id         = id,
    )
    crud.journaliser(db, pdg, boutique.nom, "creation_vendeur", {
        "vendeur_id"  : vendeur.id,
        "vendeur_nom" : f"{vendeur.prenom} {vendeur.nom_famille}",
        "vendeur_tel" : vendeur.telephone,
    })
    return vendeur


@router.get("/boutiques/{id}/equipe", response_model=list[schemas.ReponseUtilisateur],
            summary="Voir tous les membres d'une boutique (noms, téléphones, rôles)")
def voir_equipe(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return crud.get_utilisateurs_de_boutique(db, id)


# ============================================================
# PERMISSIONS DES DIRECTEURS
# ============================================================

@router.get("/directeurs/{id}/permissions", response_model=schemas.ReponsePermissions)
def voir_permissions(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
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


@router.put("/directeurs/{id}/permissions", response_model=schemas.ReponsePermissions)
def modifier_permissions(
    id      : int,
    demande : schemas.DemandeModifierPermissions,
    db      : Session = Depends(get_db),
    pdg     = Depends(exiger_pdg),
):
    directeur = crud.modifier_permissions(db, id, demande.permissions)
    if not directeur:
        raise HTTPException(status_code=404, detail="Directeur introuvable")
    crud.journaliser(db, pdg, None, "modification_permissions", {
        "directeur_id"       : id,
        "permissions_accordees": demande.permissions,
    })
    permissions_manquantes = [p for p in TOUTES_LES_PERMISSIONS if p not in (directeur.permissions or [])]
    return schemas.ReponsePermissions(
        directeur_id           = directeur.id,
        nom_utilisateur        = directeur.nom_utilisateur,
        boutique_id            = directeur.boutique_id,
        est_actif              = directeur.est_actif,
        permissions            = directeur.permissions or [],
        permissions_manquantes = permissions_manquantes,
    )


@router.put("/directeurs/{id}/suspendre", response_model=schemas.ReponseUtilisateur)
def suspendre(id: int, db: Session = Depends(get_db), pdg=Depends(exiger_pdg)):
    u = crud.suspendre_utilisateur(db, id)
    if not u:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    crud.journaliser(db, pdg, None, "suspension_compte", {
        "utilisateur_id" : id, "nom_complet": f"{u.prenom} {u.nom_famille}",
    })
    return u


@router.put("/directeurs/{id}/reactiver", response_model=schemas.ReponseUtilisateur)
def reactiver(id: int, db: Session = Depends(get_db), pdg=Depends(exiger_pdg)):
    u = crud.reactiver_utilisateur(db, id)
    if not u:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    crud.journaliser(db, pdg, None, "reactivation_compte", {
        "utilisateur_id" : id, "nom_complet": f"{u.prenom} {u.nom_famille}",
    })
    return u


# ============================================================
# CRÉDITS — vue PDG (toutes boutiques)
# ============================================================

@router.get("/credits", summary="Vue globale des crédits de toutes les boutiques")
def credits_entreprise(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    """
    Retourne pour chaque boutique active :
    - les ventes à crédit non soldées (clients qui doivent)
    - les achats à crédit non soldés (fournisseurs à payer)
    """
    boutiques = [b for b in crud.get_boutiques(db) if b.est_active]
    return [
        {
            "boutique": b,
            **crud.get_resume_credits_boutique(db, b.id),
        }
        for b in boutiques
    ]


@router.get("/credits/en-retard", summary="Tous les crédits en retard (PDG)")
def credits_en_retard(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    """Crédits dont la date d'échéance est dépassée et qui ne sont pas soldés."""
    ventes_retard = db.query(VenteCredit).filter(
        VenteCredit.statut == "en_retard"
    ).order_by(VenteCredit.date_echeance.asc()).all()

    achats_retard = db.query(AchatCredit).filter(
        AchatCredit.statut == "en_retard"
    ).order_by(AchatCredit.date_echeance.asc()).all()

    return {
        "ventes_en_retard": ventes_retard,
        "achats_en_retard": achats_retard,
        "total_en_retard" : len(ventes_retard) + len(achats_retard),
    }


@router.get("/boutiques/{id}/credits", summary="Crédits détaillés d'une boutique (PDG)")
def credits_boutique(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return {
        "boutique"      : boutique,
        "resume"        : crud.get_resume_credits_boutique(db, id),
        "ventes_credit" : crud.get_ventes_credit(db, id),
        "achats_credit" : crud.get_achats_credit(db, id),
    }


# ============================================================
# JOURNAL — vue PDG (toutes boutiques)
# ============================================================

@router.get("/journal", response_model=list[schemas.EntreeJournal],
            summary="Journal d'activité global de toute l'entreprise")
def journal_global(
    limite : int = Query(default=200, ge=1, le=1000),
    db     : Session = Depends(get_db),
    _pdg   = Depends(exiger_pdg),
):
    """
    Retourne toutes les actions de toutes les boutiques, les plus récentes en premier.
    Chaque entrée contient : qui a fait quoi, dans quelle boutique, à quelle heure.
    """
    return crud.get_journal(db, boutique_id=None, limite=limite)


@router.get("/boutiques/{id}/journal", response_model=list[schemas.EntreeJournal],
            summary="Journal d'une boutique spécifique (PDG)")
def journal_boutique(
    id     : int,
    limite : int = Query(default=100, ge=1, le=500),
    db     : Session = Depends(get_db),
    _pdg   = Depends(exiger_pdg),
):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return crud.get_journal(db, boutique_id=id, limite=limite)


# ============================================================
# DASHBOARD PDG
# ============================================================

@router.get("/dashboard", response_model=schemas.DashboardPDG)
def dashboard(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutiques         = crud.get_boutiques(db)
    boutiques_actives = [b for b in boutiques if b.est_active]

    total_a_encaisser = crud.get_total_a_encaisser_entreprise(db)
    total_a_payer     = crud.get_total_a_payer_entreprise(db)

    classement = sorted(
        [
            schemas.StatsBoutique(
                boutique          = b,
                nb_articles       = crud.get_nb_articles_boutique(db, b.id),
                nb_vendeurs       = crud.get_vendeurs_de_boutique(db, b.id),
                benefice_total    = crud.get_total_profit_boutique(db, b.id),
                ventes_du_mois    = crud.get_ventes_du_mois_boutique(db, b.id),
                total_a_encaisser = crud.get_resume_credits_boutique(db, b.id)["total_a_encaisser"],
                total_a_payer     = crud.get_resume_credits_boutique(db, b.id)["total_a_payer"],
            )
            for b in boutiques_actives
        ],
        key=lambda s: s.benefice_total, reverse=True,
    )

    activite = [schemas.MouvementRecent(**m) for m in crud.get_activite_recente(db, limite=10)]

    return schemas.DashboardPDG(
        nb_boutiques                = len(boutiques),
        nb_boutiques_actives        = len(boutiques_actives),
        benefice_total_entreprise   = crud.get_benefice_total_entreprise(db),
        ventes_totales_du_mois      = crud.get_ventes_totales_du_mois(db),
        articles_en_alerte          = crud.get_nb_articles_en_alerte_total(db),
        total_a_encaisser_entreprise= total_a_encaisser,
        total_a_payer_entreprise    = total_a_payer,
        solde_net_credit_entreprise = round(total_a_encaisser - total_a_payer, 2),
        credits_en_retard           = crud.get_nb_credits_en_retard(db),
        classement_boutiques        = classement,
        activite_recente            = activite,
    )


@router.get("/boutiques/{id}/stats", response_model=schemas.StatsBoutique)
def stats_boutique(id: int, db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutique = crud.get_boutique(db, id)
    if not boutique:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    resume = crud.get_resume_credits_boutique(db, id)
    return schemas.StatsBoutique(
        boutique          = boutique,
        nb_articles       = crud.get_nb_articles_boutique(db, id),
        nb_vendeurs       = crud.get_vendeurs_de_boutique(db, id),
        benefice_total    = crud.get_total_profit_boutique(db, id),
        ventes_du_mois    = crud.get_ventes_du_mois_boutique(db, id),
        total_a_encaisser = resume["total_a_encaisser"],
        total_a_payer     = resume["total_a_payer"],
    )


@router.get("/evolution", response_model=list[schemas.PointEvolution])
def evolution_ventes(
    nb_jours : int = Query(default=30, ge=7, le=365),
    db       : Session = Depends(get_db),
    _pdg     = Depends(exiger_pdg),
):
    return crud.get_evolution_ventes(db, nb_jours)


@router.get("/classement", response_model=list[schemas.StatsBoutique])
def classement_boutiques(db: Session = Depends(get_db), _pdg=Depends(exiger_pdg)):
    boutiques = [b for b in crud.get_boutiques(db) if b.est_active]
    return sorted(
        [
            schemas.StatsBoutique(
                boutique          = b,
                nb_articles       = crud.get_nb_articles_boutique(db, b.id),
                nb_vendeurs       = crud.get_vendeurs_de_boutique(db, b.id),
                benefice_total    = crud.get_total_profit_boutique(db, b.id),
                ventes_du_mois    = crud.get_ventes_du_mois_boutique(db, b.id),
                total_a_encaisser = crud.get_resume_credits_boutique(db, b.id)["total_a_encaisser"],
                total_a_payer     = crud.get_resume_credits_boutique(db, b.id)["total_a_payer"],
            )
            for b in boutiques
        ],
        key=lambda s: s.benefice_total, reverse=True,
    )
