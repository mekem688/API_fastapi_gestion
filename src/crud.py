from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from .models import Article, StockMovement


# ============================================================
# ARTICLES
# ============================================================

def create_article(db: Session, article):
    """Crée un nouvel article avec un stock initial à 0."""
    nouvel_article = Article(**article.model_dump(), quantity=0)
    db.add(nouvel_article)
    db.commit()
    db.refresh(nouvel_article)
    return nouvel_article


def get_articles(db: Session, skip: int = 0, limit: int = 50):
    """Retourne la liste des articles avec pagination (skip = décalage, limit = max)."""
    return db.query(Article).offset(skip).limit(limit).all()


def get_article(db: Session, article_id: int):
    """Retourne un seul article par son identifiant, ou None s'il n'existe pas."""
    return db.query(Article).filter(Article.id == article_id).first()


# ============================================================
# MOUVEMENTS DE STOCK
# ============================================================

def enregistrer_mouvement(
    db: Session,
    article_id: int,
    type_mouvement: str,   # "IN" pour achat, "OUT" pour vente
    quantite: int,
    prix_unitaire: float,  # prix d'achat pour IN, prix de vente pour OUT
):
    """
    Enregistre un mouvement de stock (entrée ou sortie).
    Le prix_unitaire est sauvegardé tel quel au moment de la transaction
    pour garder un historique fidèle même si le prix change plus tard.
    """
    mouvement = StockMovement(
        article_id    = article_id,
        movement_type = type_mouvement,
        quantity      = quantite,
        unit_price    = prix_unitaire,
        created_at    = datetime.now(timezone.utc),
    )
    db.add(mouvement)
    db.commit()
    db.refresh(mouvement)
    return mouvement


def get_movements(db: Session, skip: int = 0, limit: int = 100):
    """Retourne tous les mouvements, du plus récent au plus ancien."""
    return (
        db.query(StockMovement)
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_movements_by_date(db: Session, date_debut: datetime, skip: int = 0, limit: int = 100):
    """Retourne les mouvements à partir d'une date donnée."""
    return (
        db.query(StockMovement)
        .filter(StockMovement.created_at >= date_debut)
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# LOGIQUE DE STOCK
# ============================================================

def add_stock(db: Session, article_id: int, quantite: int):
    """
    Entrée de stock (achat).
    - Augmente la quantité disponible
    - Enregistre le mouvement au prix d'achat actuel
    """
    article = get_article(db, article_id)
    if not article:
        return None

    # On augmente le stock
    article.quantity += quantite

    # On trace l'entrée au prix d'achat du moment
    enregistrer_mouvement(
        db,
        article_id    = article_id,
        type_mouvement = "IN",
        quantite      = quantite,
        prix_unitaire = article.price_achat,
    )

    db.commit()
    db.refresh(article)
    return article


def remove_stock(db: Session, article_id: int, quantite: int):
    """
    Sortie de stock (vente).
    - Vérifie qu'il y a assez de stock
    - Diminue la quantité disponible
    - Enregistre le mouvement au prix de vente actuel
    - Retourne l'article mis à jour + le bénéfice de cette vente
    """
    article = get_article(db, article_id)
    if not article:
        return None

    # Vérification : stock suffisant ?
    if article.quantity < quantite:
        raise ValueError("Stock insuffisant")

    # On diminue le stock
    article.quantity -= quantite

    # Prix de vente au moment de la transaction (sauvegardé pour l'historique)
    prix_de_vente_actuel = article.price_vente

    # On trace la sortie au prix de vente du moment
    enregistrer_mouvement(
        db,
        article_id    = article_id,
        type_mouvement = "OUT",
        quantite      = quantite,
        prix_unitaire = prix_de_vente_actuel,
    )

    db.commit()
    db.refresh(article)

    # Bénéfice immédiat de cette vente
    benefice = (article.price_vente - article.price_achat) * quantite

    return {
        "article": article,
        "benefice_de_la_vente": benefice,
    }


# ============================================================
# CALCUL DES BÉNÉFICES
# ============================================================

def get_article_profit(db: Session, article_id: int):
    """
    Calcule le bénéfice total réalisé sur un article donné.

    COMMENT : on utilise le prix de vente enregistré dans chaque mouvement
    (unit_price des sorties "OUT") au lieu du prix actuel de l'article.
    Ainsi, si le prix change après une vente, l'historique reste correct.

    Bénéfice d'une vente = (prix vendu à l'époque) - (prix d'achat actuel) × quantité
    """
    article = get_article(db, article_id)
    if not article:
        return None

    # On récupère toutes les ventes (mouvements de type OUT) pour cet article
    ventes = (
        db.query(StockMovement)
        .filter(
            StockMovement.article_id    == article_id,
            StockMovement.movement_type == "OUT",
        )
        .all()
    )

    benefice_total = 0.0
    for vente in ventes:
        # prix_vendu    : prix de vente au moment de la transaction (historique)
        # price_achat   : prix d'achat actuel de l'article
        prix_vendu  = vente.unit_price
        prix_achat  = article.price_achat
        benefice_total += (prix_vendu - prix_achat) * vente.quantity

    return {
        "article_id"   : article_id,
        "benefice_total": round(benefice_total, 2),
    }


def get_total_profit(db: Session):
    """
    Calcule le bénéfice total sur tous les articles en une seule requête SQL.

    AVANT (bug) : une boucle Python faisait 1 requête par article → très lent.
    MAINTENANT  : on utilise un JOIN + SUM directement en base → 1 seule requête.

    Formule : SUM( (prix_vendu_à_l_époque - prix_achat_actuel) × quantité )
              pour tous les mouvements de type "OUT"
    """
    benefice_total = (
        db.query(
            # On somme directement en SQL : (prix de vente historique - prix d'achat actuel) × quantité
            func.sum(
                (StockMovement.unit_price - Article.price_achat) * StockMovement.quantity
            )
        )
        .join(Article, Article.id == StockMovement.article_id)
        .filter(StockMovement.movement_type == "OUT")
        .scalar()  # scalar() retourne directement la valeur numérique
    )

    # Si aucune vente n'a encore eu lieu, scalar() retourne None → on met 0
    return {"benefice_total": round(benefice_total or 0.0, 2)}


# ============================================================
# ALERTES STOCK FAIBLE
# ============================================================

def get_low_stock_articles(db: Session):
    """
    Retourne les articles dont le stock actuel est
    inférieur ou égal au seuil d'alerte (low_stock_threshold).
    """
    return (
        db.query(Article)
        .filter(Article.quantity <= Article.low_stock_threshold)
        .all()
    )
