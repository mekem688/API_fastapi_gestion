from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from ..dependencies import get_db
from .. import crud, schemas

router = APIRouter(prefix="/articles", tags=["Articles"])


# =========================
# ARTICLES
# =========================

@router.post("/", response_model=schemas.ArticleResponse)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    return crud.create_article(db, article)


@router.get("/", response_model=list[schemas.ArticleResponse])
def get_articles(
    skip:  int = Query(default=0,  ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.get_articles(db, skip=skip, limit=limit)


@router.get("/by-id/{id}", response_model=schemas.ArticleResponse)
def get_article(id: int, db: Session = Depends(get_db)):
    article = crud.get_article(db, id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


# =========================
# STOCK
# =========================

@router.post("/{id}/stock/in")
def stock_in(
    id:       int,
    quantity: int = Query(gt=0, description="Quantité à ajouter (doit être > 0)"),
    db: Session = Depends(get_db),
):
    article = crud.add_stock(db, id, quantity)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return {"message": "Stock ajouté", "data": article}


@router.post("/{id}/stock/out")
def stock_out(
    id:       int,
    quantity: int = Query(gt=0, description="Quantité à retirer (doit être > 0)"),
    db: Session = Depends(get_db),
):
    try:
        result = crud.remove_stock(db, id, quantity)
        if not result:
            raise HTTPException(status_code=404, detail="Article introuvable")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# MOVEMENTS
# =========================

@router.get("/movements", response_model=list[schemas.MovementResponse])
def movements(
    skip:  int = Query(default=0,   ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.get_movements(db, skip=skip, limit=limit)


@router.get("/movements/day", response_model=list[schemas.MovementResponse])
def movements_day(db: Session = Depends(get_db)):
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return crud.get_movements_by_date(db, start)


@router.get("/movements/week", response_model=list[schemas.MovementResponse])
def movements_week(db: Session = Depends(get_db)):
    start = datetime.now(timezone.utc) - timedelta(days=7)
    return crud.get_movements_by_date(db, start)


@router.get("/movements/month", response_model=list[schemas.MovementResponse])
def movements_month(db: Session = Depends(get_db)):
    start = datetime.now(timezone.utc) - timedelta(days=30)
    return crud.get_movements_by_date(db, start)


# =========================
# ALERTS
# =========================

@router.get("/alerts/low-stock", response_model=list[schemas.ArticleResponse])
def low_stock(db: Session = Depends(get_db)):
    return crud.get_low_stock_articles(db)


# =========================
# PROFIT — /profit/total AVANT /{id}/profit pour éviter tout conflit de route
# =========================

@router.get("/profit/total")
def total_profit(db: Session = Depends(get_db)):
    return crud.get_total_profit(db)


@router.get("/{id}/profit")
def article_profit(id: int, db: Session = Depends(get_db)):
    result = crud.get_article_profit(db, id)
    if not result:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return result
