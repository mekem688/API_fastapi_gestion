"""
widgets/kpi_card.py — Carte indicateur réutilisable (KPI)

Affiche un titre, une grande valeur et une couleur d'accent.
Utilisée sur tous les tableaux de bord (PDG, DG, Vendeur).
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ..config import COULEUR_CARTE, COULEUR_TEXTE_DOUX, COULEUR_BORDURE


class CarteKPI(QFrame):
    def __init__(self, titre: str, valeur: str, couleur_accent: str = "#1E3A5F"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COULEUR_CARTE};
                border: 1px solid {COULEUR_BORDURE};
                border-radius: 10px;
                border-left: 4px solid {couleur_accent};
            }}
        """)
        self.setMinimumHeight(90)

        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(16, 12, 16, 12)

        etiquette_titre = QLabel(titre)
        etiquette_titre.setStyleSheet(f"color: {COULEUR_TEXTE_DOUX}; font-size: 12px; border:none;")

        etiquette_valeur = QLabel(valeur)
        etiquette_valeur.setStyleSheet(f"color: {couleur_accent}; font-size: 22px; font-weight: bold; border:none;")

        disposition.addWidget(etiquette_titre)
        disposition.addWidget(etiquette_valeur)
        disposition.addStretch()

    def definir_valeur(self, nouvelle_valeur: str) -> None:
        widget_valeur = self.layout().itemAt(1).widget()
        widget_valeur.setText(nouvelle_valeur)
