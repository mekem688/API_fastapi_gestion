"""
windows/login_window.py — Écran de connexion

Point d'entrée visuel de l'application. Après connexion réussie,
redirige automatiquement vers la bonne fenêtre selon le rôle renvoyé
par l'API : pdg → FenetrePDG, directeur → FenetreDG, vendeur → FenetreVendeur.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

from ..config import API_URL, COULEUR_FOND, COULEUR_PRIMAIRE, COULEUR_TEXTE_DOUX, COULEUR_DANGER
from ..services.api_client import client_api, ErreurConnexionAPI
from ..services import local_db


class FenetreConnexion(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIGE.DESKTOP — Connexion")
        self.setFixedSize(420, 480)
        self.setStyleSheet(f"background-color: {COULEUR_FOND};")

        self.fenetre_principale = None  # référence gardée pour éviter le garbage collector

        self._construire_interface()

    def _construire_interface(self) -> None:
        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(50, 50, 50, 30)
        disposition.setSpacing(14)

        titre = QLabel("SIGE")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COULEUR_PRIMAIRE};")

        sous_titre = QLabel("Système Intégré de Gestion d'Entreprise")
        sous_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sous_titre.setStyleSheet(f"font-size: 12px; color: {COULEUR_TEXTE_DOUX}; margin-bottom: 20px;")

        self.champ_utilisateur = QLineEdit()
        self.champ_utilisateur.setPlaceholderText("Nom d'utilisateur")
        self.champ_utilisateur.setStyleSheet(self._style_champ())

        self.champ_mot_de_passe = QLineEdit()
        self.champ_mot_de_passe.setPlaceholderText("Mot de passe")
        self.champ_mot_de_passe.setEchoMode(QLineEdit.EchoMode.Password)
        self.champ_mot_de_passe.setStyleSheet(self._style_champ())
        self.champ_mot_de_passe.returnPressed.connect(self._tenter_connexion)

        self.bouton_connexion = QPushButton("Se connecter")
        self.bouton_connexion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bouton_connexion.setStyleSheet(f"""
            QPushButton {{
                background-color: {COULEUR_PRIMAIRE};
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #2C5282; }}
        """)
        self.bouton_connexion.clicked.connect(self._tenter_connexion)

        self.etiquette_erreur = QLabel("")
        self.etiquette_erreur.setStyleSheet(f"color: {COULEUR_DANGER}; font-size: 12px;")
        self.etiquette_erreur.setWordWrap(True)
        self.etiquette_erreur.setAlignment(Qt.AlignmentFlag.AlignCenter)

        etiquette_url = QLabel(f"API : {API_URL}")
        etiquette_url.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiquette_url.setStyleSheet(f"color: {COULEUR_TEXTE_DOUX}; font-size: 10px; margin-top: 20px;")

        disposition.addWidget(titre)
        disposition.addWidget(sous_titre)
        disposition.addWidget(self.champ_utilisateur)
        disposition.addWidget(self.champ_mot_de_passe)
        disposition.addWidget(self.etiquette_erreur)
        disposition.addWidget(self.bouton_connexion)
        disposition.addStretch()
        disposition.addWidget(etiquette_url)

    @staticmethod
    def _style_champ() -> str:
        return """
            QLineEdit {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus { border: 1px solid #1E3A5F; }
        """

    def _tenter_connexion(self) -> None:
        nom_utilisateur = self.champ_utilisateur.text().strip()
        mot_de_passe = self.champ_mot_de_passe.text()

        if not nom_utilisateur or not mot_de_passe:
            self.etiquette_erreur.setText("Veuillez remplir tous les champs.")
            return

        self.etiquette_erreur.setText("")
        self.bouton_connexion.setEnabled(False)
        self.bouton_connexion.setText("Connexion...")

        try:
            reponse = client_api.connexion(nom_utilisateur, mot_de_passe)
            client_api.definir_token(reponse["access_token"])
            profil = client_api.profil_utilisateur()

            local_db.sauvegarder_session(reponse["access_token"], profil["nom_utilisateur"], profil["role"])

            self._rediriger_selon_role(profil)

        except ValueError as erreur:
            self.etiquette_erreur.setText(str(erreur))
        except ErreurConnexionAPI:
            self.etiquette_erreur.setText(
                "Impossible de joindre le serveur. Vérifiez votre connexion internet."
            )
        finally:
            self.bouton_connexion.setEnabled(True)
            self.bouton_connexion.setText("Se connecter")

    def _rediriger_selon_role(self, profil: dict) -> None:
        role = profil["role"]

        if role == "pdg":
            from .pdg_window import FenetrePDG
            self.fenetre_principale = FenetrePDG(profil)
        elif role == "directeur":
            from .dg_window import FenetreDG
            self.fenetre_principale = FenetreDG(profil)
        elif role == "vendeur":
            from .vendeur_window import FenetreVendeur
            self.fenetre_principale = FenetreVendeur(profil)
        else:
            QMessageBox.critical(self, "Erreur", f"Rôle inconnu : {role}")
            return

        self.fenetre_principale.show()
        self.close()
