from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from .models import Article, StockMovement, Utilisateur, Boutique
from .auth import hacher_mot_de_passe, verifier_mot_de_passe


# ============================================================
# UTILISATEURS
# ============================================================

def get_utilisateur_par_nom(db: Session, nom_utilisateur: str):
    return db.query(Utilisateur).filter(
        Utilisateur.nom_utilisateur == nom_utilisateur
    ).first()


def get_nombre_utilisateurs(db: Session) -> int:
    return db.query(Utilisateur).count()


def creer_utilisateur(
    db: Session,
    nom_utilisateur: str,
    mot_de_passe: str,
    role: str,
    boutique_id: int | None = None,
):
    """
    Crée un utilisateur. Le mot de passe est haché avant stockage.
    boutique_id est None pour le PDG, requis pour directeur et vendeur.
    """
    hash_securise = hacher_mot_de_passe(mot_de_passe)
    utilisateur   = Utilisateur(
        nom_utilisateur   = nom_utilisateur,
        mot_de_passe_hash = hash_securise,
        role              = role,
        boutique_id       = boutique_id,
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


def verifier_connexion(db: Session, nom_utilisateur: str, mot_de_passe: str):
    utilisateur = get_utilisateur_par_nom(db, nom_utilisateur)
    if utilisateur is None:
        return None
    if not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash):
        return None
    return utilisateur


def get_vendeurs_de_boutique(db: Session, boutique_id: int) -> int:
    """Retourne le nombre de vendeurs d'une boutique."""
    return db.query(Utilisateur).filter(
        Utilisateur.boutique_id == boutique_id,
        Utilisateur.role        == "vendeur",
    ).count()


# ============================================================
# BOUTIQUES
# ============================================================

def creer_boutique(db: Session, nom: str, ville: str, adresse: str | None):
    boutique = Boutique(nom=nom, ville=ville, adresse=adresse)
    db.add(boutique)
    db.commit()
    db.refresh(boutique)
    return boutique


def get_boutiques(db: Session):
    """Retourne toutes les boutiques (actives et archivées)."""
    return db.query(Boutique).order_by(Boutique.date_creation.desc()).all()


def get_boutique(db: Session, boutique_id: int):
    return db.query(Boutique).filter(Boutique.id == boutique_id).first()


def archiver_boutique(db: Session, boutique_id: int):
    """Archive une boutique (soft delete — les données restent intactes)."""
    boutique = get_boutique(db, boutique_id)
    if boutique:
        boutique.est_active = False
        db.commit()
        db.refresh(boutique)
    return boutique


# ============================================================
# ARTICLES — filtrés par boutique
# ============================================================

def create_article(db: Session, article, boutique_id: int):
    """Crée un article dans la boutique du directeur connecté."""
    nouvel_article = Article(
        **article.model_dump(),
        boutique_id = boutique_id,
        quantity    = 0,
    )
    db.add(nouvel_article)
    db.commit()
    db.refresh(nouvel_article)
    return nouvel_article


