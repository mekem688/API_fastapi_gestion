from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from .models import (
    Article, StockMovement, Utilisateur, Boutique,
    VenteCredit, PaiementRecu, AchatCredit, PaiementEffectue,
    JournalActivite,
)
from .auth import hacher_mot_de_passe, verifier_mot_de_passe
from .permissions import TOUTES_LES_PERMISSIONS


# ============================================================
# JOURNAL D'ACTIVITÉ
# ============================================================

def journaliser(
    db: Session,
    utilisateur,          # objet Utilisateur complet
    boutique_nom: str | None,
    action: str,
    details: dict | None = None,
):
    """
    Enregistre une action dans le journal.
    Appelé automatiquement après chaque opération importante.
    nom_utilisateur et nom_complet sont copiés en dur pour la traçabilité.
    """
    entree = JournalActivite(
        utilisateur_id  = utilisateur.id,
        nom_utilisateur = utilisateur.nom_utilisateur,
        nom_complet     = f"{utilisateur.prenom} {utilisateur.nom_famille}",
        boutique_id     = utilisateur.boutique_id,
        boutique_nom    = boutique_nom,
        action          = action,
        details         = details,
    )
    db.add(entree)
    db.commit()


def get_journal(db: Session, boutique_id: int | None = None, limite: int = 100):
    """Retourne le journal — filtré par boutique si boutique_id fourni, sinon tout."""
    requete = db.query(JournalActivite).order_by(JournalActivite.date_heure.desc())
    if boutique_id is not None:
        requete = requete.filter(JournalActivite.boutique_id == boutique_id)
    return requete.limit(limite).all()


# ============================================================
# UTILISATEURS
# ============================================================

def get_utilisateur_par_nom(db: Session, nom_utilisateur: str):
    return db.query(Utilisateur).filter(
        Utilisateur.nom_utilisateur == nom_utilisateur
    ).first()


def get_utilisateur_par_id(db: Session, utilisateur_id: int):
    return db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()


def get_nombre_utilisateurs(db: Session) -> int:
    return db.query(Utilisateur).count()


