# 🏢 API FastAPI Gestion - Système Intégré de Gestion d'Entreprise (SIGE)

Bienvenue dans **API_fastapi_gestion**, une solution complète de gestion d'entreprise construite avec **FastAPI** et **Python**. Ce projet fournit une API robuste pour gérer les boutiques, les articles, les stocks, les ventes et les utilisateurs avec un système de rôles et de permissions.

---

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Lancement](#lancement)
- [Configuration](#configuration)
- [Fonctionnalités principales](#fonctionnalités-principales)
- [Structure du projet](#structure-du-projet)
- [API Documentation](#api-documentation)
- [Application Desktop](#application-desktop)
- [Mode hors-ligne](#mode-hors-ligne)
- [Contribution](#contribution)
- [License](#license)

---

## 👁️ Vue d'ensemble

**API_fastapi_gestion** est un système intégré de gestion d'entreprise (SIGE) qui offre :

✅ **Gestion des utilisateurs** avec système d'authentification robuste  
✅ **Gestion des boutiques** et des points de vente  
✅ **Gestion des articles et du stock** en temps réel  
✅ **Suivi des ventes** et historique  
✅ **Gestion des crédits** clients et fournisseurs  
✅ **Système de rôles et permissions** (PDG, Directeur, Vendeur)  
✅ **Génération de factures** professionnelles  
✅ **API REST complète** avec documentation interactive (Swagger)  
✅ **Mode hors-ligne** avec synchronisation automatique  

---

## 🏗️ Architecture

### Stack technologique

- **Backend** : FastAPI (Python 3.9+)
- **Base de données** : PostgreSQL / SQLite
- **Frontend Desktop** : PyQt6 (voir `SIGE.DESKTOP/`)
- **Documentation API** : Swagger UI / ReDoc
- **Authentification** : JWT Tokens
- **Synchronisation** : Architecture client-serveur avec cache local

### Composants principaux

```
API_fastapi_gestion/
├── api/                    # Endpoint FastAPI
│   ├── routes/             # Routage des endpoints
│   ├── models/             # Modèles Pydantic
│   ├── schemas/            # Schémas de validation
│   └── dependencies/       # Dépendances (auth, etc.)
├── core/                   # Logique métier
│   ├── security/           # Authentification & JWT
│   ├── config/             # Configuration
│   └── exceptions/         # Exceptions personnalisées
├── db/                     # Base de données
│   ├── models/             # Modèles ORM
│   └── session/            # Gestion des sessions DB
├── SIGE.DESKTOP/           # Application desktop PyQt6
├── tests/                  # Suite de tests
├── main.py                 # Point d'entrée
└── requirements.txt        # Dépendances Python
```

---

## 📦 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Python 3.9+** → [Télécharger Python](https://www.python.org/)
- **pip** → Gestionnaire de paquets Python
- **Git** → [Télécharger Git](https://git-scm.com/)
- **PostgreSQL** (optionnel) → Si vous utilisez PostgreSQL au lieu de SQLite

### Vérification

```bash
python --version
pip --version
git --version
```

---

## 🚀 Installation

### 1️⃣ Cloner le dépôt

```bash
git clone https://github.com/mekem688/API_fastapi_gestion.git
cd API_fastapi_gestion
```

### 2️⃣ Créer un environnement virtuel

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4️⃣ Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Base de données
DATABASE_URL=sqlite:///./sige.db
# ou pour PostgreSQL :
# DATABASE_URL=postgresql://user:password@localhost:5432/sige_db

# Authentification JWT
SECRET_KEY=votre_clé_secrète_très_sécurisée_ici
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuration API
API_TITLE=SIGE - Système Intégré de Gestion d'Entreprise
API_VERSION=1.0.0
DEBUG=True
```

⚠️ **Important** : Pour la production, utilisez une clé secrète forte et sécurisée !

### 5️⃣ Initialiser la base de données

```bash
# Si vous utilisez Alembic pour les migrations
alembic upgrade head

# Sinon, les tables seront créées au premier lancement
```

---

## ▶️ Lancement

### Option 1 : Lancer l'API FastAPI

```bash
# Développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

L'API sera accessible à : **http://localhost:8000**

### Option 2 : Accéder à la documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Option 3 : Lancer l'application Desktop (SIGE.DESKTOP)

```bash
cd SIGE.DESKTOP
bash start.sh
```

Ou manuellement :

```bash
cd SIGE.DESKTOP
python -m app.main
```

---

## ⚙️ Configuration

### Variables d'environnement principales

| Variable | Description | Valeur défaut |
|----------|-------------|---------------|
| `DATABASE_URL` | Connexion base de données | `sqlite:///./sige.db` |
| `SECRET_KEY` | Clé JWT | *(à définir)* |
| `ALGORITHM` | Algorithme JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée du token | `30` |
| `DEBUG` | Mode debug | `False` |
| `API_PORT` | Port API | `8000` |

### Configuration de la base de données

#### SQLite (développement)
```env
DATABASE_URL=sqlite:///./sige.db
```

#### PostgreSQL (production)
```env
DATABASE_URL=postgresql://username:password@localhost:5432/sige_db
```

---

## ✨ Fonctionnalités principales

### 👥 Gestion des utilisateurs

- Création et modification de comptes utilisateur
- Authentification sécurisée par JWT
- Gestion des rôles (PDG, Directeur, Vendeur)
- Permissions granulaires

### 🏪 Gestion des boutiques

- Création et gestion des points de vente
- Suivi des performances par boutique
- Classement et statistiques

### 📦 Gestion des articles et du stock

- Catalogue d'articles avec prix d'achat/vente
- Suivi du stock en temps réel
- Alertes de rupture de stock
- Historique des mouvements

### 💳 Gestion des crédits

- Crédits clients
- Crédits fournisseurs
- Suivi des paiements
- Historique des transactions

### 📄 Factures et ventes

- Génération automatique de factures (HTML)
- Personnalisation de l'en-tête
- Impression directe
- Archivage automatique

### 📊 Tableaux de bord

- Dashboard PDG : vue d'ensemble de l'entreprise
- Dashboard Directeur : gestion de la boutique
- Dashboard Vendeur : ventes et stock

---

## 📁 Structure du projet

```
API_fastapi_gestion/
├── main.py                           # Point d'entrée FastAPI
├── requirements.txt                  # Dépendances Python
├── .env.example                      # Modèle de configuration
├── .gitignore                        # Fichiers ignorés par Git
│
├── app/                              # Application principale
│   ├── __init__.py
│   ├── api/
│   │   ├── routes/                   # Endpoint API
│   │   │   ├── users.py              # Gestion utilisateurs
│   │   │   ├── shops.py              # Gestion boutiques
│   │   │   ├── articles.py           # Gestion articles
│   │   │   ├── sales.py              # Gestion ventes
│   │   │   └── ...
│   │   ├── models/                   # Modèles Pydantic
│   │   └── dependencies/             # Dépendances
│   │
│   ├── core/
│   │   ├── security.py               # JWT, hachage password
│   │   ├── config.py                 # Configuration
│   │   └── exceptions.py             # Exceptions
│   │
│   ├── db/
│   │   ├── models/                   # Modèles ORM SQLAlchemy
│   │   ├── session.py                # Gestion session DB
│   │   └── init_db.py                # Initialisation DB
│   │
│   └── services/                     # Logique métier
│
├── SIGE.DESKTOP/                     # Application PyQt6
│   ├── start.sh                      # Script de lancement
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── services/
│   │   │   ├── api_client.py
│   │   │   ├── local_db.py
│   │   │   ├── sync_service.py
│   │   │   └── invoice_service.py
│   │   ├── widgets/
│   │   ├── windows/
│   │   │   ├── login_window.py
│   │   │   ├── pdg_window.py
│   │   │   ├── dg_window.py
│   │   │   └── vendeur_window.py
│   │
│   └── factures/                     # Factures générées
│
├── tests/                            # Suite de tests
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_articles.py
│   └── ...
│
├── migrations/                       # Migrations Alembic (optionnel)
│
└── docs/                             # Documentation
    ├── API.md
    ├── ARCHITECTURE.md
    └── DEPLOYMENT.md
```

---

## 📚 API Documentation

### Endpoints principaux

#### Authentification
```
POST   /api/auth/login              # Connexion
POST   /api/auth/logout             # Déconnexion
POST   /api/auth/refresh            # Renouveler token
```

#### Utilisateurs
```
GET    /api/users/                  # Lister les utilisateurs
POST   /api/users/                  # Créer un utilisateur
GET    /api/users/{id}              # Détails utilisateur
PUT    /api/users/{id}              # Modifier utilisateur
DELETE /api/users/{id}              # Supprimer utilisateur
```

#### Boutiques
```
GET    /api/shops/                  # Lister les boutiques
POST   /api/shops/                  # Créer une boutique
GET    /api/shops/{id}              # Détails boutique
PUT    /api/shops/{id}              # Modifier boutique
```

#### Articles
```
GET    /api/articles/               # Lister les articles
POST   /api/articles/               # Créer un article
GET    /api/articles/{id}           # Détails article
PUT    /api/articles/{id}           # Modifier article
```

#### Ventes
```
GET    /api/sales/                  # Lister les ventes
POST   /api/sales/                  # Créer une vente
GET    /api/sales/{id}              # Détails vente
```

**Documentation complète** : http://localhost:8000/docs (Swagger UI)

---

## 🖥️ Application Desktop

### Fonctionnalités

- ✅ **Interface graphique PyQt6** professionnelle
- ✅ **Connexion par rôle** (PDG, Directeur, Vendeur)
- ✅ **Mode hors-ligne** avec synchronisation automatique
- ✅ **Génération de factures** en temps réel
- ✅ **Gestion du stock** instantanée
- ✅ **Tableaux de bord** intuitifs

### Lancement

```bash
cd SIGE.DESKTOP
bash start.sh
```

### Configuration

Éditez `.env` dans `SIGE.DESKTOP/` :

```env
API_URL=http://localhost:8000
```

📖 **Voir** : [SIGE.DESKTOP/README.md](SIGE.DESKTOP/README.md)

---

## 🔄 Mode hors-ligne

L'application desktop supporte le mode hors-ligne :

- 📍 Les données sont sauvegardées localement en SQLite (`local_data.db`)
- 📤 Les ventes hors-ligne sont préfixées par `HL-`
- 🔄 Synchronisation automatique dès que la connexion revient
- 🔐 Les données du serveur ont la priorité en cas de conflit

---

## 🧪 Tests

### Exécuter les tests

```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_auth.py

# Avec coverage
pytest --cov=app
```

---

## 📝 Exemple d'utilisation

### Créer un utilisateur (avec la CLI ou l'API)

```bash
curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "role": "vendeur"
  }'
```

### Se connecter

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePassword123!"
  }'
```

---

## 🐛 Dépannage

### Le port 8000 est déjà utilisé

```bash
# Utiliser un autre port
uvicorn main:app --port 8001
```

### Erreur de base de données

```bash
# Réinitialiser la base de données
rm sige.db
# Relancer l'application
```

### Problème de connexion API (mode desktop)

Vérifiez la variable `API_URL` dans `.env` de `SIGE.DESKTOP/`

---

## 🤝 Contribution

Les contributions sont bienvenues ! Pour contribuer :

1. 🍴 Forkez le dépôt
2. 🌿 Créez une branche : `git checkout -b feature/nom-feature`
3. 💾 Committez vos changements : `git commit -m "Ajout: description"`
4. 📤 Poussez : `git push origin feature/nom-feature`
5. 📬 Ouvrez une Pull Request

---

## 📞 Support

- 📧 **Email** : support@example.com
- 💬 **Issues** : [Ouvrir une issue](https://github.com/mekem688/API_fastapi_gestion/issues)
- 📖 **Documentation** : [Wiki](https://github.com/mekem688/API_fastapi_gestion/wiki)

---

## 📄 License

Ce projet est sous license **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 👨‍💻 Auteur

Développé par **mekem688**

- GitHub : [@mekem688](https://github.com/mekem688)
- Dépôt : [API_fastapi_gestion](https://github.com/mekem688/API_fastapi_gestion)

---

## 🎉 Remerciements

Merci d'utiliser **SIGE** ! N'hésitez pas à laisser une ⭐ si ce projet vous a été utile !

---

**Dernière mise à jour** : 2 juillet 2026  
**Version** : 1.0.0
