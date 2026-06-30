from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================
# AUTHENTIFICATION
# ============================================================

class DemandeConnexion(BaseModel):
    nom_utilisateur : str
    mot_de_passe    : str


class DemandeCreationUtilisateur(BaseModel):
    nom_utilisateur : str = Field(min_length=3, max_length=50)
    mot_de_passe    : str = Field(min_length=6)
    role            : str = Field(pattern="^(pdg|directeur|vendeur)$")


class ReponseToken(BaseModel):
    access_token : str
    type_token   : str = "bearer"


class ReponseUtilisateur(BaseModel):
    id              : int
    nom_utilisateur : str
    role            : str
    boutique_id     : int | None = None
    est_actif       : bool
    permissions     : list[str] = []

    class Config:
        from_attributes = True


# ============================================================
# BOUTIQUES
# ============================================================

class DemandeCréerBoutique(BaseModel):
    nom     : str = Field(min_length=2, max_length=100)
    ville   : str = Field(min_length=2, max_length=100)
    adresse : str | None = None


class ReponseBoutique(BaseModel):
    id            : int
    nom           : str
    ville         : str
    adresse       : str | None
    est_active    : bool
    date_creation : datetime

    class Config:
        from_attributes = True


class DemandeAjouterDirecteur(BaseModel):
    nom_utilisateur : str = Field(min_length=3, max_length=50)
    mot_de_passe    : str = Field(min_length=6)


class DemandeAjouterVendeur(BaseModel):
    nom_utilisateur : str = Field(min_length=3, max_length=50)
    mot_de_passe    : str = Field(min_length=6)


# ============================================================
# PERMISSIONS
# ============================================================

class DemandeModifierPermissions(BaseModel):
    """
    Le PDG envoie la liste complète des permissions accordées au directeur.
    Exemple : ["voir_profits", "faire_achats"]
    Pour tout bloquer : []
    Pour tout accorder : ["voir_profits", "faire_achats", "creer_articles", "voir_alertes", "gerer_vendeurs"]
    """
    permissions : list[str] = Field(
        description="Liste des permissions. Valeurs possibles : voir_profits, faire_achats, creer_articles, voir_alertes, gerer_vendeurs"
    )


class ReponsePermissions(BaseModel):
    """Résumé des droits d'un directeur."""
    directeur_id    : int
    nom_utilisateur : str
    boutique_id     : int | None
    est_actif       : bool
    permissions     : list[str]
    permissions_manquantes : list[str]   # droits qu'il n'a PAS

    class Config:
        from_attributes = True


# ============================================================
# DASHBOARD PDG
# ============================================================

class StatsBoutique(BaseModel):
    boutique       : ReponseBoutique
    nb_articles    : int
    nb_vendeurs    : int
    benefice_total : float
    ventes_du_mois : int


class MouvementRecent(BaseModel):
    boutique_nom   : str
    article_nom    : str
    type_mouvement : str
    quantite       : int
    date           : datetime


class DashboardPDG(BaseModel):
    nb_boutiques              : int
    nb_boutiques_actives      : int
    benefice_total_entreprise : float
    ventes_totales_du_mois    : int
    articles_en_alerte        : int
    classement_boutiques      : list[StatsBoutique]
    activite_recente          : list[MouvementRecent]


class PointEvolution(BaseModel):
    date          : str
    nb_ventes     : int
    benefice_jour : float


# ============================================================
# ARTICLES
# ============================================================

class ArticleCreate(BaseModel):
    name                : str
    description         : str | None = None
    price_achat         : float = Field(gt=0)
    price_vente         : float = Field(gt=0)
    low_stock_threshold : int   = Field(default=5, ge=0)


class ArticleResponse(ArticleCreate):
    id          : int
    boutique_id : int
    quantity    : int

    class Config:
        from_attributes = True


# ============================================================
# MOUVEMENTS DE STOCK
# ============================================================

class MovementResponse(BaseModel):
    id            : int
    boutique_id   : int
    article_id    : int
    movement_type : str
    quantity      : int
    unit_price    : float
    created_at    : datetime

    class Config:
        from_attributes = True
