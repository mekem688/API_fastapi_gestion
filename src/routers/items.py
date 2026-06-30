"""
routers/items.py — Gestion des articles et du stock

Chaque action est automatiquement journalisée.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from ..dependencies import get_db, exiger_vendeur, exiger_directeur
from ..permissions import verifier_permission
from .. import crud, schemas

router = APIRouter(prefix="/articles", tags=["Articles"])


def _boutique_id(utilisateur) -> int:
    if utilisateur.boutique_id is None:
        raise HTTPException(status_code=403,
                            detail="Le PDG utilise les routes /pdg/ pour accéder aux données.")
    return utilisateur.boutique_id


# ============================================================
# ARTICLES
# ============================================================

@router.post("/", response_model=schemas.ArticleResponse, status_code=201)
def create_article(
    article   : schemas.ArticleCreate,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    verifier_permission(directeur, "creer_articles")
    boutique_id = _boutique_id(directeur)
    nouvel      = crud.create_article(db, article, boutique_id)
    boutique    = crud.get_boutique(db, boutique_id)
    crud.journaliser(db, directeur, boutique.nom if boutique else None, "creation_article", {
        "article_id": nouvel.id, "article_nom": nouvel.name,
    })
    return nouvel


@router.get("/", response_model=list[schemas.ArticleResponse])
def get_articles(
    skip        : int = Query(default=0, ge=0),
    limit       : int = Query(default=50, ge=1, le=200),
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_articles(db, boutique_id, skip=skip, limit=limit)


@router.get("/by-id/{id}", response_model=schemas.ArticleResponse)
def get_article(
    id          : int,
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    boutique_id = _boutique_id(utilisateur)
    article     = crud.get_article(db, id, boutique_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


# ============================================================
# STOCK
# ============================================================

@router.post("/{id}/stock/in")
def stock_in(
    id        : int,
    quantite  : int = Query(gt=0),
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    verifier_permission(directeur, "faire_achats")
    boutique_id = _boutique_id(directeur)
    article     = crud.add_stock(db, id, quantite, boutique_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    boutique = crud.get_boutique(db, boutique_id)
    crud.journaliser(db, directeur, boutique.nom if boutique else None, "achat_stock", {
        "article_id": id, "article_nom": article.name, "quantite": quantite,
    })
    return {"message": f"{quantite} unités ajoutées", "article": article}


@router.post("/{id}/stock/out")
def stock_out(
    id          : int,
    quantite    : int = Query(gt=0),
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    boutique_id = _boutique_id(utilisateur)
    try:
        resultat = crud.remove_stock(db, id, quantite, boutique_id)
        if not resultat:
            raise HTTPException(status_code=404, detail="Article introuvable")
        boutique = crud.get_boutique(db, boutique_id)
        crud.journaliser(db, utilisateur, boutique.nom if boutique else None, "vente_article", {
            "article_id" : id,
            "article_nom": resultat["article"].name,
            "quantite"   : quantite,
            "benefice"   : resultat["benefice_de_la_vente"],
        })
        return resultat
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))


# ============================================================
# MOUVEMENTS
# ============================================================

@router.get("/movements", response_model=list[schemas.MovementResponse])
def movements(
    skip        : int = Query(default=0, ge=0),
    limit       : int = Query(default=100, ge=1, le=500),
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_movements(db, boutique_id, skip=skip, limit=limit)


@router.get("/movements/day", response_model=list[schemas.MovementResponse])
def movements_day(db: Session = Depends(get_db), utilisateur=Depends(exiger_vendeur)):
    boutique_id   = _boutique_id(utilisateur)
    debut_du_jour = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return crud.get_movements_by_date(db, boutique_id, debut_du_jour)


@router.get("/movements/week", response_model=list[schemas.MovementResponse])
def movements_week(db: Session = Depends(get_db), utilisateur=Depends(exiger_vendeur)):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_movements_by_date(db, boutique_id, datetime.now(timezone.utc) - timedelta(days=7))


@router.get("/movements/month", response_model=list[schemas.MovementResponse])
def movements_month(db: Session = Depends(get_db), utilisateur=Depends(exiger_vendeur)):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_movements_by_date(db, boutique_id, datetime.now(timezone.utc) - timedelta(days=30))


# ============================================================
# ALERTES ET PROFITS
# ============================================================

@router.get("/alerts/low-stock", response_model=list[schemas.ArticleResponse])
def low_stock(db: Session = Depends(get_db), directeur=Depends(exiger_directeur)):
    verifier_permission(directeur, "voir_alertes")
    boutique_id = _boutique_id(directeur)
    return crud.get_articles_en_alerte_boutique(db, boutique_id)


@router.get("/profit/total")
def total_profit(db: Session = Depends(get_db), directeur=Depends(exiger_directeur)):
    verifier_permission(directeur, "voir_profits")
    boutique_id = _boutique_id(directeur)
    return {"benefice_total": crud.get_total_profit_boutique(db, boutique_id)}


@router.get("/{id}/profit")
def article_profit(
    id        : int,
    db        : Session = Depends(get_db),
    directeur = Depends(exiger_directeur),
):
    verifier_permission(directeur, "voir_profits")
    boutique_id = _boutique_id(directeur)
    resultat    = crud.get_article_profit(db, id, boutique_id)
    if not resultat:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return resultat
