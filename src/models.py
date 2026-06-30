from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from datetime import datetime, timezone
from .data import Base


class Boutique(Base):
    """
    Représente une boutique de l'entreprise.
    est_active = False signifie archivée (jamais supprimée en dur).
    """
    __tablename__ = "boutiques"

    id             = Column(Integer, primary_key=True, index=True)
    nom            = Column(String(100), nullable=False)
    ville          = Column(String(100), nullable=False)
    adresse        = Column(String(200))
    est_active     = Column(Boolean, default=True)
    date_creation  = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Utilisateur(Base):
    """
    Représente un utilisateur du système.
    Rôles : "pdg" | "directeur" | "vendeur"
    boutique_id est NULL pour le PDG (il n'appartient à aucune boutique).
    """
    __tablename__ = "utilisateurs"

    id                = Column(Integer, primary_key=True, index=True)
    nom_utilisateur   = Column(String(50), unique=True, nullable=False, index=True)
    mot_de_passe_hash = Column(String, nullable=False)
    role              = Column(String(20), nullable=False)   # "pdg" | "directeur" | "vendeur"
    boutique_id       = Column(Integer, ForeignKey("boutiques.id"), nullable=True)
    # NULL pour le PDG, obligatoire pour directeur et vendeur


class Article(Base):
    """Représente un produit vendu dans une boutique spécifique."""
    __tablename__ = "articles"

    id                  = Column(Integer, primary_key=True, index=True)
    boutique_id         = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    name                = Column(String(100), nullable=False)
    description         = Column(String)
    quantity            = Column(Integer, default=0)
    price_achat         = Column(Float, nullable=False)
    price_vente         = Column(Float, nullable=False)
    low_stock_threshold = Column(Integer, default=5)


class StockMovement(Base):
    """Trace chaque entrée ou sortie de stock, liée à une boutique."""
    __tablename__ = "stock_movements"

    id            = Column(Integer, primary_key=True, index=True)
    boutique_id   = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    article_id    = Column(Integer, ForeignKey("articles.id"))
    movement_type = Column(String)         # "IN" = achat, "OUT" = vente
    quantity      = Column(Integer)
    unit_price    = Column(Float)          # prix au moment de la transaction
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
