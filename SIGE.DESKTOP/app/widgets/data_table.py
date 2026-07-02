"""
widgets/data_table.py — Tableau générique réutilisable

Reçoit une liste d'en-têtes de colonnes et une liste de lignes (listes de
valeurs déjà formatées en texte). Style clair professionnel appliqué
automatiquement.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

from ..config import COULEUR_CARTE, COULEUR_BORDURE, COULEUR_PRIMAIRE


class TableauDonnees(QTableWidget):
    def __init__(self, en_tetes: list[str]):
        super().__init__()
        self.setColumnCount(len(en_tetes))
        self.setHorizontalHeaderLabels(en_tetes)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COULEUR_CARTE};
                border: 1px solid {COULEUR_BORDURE};
                border-radius: 6px;
                gridline-color: {COULEUR_BORDURE};
            }}
            QHeaderView::section {{
                background-color: {COULEUR_PRIMAIRE};
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
        """)

    def remplir(self, lignes: list[list[str]]) -> None:
        self.setRowCount(len(lignes))
        for indice_ligne, ligne in enumerate(lignes):
            for indice_colonne, valeur in enumerate(ligne):
                self.setItem(indice_ligne, indice_colonne, QTableWidgetItem(str(valeur)))
