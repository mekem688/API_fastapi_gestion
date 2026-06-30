"""
routers/items.py — Routes de gestion des articles et du stock

Accès par rôle :
  vendeur    → voir articles, faire des ventes, voir les mouvements
  directeur  → tout + créer articles, faire des achats, voir profits et alertes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from ..dependencies import get_db, exiger_vendeur, exiger_directeur
from .. import crud, schemas

router = APIRouter(prefix="/articles", tags=["Articles"])


# ============================================================
# ARTICLES
# ============================================================

@router.post(
    "/",
    response_model=schemas.ArticleResponse,
    status_code=201,
    summary="Créer un article — directeur uniquement",
)
def create_article(
    article     : schemas.ArticleCreate,
    db          : Session = Depends(get_db),
    _directeur  = Depends(exiger_directeur),    # réservé au directeur
):
    return crud.create_article(db, article)


@router.get(
    "/",
    response_model=list[schemas.ArticleResponse],
    summary="Lister les articles — vendeur et directeur",
)
def get_articles(
    skip        : int = Query(default=0,  ge=0),
    limit       : int = Query(default=50, ge=1, le=200),
    db          : Session = Depends(get_db),
    _utilisateur = Depends(exiger_vendeur),     # vendeur et directeur autorisés
):
    return crud.get_articles(db, skip=skip, limit=limit)


@router.get(
    "/by-id/{id}",
    response_model=schemas.ArticleResponse,
    summary="Voir un article — vendeur et directeur",
)
def get_article(
    id          : int,
    db          : Session = Depends(get_db),
    _utilisateur = Depends(exiger_vendeur),
):
    article = crud.get_article(db, id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


# ============================================================
# STOCK
# ============================================================

@router.post(
    "/{id}/stock/in",
    summary="Entrée de stock (achat) — directeur uniquement",
)
def stock_in(
    id          : int,
    quantite    : int = Query(gt=0, description="Quantité à ajouter (doit être > 0)"),
    db          : Session = Depends(get_db),
    _directeur  = Depends(exiger_directeur),    # réservé au directeur
):
    article = crud.add_stock(db, id, quantite)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return {"message": f"{quantite} unités ajoutées au stock", "article": article}


@router.post(
    "/{id}/stock/out",
    summary="Sortie de stock (vente) — vendeur et directeur",
)
def stock_out(
    id          : int,
    quantite    : int = Query(gt=0, description="Quantité à vendre (doit être > 0)"),
    db          : Session = Depends(get_db),
    _utilisateur = Depends(exiger_vendeur),     # vendeur et directeur autorisés
):
    try:
        resultat = crud.remove_stock(db, id, quantite)
        if not resultat:
            raise HTTPException(status_code=404, detail="Article introuvable")
        return resultat
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))


# ============================================================
# MOUVEMENTS DE STOCK
# ============================================================

@router.get(
    "/movements",
    response_model=list[schemas.MovementResponse],
    summary="Tous les mouvements — vendeur et directeur",
)
def movements(
    skip        : int = Query(default=0,   ge=0),
    limit       : int = Query(default=100, ge=1, le=500),
    db          : Session = Depends(get_db),
    _utilisateur = Depends(exiger_vendeur),
):
    return crud.get_movements(db, skip=skip, limit=limit)


@router.get(
    "/movements/day",
    response_model=list[schemas.MovementResponse],
    summary="Mouvements du jour — vendeur et directeur",
)
def movements_day(
    db          : Session = Depends(get_db),
    _utilisateur = Depends(exiger_vendeur),
):
    debut_du_jour = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return crud.get_movements_by_date(db, debut_du_jour)


@router.get(
    "/movements/week",
    response_model=list[schemas.MovementResponse],
    summary="Mouvements de la semaine — vendeur et directeur",
)
def movements_week(
    db          : Session = Depends(get_db),
    _utilisateur = Depends(exiger_vendeur),
):
    il_y_a_7_jours = datetime.now(timezone.utc) - timedelta(days=7)
    return crud.get_movements_by_date(db, il_y_a_7_jours)


@router.get(
    "/movements/month",
    response_model=list[schemas.MovementResponse],
    summary="Mouvements du mois — vendeur et directeur",
)
def movements_month(
    db          : Session = Depends(get_db),
    _utilisateur = Depends(exiger_vendeur),
):
    il_y_a_30_jours = datetime.now(timezone.utc) - timedelta(days=30)
    return crud.get_movements_by_date(db, il_y_a_30_jours)


# ============================================================
# ALERTES — directeur uniquement
# ============================================================

@router.get(
    "/alerts/low-stock",
    response_model=list[schemas.ArticleResponse],
    summary="Articles en stock faible — directeur uniquement",
)
def low_stock(
    db          : Session = Depends(get_db),
    _directeur  = Depends(exiger_directeur),
):
    return crud.get_low_stock_articles(db)


# ============================================================
# PROFITS — directeur uniquement
# IMPORTANT : /profit/total DOIT être défini AVANT /{id}/profit
# pour éviter que FastAPI confonde "total" avec un identifiant entier
# ============================================================

@router.get(
    "/profit/total",
    summary="Bénéfice total sur tous les articles — directeur uniquement",
)
def total_profit(
    db          : Session = Depends(get_db),
    _directeur  = Depends(exiger_directeur),
):
    return crud.get_total_profit(db)


@router.get(
    "/{id}/profit",
    summary="Bénéfice d'un article — directeur uniquement",
)
def article_profit(
    id          : int,
    db          : Session = Depends(get_db),
    _directeur  = Depends(exiger_directeur),
):
    resultat = crud.get_article_profit(db, id)
    if not resultat:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return resultat
