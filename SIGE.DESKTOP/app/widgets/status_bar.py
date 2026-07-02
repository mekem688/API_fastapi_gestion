"""
widgets/status_bar.py — Bannière d'état de connexion (en ligne / hors-ligne)

Affichée en haut de chaque fenêtre principale. Change de couleur et de
texte selon l'état réseau, et affiche le nombre de ventes en attente
de synchronisation quand l'app est hors-ligne.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from ..config import COULEUR_SUCCES, COULEUR_ALERTE
from ..services import local_db


class BanniereConnexion(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.afficher_en_ligne()

    def afficher_en_ligne(self) -> None:
        self.setText("🟢 En ligne")
        self.setStyleSheet(f"background-color:{COULEUR_SUCCES}; color:white; font-size:12px;")

    def afficher_hors_ligne(self) -> None:
        nb_en_attente = local_db.compter_ventes_en_attente()
        texte = "🟡 Mode hors-ligne"
        if nb_en_attente:
            texte += f" — {nb_en_attente} vente(s) en attente de synchronisation"
        self.setText(texte)
        self.setStyleSheet(f"background-color:{COULEUR_ALERTE}; color:white; font-size:12px;")

    def afficher_synchronisation_reussie(self, nb_ventes: int) -> None:
        if nb_ventes > 0:
            self.setText(f"✅ {nb_ventes} vente(s) synchronisée(s) avec le serveur")
            self.setStyleSheet(f"background-color:{COULEUR_SUCCES}; color:white; font-size:12px;")
        else:
            self.afficher_en_ligne()
