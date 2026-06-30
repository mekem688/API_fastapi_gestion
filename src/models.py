from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON
from datetime import datetime, timezone
from .data import Base


class Boutique(Base):
    """
    Représente une boutique de l'entreprise.
    est_active = False → archivée (jamais supprimée en dur).
    """
    __tablename__ = "boutiques"

    id            = Column(Integer, primary_key=True, index=True)
    nom           = Column(String(100), nullable=False)
    ville         = Column(String(100), nullable=False)
    adresse       = Column(String(200))
    est_active    = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Utilisateur(Base):
    """
    Représente un utilisateur du système.

    Rôles : "pdg" | "directeur" | "vendeur"
    boutique_id : NULL pour le PDG, obligatoire pour directeur et vendeur.

    est_actif   : False → compte suspendu par le PDG (connexion bloquée).
    permissions : Liste JSON des droits accordés au directeur par le PDG.
                  Vide ou NULL = aucun droit restreint (tout est bloqué).
                  Le PDG ignore ce champ — il a toujours tous les droits.

    Permissions possibles pour un directeur :
      - "voir_profits"    → accès aux bénéfices
      - "faire_achats"    → entrées de stock
      - "creer_articles"  → créer de nouveaux articles
      - "voir_alertes"    → alertes stock faible
      - "gerer_vendeurs"  → créer et suspendre les vendeurs
    """
    __tablename__ = "utilisateurs"

    id                = Column(Integer, primary_key=True, index=True)
    nom_utilisateur   = Column(String(50), unique=True, nullable=False, index=True)
    mot_de_passe_hash = Column(String, nullable=False)
    role              = Column(String(20), nullable=False)
    boutique_id       = Column(Integer, ForeignKey("boutiques.id"), nullable=True)
    est_actif         = Column(Boolean, default=True)       # False = compte suspendu
    permissions       = Column(JSON, default=list)          # liste de strings pour les directeurs


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
    """Trace chaque entrée ou sortie de stock."""
    __tablename__ = "stock_movements"

    id            = Column(Integer, primary_key=True, index=True)
    boutique_id   = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    article_id    = Column(Integer, ForeignKey("articles.id"))
    movement_type = Column(String)
    quantity      = Column(Integer)
    unit_price    = Column(Float)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
