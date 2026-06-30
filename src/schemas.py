from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


# ============================================================
# AUTHENTIFICATION & PROFILS
# ============================================================

class DemandeConnexion(BaseModel):
    nom_utilisateur : str
    mot_de_passe    : str


class DemandeCreationUtilisateur(BaseModel):
    """Création d'un compte avec identité complète (obligatoire pour traçabilité)."""
    nom_utilisateur     : str = Field(min_length=3, max_length=50)
    mot_de_passe        : str = Field(min_length=6)
    role                : str = Field(pattern="^(pdg|directeur|vendeur)$")
    prenom              : str = Field(min_length=1, max_length=50)
    nom_famille         : str = Field(min_length=1, max_length=50)
    telephone           : str = Field(min_length=8, max_length=20)
    adresse_personnelle : str | None = None


class DemandeAjouterDirecteur(BaseModel):
    nom_utilisateur     : str = Field(min_length=3, max_length=50)
    mot_de_passe        : str = Field(min_length=6)
    prenom              : str = Field(min_length=1, max_length=50)
    nom_famille         : str = Field(min_length=1, max_length=50)
    telephone           : str = Field(min_length=8, max_length=20)
    adresse_personnelle : str | None = None


class DemandeAjouterVendeur(BaseModel):
    nom_utilisateur     : str = Field(min_length=3, max_length=50)
    mot_de_passe        : str = Field(min_length=6)
    prenom              : str = Field(min_length=1, max_length=50)
    nom_famille         : str = Field(min_length=1, max_length=50)
    telephone           : str = Field(min_length=8, max_length=20)
    adresse_personnelle : str | None = None


class ReponseToken(BaseModel):
    access_token : str
    type_token   : str = "bearer"


class ReponseUtilisateur(BaseModel):
    id                   : int
    nom_utilisateur      : str
    prenom               : str
    nom_famille          : str
    telephone            : str
    adresse_personnelle  : str | None = None
    role                 : str
    boutique_id          : int | None = None
    est_actif            : bool
    permissions          : list[str] = []
    date_creation_compte : datetime

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


# ============================================================
# PERMISSIONS
# ============================================================

class DemandeModifierPermissions(BaseModel):
    permissions : list[str]


class ReponsePermissions(BaseModel):
    directeur_id           : int
    nom_utilisateur        : str
    boutique_id            : int | None
    est_actif              : bool
    permissions            : list[str]
    permissions_manquantes : list[str]

    class Config:
        from_attributes = True


# ============================================================
# CRÉDITS VENTES — le client doit de l'argent
# ============================================================

class DemandeVenteCredit(BaseModel):
    # Identité du client
    client_nom        : str   = Field(min_length=2)
    client_entreprise : str | None = None
    client_telephone  : str   = Field(min_length=8)
    client_adresse    : str | None = None
    # Transaction
    montant_total     : float = Field(gt=0)
    date_echeance     : datetime
    note              : str | None = None


class DemandePaiementRecu(BaseModel):
    montant_verse : float = Field(gt=0, description="Montant versé par le client (doit être > 0)")
    note          : str | None = None


class ReponseVenteCredit(BaseModel):
    id                : int
    boutique_id       : int
    directeur_id      : int
    client_nom        : str
    client_entreprise : str | None
    client_telephone  : str
    client_adresse    : str | None
    montant_total     : float
    montant_paye      : float
    montant_restant   : float
    date_vente        : datetime
    date_echeance     : datetime
    statut            : str
    note              : str | None

    class Config:
        from_attributes = True


class ReponsePaiementRecu(BaseModel):
    id              : int
    vente_credit_id : int
    directeur_id    : int
    montant_verse   : float
    date_paiement   : datetime
    note            : str | None

    class Config:
        from_attributes = True


# ============================================================
# CRÉDITS ACHATS — la boutique doit de l'argent au fournisseur
# ============================================================

class DemandeAchatCredit(BaseModel):
    # Identité du fournisseur
    fournisseur_nom       : str   = Field(min_length=2)
    fournisseur_entreprise: str | None = None
    fournisseur_telephone : str   = Field(min_length=8)
    fournisseur_adresse   : str | None = None
    # Transaction
    montant_total         : float = Field(gt=0)
    date_echeance         : datetime
    note                  : str | None = None


class DemandePaiementEffectue(BaseModel):
    montant_verse : float = Field(gt=0)
    note          : str | None = None


class ReponseAchatCredit(BaseModel):
    id                     : int
    boutique_id            : int
    directeur_id           : int
    fournisseur_nom        : str
    fournisseur_entreprise : str | None
    fournisseur_telephone  : str
    fournisseur_adresse    : str | None
    montant_total          : float
    montant_paye           : float
    montant_restant        : float
    date_achat             : datetime
    date_echeance          : datetime
    statut                 : str
    note                   : str | None

    class Config:
        from_attributes = True


class ReponsePaiementEffectue(BaseModel):
    id              : int
    achat_credit_id : int
    directeur_id    : int
    montant_verse   : float
    date_paiement   : datetime
    note            : str | None

    class Config:
        from_attributes = True


class ResumeCredits(BaseModel):
    """Résumé financier des crédits d'une boutique."""
    boutique_id          : int
    # Ce que les clients doivent
    total_a_encaisser    : float   # somme des montants_restants (ventes crédit)
    nb_clients_debiteurs : int
    nb_en_retard_ventes  : int
    # Ce que la boutique doit
    total_a_payer        : float   # somme des montants_restants (achats crédit)
    nb_fournisseurs_dus  : int
    nb_en_retard_achats  : int
    # Solde net
    solde_net_credit     : float   # total_a_encaisser - total_a_payer


# ============================================================
# JOURNAL D'ACTIVITÉ
# ============================================================

class EntreeJournal(BaseModel):
    id              : int
    utilisateur_id  : int
    nom_utilisateur : str
    nom_complet     : str
    boutique_id     : int | None
    boutique_nom    : str | None
    action          : str
    details         : Any | None
    date_heure      : datetime

    class Config:
        from_attributes = True


# ============================================================
# DASHBOARD PDG
# ============================================================

class StatsBoutique(BaseModel):
    boutique             : ReponseBoutique
    nb_articles          : int
    nb_vendeurs          : int
    benefice_total       : float
    ventes_du_mois       : int
    total_a_encaisser    : float
    total_a_payer        : float


class MouvementRecent(BaseModel):
    boutique_nom   : str
    article_nom    : str
    type_mouvement : str
    quantite       : int
    date           : datetime


class DashboardPDG(BaseModel):
    nb_boutiques                : int
    nb_boutiques_actives        : int
    benefice_total_entreprise   : float
    ventes_totales_du_mois      : int
    articles_en_alerte          : int
    total_a_encaisser_entreprise: float
    total_a_payer_entreprise    : float
    solde_net_credit_entreprise : float
    credits_en_retard           : int
    classement_boutiques        : list[StatsBoutique]
    activite_recente            : list[MouvementRecent]


class PointEvolution(BaseModel):
    date          : str
    nb_ventes     : int
    benefice_jour : float


# ============================================================
# ARTICLES & MOUVEMENTS
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
