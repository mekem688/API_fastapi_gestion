from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON
from datetime import datetime, timezone
from .data import Base


class Boutique(Base):
    __tablename__ = "boutiques"
    id            = Column(Integer, primary_key=True, index=True)
    nom           = Column(String(100), nullable=False)
    ville         = Column(String(100), nullable=False)
    adresse       = Column(String(200))
    est_active    = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Utilisateur(Base):
    """
    Profil complet d'un utilisateur.
    Les champs identité (prenom, nom_famille, telephone) sont obligatoires
    à la création — nécessaires pour la traçabilité.
    """
    __tablename__ = "utilisateurs"
    id                  = Column(Integer, primary_key=True, index=True)
    nom_utilisateur     = Column(String(50), unique=True, nullable=False, index=True)
    mot_de_passe_hash   = Column(String, nullable=False)
    role                = Column(String(20), nullable=False)   # pdg | directeur | vendeur
    boutique_id         = Column(Integer, ForeignKey("boutiques.id"), nullable=True)
    est_actif           = Column(Boolean, default=True)
    permissions         = Column(JSON, default=list)

    # ── Identité réelle (pour la traçabilité) ──────────────────
    prenom              = Column(String(50),  nullable=False)
    nom_famille         = Column(String(50),  nullable=False)
    telephone           = Column(String(20),  nullable=False)
    adresse_personnelle = Column(String(200), nullable=True)
    date_creation_compte = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Article(Base):
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
    __tablename__ = "stock_movements"
    id            = Column(Integer, primary_key=True, index=True)
    boutique_id   = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    article_id    = Column(Integer, ForeignKey("articles.id"))
    movement_type = Column(String)
    quantity      = Column(Integer)
    unit_price    = Column(Float)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ================================================================
# CRÉDITS VENTES — argent que les clients doivent à la boutique
# ================================================================

class VenteCredit(Base):
    """
    Une vente réalisée sans paiement immédiat.
    Le client s'engage à payer avant la date d'échéance.
    """
    __tablename__ = "ventes_credit"
    id                  = Column(Integer, primary_key=True, index=True)
    boutique_id         = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    directeur_id        = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)

    # Identité du client
    client_nom          = Column(String(100), nullable=False)
    client_entreprise   = Column(String(100), nullable=True)   # boutique ou entreprise du client
    client_telephone    = Column(String(20),  nullable=False)
    client_adresse      = Column(String(200), nullable=True)

    # Montants
    montant_total       = Column(Float, nullable=False)
    montant_paye        = Column(Float, default=0.0)           # mis à jour à chaque paiement
    montant_restant     = Column(Float, nullable=False)        # montant_total - montant_paye

    # Dates et statut
    date_vente          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    date_echeance       = Column(DateTime, nullable=False)
    statut              = Column(String(20), default="en_cours")
    # statut : "en_cours" | "partiellement_paye" | "solde" | "en_retard"
    note                = Column(String(500), nullable=True)


class PaiementRecu(Base):
    """Enregistre chaque versement d'un client pour solder sa dette."""
    __tablename__ = "paiements_recus"
    id               = Column(Integer, primary_key=True, index=True)
    vente_credit_id  = Column(Integer, ForeignKey("ventes_credit.id"), nullable=False)
    directeur_id     = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    montant_verse    = Column(Float, nullable=False)
    date_paiement    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    note             = Column(String(500), nullable=True)


# ================================================================
# CRÉDITS ACHATS — argent que la boutique doit aux fournisseurs
# ================================================================

class AchatCredit(Base):
    """
    Un achat de stock réalisé sans paiement immédiat au fournisseur.
    La boutique s'engage à payer avant la date d'échéance.
    """
    __tablename__ = "achats_credit"
    id                      = Column(Integer, primary_key=True, index=True)
    boutique_id             = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    directeur_id            = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)

    # Identité du fournisseur
    fournisseur_nom         = Column(String(100), nullable=False)
    fournisseur_entreprise  = Column(String(100), nullable=True)
    fournisseur_telephone   = Column(String(20),  nullable=False)
    fournisseur_adresse     = Column(String(200), nullable=True)

    # Montants
    montant_total           = Column(Float, nullable=False)
    montant_paye            = Column(Float, default=0.0)
    montant_restant         = Column(Float, nullable=False)

    # Dates et statut
    date_achat              = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    date_echeance           = Column(DateTime, nullable=False)
    statut                  = Column(String(20), default="en_cours")
    note                    = Column(String(500), nullable=True)


class PaiementEffectue(Base):
    """Enregistre chaque versement de la boutique vers un fournisseur."""
    __tablename__ = "paiements_effectues"
    id               = Column(Integer, primary_key=True, index=True)
    achat_credit_id  = Column(Integer, ForeignKey("achats_credit.id"), nullable=False)
    directeur_id     = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    montant_verse    = Column(Float, nullable=False)
    date_paiement    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    note             = Column(String(500), nullable=True)


# ================================================================
# JOURNAL D'ACTIVITÉ — traçabilité de toutes les actions
# ================================================================

class JournalActivite(Base):
    """
    Enregistre automatiquement chaque action significative.
    Les informations nom_utilisateur et boutique_nom sont dénormalisées
    (copiées en dur) pour rester lisibles même si un compte est supprimé.
    """
    __tablename__ = "journal_activite"
    id              = Column(Integer, primary_key=True, index=True)
    utilisateur_id  = Column(Integer, nullable=False)
    nom_utilisateur = Column(String(50), nullable=False)    # copie en dur
    nom_complet     = Column(String(100), nullable=False)   # "Prénom Nom"
    boutique_id     = Column(Integer, nullable=True)
    boutique_nom    = Column(String(100), nullable=True)    # copie en dur
    action          = Column(String(50), nullable=False)
    details         = Column(JSON, nullable=True)
    date_heure      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
