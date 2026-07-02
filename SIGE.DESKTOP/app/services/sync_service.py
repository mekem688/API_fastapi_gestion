"""
services/sync_service.py — Synchronisation hors-ligne / en ligne

Un QTimer vérifie la connexion toutes les INTERVALLE_PING_MS millisecondes.
À chaque reconnexion détectée, les ventes locales en attente sont envoyées
au serveur. Le serveur a toujours la priorité : une fois synchronisée,
une vente locale n'est jamais renvoyée à nouveau (statut 'synchronise').

Émet des signaux Qt pour que l'interface puisse afficher une bannière
"hors-ligne" ou une notification de succès.
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from ..config import INTERVALLE_PING_MS
from . import local_db
from .api_client import client_api, ErreurConnexionAPI


class ServiceSynchronisation(QObject):
    connexion_retablie = pyqtSignal(int)   # nombre de ventes synchronisées
    connexion_perdue    = pyqtSignal()
    etat_change         = pyqtSignal(bool)  # True = en ligne, False = hors-ligne

    def __init__(self):
        super().__init__()
        self._en_ligne_precedemment = True
        self._minuteur = QTimer()
        self._minuteur.timeout.connect(self._verifier_connexion)

    def demarrer(self) -> None:
        self._minuteur.start(INTERVALLE_PING_MS)
        self._verifier_connexion()

    def arreter(self) -> None:
        self._minuteur.stop()

    def _verifier_connexion(self) -> None:
        en_ligne = client_api.est_en_ligne()

        if en_ligne and not self._en_ligne_precedemment:
            # On vient de retrouver internet → on synchronise
            nb_synchronisees = self._synchroniser_ventes_en_attente()
            self.connexion_retablie.emit(nb_synchronisees)

        if not en_ligne and self._en_ligne_precedemment:
            self.connexion_perdue.emit()

        if en_ligne != self._en_ligne_precedemment:
            self.etat_change.emit(en_ligne)

        self._en_ligne_precedemment = en_ligne

    def _synchroniser_ventes_en_attente(self) -> int:
        """Envoie chaque vente en attente au serveur. Priorité totale au serveur."""
        ventes_en_attente = local_db.lister_ventes_en_attente()
        nb_reussies = 0

        for vente in ventes_en_attente:
            try:
                client_api.sortie_stock(vente["article_id"], vente["quantite"])
                local_db.marquer_vente_synchronisee(vente["id_local"])
                nb_reussies += 1
            except (ErreurConnexionAPI, ValueError):
                # On s'arrête au premier échec — on réessaiera au prochain ping
                break

        return nb_reussies


service_sync = ServiceSynchronisation()
