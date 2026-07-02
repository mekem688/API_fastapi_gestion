"""
windows/vendeur_window.py — Fenêtre principale du Vendeur

Onglets : Vente rapide, Stock (lecture seule), Mes ventes, Profil.

Le vendeur ne voit JAMAIS le prix d'achat ni le bénéfice — ni dans le
stock, ni dans ses ventes. La vente fonctionne même hors-ligne (cache
local SQLite), et une facture texte peut être imprimée à chaque vente.
"""

from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt

from ..config import COULEUR_FOND, COULEUR_PRIMAIRE, COULEUR_DANGER, COULEUR_SUCCES
from ..services.api_client import client_api, ErreurConnexionAPI
from ..services.sync_service import service_sync
from ..services import local_db
from ..services.invoice_service import generer_numero_facture, construire_html_facture, imprimer_facture
from ..widgets.data_table import TableauDonnees
from ..widgets.status_bar import BanniereConnexion


class FenetreVendeur(QMainWindow):
    def __init__(self, profil: dict):
        super().__init__()
        self.profil = profil
        self.boutique_id = profil.get("boutique_id")
        self.article_selectionne: dict | None = None
        self.compteur_factures_du_jour = 0

        self.setWindowTitle(f"SIGE.DESKTOP — Vendeur : {profil['prenom']} {profil['nom_famille']}")
        self.resize(1000, 650)
        self.setStyleSheet(f"background-color: {COULEUR_FOND};")

        self._construire_interface()
        self._connecter_synchronisation()

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

        titre = QLabel(f"Vendeur — {self.profil['prenom']} {self.profil['nom_famille']}")
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
        self.onglets.addTab(self._construire_onglet_vente(), "🛒 Vente rapide")
        self.onglets.addTab(self._construire_onglet_stock(), "📦 Stock")
        self.onglets.addTab(self._construire_onglet_mes_ventes(), "📋 Mes ventes")
        self.onglets.addTab(self._construire_onglet_profil(), "👤 Profil")

        disposition.addWidget(entete)
        disposition.addWidget(self.banniere_connexion)
        disposition.addWidget(self.onglets)

        self._charger_stock()

    def _connecter_synchronisation(self) -> None:
        service_sync.etat_change.connect(self._sur_changement_etat_reseau)
        service_sync.connexion_retablie.connect(self._sur_synchronisation_reussie)
        service_sync.demarrer()

    def _sur_changement_etat_reseau(self, en_ligne: bool) -> None:
        if en_ligne:
            self.banniere_connexion.afficher_en_ligne()
        else:
            self.banniere_connexion.afficher_hors_ligne()

    def _sur_synchronisation_reussie(self, nb_ventes: int) -> None:
        self.banniere_connexion.afficher_synchronisation_reussie(nb_ventes)

    # ------------------------------------------------------------------
    # Onglet Vente rapide
    # ------------------------------------------------------------------
    def _construire_onglet_vente(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        disposition.setSpacing(12)

        titre = QLabel("Vente rapide")
        titre.setStyleSheet("font-size:16px; font-weight:bold;")
        disposition.addWidget(titre)

        formulaire = QFormLayout()
        self.champ_recherche_article = QLineEdit()
        self.champ_recherche_article.setPlaceholderText("Nom exact de l'article")
        formulaire.addRow("Rechercher article :", self.champ_recherche_article)

        self.champ_quantite_vente = QSpinBox()
        self.champ_quantite_vente.setMinimum(1)
        self.champ_quantite_vente.setMaximum(999999)
        formulaire.addRow("Quantité :", self.champ_quantite_vente)

        disposition.addLayout(formulaire)

        bouton_rechercher = QPushButton("Rechercher")
        bouton_rechercher.clicked.connect(self._rechercher_article)
        disposition.addWidget(bouton_rechercher)

        self.etiquette_resultat_recherche = QLabel("")
        self.etiquette_resultat_recherche.setStyleSheet("color:#374151; font-size:13px;")
        disposition.addWidget(self.etiquette_resultat_recherche)

        bouton_vendre = QPushButton("Enregistrer la vente")
        bouton_vendre.setStyleSheet(f"background-color:{COULEUR_SUCCES}; color:white; padding:10px; border-radius:4px; font-weight:bold;")
        bouton_vendre.clicked.connect(self._enregistrer_vente)
        disposition.addWidget(bouton_vendre)

        disposition.addStretch()
        return widget

    def _rechercher_article(self) -> None:
        nom_recherche = self.champ_recherche_article.text().strip().lower()
        if not nom_recherche:
            return

        self.article_selectionne = None

        try:
            articles = client_api.lister_articles()
            for article in articles:
                if article["name"].lower() == nom_recherche:
                    self.article_selectionne = {
                        "id": article["id"], "name": article["name"],
                        "quantity": article["quantity"], "price_vente": article["price_vente"],
                    }
                    break
        except ErreurConnexionAPI:
            # Hors-ligne → recherche dans le cache local
            if self.boutique_id:
                for ligne in local_db.lire_cache_articles(self.boutique_id):
                    if ligne["nom"].lower() == nom_recherche:
                        self.article_selectionne = {
                            "id": ligne["id"], "name": ligne["nom"],
                            "quantity": ligne["stock"], "price_vente": ligne["prix_vente"],
                        }
                        break

        if self.article_selectionne:
            article = self.article_selectionne
            self.etiquette_resultat_recherche.setText(
                f"✅ {article['name']} — Stock : {article['quantity']} — Prix : {article['price_vente']:,.0f} F"
            )
        else:
            self.etiquette_resultat_recherche.setText("❌ Article introuvable.")

    def _enregistrer_vente(self) -> None:
        if not self.article_selectionne:
            QMessageBox.warning(self, "Erreur", "Recherchez d'abord un article.")
            return

        quantite = self.champ_quantite_vente.value()
        article = self.article_selectionne
        hors_ligne = False

        try:
            resultat = client_api.sortie_stock(article["id"], quantite)
            self.compteur_factures_du_jour += 1
            numero_facture = generer_numero_facture(self.compteur_factures_du_jour)
        except ErreurConnexionAPI:
            # Pas d'internet → on enregistre localement, on synchronisera plus tard
            hors_ligne = True
            self.compteur_factures_du_jour += 1
            numero_facture = generer_numero_facture(self.compteur_factures_du_jour, hors_ligne=True)
            local_db.enregistrer_vente_locale(
                article["id"], article["name"], quantite, article["price_vente"], numero_facture
            )
        except ValueError as erreur:
            QMessageBox.warning(self, "Vente impossible", str(erreur))
            return

        QMessageBox.information(
            self, "Vente enregistrée",
            f"{quantite} x {article['name']} — Facture {numero_facture}"
            + (" (hors-ligne, sera synchronisée)" if hors_ligne else "")
        )

        self._proposer_impression(article, quantite, numero_facture, hors_ligne)
        self.champ_recherche_article.clear()
        self.etiquette_resultat_recherche.setText("")
        self.article_selectionne = None
        self._charger_stock()

    def _proposer_impression(self, article: dict, quantite: int, numero_facture: str, hors_ligne: bool) -> None:
        reponse = QMessageBox.question(
            self, "Imprimer la facture ?",
            "Voulez-vous imprimer la facture de cette vente ?",
        )
        if reponse != QMessageBox.StandardButton.Yes:
            return

        try:
            config_boutique = client_api.config_facture_pour_impression()
        except ErreurConnexionAPI:
            config_boutique = {"nom_boutique": "Boutique", "pied_de_page": "Merci pour votre confiance !"}

        html = construire_html_facture(
            config_boutique=config_boutique,
            numero_facture=numero_facture,
            nom_vendeur=f"{self.profil['prenom']} {self.profil['nom_famille']}",
            lignes=[{"nom": article["name"], "quantite": quantite, "prix_unitaire": article["price_vente"]}],
            hors_ligne=hors_ligne,
        )
        imprimer_facture(self, html, numero_facture)

    # ------------------------------------------------------------------
    # Onglet Stock (lecture seule, jamais de profit)
    # ------------------------------------------------------------------
    def _construire_onglet_stock(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_stock = TableauDonnees(["Article", "Prix de vente", "Stock disponible"])
        disposition.addWidget(self.tableau_stock)
        return widget

    def _charger_stock(self) -> None:
        try:
            articles = client_api.lister_articles()
            lignes = [[a["name"], f"{a['price_vente']:,.0f} F", a["quantity"]] for a in articles]
        except ErreurConnexionAPI:
            if not self.boutique_id:
                return
            lignes = [
                [ligne["nom"], f"{ligne['prix_vente']:,.0f} F", ligne["stock"]]
                for ligne in local_db.lire_cache_articles(self.boutique_id)
            ]
        self.tableau_stock.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Mes ventes (jamais de bénéfice affiché)
    # ------------------------------------------------------------------
    def _construire_onglet_mes_ventes(self) -> QWidget:
        widget = QWidget()
        disposition = QVBoxLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)
        self.tableau_mes_ventes = TableauDonnees(["Facture", "Article", "Quantité", "Montant", "Statut"])
        disposition.addWidget(self.tableau_mes_ventes)
        bouton_actualiser = QPushButton("Actualiser")
        bouton_actualiser.clicked.connect(self._charger_mes_ventes)
        disposition.addWidget(bouton_actualiser)
        self._charger_mes_ventes()
        return widget

    def _charger_mes_ventes(self) -> None:
        connexion = local_db.obtenir_connexion()
        ventes = connexion.execute(
            "SELECT * FROM ventes_locales ORDER BY id_local DESC LIMIT 100"
        ).fetchall()
        connexion.close()

        lignes = [
            [
                vente["numero_facture"], vente["article_nom"], vente["quantite"],
                f"{vente['quantite'] * vente['prix_unitaire']:,.0f} F",
                "✅ Synchronisée" if vente["statut_sync"] == "synchronise" else "🟡 En attente",
            ]
            for vente in ventes
        ]
        self.tableau_mes_ventes.remplir(lignes)

    # ------------------------------------------------------------------
    # Onglet Profil
    # ------------------------------------------------------------------
    def _construire_onglet_profil(self) -> QWidget:
        widget = QWidget()
        disposition = QFormLayout(widget)
        disposition.setContentsMargins(20, 20, 20, 20)

        disposition.addRow("Nom complet :", QLabel(f"{self.profil['prenom']} {self.profil['nom_famille']}"))
        disposition.addRow("Nom d'utilisateur :", QLabel(self.profil["nom_utilisateur"]))
        disposition.addRow("Téléphone :", QLabel(self.profil.get("telephone") or "—"))
        disposition.addRow("Rôle :", QLabel("Vendeur"))
        disposition.addRow("Boutique ID :", QLabel(str(self.profil.get("boutique_id") or "—")))

        return widget

    # ------------------------------------------------------------------
    def _deconnexion(self) -> None:
        service_sync.arreter()
        local_db.effacer_session()
        from .login_window import FenetreConnexion
        self.fenetre_connexion = FenetreConnexion()
        self.fenetre_connexion.show()
        self.close()