def get_articles(db: Session, boutique_id: int, skip: int = 0, limit: int = 50):
    """Retourne uniquement les articles de la boutique de l'utilisateur."""
    return (
        db.query(Article)
        .filter(Article.boutique_id == boutique_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_article(db: Session, article_id: int, boutique_id: int):
    """Retourne un article seulement s'il appartient à la boutique de l'utilisateur."""
    return db.query(Article).filter(
        Article.id          == article_id,
        Article.boutique_id == boutique_id,
    ).first()


def get_nb_articles_boutique(db: Session, boutique_id: int) -> int:
    return db.query(Article).filter(Article.boutique_id == boutique_id).count()


# ============================================================
# MOUVEMENTS DE STOCK
# ============================================================

def enregistrer_mouvement(
    db: Session,
    boutique_id: int,
    article_id: int,
    type_mouvement: str,
    quantite: int,
    prix_unitaire: float,
):
    mouvement = StockMovement(
        boutique_id   = boutique_id,
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


def get_movements(db: Session, boutique_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(StockMovement)
        .filter(StockMovement.boutique_id == boutique_id)
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_movements_by_date(
    db: Session,
    boutique_id: int,
    date_debut: datetime,
    skip: int = 0,
    limit: int = 100,
):
    return (
        db.query(StockMovement)
        .filter(
            StockMovement.boutique_id == boutique_id,
            StockMovement.created_at  >= date_debut,
        )
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# LOGIQUE DE STOCK
# ============================================================

def add_stock(db: Session, article_id: int, quantite: int, boutique_id: int):
    article = get_article(db, article_id, boutique_id)
    if not article:
        return None
    article.quantity += quantite
    enregistrer_mouvement(db, boutique_id, article_id, "IN", quantite, article.price_achat)
    db.commit()
    db.refresh(article)
    return article


def remove_stock(db: Session, article_id: int, quantite: int, boutique_id: int):
    article = get_article(db, article_id, boutique_id)
    if not article:
        return None
    if article.quantity < quantite:
        raise ValueError("Stock insuffisant")
    article.quantity -= quantite
    prix_de_vente_actuel = article.price_vente
    enregistrer_mouvement(db, boutique_id, article_id, "OUT", quantite, prix_de_vente_actuel)
    db.commit()
    db.refresh(article)
    benefice = (article.price_vente - article.price_achat) * quantite
    return {"article": article, "benefice_de_la_vente": round(benefice, 2)}


# ============================================================
# PROFITS — par boutique
# ============================================================

def get_article_profit(db: Session, article_id: int, boutique_id: int):
    article = get_article(db, article_id, boutique_id)
    if not article:
        return None
    ventes = db.query(StockMovement).filter(
        StockMovement.article_id    == article_id,
        StockMovement.boutique_id   == boutique_id,
        StockMovement.movement_type == "OUT",
    ).all()
    benefice_total = 0.0
    for vente in ventes:
        benefice_total += (vente.unit_price - article.price_achat) * vente.quantity
    return {"article_id": article_id, "benefice_total": round(benefice_total, 2)}


def get_total_profit_boutique(db: Session, boutique_id: int) -> float:
    """Bénéfice total d'une seule boutique (une requête SQL)."""
    resultat = (
        db.query(
            func.sum(
                (StockMovement.unit_price - Article.price_achat) * StockMovement.quantity
            )
        )
        .join(Article, Article.id == StockMovement.article_id)
        .filter(
            StockMovement.movement_type == "OUT",
            StockMovement.boutique_id   == boutique_id,
        )
        .scalar()
    )
    return round(resultat or 0.0, 2)


def get_ventes_du_mois_boutique(db: Session, boutique_id: int) -> int:
    """Nombre de mouvements OUT dans les 30 derniers jours pour une boutique."""
    il_y_a_30_jours = datetime.now(timezone.utc) - timedelta(days=30)
    return (
        db.query(StockMovement)
        .filter(
            StockMovement.boutique_id   == boutique_id,
            StockMovement.movement_type == "OUT",
            StockMovement.created_at    >= il_y_a_30_jours,
        )
        .count()
    )


def get_articles_en_alerte_boutique(db: Session, boutique_id: int) -> list:
    """Articles dont le stock est sous le seuil d'alerte dans une boutique."""
    return db.query(Article).filter(
        Article.boutique_id == boutique_id,
        Article.quantity    <= Article.low_stock_threshold,
    ).all()


# ============================================================
# DASHBOARD PDG — toutes boutiques
# ============================================================

def get_benefice_total_entreprise(db: Session) -> float:
    """Bénéfice total de TOUTES les boutiques en une requête."""
    resultat = (
        db.query(
            func.sum(
                (StockMovement.unit_price - Article.price_achat) * StockMovement.quantity
            )
        )
        .join(Article, Article.id == StockMovement.article_id)
        .filter(StockMovement.movement_type == "OUT")
        .scalar()
    )
    return round(resultat or 0.0, 2)


def get_ventes_totales_du_mois(db: Session) -> int:
    """Nombre total de ventes de toutes les boutiques sur 30 jours."""
    il_y_a_30_jours = datetime.now(timezone.utc) - timedelta(days=30)
    return (
        db.query(StockMovement)
        .filter(
            StockMovement.movement_type == "OUT",
            StockMovement.created_at    >= il_y_a_30_jours,
        )
        .count()
    )


def get_nb_articles_en_alerte_total(db: Session) -> int:
    """Nombre total d'articles en alerte dans toute l'entreprise."""
    return (
        db.query(Article)
        .filter(Article.quantity <= Article.low_stock_threshold)
        .count()
    )


def get_activite_recente(db: Session, limite: int = 10):
    """
    Retourne les derniers mouvements de stock de toutes les boutiques,
    avec le nom de la boutique et de l'article.
    """
    mouvements = (
        db.query(StockMovement, Article, Boutique)
        .join(Article,  Article.id  == StockMovement.article_id)
        .join(Boutique, Boutique.id == StockMovement.boutique_id)
        .order_by(StockMovement.created_at.desc())
        .limit(limite)
        .all()
    )
    return [
        {
            "boutique_nom"  : boutique.nom,
            "article_nom"   : article.name,
            "type_mouvement": mouvement.movement_type,
            "quantite"      : mouvement.quantity,
            "date"          : mouvement.created_at,
        }
        for mouvement, article, boutique in mouvements
    ]


def get_evolution_ventes(db: Session, nb_jours: int = 30):
    """
    Retourne les ventes jour par jour sur les nb_jours derniers jours,
    pour toutes les boutiques.
    Format : [{"date": "2024-06-01", "nb_ventes": 5, "benefice_jour": 12500.0}, ...]
    """
    date_debut = datetime.now(timezone.utc) - timedelta(days=nb_jours)

    mouvements = (
        db.query(StockMovement, Article)
        .join(Article, Article.id == StockMovement.article_id)
        .filter(
            StockMovement.movement_type == "OUT",
            StockMovement.created_at    >= date_debut,
        )
        .all()
    )

    # Regrouper par date
    par_jour: dict[str, dict] = {}
    for mouvement, article in mouvements:
        cle_date  = mouvement.created_at.strftime("%Y-%m-%d")
        benefice  = (mouvement.unit_price - article.price_achat) * mouvement.quantity

        if cle_date not in par_jour:
            par_jour[cle_date] = {"date": cle_date, "nb_ventes": 0, "benefice_jour": 0.0}

        par_jour[cle_date]["nb_ventes"]     += mouvement.quantity
        par_jour[cle_date]["benefice_jour"] += benefice

    # Trier par date croissante et arrondir les bénéfices
    resultat = sorted(par_jour.values(), key=lambda x: x["date"])
    for point in resultat:
        point["benefice_jour"] = round(point["benefice_jour"], 2)

    return resultat
