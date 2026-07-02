"""
windows/pdg_window.py — Fenêtre principale du PDG

Onglets : Dashboard, Boutiques, Classement, Crédits, Journal, Équipe.
Le PDG voit toutes les boutiques et n'a aucune restriction de permission.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

from ..config import COULEUR_FOND, COULEUR_PRIMAIRE, COULEUR_DANGER, COULEUR_SUCCES, COULEUR_ALERTE
from ..services.api_client import client_api, ErreurConnexionAPI
from ..services.sync_service import service_sync
from ..widgets.kpi_card import CarteKPI
from ..widgets.data_table import TableauDonnees
from ..widgets.status_bar import BanniereConnexion


class FenetrePDG(QMainWindow):
    def __init__(self, profil: dict):
        super().__init__()
        self.profil = profil
        self.setWindowTitle(f"SIGE.DESKTOP — PDG : {profil['prenom']} {profil['nom_famille']}")
        self.resize(1100, 700)
        self.setStyleSheet(f"background-color: {COULEUR_FOND};")

        self._construire_interface()
        self._connecter_synchronisation()
        self._charger_dashboard()

    # ------------------------------------------------------------------
    def _construire_interface(self) -> None:
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        disposition = QVBoxLayout(widget_central)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(0)

        # En-tête
        entete = QWidget()
        entete.setStyleSheet(f"background-color: {COULEUR_PRIMAIRE};")
        disposition_entete = QHBoxLayout(entete)
        disposition_entete.setContentsMargins(20, 12, 20, 12)

        titre = QLabel(f"PDG — {self.profil['prenom']} {self.profil['nom_famille']}")
        titre.setStyleSheet("color:white; font-size:16px; font-weight:bold;")

        bouton_deconnexion = QPushButton("Déconnexion")
        bouton_deconnexion.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton_deconnexion.setStyleSheet(f"""
            QPushButton {{ background-color: {COULEUR_DANGER}; color:white; border-radius:4px; padding:6px 14px; }}
        """)
        bouton_deconnexion.clicked.connect(self._deconnexion)

        disposition_entete.addWidget(titre)
        disposition_entete.addStretch()
        disposition_entete.addWidget(bouton_deconnexion)

        self.banniere_connexion = BanniereConnexion()

        # Onglets
        self.onglets = QTabWidget()
        self.onglets.setStyleSheet("QTabBar::tab { padding: 10px 18px; }")

        self.onglet_dashboard = self._construire_onglet_dashboard()
        self.onglet_boutiques = self._construire_onglet_boutiques()
        self.onglet_classement = self._construire_onglet_classement()
        self.onglet_credits = self._construire_onglet_credits()
        self.onglet_journal = self._construire_onglet_journal()
        self.onglet_equipe = self._construire_onglet_equipe()

        self.onglets.addTab(self.onglet_dashboard, "📊 Dashboard")
        self.onglets.addTab(self.onglet_boutiques, "🏪 Boutiques")
        self.onglets.addTab(self.onglet_classement, "🏆 Classement")
        self.onglets.addTab(self.onglet_credits, "💳 Crédits")
        self.onglets.addTab(self.onglet_journal, "📋 Journal")
        self.onglets.addTab(self.onglet_equipe, "👥 Équipe")

        disposition.addWidget(entete)
        disposition.addWidget(self.banniere_connexion)
        disposition.addWidget(self.onglets)

    # ------------------------------------------------------------------
    def _connecter_synchronisation(self) -> None:
        service_sync.etat_change.connect(self._sur_changement_etat_reseau)
        service_sync.demarrer()

    def _sur_changement_etat_reseau(self, en_ligne: bool) -> None:
        if en_ligne:
            self.banniere_connexion.afficher_en_ligne()
        else:
            self.banniere_connexion.afficher_hors_ligne()

    # ------------------------------------------------------------------
    # Onglet Dashboard
    # ------------------------------------------------------------------
    def _construire_onglet_dashboard(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)

        ligne_cartes = QHBoxLayout()
        self.carte_boutiques = CarteKPI("Boutiques actives", "—", COULEUR_PRIMAIRE)
        self.carte_benefice = CarteKPI("Bénéfice total", "—", COULEUR_SUCCES)
        self.carte_a_encaisser = CarteKPI("À encaisser", "—", COULEUR_ALERTE)
        self.carte_a_payer = CarteKPI("À payer", "—", COULEUR_DANGER)

        for carte in (self.carte_boutiques, self.carte_benefice, self.carte_a_encaisser, self.carte_a_payer):
            ligne_cartes.addWidget(carte)

        disposition.addLayout(ligne_cartes)

        titre_activite = QLabel("Activité récente")
        titre_activite.setStyleSheet("font-size:14px; font-weight:bold; margin-top:16px;")
        disposition.addWidget(titre_activite)

        self.tableau_activite = TableauDonnees(["Boutique", "Article", "Type", "Quantité", "Date"])
        disposition.addWidget(self.tableau_activite)

        return widget

    def _charger_dashboard(self) -> None:
        try:
            donnees = client_api.dashboard_pdg()
        except ErreurConnexionAPI:
            self.banniere_connexion.afficher_hors_ligne()
            return

        self.carte_boutiques.definir_valeur(str(donnees["nb_boutiques_actives"]))
        self.carte_benefice.definir_valeur(f"{donnees['benefice_total_entreprise']:,.0f} F")
        self.carte_a_encaisser.definir_valeur(f"{donnees['total_a_encaisser_entreprise']:,.0f} F")
        self.carte_a_payer.definir_valeur(f"{donnees['total_a_payer_entreprise']:,.0f} F")

        lignes = [
            [m["boutique_nom"], m["article_nom"], m["type_mouvement"], m["quantite"], m["date"][:16]]
            for m in donnees["activite_recente"]
        ]
        self.tableau_activite.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Boutiques
    # ------------------------------------------------------------------
    def _construire_onglet_boutiques(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_boutiques = TableauDonnees(["Nom", "Ville", "Adresse", "Statut"])
        disposition.addWidget(self.tableau_boutiques)
        self._charger_boutiques()
        return widget

    def _charger_boutiques(self) -> None:
        try:
            boutiques = client_api.lister_boutiques()
        except ErreurConnexionAPI:
            return
        lignes = [
            [b["nom"], b["ville"], b["adresse"] or "—", "Active" if b["est_active"] else "Archivée"]
            for b in boutiques
        ]
        self.tableau_boutiques.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Classement
    # ------------------------------------------------------------------
    def _construire_onglet_classement(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_classement = TableauDonnees(["Boutique", "Bénéfice total", "Ventes du mois", "Articles"])
        disposition.addWidget(self.tableau_classement)
        self._charger_classement()
        return widget

    def _charger_classement(self) -> None:
        try:
            classement = client_api.classement_boutiques()
        except ErreurConnexionAPI:
            return
        lignes = [
            [s["boutique"]["nom"], f"{s['benefice_total']:,.0f} F", s["ventes_du_mois"], s["nb_articles"]]
            for s in classement
        ]
        self.tableau_classement.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Crédits
    # ------------------------------------------------------------------
    def _construire_onglet_credits(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_credits = TableauDonnees(
            ["Boutique", "À encaisser", "Clients débiteurs", "À payer", "Fournisseurs dus"]
        )
        disposition.addWidget(self.tableau_credits)
        self._charger_credits()
        return widget

    def _charger_credits(self) -> None:
        try:
            credits_entreprise = client_api.credits_entreprise()
        except ErreurConnexionAPI:
            return
        lignes = [
            [
                c["boutique"]["nom"],
                f"{c['total_a_encaisser']:,.0f} F",
                c["nb_clients_debiteurs"],
                f"{c['total_a_payer']:,.0f} F",
                c["nb_fournisseurs_dus"],
            ]
            for c in credits_entreprise
        ]
        self.tableau_credits.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Journal
    # ------------------------------------------------------------------
    def _construire_onglet_journal(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_journal = TableauDonnees(["Date", "Utilisateur", "Boutique", "Action"])
        disposition.addWidget(self.tableau_journal)
        self._charger_journal()
        return widget

    def _charger_journal(self) -> None:
        try:
            entrees = client_api.journal_global()
        except ErreurConnexionAPI:
            return
        lignes = [
            [e["date_heure"][:16], e["nom_complet"], e["boutique_nom"] or "—", e["action"]]
            for e in entrees
        ]
        self.tableau_journal.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Équipe
    # ------------------------------------------------------------------
    def _construire_onglet_equipe(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)

        info = QLabel("Sélectionnez une boutique dans l'onglet « Boutiques » pour voir son équipe complète.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#6B7280;")
        disposition.addWidget(info)

        self.tableau_equipe = TableauDonnees(["Nom complet", "Rôle", "Téléphone", "Statut"])
        disposition.addWidget(self.tableau_equipe)
        return widget

    # ------------------------------------------------------------------
    def _deconnexion(self) -> None:
        from ..services import local_db
        service_sync.arreter()
        local_db.effacer_session()
        from .login_window import FenetreConnexion
        self.fenetre_connexion = FenetreConnexion()
        self.fenetre_connexion.show()
        self.close()
