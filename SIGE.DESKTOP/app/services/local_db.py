"""
services/local_db.py — Base de données locale SQLite (mode hors-ligne)

Sert de cache et de file d'attente quand l'application n'a pas accès
à internet. Trois tables :

  articles_cache   → copie des articles vus en ligne (nom, prix, stock)
  ventes_locales   → ventes enregistrées hors-ligne, en attente de sync
  session_locale   → dernier token + infos utilisateur (reconnexion auto)

Règle importante : le serveur a toujours la priorité. Les données locales
ne sont qu'une roue de secours en cas de coupure internet.
"""

import sqlite3
from datetime import datetime, timezone

from ..config import CHEMIN_BASE_LOCALE


def obtenir_connexion() -> sqlite3.Connection:
    connexion = sqlite3.connect(str(CHEMIN_BASE_LOCALE))
    connexion.row_factory = sqlite3.Row
    return connexion


def initialiser_base_locale() -> None:
    """Crée les tables locales si elles n'existent pas encore."""
    connexion = obtenir_connexion()
    curseur = connexion.cursor()

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS articles_cache (
            id INTEGER PRIMARY KEY,
            boutique_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            prix_vente REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS ventes_locales (
            id_local INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            article_nom TEXT NOT NULL,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            date_vente TEXT NOT NULL,
            numero_facture TEXT NOT NULL,
            statut_sync TEXT NOT NULL DEFAULT 'en_attente'
        )
    """)

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS session_locale (
            cle TEXT PRIMARY KEY,
            valeur TEXT
        )
    """)

    connexion.commit()
    connexion.close()


# ------------------------------------------------------------------
# Cache des articles (pour pouvoir vendre même hors-ligne)
# ------------------------------------------------------------------

def mettre_a_jour_cache_articles(boutique_id: int, articles: list[dict]) -> None:
    connexion = obtenir_connexion()
    curseur = connexion.cursor()
    curseur.execute("DELETE FROM articles_cache WHERE boutique_id = ?", (boutique_id,))
    for article in articles:
        curseur.execute(
            "INSERT INTO articles_cache (id, boutique_id, nom, prix_vente, stock) VALUES (?, ?, ?, ?, ?)",
            (article["id"], boutique_id, article["name"], article["price_vente"], article["quantity"]),
        )
    connexion.commit()
    connexion.close()


def lire_cache_articles(boutique_id: int) -> list[sqlite3.Row]:
    connexion = obtenir_connexion()
    resultats = connexion.execute(
        "SELECT * FROM articles_cache WHERE boutique_id = ? ORDER BY nom", (boutique_id,)
    ).fetchall()
    connexion.close()
    return resultats


# ------------------------------------------------------------------
# Ventes enregistrées hors-ligne, en attente de synchronisation
# ------------------------------------------------------------------

def enregistrer_vente_locale(article_id: int, article_nom: str, quantite: int,
                              prix_unitaire: float, numero_facture: str) -> int:
    connexion = obtenir_connexion()
    curseur = connexion.cursor()
    curseur.execute(
        """INSERT INTO ventes_locales
           (article_id, article_nom, quantite, prix_unitaire, date_vente, numero_facture, statut_sync)
           VALUES (?, ?, ?, ?, ?, ?, 'en_attente')""",
        (article_id, article_nom, quantite, prix_unitaire,
         datetime.now(timezone.utc).isoformat(), numero_facture),
    )
    id_local = curseur.lastrowid
    connexion.commit()
    connexion.close()
    return id_local


def lister_ventes_en_attente() -> list[sqlite3.Row]:
    connexion = obtenir_connexion()
    resultats = connexion.execute(
        "SELECT * FROM ventes_locales WHERE statut_sync = 'en_attente' ORDER BY id_local"
    ).fetchall()
    connexion.close()
    return resultats


def compter_ventes_en_attente() -> int:
    connexion = obtenir_connexion()
    total = connexion.execute(
        "SELECT COUNT(*) AS total FROM ventes_locales WHERE statut_sync = 'en_attente'"
    ).fetchone()["total"]
    connexion.close()
    return total


def marquer_vente_synchronisee(id_local: int) -> None:
    connexion = obtenir_connexion()
    connexion.execute(
        "UPDATE ventes_locales SET statut_sync = 'synchronise' WHERE id_local = ?", (id_local,)
    )
    connexion.commit()
    connexion.close()


# ------------------------------------------------------------------
# Session locale (reconnexion automatique)
# ------------------------------------------------------------------

def sauvegarder_session(token: str, nom_utilisateur: str, role: str) -> None:
    connexion = obtenir_connexion()
    curseur = connexion.cursor()
    for cle, valeur in [("token", token), ("nom_utilisateur", nom_utilisateur), ("role", role)]:
        curseur.execute(
            "INSERT INTO session_locale (cle, valeur) VALUES (?, ?) "
            "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
            (cle, valeur),
        )
    connexion.commit()
    connexion.close()


def lire_session() -> dict:
    connexion = obtenir_connexion()
    lignes = connexion.execute("SELECT cle, valeur FROM session_locale").fetchall()
    connexion.close()
    return {ligne["cle"]: ligne["valeur"] for ligne in lignes}


def effacer_session() -> None:
    connexion = obtenir_connexion()
    connexion.execute("DELETE FROM session_locale")
    connexion.commit()
    connexion.close()
