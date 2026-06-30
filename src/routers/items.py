"""
routers/items.py — Gestion des articles et du stock

Toutes les données sont automatiquement filtrées
par la boutique de l'utilisateur connecté (boutique_id).

  vendeur    → voir articles, vendre, voir mouvements
  directeur  → tout + achats, profits, alertes, créer articles
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from ..dependencies import get_db, exiger_vendeur, exiger_directeur
from .. import crud, schemas

router = APIRouter(prefix="/articles", tags=["Articles"])


def _boutique_id(utilisateur) -> int:
    """
    Retourne le boutique_id de l'utilisateur.
    Le PDG n'a pas de boutique_id — il passe par les routes /pdg/.
    """
    if utilisateur.boutique_id is None:
        raise HTTPException(
            status_code=403,
            detail="Le PDG utilise les routes /pdg/ pour accéder aux données.",
        )
    return utilisateur.boutique_id


# ============================================================
# ARTICLES
# ============================================================

@router.post("/", response_model=schemas.ArticleResponse, status_code=201,
             summary="Créer un article — directeur")
def create_article(
    article    : schemas.ArticleCreate,
    db         : Session = Depends(get_db),
    directeur  = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    return crud.create_article(db, article, boutique_id)


@router.get("/", response_model=list[schemas.ArticleResponse],
            summary="Lister les articles — vendeur et directeur")
def get_articles(
    skip        : int = Query(default=0,  ge=0),
    limit       : int = Query(default=50, ge=1, le=200),
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_articles(db, boutique_id, skip=skip, limit=limit)


@router.get("/by-id/{id}", response_model=schemas.ArticleResponse,
            summary="Voir un article — vendeur et directeur")
def get_article(
    id          : int,
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    boutique_id = _boutique_id(utilisateur)
    article = crud.get_article(db, id, boutique_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


# ============================================================
# STOCK
# ============================================================

@router.post("/{id}/stock/in", summary="Entrée de stock (achat) — directeur")
def stock_in(
    id         : int,
    quantite   : int = Query(gt=0),
    db         : Session = Depends(get_db),
    directeur  = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    article = crud.add_stock(db, id, quantite, boutique_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return {"message": f"{quantite} unités ajoutées", "article": article}


@router.post("/{id}/stock/out", summary="Sortie de stock (vente) — vendeur et directeur")
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
        return resultat
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))


# ============================================================
# MOUVEMENTS
# ============================================================

@router.get("/movements", response_model=list[schemas.MovementResponse],
            summary="Tous les mouvements — vendeur et directeur")
def movements(
    skip        : int = Query(default=0,   ge=0),
    limit       : int = Query(default=100, ge=1, le=500),
    db          : Session = Depends(get_db),
    utilisateur = Depends(exiger_vendeur),
):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_movements(db, boutique_id, skip=skip, limit=limit)


@router.get("/movements/day", response_model=list[schemas.MovementResponse],
            summary="Mouvements du jour")
def movements_day(db: Session = Depends(get_db), utilisateur=Depends(exiger_vendeur)):
    boutique_id  = _boutique_id(utilisateur)
    debut_du_jour = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return crud.get_movements_by_date(db, boutique_id, debut_du_jour)


@router.get("/movements/week", response_model=list[schemas.MovementResponse],
            summary="Mouvements de la semaine")
def movements_week(db: Session = Depends(get_db), utilisateur=Depends(exiger_vendeur)):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_movements_by_date(db, boutique_id, datetime.now(timezone.utc) - timedelta(days=7))


@router.get("/movements/month", response_model=list[schemas.MovementResponse],
            summary="Mouvements du mois")
def movements_month(db: Session = Depends(get_db), utilisateur=Depends(exiger_vendeur)):
    boutique_id = _boutique_id(utilisateur)
    return crud.get_movements_by_date(db, boutique_id, datetime.now(timezone.utc) - timedelta(days=30))


# ============================================================
# ALERTES ET PROFITS — directeur uniquement
# IMPORTANT : /profit/total AVANT /{id}/profit
# ============================================================

@router.get("/alerts/low-stock", response_model=list[schemas.ArticleResponse],
            summary="Stock faible — directeur")
def low_stock(db: Session = Depends(get_db), directeur=Depends(exiger_directeur)):
    boutique_id = _boutique_id(directeur)
    return crud.get_articles_en_alerte_boutique(db, boutique_id)


@router.get("/profit/total", summary="Bénéfice total de la boutique — directeur")
def total_profit(db: Session = Depends(get_db), directeur=Depends(exiger_directeur)):
    boutique_id = _boutique_id(directeur)
    benefice    = crud.get_total_profit_boutique(db, boutique_id)
    return {"benefice_total": benefice}


@router.get("/{id}/profit", summary="Bénéfice d'un article — directeur")
def article_profit(
    id         : int,
    db         : Session = Depends(get_db),
    directeur  = Depends(exiger_directeur),
):
    boutique_id = _boutique_id(directeur)
    resultat    = crud.get_article_profit(db, id, boutique_id)
    if not resultat:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return resultat
