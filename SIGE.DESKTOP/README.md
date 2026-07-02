# SIGE.DESKTOP

Application de bureau (PyQt6) du Système Intégré de Gestion d'Entreprise (SIGE).
Elle se connecte à l'API existante de ce dépôt (`API_fastapi_gestion`) et fournit
une interface adaptée à chacun des trois rôles : **PDG**, **Directeur (DG)** et
**Vendeur**.

## Fonctionnalités principales

- **Connexion unique avec redirection automatique par rôle** : après
  authentification, l'utilisateur est dirigé vers la fenêtre PDG, Directeur ou
  Vendeur selon le rôle renvoyé par l'API.
- **PDG** : dashboard entreprise, liste des boutiques, classement, crédits
  consolidés, journal global, équipe.
- **Directeur** : gestion des articles et du stock, crédits clients et
  fournisseurs, journal de sa boutique, personnalisation de l'en-tête des
  factures. Les fonctionnalités sensibles (voir les bénéfices, faire des
  achats, créer des articles) sont soumises aux permissions accordées par le
  PDG.
- **Vendeur** : vente rapide, consultation du stock, historique de ses ventes,
  impression de factures. **Le vendeur ne voit jamais le prix d'achat ni le
  bénéfice**, nulle part dans l'application.
- **Factures texte imprimables** : générées en HTML simple (sans logo), avec
  un en-tête personnalisable par le Directeur (nom, slogan, téléphone,
  adresse, email, pied de page).
- **Mode hors-ligne** : si l'API est injoignable, les ventes sont enregistrées
  dans une base SQLite locale (`local_data.db`) avec le préfixe de facture
  `HL-`. Une synchronisation automatique a lieu dès que la connexion revient ;
  le serveur a toujours la priorité sur les données locales.

## Installation et lancement

```bash
cd SIGE.DESKTOP
bash start.sh
```

Le script `start.sh` :
1. Crée un environnement virtuel Python (`.venv`) s'il n'existe pas.
2. Installe les dépendances de `requirements.txt`.
3. Crée le fichier `.env` à partir de `.env.example` si nécessaire.
4. Lance l'application avec `python -m app.main`.

## Configuration

Le fichier `.env` (copié depuis `.env.example`) contient :

```
API_URL=http://localhost:8000
```

Modifiez `API_URL` pour pointer vers l'adresse de votre serveur API
(`API_fastapi_gestion`), en local ou en production.

## Structure du projet

```
SIGE.DESKTOP/
  start.sh              → script de lancement
  requirements.txt       → dépendances Python
  .env.example           → exemple de configuration
  app/
    main.py               → point d'entrée (python -m app.main)
    config.py             → constantes (URL API, couleurs, chemins)
    services/
      api_client.py        → client HTTP vers l'API FastAPI
      local_db.py           → base SQLite locale (cache + file d'attente hors-ligne)
      sync_service.py       → surveillance de la connexion + synchronisation auto
      invoice_service.py    → génération et impression des factures texte
    widgets/
      kpi_card.py            → carte indicateur réutilisable
      data_table.py          → tableau de données réutilisable
      status_bar.py          → bannière d'état de connexion
    windows/
      login_window.py        → écran de connexion + redirection par rôle
      pdg_window.py           → fenêtre PDG
      dg_window.py            → fenêtre Directeur
      vendeur_window.py       → fenêtre Vendeur
```

## Notes techniques

- L'application est un package Python (`app/`) : elle doit être lancée avec
  `python -m app.main` (et non `python app/main.py`) pour que les imports
  relatifs fonctionnent correctement.
- Toutes les factures imprimées sont également sauvegardées en copie texte
  dans le dossier `factures/`.
- La base locale (`local_data.db`) et le dossier `factures/` sont créés
  automatiquement au premier lancement.
