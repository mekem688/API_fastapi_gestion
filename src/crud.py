from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .models import Article, StockMovement


# =========================
# ARTICLE
# =========================

def create_article(db: Session, article):
    db_article = Article(**article.model_dump(), quantity=0)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


def get_articles(db: Session, skip: int = 0, limit: int = 50):
    return db.query(Article).offset(skip).limit(limit).all()


def get_article(db: Session, article_id: int):
    return db.query(Article).filter(Article.id == article_id).first()


# =========================
# MOVEMENT
# =========================

def create_movement(db: Session, article_id: int, movement_type: str, quantity: int, unit_price: float):
    movement = StockMovement(
        article_id    = article_id,
        movement_type = movement_type,
        quantity      = quantity,
        unit_price    = unit_price,
        created_at    = datetime.now(timezone.utc),
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def get_movements(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(StockMovement)
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_movements_by_date(db: Session, start_date: datetime, skip: int = 0, limit: int = 100):
    return (
        db.query(StockMovement)
        .filter(StockMovement.created_at >= start_date)
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# STOCK LOGIC
# =========================

def add_stock(db: Session, article_id: int, quantity: int):
    article = get_article(db, article_id)
    if not article:
        return None

    article.quantity += quantity
    create_movement(db, article_id, "IN", quantity, article.price_achat)
    db.commit()
    db.refresh(article)
    return article


def remove_stock(db: Session, article_id: int, quantity: int):
    article = get_article(db, article_id)
    if not article:
        return None

    if article.quantity < quantity:
        raise ValueError("Stock insuffisant")

    article.quantity -= quantity
    create_movement(db, article_id, "OUT", quantity, article.price_vente)
    db.commit()
    db.refresh(article)

    profit = (article.price_vente - article.price_achat) * quantity
    return {"article": article, "profit": profit}


# =========================
# PROFIT ARTICLE
# =========================

def get_article_profit(db: Session, article_id: int):
    article = get_article(db, article_id)
    if not article:
        return None

    movements = (
        db.query(StockMovement)
        .filter(
            StockMovement.article_id    == article_id,
            StockMovement.movement_type == "OUT",
        )
        .all()
    )

    total = sum((article.price_vente - article.price_achat) * m.quantity for m in movements)
    return {"article_id": article_id, "total_profit": total}


# =========================
# PROFIT TOTAL
# =========================

def get_total_profit(db: Session):
    articles = db.query(Article).all()
    total = 0.0

    for article in articles:
        movements = (
            db.query(StockMovement)
            .filter(
                StockMovement.article_id    == article.id,
                StockMovement.movement_type == "OUT",
            )
            .all()
        )
        total += sum((article.price_vente - article.price_achat) * m.quantity for m in movements)

    return {"total_profit": total}


# =========================
# ALERT STOCK FAIBLE
# =========================

def get_low_stock_articles(db: Session):
    return db.query(Article).filter(Article.quantity <= Article.low_stock_threshold).all()
