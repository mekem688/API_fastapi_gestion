"""
main.py — Point d'entrée de l'application SIGE.DESKTOP

Lance l'écran de connexion. Après authentification, l'utilisateur est
automatiquement redirigé vers la fenêtre correspondant à son rôle
(PDG, Directeur, ou Vendeur).

Lancement : bash start.sh (voir le fichier à la racine du dossier).
"""

import sys
from PyQt6.QtWidgets import QApplication

from .services import local_db
from .windows.login_window import FenetreConnexion


def demarrer_application() -> None:
    local_db.initialiser_base_locale()

    application = QApplication(sys.argv)
    application.setStyle("Fusion")

    fenetre_connexion = FenetreConnexion()
    fenetre_connexion.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    demarrer_application()
