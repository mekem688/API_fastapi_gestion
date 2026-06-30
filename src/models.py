from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime, timezone
from .data import Base


class Article(Base):
    __tablename__ = "articles"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(100), nullable=False)
    description         = Column(String)
    quantity            = Column(Integer, default=0)
    price_achat         = Column(Float, nullable=False)
    price_vente         = Column(Float, nullable=False)
    low_stock_threshold = Column(Integer, default=5)


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id            = Column(Integer, primary_key=True, index=True)
    article_id    = Column(Integer, ForeignKey("articles.id"))
    movement_type = Column(String)          # "IN" = achat, "OUT" = vente
    quantity      = Column(Integer)
    unit_price    = Column(Float)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
