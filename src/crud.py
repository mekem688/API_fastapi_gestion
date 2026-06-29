from sqlalchemy.orm import Session
from datetime import datetime

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


def get_articles(db: Session):
    return db.query(Article).all()


def get_article(db: Session, article_id: int):
    return db.query(Article).filter(Article.id == article_id).first()


# =========================
# MOVEMENT
# =========================

def create_movement(db, article_id, type, quantity, unit_price):
    movement = StockMovement(
        article_id=article_id,
        type=type,
        quantity=quantity,
        unit_price=unit_price,
        created_at=datetime.utcnow()
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def get_movements(db: Session):
    return db.query(StockMovement).order_by(StockMovement.created_at.desc()).all()


def get_movements_by_date(db: Session, start_date: datetime):
    return db.query(StockMovement).filter(
        StockMovement.created_at >= start_date
    ).order_by(StockMovement.created_at.desc()).all()


# =========================
# STOCK LOGIC
# =========================

# 📥 ACHAT (IN)
def add_stock(db: Session, article_id: int, quantity: int):
    article = get_article(db, article_id)
    if not article:
        return None

    article.quantity += quantity

    create_movement(
        db,
        article_id,
        "IN",
        quantity,
        article.price_achat
    )

    db.commit()
    db.refresh(article)
    return article


# 📤 VENTE (OUT)
def remove_stock(db: Session, article_id: int, quantity: int):
    article = get_article(db, article_id)
    if not article:
        return None

    if article.quantity < quantity:
        raise ValueError("Stock insuffisant")

    article.quantity -= quantity

    create_movement(
        db,
        article_id,
        "OUT",
        quantity,
        article.price_vente
    )

    db.commit()
    db.refresh(article)

    profit = (article.price_vente - article.price_achat) * quantity

    return {
        "article": article,
        "profit": profit
    }


# =========================
# PROFIT ARTICLE
# =========================

def get_article_profit(db: Session, article_id: int):
    article = get_article(db, article_id)

    if not article:
        return None

    movements = db.query(StockMovement).filter(
        StockMovement.article_id == article_id,
        StockMovement.type == "OUT"
    ).all()

    total = 0

    for m in movements:
        total += (article.price_vente - article.price_achat) * m.quantity

    return {
        "article_id": article_id,
        "total_profit": total
    }


# =========================
# PROFIT TOTAL
# =========================

def get_total_profit(db: Session):
    articles = db.query(Article).all()

    total = 0

    for article in articles:
        movements = db.query(StockMovement).filter(
            StockMovement.article_id == article.id,
            StockMovement.type == "OUT"
        ).all()

        for m in movements:
            total += (article.price_vente - article.price_achat) * m.quantity

    return {"total_profit": total}


# =========================
# ALERT STOCK FAIBLE
# =========================

def get_low_stock_articles(db: Session):
    return db.query(Article).filter(
        Article.quantity <= Article.low_stock_threshold
    ).all()