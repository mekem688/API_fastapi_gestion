from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime, timezone
from .data import Base


class Utilisateur(Base):
    """
    Représente un utilisateur du système.
    Rôles possibles : "vendeur" ou "directeur"
    """
    __tablename__ = "utilisateurs"

    id             = Column(Integer, primary_key=True, index=True)
    nom_utilisateur = Column(String(50), unique=True, nullable=False, index=True)
    mot_de_passe_hash = Column(String, nullable=False)   # jamais le mot de passe en clair
    role           = Column(String(20), nullable=False)  # "vendeur" ou "directeur"


class Article(Base):
    """Représente un produit en stock."""
    __tablename__ = "articles"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(100), nullable=False)
    description         = Column(String)
    quantity            = Column(Integer, default=0)
    price_achat         = Column(Float, nullable=False)
    price_vente         = Column(Float, nullable=False)
    low_stock_threshold = Column(Integer, default=5)


class StockMovement(Base):
    """Trace chaque entrée ou sortie de stock."""
    __tablename__ = "stock_movements"

    id            = Column(Integer, primary_key=True, index=True)
    article_id    = Column(Integer, ForeignKey("articles.id"))
    movement_type = Column(String)          # "IN" = achat, "OUT" = vente
    quantity      = Column(Integer)
    unit_price    = Column(Float)           # prix au moment de la transaction
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
