"""
routers/credits.py — Gestion des crédits ventes et achats

Accessible au directeur (sans permission granulaire supplémentaire).
Le PDG voit tout via /pdg/credits/*.

VENTES À CRÉDIT (argent que les clients doivent) :
  POST /credits/ventes                    → enregistrer une vente à crédit
  GET  /credits/ventes                    → lister (filtre optionnel par statut)
  GET  /credits/ventes/{id}               → détail d'une vente
  POST /credits/ventes/{id}/paiement      → enregistrer un versement reçu
  GET  /credits/ventes/{id}/paiements     → historique des versements

ACHATS À CRÉDIT (argent que la boutique doit) :
  POST /credits/achats                    → enregistrer un achat à crédit
  GET  /credits/achats                    → lister
  GET  /credits/achats/{id}               → détail
  POST /credits/achats/{id}/paiement      → enregistrer un versement effectué
  GET  /credits/achats/{id}/paiements     → historique des versements

RÉSUMÉ :
  GET  /credits/resume                    → solde global de la boutique
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, exiger_directeur, exiger_vendeur
from ..models import PaiementRecu, PaiementEffectue
from .. import crud, schemas

router = APIRouter(prefix="/credits", tags=["Crédits"])


def _boutique_id(directeur) -> int:
    if directeur.boutique_id is None:
        raise HTTPException(status_code=403,
                            detail="Le PDG utilise /pdg/credits/ pour accéder aux crédits.")
    return directeur.boutique_id


# ================================================================
# VENTES À CRÉDIT
# ================================================================

@router.post(
    "/ventes",
    response_model=schemas.ReponseVenteCredit,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer une vente à crédit — directeur",
)
def creer_vente_credit(
    data      : schemas.DemandeVenteCredit,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    """
    Enregistre une marchandise vendue sans paiement immédiat.
    Informations client obligatoires : nom, téléphone, montant, date d'échéance.
    """
    boutique_id = _boutique_id(directeur)
    boutique    = crud.get_boutique(db, boutique_id)

    vente = crud.creer_vente_credit(db, directeur, data)

    crud.journaliser(db, directeur, boutique.nom if boutique else None, "vente_credit", {
        "client_nom"      : data.client_nom,
        "client_telephone": data.client_telephone,
        "montant_total"   : data.montant_total,
        "date_echeance"   : data.date_echeance.isoformat(),
    })

    return vente


@router.get(
    "/ventes",
    response_model=list[schemas.ReponseVenteCredit],
    summary="Lister les ventes à crédit de la boutique",
)
def lister_ventes_credit(
    statut    : str | None = Query(default=None,
                                   description="Filtrer : en_cours | partiellement_paye | en_retard | solde"),
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    return crud.get_ventes_credit(db, boutique_id, statut)


@router.get(
    "/ventes/{id}",
    response_model=schemas.ReponseVenteCredit,
    summary="Détail d'une vente à crédit",
)
def detail_vente_credit(
    id        : int,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    vente = crud.get_vente_credit(db, id, boutique_id)
    if not vente:
        raise HTTPException(status_code=404, detail="Vente à crédit introuvable")
    return vente


@router.post(
    "/ventes/{id}/paiement",
    response_model=schemas.ReponsePaiementRecu,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un versement reçu d'un client",
)
def paiement_recu(
    id        : int,
    data      : schemas.DemandePaiementRecu,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    """
    Enregistre un paiement partiel ou total du client.
    Le statut (partiellement_paye / solde / en_retard) est mis à jour automatiquement.
    """
    boutique    = crud.get_boutique(db, _boutique_id(directeur))
    vente       = crud.get_vente_credit(db, id, directeur.boutique_id)
    if not vente:
        raise HTTPException(status_code=404, detail="Vente à crédit introuvable")
    if vente.statut == "solde":
        raise HTTPException(status_code=400, detail="Cette vente est déjà soldée.")

    paiement = crud.enregistrer_paiement_recu(db, id, directeur, data.montant_verse, data.note)

    crud.journaliser(db, directeur, boutique.nom if boutique else None, "paiement_recu", {
        "vente_credit_id" : id,
        "client_nom"      : vente.client_nom,
        "client_telephone": vente.client_telephone,
        "montant_verse"   : data.montant_verse,
    })

    return paiement


@router.get(
    "/ventes/{id}/paiements",
    response_model=list[schemas.ReponsePaiementRecu],
    summary="Historique des versements reçus pour une vente à crédit",
)
def historique_paiements_recu(
    id        : int,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    _boutique_id(directeur)
    return (
        db.query(PaiementRecu)
        .filter(PaiementRecu.vente_credit_id == id)
        .order_by(PaiementRecu.date_paiement.desc())
        .all()
    )


# ================================================================
# ACHATS À CRÉDIT
# ================================================================

@router.post(
    "/achats",
    response_model=schemas.ReponseAchatCredit,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un achat à crédit chez un fournisseur — directeur",
)
def creer_achat_credit(
    data      : schemas.DemandeAchatCredit,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    boutique    = crud.get_boutique(db, boutique_id)

    achat = crud.creer_achat_credit(db, directeur, data)

    crud.journaliser(db, directeur, boutique.nom if boutique else None, "achat_credit", {
        "fournisseur_nom"      : data.fournisseur_nom,
        "fournisseur_telephone": data.fournisseur_telephone,
        "montant_total"        : data.montant_total,
        "date_echeance"        : data.date_echeance.isoformat(),
    })

    return achat


@router.get(
    "/achats",
    response_model=list[schemas.ReponseAchatCredit],
    summary="Lister les achats à crédit de la boutique",
)
def lister_achats_credit(
    statut    : str | None = Query(default=None),
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    return crud.get_achats_credit(db, boutique_id, statut)


@router.get(
    "/achats/{id}",
    response_model=schemas.ReponseAchatCredit,
    summary="Détail d'un achat à crédit",
)
def detail_achat_credit(
    id        : int,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    achat = crud.get_achat_credit(db, id, boutique_id)
    if not achat:
        raise HTTPException(status_code=404, detail="Achat à crédit introuvable")
    return achat


@router.post(
    "/achats/{id}/paiement",
    response_model=schemas.ReponsePaiementEffectue,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un versement effectué au fournisseur",
)
def paiement_effectue(
    id        : int,
    data      : schemas.DemandePaiementEffectue,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique = crud.get_boutique(db, _boutique_id(directeur))
    achat    = crud.get_achat_credit(db, id, directeur.boutique_id)
    if not achat:
        raise HTTPException(status_code=404, detail="Achat à crédit introuvable")
    if achat.statut == "solde":
        raise HTTPException(status_code=400, detail="Cet achat est déjà soldé.")

    paiement = crud.enregistrer_paiement_effectue(db, id, directeur, data.montant_verse, data.note)

    crud.journaliser(db, directeur, boutique.nom if boutique else None, "paiement_effectue", {
        "achat_credit_id"      : id,
        "fournisseur_nom"      : achat.fournisseur_nom,
        "fournisseur_telephone": achat.fournisseur_telephone,
        "montant_verse"        : data.montant_verse,
    })

    return paiement


@router.get(
    "/achats/{id}/paiements",
    response_model=list[schemas.ReponsePaiementEffectue],
    summary="Historique des versements effectués pour un achat à crédit",
)
def historique_paiements_effectue(
    id        : int,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    _boutique_id(directeur)
    return (
        db.query(PaiementEffectue)
        .filter(PaiementEffectue.achat_credit_id == id)
        .order_by(PaiementEffectue.date_paiement.desc())
        .all()
    )


# ================================================================
# RÉSUMÉ
# ================================================================

@router.get(
    "/resume",
    response_model=schemas.ResumeCredits,
    summary="Résumé financier des crédits de la boutique",
)
def resume_credits(
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    return crud.get_resume_credits_boutique(db, boutique_id)


# ================================================================
# JOURNAL DE LA BOUTIQUE
# ================================================================

@router.get(
    "/journal",
    response_model=list[schemas.EntreeJournal],
    summary="Journal d'activité de la boutique",
)
def journal_boutique(
    limite    : int = Query(default=100, ge=1, le=500),
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    """
    Retourne toutes les actions tracées dans la boutique du directeur :
    connexions, ventes, achats, crédits, paiements, créations de compte, etc.
    """
    boutique_id = _boutique_id(directeur)
    return crud.get_journal(db, boutique_id=boutique_id, limite=limite)


# ================================================================
# CONFIGURATION DE LA FACTURE — en-tête personnalisable par le DG
# ================================================================

@router.get(
    "/config-facture",
    response_model=schemas.ReponseConfigFacture,
    summary="Lire la configuration de facture de sa boutique",
)
def lire_config_facture(
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    config = crud.get_config_facture(db, boutique_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail="Aucune configuration de facture définie pour cette boutique. Utilisez PUT pour la créer.",
        )
    return config


@router.put(
    "/config-facture",
    response_model=schemas.ReponseConfigFacture,
    summary="Créer ou modifier l'en-tête de facture de sa boutique",
)
def modifier_config_facture(
    data      : schemas.DemandeConfigFacture,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    """
    Le DG personnalise l'en-tête imprimé sur chaque facture de sa boutique :
    nom, slogan, téléphone, adresse, email, pied de page.
    """
    boutique_id = _boutique_id(directeur)
    boutique    = crud.get_boutique(db, boutique_id)
    config      = crud.enregistrer_config_facture(db, boutique_id, data)

    crud.journaliser(db, directeur, boutique.nom if boutique else None, "config_facture_modifiee", {
        "nom_boutique": data.nom_boutique,
    })

    return config


@router.get(
    "/config-facture/impression",
    response_model=schemas.ReponseConfigFacture,
    summary="Lire l'en-tête de facture pour l'impression — accessible au vendeur",
)
def config_facture_pour_impression(
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    """
    Route utilisée par l'application de bureau (vendeur) au moment d'imprimer
    une facture. Si aucune configuration n'a été définie par le DG, retourne
    des valeurs par défaut plutôt qu'une erreur (pour ne jamais bloquer la vente).
    """
    boutique_id = _boutique_id(utilisateur)
    config      = crud.get_config_facture(db, boutique_id)
    if config:
        return config

    boutique = crud.get_boutique(db, boutique_id)
    return schemas.ReponseConfigFacture(
        id           = 0,
        boutique_id  = boutique_id,
        nom_boutique = boutique.nom if boutique else "Boutique",
        slogan       = None,
        telephone    = None,
        adresse      = boutique.adresse if boutique else None,
        email        = None,
        pied_de_page = "Merci pour votre confiance !",
    )
