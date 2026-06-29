from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

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
def get_articles(db: Session = Depends(get_db)):
    return crud.get_articles(db)


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
def stock_in(id: int, quantity: int, db: Session = Depends(get_db)):
    article = crud.add_stock(db, id, quantity)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return {"message": "Stock ajouté", "data": article}


@router.post("/{id}/stock/out")
def stock_out(id: int, quantity: int, db: Session = Depends(get_db)):
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

@router.get("/movements")
def movements(db: Session = Depends(get_db)):
    return crud.get_movements(db)


@router.get("/movements/day")
def movements_day(db: Session = Depends(get_db)):
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return crud.get_movements_by_date(db, start)


@router.get("/movements/week")
def movements_week(db: Session = Depends(get_db)):
    start = datetime.now() - timedelta(days=7)
    return crud.get_movements_by_date(db, start)


@router.get("/movements/month")
def movements_month(db: Session = Depends(get_db)):
    start = datetime.now() - timedelta(days=30)
    return crud.get_movements_by_date(db, start)


# =========================
# ALERTS
# =========================

@router.get("/alerts/low-stock")
def low_stock(db: Session = Depends(get_db)):
    return crud.get_low_stock_articles(db)


# =========================
# PROFIT ARTICLE
# =========================
@router.get("/{id}/profit")
def article_profit(id: int, db: Session = Depends(get_db)):
    return crud.get_article_profit(db, id)


# =========================
# PROFIT TOTAL
# =========================
@router.get("/profit/total")
def total_profit(db: Session = Depends(get_db)):
    return crud.get_total_profit(db)