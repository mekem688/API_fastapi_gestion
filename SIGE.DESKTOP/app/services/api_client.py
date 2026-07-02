"""
services/api_client.py — Client HTTP vers l'API FastAPI (API_fastapi_gestion)

Toutes les requêtes réseau de l'application passent par cette classe.
Elle gère automatiquement :
  - l'ajout du token JWT dans l'en-tête Authorization
  - la détection d'une coupure réseau (ConnectionError, Timeout)
"""

import requests

from ..config import API_URL


class ErreurConnexionAPI(Exception):
    """Levée quand l'API est injoignable (pas d'internet, serveur éteint, etc.)."""
    pass


class ClientAPI:
    def __init__(self):
        self.token: str | None = None

    def definir_token(self, token: str) -> None:
        self.token = token

    def _entetes(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _url(self, chemin: str) -> str:
        return f"{API_URL}{chemin}"

    def _traiter_erreurs_reseau(self, appel):
        try:
            return appel()
        except (requests.ConnectionError, requests.Timeout) as erreur:
            raise ErreurConnexionAPI("Impossible de joindre le serveur.") from erreur

    # ------------------------------------------------------------------
    # Vérification de la connexion (utilisée par le service de sync)
    # ------------------------------------------------------------------

    def est_en_ligne(self) -> bool:
        try:
            reponse = requests.get(self._url("/"), timeout=3)
            return reponse.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    # ------------------------------------------------------------------
    # Authentification
    # ------------------------------------------------------------------

    def connexion(self, nom_utilisateur: str, mot_de_passe: str) -> dict:
        def appel():
            reponse = requests.post(
                self._url("/auth/connexion"),
                json={"nom_utilisateur": nom_utilisateur, "mot_de_passe": mot_de_passe},
                timeout=8,
            )
            if reponse.status_code != 200:
                detail = reponse.json().get("detail", "Identifiants incorrects.")
                raise ValueError(detail)
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def profil_utilisateur(self) -> dict:
        def appel():
            reponse = requests.get(self._url("/auth/moi"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    # ------------------------------------------------------------------
    # Articles et stock (directeur / vendeur)
    # ------------------------------------------------------------------

    def lister_articles(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/articles/"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def creer_article(self, donnees: dict) -> dict:
        def appel():
            reponse = requests.post(self._url("/articles/"), json=donnees, headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def sortie_stock(self, article_id: int, quantite: int) -> dict:
        def appel():
            reponse = requests.post(
                self._url(f"/articles/{article_id}/stock/out"),
                params={"quantite": quantite},
                headers=self._entetes(), timeout=8,
            )
            if reponse.status_code != 200:
                detail = reponse.json().get("detail", "Vente impossible.")
                raise ValueError(detail)
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def entree_stock(self, article_id: int, quantite: int) -> dict:
        def appel():
            reponse = requests.post(
                self._url(f"/articles/{article_id}/stock/in"),
                params={"quantite": quantite},
                headers=self._entetes(), timeout=8,
            )
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def alertes_stock_faible(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/articles/alerts/low-stock"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def profit_total(self) -> dict:
        def appel():
            reponse = requests.get(self._url("/articles/profit/total"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    # ------------------------------------------------------------------
    # Crédits (directeur)
    # ------------------------------------------------------------------

    def resume_credits(self) -> dict:
        def appel():
            reponse = requests.get(self._url("/credits/resume"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def lister_ventes_credit(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/credits/ventes"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def creer_vente_credit(self, donnees: dict) -> dict:
        def appel():
            reponse = requests.post(self._url("/credits/ventes"), json=donnees, headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def paiement_vente_credit(self, vente_id: int, montant: float, note: str | None = None) -> dict:
        def appel():
            reponse = requests.post(
                self._url(f"/credits/ventes/{vente_id}/paiement"),
                json={"montant_verse": montant, "note": note},
                headers=self._entetes(), timeout=8,
            )
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def lister_achats_credit(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/credits/achats"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def creer_achat_credit(self, donnees: dict) -> dict:
        def appel():
            reponse = requests.post(self._url("/credits/achats"), json=donnees, headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def paiement_achat_credit(self, achat_id: int, montant: float, note: str | None = None) -> dict:
        def appel():
            reponse = requests.post(
                self._url(f"/credits/achats/{achat_id}/paiement"),
                json={"montant_verse": montant, "note": note},
                headers=self._entetes(), timeout=8,
            )
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    # ------------------------------------------------------------------
    # Journal
    # ------------------------------------------------------------------

    def journal_boutique(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/credits/journal"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def journal_global(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/pdg/journal"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    # ------------------------------------------------------------------
    # En-tête de facture personnalisable (DG)
    # ------------------------------------------------------------------

    def lire_config_facture(self) -> dict | None:
        def appel():
            reponse = requests.get(self._url("/credits/config-facture"), headers=self._entetes(), timeout=8)
            if reponse.status_code == 404:
                return None
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def enregistrer_config_facture(self, donnees: dict) -> dict:
        def appel():
            reponse = requests.put(self._url("/credits/config-facture"), json=donnees, headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def config_facture_pour_impression(self) -> dict:
        def appel():
            reponse = requests.get(self._url("/credits/config-facture/impression"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    # ------------------------------------------------------------------
    # PDG — vue entreprise
    # ------------------------------------------------------------------

    def dashboard_pdg(self) -> dict:
        def appel():
            reponse = requests.get(self._url("/pdg/dashboard"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def lister_boutiques(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/pdg/boutiques"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def classement_boutiques(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/pdg/classement"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def credits_entreprise(self) -> list[dict]:
        def appel():
            reponse = requests.get(self._url("/pdg/credits"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def equipe_boutique(self, boutique_id: int) -> list[dict]:
        def appel():
            reponse = requests.get(self._url(f"/pdg/boutiques/{boutique_id}/equipe"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def suspendre_utilisateur(self, utilisateur_id: int) -> dict:
        def appel():
            reponse = requests.put(self._url(f"/pdg/directeurs/{utilisateur_id}/suspendre"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)

    def reactiver_utilisateur(self, utilisateur_id: int) -> dict:
        def appel():
            reponse = requests.put(self._url(f"/pdg/directeurs/{utilisateur_id}/reactiver"), headers=self._entetes(), timeout=8)
            reponse.raise_for_status()
            return reponse.json()
        return self._traiter_erreurs_reseau(appel)


# Instance unique partagée par toute l'application
client_api = ClientAPI()