def creer_utilisateur(
    db: Session,
    nom_utilisateur: str,
    mot_de_passe: str,
    role: str,
    prenom: str,
    nom_famille: str,
    telephone: str,
    adresse_personnelle: str | None = None,
    boutique_id: int | None = None,
):
    hash_securise         = hacher_mot_de_passe(mot_de_passe)
    permissions_initiales = [] if role == "directeur" else None

    utilisateur = Utilisateur(
        nom_utilisateur     = nom_utilisateur,
        mot_de_passe_hash   = hash_securise,
        role                = role,
        boutique_id         = boutique_id,
        est_actif           = True,
        permissions         = permissions_initiales,
        prenom              = prenom,
        nom_famille         = nom_famille,
        telephone           = telephone,
        adresse_personnelle = adresse_personnelle,
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
    if not utilisateur.est_actif:
        return "suspendu"
    return utilisateur


def get_vendeurs_de_boutique(db: Session, boutique_id: int) -> int:
    return db.query(Utilisateur).filter(
        Utilisateur.boutique_id == boutique_id,
        Utilisateur.role        == "vendeur",
    ).count()


def get_utilisateurs_de_boutique(db: Session, boutique_id: int):
    return db.query(Utilisateur).filter(
        Utilisateur.boutique_id == boutique_id,
    ).all()


def modifier_permissions(db: Session, directeur_id: int, nouvelles_permissions: list[str]):
    directeur = get_utilisateur_par_id(db, directeur_id)
    if not directeur or directeur.role != "directeur":
        return None
    directeur.permissions = [p for p in nouvelles_permissions if p in TOUTES_LES_PERMISSIONS]
    db.commit()
    db.refresh(directeur)
    return directeur


def suspendre_utilisateur(db: Session, utilisateur_id: int):
    utilisateur = get_utilisateur_par_id(db, utilisateur_id)
    if utilisateur:
        utilisateur.est_actif = False
        db.commit()
        db.refresh(utilisateur)
    return utilisateur


def reactiver_utilisateur(db: Session, utilisateur_id: int):
    utilisateur = get_utilisateur_par_id(db, utilisateur_id)
    if utilisateur:
        utilisateur.est_actif = True
        db.commit()
        db.refresh(utilisateur)
    return utilisateur


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
    return db.query(Boutique).order_by(Boutique.date_creation.desc()).all()


def get_boutique(db: Session, boutique_id: int):
    return db.query(Boutique).filter(Boutique.id == boutique_id).first()


def archiver_boutique(db: Session, boutique_id: int):
    boutique = get_boutique(db, boutique_id)
    if boutique:
        boutique.est_active = False
        db.commit()
        db.refresh(boutique)
    return boutique


# ============================================================
# ARTICLES
# ============================================================

def create_article(db: Session, article, boutique_id: int):
    nouvel_article = Article(**article.model_dump(), boutique_id=boutique_id, quantity=0)
    db.add(nouvel_article)
    db.commit()
    db.refresh(nouvel_article)
    return nouvel_article


def get_articles(db: Session, boutique_id: int, skip: int = 0, limit: int = 50):
    return (
        db.query(Article)
        .filter(Article.boutique_id == boutique_id)
        .offset(skip).limit(limit).all()
    )


def get_article(db: Session, article_id: int, boutique_id: int):
    return db.query(Article).filter(
        Article.id == article_id,
        Article.boutique_id == boutique_id,
    ).first()


def get_nb_articles_boutique(db: Session, boutique_id: int) -> int:
    return db.query(Article).filter(Article.boutique_id == boutique_id).count()


# ============================================================
# MOUVEMENTS DE STOCK
# ============================================================

def enregistrer_mouvement(
    db: Session, boutique_id: int, article_id: int,
    type_mouvement: str, quantite: int, prix_unitaire: float,
):
    mouvement = StockMovement(
        boutique_id=boutique_id, article_id=article_id,
        movement_type=type_mouvement, quantity=quantite,
        unit_price=prix_unitaire,
        created_at=datetime.now(timezone.utc),
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
        .offset(skip).limit(limit).all()
    )


def get_movements_by_date(db: Session, boutique_id: int, date_debut: datetime,
                           skip: int = 0, limit: int = 100):
    return (
        db.query(StockMovement)
        .filter(StockMovement.boutique_id == boutique_id,
                StockMovement.created_at >= date_debut)
        .order_by(StockMovement.created_at.desc())
        .offset(skip).limit(limit).all()
    )


# ============================================================
# STOCK
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
    prix_de_vente = article.price_vente
    enregistrer_mouvement(db, boutique_id, article_id, "OUT", quantite, prix_de_vente)
    db.commit()
    db.refresh(article)
    benefice = (article.price_vente - article.price_achat) * quantite
    return {"article": article, "benefice_de_la_vente": round(benefice, 2)}


# ============================================================
# PROFITS
# ============================================================

def get_article_profit(db: Session, article_id: int, boutique_id: int):
    article = get_article(db, article_id, boutique_id)
    if not article:
        return None
    ventes = db.query(StockMovement).filter(
        StockMovement.article_id == article_id,
        StockMovement.boutique_id == boutique_id,
        StockMovement.movement_type == "OUT",
    ).all()
    benefice_total = sum(
        (v.unit_price - article.price_achat) * v.quantity for v in ventes
    )
    return {"article_id": article_id, "benefice_total": round(benefice_total, 2)}


def get_total_profit_boutique(db: Session, boutique_id: int) -> float:
    resultat = (
        db.query(func.sum(
            (StockMovement.unit_price - Article.price_achat) * StockMovement.quantity
        ))
        .join(Article, Article.id == StockMovement.article_id)
        .filter(StockMovement.movement_type == "OUT",
                StockMovement.boutique_id == boutique_id)
        .scalar()
    )
    return round(resultat or 0.0, 2)


def get_ventes_du_mois_boutique(db: Session, boutique_id: int) -> int:
    il_y_a_30_jours = datetime.now(timezone.utc) - timedelta(days=30)
    return db.query(StockMovement).filter(
        StockMovement.boutique_id == boutique_id,
        StockMovement.movement_type == "OUT",
        StockMovement.created_at >= il_y_a_30_jours,
    ).count()


def get_articles_en_alerte_boutique(db: Session, boutique_id: int):
    return db.query(Article).filter(
        Article.boutique_id == boutique_id,
        Article.quantity <= Article.low_stock_threshold,
    ).all()


# ============================================================
# CRÉDITS VENTES
# ============================================================

def _calculer_statut(montant_paye: float, montant_total: float, date_echeance: datetime) -> str:
    """Calcule le statut selon les montants et la date d'échéance."""
    if montant_paye >= montant_total:
        return "solde"
    maintenant = datetime.now(timezone.utc)
    if date_echeance.tzinfo is None:
        date_echeance = date_echeance.replace(tzinfo=timezone.utc)
    if maintenant > date_echeance:
        return "en_retard"
    if montant_paye > 0:
        return "partiellement_paye"
    return "en_cours"


def creer_vente_credit(db: Session, directeur, data) -> VenteCredit:
    vente = VenteCredit(
        boutique_id       = directeur.boutique_id,
        directeur_id      = directeur.id,
        client_nom        = data.client_nom,
        client_entreprise = data.client_entreprise,
        client_telephone  = data.client_telephone,
        client_adresse    = data.client_adresse,
        montant_total     = data.montant_total,
        montant_paye      = 0.0,
        montant_restant   = data.montant_total,
        date_echeance     = data.date_echeance,
        statut            = "en_cours",
        note              = data.note,
    )
    db.add(vente)
    db.commit()
    db.refresh(vente)
    return vente


def get_ventes_credit(db: Session, boutique_id: int, statut: str | None = None):
    requete = db.query(VenteCredit).filter(VenteCredit.boutique_id == boutique_id)
    if statut:
        requete = requete.filter(VenteCredit.statut == statut)
    return requete.order_by(VenteCredit.date_echeance.asc()).all()


def get_vente_credit(db: Session, vente_id: int, boutique_id: int):
    return db.query(VenteCredit).filter(
        VenteCredit.id == vente_id,
        VenteCredit.boutique_id == boutique_id,
    ).first()


def enregistrer_paiement_recu(
    db: Session, vente_id: int, directeur, montant: float, note: str | None
) -> PaiementRecu | None:
    vente = db.query(VenteCredit).filter(VenteCredit.id == vente_id).first()
    if not vente:
        return None

    # Plafonner le paiement au montant restant
    montant_effectif = min(montant, vente.montant_restant)

    paiement = PaiementRecu(
        vente_credit_id = vente_id,
        directeur_id    = directeur.id,
        montant_verse   = montant_effectif,
        note            = note,
    )
    db.add(paiement)

    vente.montant_paye    += montant_effectif
    vente.montant_restant  = vente.montant_total - vente.montant_paye
    vente.statut           = _calculer_statut(vente.montant_paye, vente.montant_total, vente.date_echeance)

    db.commit()
    db.refresh(paiement)
    return paiement


# ============================================================
# CRÉDITS ACHATS
# ============================================================

def creer_achat_credit(db: Session, directeur, data) -> AchatCredit:
    achat = AchatCredit(
        boutique_id            = directeur.boutique_id,
        directeur_id           = directeur.id,
        fournisseur_nom        = data.fournisseur_nom,
        fournisseur_entreprise = data.fournisseur_entreprise,
        fournisseur_telephone  = data.fournisseur_telephone,
        fournisseur_adresse    = data.fournisseur_adresse,
        montant_total          = data.montant_total,
        montant_paye           = 0.0,
        montant_restant        = data.montant_total,
        date_echeance          = data.date_echeance,
        statut                 = "en_cours",
        note                   = data.note,
    )
    db.add(achat)
    db.commit()
    db.refresh(achat)
    return achat


def get_achats_credit(db: Session, boutique_id: int, statut: str | None = None):
    requete = db.query(AchatCredit).filter(AchatCredit.boutique_id == boutique_id)
    if statut:
        requete = requete.filter(AchatCredit.statut == statut)
    return requete.order_by(AchatCredit.date_echeance.asc()).all()


def get_achat_credit(db: Session, achat_id: int, boutique_id: int):
    return db.query(AchatCredit).filter(
        AchatCredit.id == achat_id,
        AchatCredit.boutique_id == boutique_id,
    ).first()


def enregistrer_paiement_effectue(
    db: Session, achat_id: int, directeur, montant: float, note: str | None
) -> PaiementEffectue | None:
    achat = db.query(AchatCredit).filter(AchatCredit.id == achat_id).first()
    if not achat:
        return None

    montant_effectif = min(montant, achat.montant_restant)

    paiement = PaiementEffectue(
        achat_credit_id = achat_id,
        directeur_id    = directeur.id,
        montant_verse   = montant_effectif,
        note            = note,
    )
    db.add(paiement)

    achat.montant_paye    += montant_effectif
    achat.montant_restant  = achat.montant_total - achat.montant_paye
    achat.statut           = _calculer_statut(achat.montant_paye, achat.montant_total, achat.date_echeance)

    db.commit()
    db.refresh(paiement)
    return paiement


# ============================================================
# RÉSUMÉ CRÉDITS PAR BOUTIQUE
# ============================================================

def get_resume_credits_boutique(db: Session, boutique_id: int) -> dict:
    ventes_actives = db.query(VenteCredit).filter(
        VenteCredit.boutique_id == boutique_id,
        VenteCredit.statut != "solde",
    ).all()

    achats_actifs = db.query(AchatCredit).filter(
        AchatCredit.boutique_id == boutique_id,
        AchatCredit.statut != "solde",
    ).all()

    total_a_encaisser   = sum(v.montant_restant for v in ventes_actives)
    total_a_payer       = sum(a.montant_restant for a in achats_actifs)
    nb_en_retard_ventes = sum(1 for v in ventes_actives if v.statut == "en_retard")
    nb_en_retard_achats = sum(1 for a in achats_actifs if a.statut == "en_retard")

    return {
        "boutique_id"         : boutique_id,
        "total_a_encaisser"   : round(total_a_encaisser, 2),
        "nb_clients_debiteurs": len(ventes_actives),
        "nb_en_retard_ventes" : nb_en_retard_ventes,
        "total_a_payer"       : round(total_a_payer, 2),
        "nb_fournisseurs_dus" : len(achats_actifs),
        "nb_en_retard_achats" : nb_en_retard_achats,
        "solde_net_credit"    : round(total_a_encaisser - total_a_payer, 2),
    }


# ============================================================
# AGRÉGATS PDG — toutes boutiques
# ============================================================

def get_benefice_total_entreprise(db: Session) -> float:
    resultat = (
        db.query(func.sum(
            (StockMovement.unit_price - Article.price_achat) * StockMovement.quantity
        ))
        .join(Article, Article.id == StockMovement.article_id)
        .filter(StockMovement.movement_type == "OUT")
        .scalar()
    )
    return round(resultat or 0.0, 2)


def get_ventes_totales_du_mois(db: Session) -> int:
    il_y_a_30_jours = datetime.now(timezone.utc) - timedelta(days=30)
    return db.query(StockMovement).filter(
        StockMovement.movement_type == "OUT",
        StockMovement.created_at >= il_y_a_30_jours,
    ).count()


def get_nb_articles_en_alerte_total(db: Session) -> int:
    return db.query(Article).filter(
        Article.quantity <= Article.low_stock_threshold
    ).count()


def get_total_a_encaisser_entreprise(db: Session) -> float:
    resultat = db.query(func.sum(VenteCredit.montant_restant)).filter(
        VenteCredit.statut != "solde"
    ).scalar()
    return round(resultat or 0.0, 2)


def get_total_a_payer_entreprise(db: Session) -> float:
    resultat = db.query(func.sum(AchatCredit.montant_restant)).filter(
        AchatCredit.statut != "solde"
    ).scalar()
    return round(resultat or 0.0, 2)


def get_nb_credits_en_retard(db: Session) -> int:
    retard_ventes = db.query(VenteCredit).filter(VenteCredit.statut == "en_retard").count()
    retard_achats = db.query(AchatCredit).filter(AchatCredit.statut == "en_retard").count()
    return retard_ventes + retard_achats


def get_activite_recente(db: Session, limite: int = 10):
    mouvements = (
        db.query(StockMovement, Article, Boutique)
        .join(Article, Article.id == StockMovement.article_id)
        .join(Boutique, Boutique.id == StockMovement.boutique_id)
        .order_by(StockMovement.created_at.desc())
        .limit(limite).all()
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
    date_debut = datetime.now(timezone.utc) - timedelta(days=nb_jours)
    mouvements = (
        db.query(StockMovement, Article)
        .join(Article, Article.id == StockMovement.article_id)
        .filter(StockMovement.movement_type == "OUT",
                StockMovement.created_at >= date_debut)
        .all()
    )
    par_jour: dict[str, dict] = {}
    for mouvement, article in mouvements:
        cle  = mouvement.created_at.strftime("%Y-%m-%d")
        ben  = (mouvement.unit_price - article.price_achat) * mouvement.quantity
        if cle not in par_jour:
            par_jour[cle] = {"date": cle, "nb_ventes": 0, "benefice_jour": 0.0}
        par_jour[cle]["nb_ventes"]     += mouvement.quantity
        par_jour[cle]["benefice_jour"] += ben
    resultat = sorted(par_jour.values(), key=lambda x: x["date"])
    for p in resultat:
        p["benefice_jour"] = round(p["benefice_jour"], 2)
    return resultat
