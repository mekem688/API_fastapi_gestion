"""
services/invoice_service.py — Génération et impression de factures (texte)

La facture est construite en HTML simple (juste du texte, pas de logo)
puis affichée dans un QPrintPreviewDialog. Cela évite toute dépendance
externe (pas de ReportLab) tout en utilisant l'imprimante du système.

Numérotation :
  - En ligne  : AAAA-MM-JJ-XXXX (XXXX = compteur du jour, séquentiel)
  - Hors-ligne: préfixe "HL-" ajouté devant, ex. HL-2024-06-30-0003
"""

from datetime import datetime, timezone

from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from ..config import DOSSIER_FACTURES


def generer_numero_facture(compteur_du_jour: int, hors_ligne: bool = False) -> str:
    date_du_jour = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    numero = f"{date_du_jour}-{compteur_du_jour:04d}"
    return f"HL-{numero}" if hors_ligne else numero


def construire_html_facture(config_boutique: dict, numero_facture: str,
                             nom_vendeur: str, lignes: list[dict], hors_ligne: bool = False) -> str:
    """
    lignes : liste de dicts {"nom": str, "quantite": int, "prix_unitaire": float}
    """
    total = sum(ligne["quantite"] * ligne["prix_unitaire"] for ligne in lignes)
    date_facture = datetime.now().strftime("%d/%m/%Y %Hh%M")

    lignes_html = ""
    for ligne in lignes:
        sous_total = ligne["quantite"] * ligne["prix_unitaire"]
        lignes_html += f"""
            <tr>
                <td>{ligne['nom']}</td>
                <td style="text-align:center;">{ligne['quantite']}</td>
                <td style="text-align:right;">{ligne['prix_unitaire']:,.0f} F</td>
                <td style="text-align:right;">{sous_total:,.0f} F</td>
            </tr>
        """

    avertissement_hors_ligne = (
        "<p style='text-align:center; font-size:11px; color:#555;'>"
        "Facture enregistrée hors-ligne — sera synchronisée au retour de la connexion."
        "</p>" if hors_ligne else ""
    )

    return f"""
    <html>
    <body style="font-family: monospace; font-size: 13px; width: 320px;">
        <div style="text-align:center;">
            <h2 style="margin:2px;">{config_boutique.get('nom_boutique', 'Boutique')}</h2>
            {"<p style='margin:2px;'>" + config_boutique['slogan'] + "</p>" if config_boutique.get('slogan') else ""}
            {"<p style='margin:2px;'>Tel : " + config_boutique['telephone'] + "</p>" if config_boutique.get('telephone') else ""}
            {"<p style='margin:2px;'>" + config_boutique['adresse'] + "</p>" if config_boutique.get('adresse') else ""}
        </div>
        <hr>
        <p>Facture N° {numero_facture}<br>
        Date : {date_facture}<br>
        Vendeur : {nom_vendeur}</p>
        <hr>
        <table width="100%" cellspacing="0" cellpadding="3">
            <tr>
                <th style="text-align:left;">Article</th>
                <th>Qté</th>
                <th style="text-align:right;">P.U.</th>
                <th style="text-align:right;">Total</th>
            </tr>
            {lignes_html}
        </table>
        <hr>
        <p style="text-align:right; font-weight:bold;">TOTAL : {total:,.0f} F</p>
        <hr>
        <div style="text-align:center;">
            <p>{config_boutique.get('pied_de_page') or 'Merci pour votre confiance !'}</p>
        </div>
        {avertissement_hors_ligne}
    </body>
    </html>
    """


def sauvegarder_copie_texte(numero_facture: str, html: str) -> None:
    """Garde une copie de chaque facture imprimée sur le disque local."""
    chemin = DOSSIER_FACTURES / f"{numero_facture}.html"
    chemin.write_text(html, encoding="utf-8")


def imprimer_facture(fenetre_parente, html: str, numero_facture: str, apercu: bool = True) -> None:
    """
    Ouvre soit un aperçu avant impression, soit directement la boîte de
    dialogue d'impression, selon le paramètre `apercu`.
    """
    document = QTextDocument()
    document.setHtml(html)

    imprimante = QPrinter(QPrinter.PrinterMode.HighResolution)

    if apercu:
        dialogue = QPrintPreviewDialog(imprimante, fenetre_parente)
        dialogue.paintRequested.connect(document.print)
        dialogue.exec()
    else:
        dialogue = QPrintDialog(imprimante, fenetre_parente)
        if dialogue.exec() == QPrintDialog.DialogCode.Accepted:
            document.print(imprimante)

    sauvegarder_copie_texte(numero_facture, html)
