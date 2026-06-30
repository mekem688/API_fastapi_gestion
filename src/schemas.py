from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================
# AUTHENTIFICATION
# ============================================================

class DemandeConnexion(BaseModel):
    """Données envoyées lors d'une connexion."""
    nom_utilisateur : str
    mot_de_passe    : str


class DemandeCreationUtilisateur(BaseModel):
    """Données pour créer un nouvel utilisateur."""
    nom_utilisateur : str = Field(min_length=3, max_length=50)
    mot_de_passe    : str = Field(min_length=6)
    role            : str = Field(pattern="^(vendeur|directeur)$")
    #                              ^ doit être exactement "vendeur" ou "directeur"


class ReponseToken(BaseModel):
    """Réponse renvoyée après une connexion réussie."""
    access_token : str        # le token JWT à utiliser dans les prochaines requêtes
    type_token   : str = "bearer"


class ReponseUtilisateur(BaseModel):
    """Informations d'un utilisateur (sans le mot de passe)."""
    id              : int
    nom_utilisateur : str
    role            : str

    class Config:
        from_attributes = True


# ============================================================
# ARTICLES
# ============================================================

class ArticleBase(BaseModel):
    name                : str
    description         : str | None = None
    price_achat         : float = Field(gt=0)
    price_vente         : float = Field(gt=0)
    low_stock_threshold : int   = Field(default=5, ge=0)


class ArticleCreate(ArticleBase):
    pass


class ArticleResponse(ArticleBase):
    id       : int
    quantity : int

    class Config:
        from_attributes = True


# ============================================================
# MOUVEMENTS DE STOCK
# ============================================================

class MovementResponse(BaseModel):
    id            : int
    article_id    : int
    movement_type : str
    quantity      : int
    unit_price    : float
    created_at    : datetime

    class Config:
        from_attributes = True
