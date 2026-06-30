from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from .models import Article, StockMovement, Utilisateur
from .auth import hacher_mot_de_passe, verifier_mot_de_passe


# ============================================================
# UTILISATEURS
# ============================================================

def get_utilisateur_par_nom(db: Session, nom_utilisateur: str):
    """Cherche un utilisateur par son nom. Retourne None s'il n'existe pas."""
    return db.query(Utilisateur).filter(
        Utilisateur.nom_utilisateur == nom_utilisateur
    ).first()


def get_nombre_utilisateurs(db: Session) -> int:
    """Retourne le nombre total d'utilisateurs enregistrés."""
    return db.query(Utilisateur).count()


def creer_utilisateur(db: Session, nom_utilisateur: str, mot_de_passe: str, role: str):
    """
    Crée un nouvel utilisateur.
    Le mot de passe est haché avant d'être stocké — jamais en clair.
    """
    hash_securise = hacher_mot_de_passe(mot_de_passe)

    nouvel_utilisateur = Utilisateur(
        nom_utilisateur   = nom_utilisateur,
        mot_de_passe_hash = hash_securise,
        role              = role,
    )
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    return nouvel_utilisateur


def verifier_connexion(db: Session, nom_utilisateur: str, mot_de_passe: str):
    """
    Vérifie les identifiants d'un utilisateur.
    Retourne l'utilisateur si tout est correct, None sinon.
    """
    utilisateur = get_utilisateur_par_nom(db, nom_utilisateur)

    # L'utilisateur n'existe pas
    if utilisateur is None:
        return None

    # Le mot de passe ne correspond pas au hash stocké
    if not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash):
        return None

    return utilisateur


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
    """Retourne la liste des articles avec pagination."""
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
    prix_unitaire: float,  # prix au moment de la transaction
):
    """
    Enregistre un mouvement de stock dans l'historique.
    Le prix est sauvegardé tel quel pour garder un historique fidèle.
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
    """Retourne tous les mouvements du plus récent au plus ancien."""
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

    article.quantity += quantite

    enregistrer_mouvement(
        db,
        article_id     = article_id,
        type_mouvement = "IN",
        quantite       = quantite,
        prix_unitaire  = article.price_achat,
    )

    db.commit()
    db.refresh(article)
    return article


def remove_stock(db: Session, article_id: int, quantite: int):
    """
    Sortie de stock (vente).
    - Vérifie qu'il y a assez de stock
    - Diminue la quantité disponible
    - Enregistre le mouvement au prix de vente du moment
    - Retourne l'article mis à jour + le bénéfice de cette vente
    """
    article = get_article(db, article_id)
    if not article:
        return None

    if article.quantity < quantite:
        raise ValueError("Stock insuffisant")

    article.quantity -= quantite

    # On sauvegarde le prix de vente actuel avant toute modification
    prix_de_vente_actuel = article.price_vente

    enregistrer_mouvement(
        db,
        article_id     = article_id,
        type_mouvement = "OUT",
        quantite       = quantite,
        prix_unitaire  = prix_de_vente_actuel,
    )

    db.commit()
    db.refresh(article)

    benefice = (article.price_vente - article.price_achat) * quantite

    return {
        "article"             : article,
        "benefice_de_la_vente": round(benefice, 2),
    }


# ============================================================
# CALCUL DES BÉNÉFICES
# ============================================================

def get_article_profit(db: Session, article_id: int):
    """
    Calcule le bénéfice total réalisé sur un article.
    Utilise le prix de vente historique (unit_price) enregistré dans chaque
    mouvement, pas le prix actuel — ainsi l'historique reste correct
    même si le prix a changé depuis.
    """
    article = get_article(db, article_id)
    if not article:
        return None

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
        prix_vendu = vente.unit_price      # prix de vente au moment de la transaction
        prix_achat = article.price_achat   # prix d'achat actuel
        benefice_total += (prix_vendu - prix_achat) * vente.quantity

    return {
        "article_id"    : article_id,
        "benefice_total": round(benefice_total, 2),
    }


def get_total_profit(db: Session):
    """
    Calcule le bénéfice total sur tous les articles en une seule requête SQL.
    Utilise JOIN + SUM pour éviter de faire une requête par article.
    """
    benefice_total = (
        db.query(
            func.sum(
                (StockMovement.unit_price - Article.price_achat) * StockMovement.quantity
            )
        )
        .join(Article, Article.id == StockMovement.article_id)
        .filter(StockMovement.movement_type == "OUT")
        .scalar()
    )

    # scalar() retourne None s'il n'y a aucune vente → on met 0
    return {"benefice_total": round(benefice_total or 0.0, 2)}


# ============================================================
# ALERTES STOCK FAIBLE
# ============================================================

def get_low_stock_articles(db: Session):
    """
    Retourne les articles dont le stock est inférieur ou égal
    au seuil d'alerte défini (low_stock_threshold).
    """
    return (
        db.query(Article)
        .filter(Article.quantity <= Article.low_stock_threshold)
        .all()
    )
