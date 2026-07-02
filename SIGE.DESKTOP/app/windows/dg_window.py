"""
windows/dg_window.py — Fenêtre principale du Directeur (DG)

Onglets : Dashboard, Articles, Stock, Crédits clients, Crédits fournisseurs,
Journal, Mon équipe, Facture (personnalisation de l'en-tête).

Certaines fonctionnalités dépendent des permissions accordées par le PDG
(voir_profits, faire_achats, creer_articles, voir_alertes, gerer_vendeurs).
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QMessageBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt

from ..config import COULEUR_FOND, COULEUR_PRIMAIRE, COULEUR_DANGER, COULEUR_SUCCES, COULEUR_ALERTE
from ..services.api_client import client_api, ErreurConnexionAPI
from ..services.sync_service import service_sync
from ..widgets.kpi_card import CarteKPI
from ..widgets.data_table import TableauDonnees
from ..widgets.status_bar import BanniereConnexion


class FenetreDG(QMainWindow):
    def __init__(self, profil: dict):
        super().__init__()
        self.profil = profil
        self.permissions = profil.get("permissions", [])
        self.setWindowTitle(f"SIGE.DESKTOP — Directeur : {profil['prenom']} {profil['nom_famille']}")
        self.resize(1100, 700)
        self.setStyleSheet(f"background-color: {COULEUR_FOND};")

        self._construire_interface()
        self._connecter_synchronisation()
        self._charger_articles()

    def _a_la_permission(self, permission: str) -> bool:
        return permission in self.permissions

    # ------------------------------------------------------------------
    def _construire_interface(self) -> None:
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        disposition = QVBoxLayout(widget_central)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(0)

        entete = QWidget()
        entete.setStyleSheet(f"background-color: {COULEUR_PRIMAIRE};")
        disposition_entete = QHBoxLayout(entete)
        disposition_entete.setContentsMargins(20, 12, 20, 12)

        titre = QLabel(f"Directeur — {self.profil['prenom']} {self.profil['nom_famille']}")
        titre.setStyleSheet("color:white; font-size:16px; font-weight:bold;")

        bouton_deconnexion = QPushButton("Déconnexion")
        bouton_deconnexion.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton_deconnexion.setStyleSheet(f"QPushButton {{ background-color: {COULEUR_DANGER}; color:white; border-radius:4px; padding:6px 14px; }}")
        bouton_deconnexion.clicked.connect(self._deconnexion)

        disposition_entete.addWidget(titre)
        disposition_entete.addStretch()
        disposition_entete.addWidget(bouton_deconnexion)

        self.banniere_connexion = BanniereConnexion()

        self.onglets = QTabWidget()

        self.onglets.addTab(self._construire_onglet_articles(), "📦 Articles")
        self.onglets.addTab(self._construire_onglet_stock(), "↕️ Stock")
        self.onglets.addTab(self._construire_onglet_credits_clients(), "💳 Crédits clients")
        self.onglets.addTab(self._construire_onglet_credits_fournisseurs(), "🏭 Crédits fournisseurs")
        self.onglets.addTab(self._construire_onglet_journal(), "📋 Journal")
        self.onglets.addTab(self._construire_onglet_facture(), "🧾 Facture")

        disposition.addWidget(entete)
        disposition.addWidget(self.banniere_connexion)
        disposition.addWidget(self.onglets)

    def _connecter_synchronisation(self) -> None:
        service_sync.etat_change.connect(self._sur_changement_etat_reseau)
        service_sync.demarrer()

    def _sur_changement_etat_reseau(self, en_ligne: bool) -> None:
        if en_ligne:
            self.banniere_connexion.afficher_en_ligne()
        else:
            self.banniere_connexion.afficher_hors_ligne()

    # ------------------------------------------------------------------
    # Onglet Articles
    # ------------------------------------------------------------------
    def _construire_onglet_articles(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)

        colonnes = ["Nom", "Prix vente", "Stock"]
        if self._a_la_permission("voir_profits"):
            colonnes.insert(1, "Prix achat")
            colonnes.append("Bénéfice unitaire")

        self.tableau_articles = TableauDonnees(colonnes)
        disposition.addWidget(self.tableau_articles)

        if self._a_la_permission("creer_articles"):
            bouton_nouveau = QPushButton("+ Nouvel article")
            bouton_nouveau.setStyleSheet(f"background-color:{COULEUR_PRIMAIRE}; color:white; padding:8px; border-radius:4px;")
            bouton_nouveau.clicked.connect(self._ouvrir_formulaire_article)
            disposition.addWidget(bouton_nouveau)

        return widget

    def _charger_articles(self) -> None:
        try:
            articles = client_api.lister_articles()
        except ErreurConnexionAPI:
            self.banniere_connexion.afficher_hors_ligne()
            return

        voir_profits = self._a_la_permission("voir_profits")
        lignes = []
        for article in articles:
            if voir_profits:
                benefice = article["price_vente"] - article["price_achat"]
                lignes.append([
                    article["name"], f"{article['price_achat']:,.0f} F",
                    f"{article['price_vente']:,.0f} F", article["quantity"], f"{benefice:,.0f} F",
                ])
            else:
                lignes.append([article["name"], f"{article['price_vente']:,.0f} F", article["quantity"]])

        self.tableau_articles.remplir(lignes)

        # Mise à jour du cache local (pour la vente hors-ligne côté vendeur)
        from ..services import local_db
        if self.profil.get("boutique_id"):
            local_db.mettre_a_jour_cache_articles(self.profil["boutique_id"], articles)

    def _ouvrir_formulaire_article(self) -> None:
        QMessageBox.information(
            self, "Nouvel article",
            "Formulaire de création d'article — à compléter avec nom, prix d'achat, "
            "prix de vente et seuil d'alerte, puis appel à client_api.creer_article()."
        )

    # ------------------------------------------------------------------
    # Onglet Stock
    # ------------------------------------------------------------------
    def _construire_onglet_stock(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)

        info = QLabel("Entrée de stock rapide (nécessite la permission « Faire des achats »).")
        info.setStyleSheet("color:#6B7280;")
        disposition.addWidget(info)

        if not self._a_la_permission("faire_achats"):
            avertissement = QLabel("⚠️ Vous n'avez pas la permission d'effectuer des entrées de stock.")
            avertissement.setStyleSheet(f"color:{COULEUR_DANGER};")
            disposition.addWidget(avertissement)

        formulaire = QFormLayout()
        self.champ_article_id = QSpinBox()
        self.champ_article_id.setMaximum(999999)
        self.champ_quantite_entree = QSpinBox()
        self.champ_quantite_entree.setMaximum(999999)
        self.champ_quantite_entree.setValue(1)

        formulaire.addRow("ID article :", self.champ_article_id)
        formulaire.addRow("Quantité à ajouter :", self.champ_quantite_entree)
        disposition.addLayout(formulaire)

        bouton_ajouter = QPushButton("Ajouter au stock")
        bouton_ajouter.setEnabled(self._a_la_permission("faire_achats"))
        bouton_ajouter.setStyleSheet(f"background-color:{COULEUR_PRIMAIRE}; color:white; padding:8px; border-radius:4px;")
        bouton_ajouter.clicked.connect(self._ajouter_stock)
        disposition.addWidget(bouton_ajouter)
        disposition.addStretch()

        return widget

    def _ajouter_stock(self) -> None:
        try:
            resultat = client_api.entree_stock(self.champ_article_id.value(), self.champ_quantite_entree.value())
            QMessageBox.information(self, "Succès", "Stock mis à jour.")
            self._charger_articles()
        except (ErreurConnexionAPI, ValueError) as erreur:
            QMessageBox.warning(self, "Erreur", str(erreur))

    # ------------------------------------------------------------------
    # Onglet Crédits clients
    # ------------------------------------------------------------------
    def _construire_onglet_credits_clients(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_credits_clients = TableauDonnees(
            ["Client", "Téléphone", "Montant total", "Restant", "Statut"]
        )
        disposition.addWidget(self.tableau_credits_clients)
        self._charger_credits_clients()
        return widget

    def _charger_credits_clients(self) -> None:
        try:
            ventes = client_api.lister_ventes_credit()
        except ErreurConnexionAPI:
            return
        lignes = [
            [v["client_nom"], v["client_telephone"], f"{v['montant_total']:,.0f} F",
             f"{v['montant_restant']:,.0f} F", v["statut"]]
            for v in ventes
        ]
        self.tableau_credits_clients.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Crédits fournisseurs
    # ------------------------------------------------------------------
    def _construire_onglet_credits_fournisseurs(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_credits_fournisseurs = TableauDonnees(
            ["Fournisseur", "Téléphone", "Montant total", "Restant", "Statut"]
        )
        disposition.addWidget(self.tableau_credits_fournisseurs)
        self._charger_credits_fournisseurs()
        return widget

    def _charger_credits_fournisseurs(self) -> None:
        try:
            achats = client_api.lister_achats_credit()
        except ErreurConnexionAPI:
            return
        lignes = [
            [a["fournisseur_nom"], a["fournisseur_telephone"], f"{a['montant_total']:,.0f} F",
             f"{a['montant_restant']:,.0f} F", a["statut"]]
            for a in achats
        ]
        self.tableau_credits_fournisseurs.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Journal
    # ------------------------------------------------------------------
    def _construire_onglet_journal(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_journal = TableauDonnees(["Date", "Utilisateur", "Action"])
        disposition.addWidget(self.tableau_journal)
        self._charger_journal()
        return widget

    def _charger_journal(self) -> None:
        try:
            entrees = client_api.journal_boutique()
        except ErreurConnexionAPI:
            return
        lignes = [[e["date_heure"][:16], e["nom_complet"], e["action"]] for e in entrees]
        self.tableau_journal.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Facture — personnalisation de l'en-tête
    # ------------------------------------------------------------------
    def _construire_onglet_facture(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)

        titre = QLabel("Personnaliser l'en-tête de facture de votre boutique")
        titre.setStyleSheet("font-size:14px; font-weight:bold;")
        disposition.addWidget(titre)

        formulaire = QFormLayout()
        self.champ_nom_boutique = QLineEdit()
        self.champ_slogan = QLineEdit()
        self.champ_telephone_facture = QLineEdit()
        self.champ_adresse_facture = QLineEdit()
        self.champ_email_facture = QLineEdit()
        self.champ_pied_de_page = QLineEdit()

        formulaire.addRow("Nom boutique :", self.champ_nom_boutique)
        formulaire.addRow("Slogan :", self.champ_slogan)
        formulaire.addRow("Téléphone :", self.champ_telephone_facture)
        formulaire.addRow("Adresse :", self.champ_adresse_facture)
        formulaire.addRow("Email :", self.champ_email_facture)
        formulaire.addRow("Pied de page :", self.champ_pied_de_page)

        disposition.addLayout(formulaire)

        bouton_enregistrer = QPushButton("💾 Enregistrer")
        bouton_enregistrer.setStyleSheet(f"background-color:{COULEUR_SUCCES}; color:white; padding:8px; border-radius:4px;")
        bouton_enregistrer.clicked.connect(self._enregistrer_config_facture)
        disposition.addWidget(bouton_enregistrer)
        disposition.addStretch()

        self._charger_config_facture()
        return widget

    def _charger_config_facture(self) -> None:
        try:
            config = client_api.lire_config_facture()
        except ErreurConnexionAPI:
            return
        if config:
            self.champ_nom_boutique.setText(config.get("nom_boutique") or "")
            self.champ_slogan.setText(config.get("slogan") or "")
            self.champ_telephone_facture.setText(config.get("telephone") or "")
            self.champ_adresse_facture.setText(config.get("adresse") or "")
            self.champ_email_facture.setText(config.get("email") or "")
            self.champ_pied_de_page.setText(config.get("pied_de_page") or "")

    def _enregistrer_config_facture(self) -> None:
        if not self.champ_nom_boutique.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom de la boutique est obligatoire.")
            return
        donnees = {
            "nom_boutique": self.champ_nom_boutique.text().strip(),
            "slogan": self.champ_slogan.text().strip() or None,
            "telephone": self.champ_telephone_facture.text().strip() or None,
            "adresse": self.champ_adresse_facture.text().strip() or None,
            "email": self.champ_email_facture.text().strip() or None,
            "pied_de_page": self.champ_pied_de_page.text().strip() or "Merci pour votre confiance !",
        }
        try:
            client_api.enregistrer_config_facture(donnees)
            QMessageBox.information(self, "Succès", "En-tête de facture mis à jour.")
        except ErreurConnexionAPI:
            QMessageBox.warning(self, "Erreur", "Impossible de joindre le serveur.")

    # ------------------------------------------------------------------
    def _deconnexion(self) -> None:
        from ..services import local_db
        service_sync.arreter()
        local_db.effacer_session()
        from .login_window import FenetreConnexion
        self.fenetre_connexion = FenetreConnexion()
        self.fenetre_connexion.show()
        self.close()
