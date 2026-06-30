from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data import Base, engine
from .routers import items
from .routers import auth as auth_router
from .routers import pdg as pdg_router

# Création automatique des tables si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title       = "API Gestion de Stock Multi-Boutiques",
    description = (
        "API REST avec authentification JWT et gestion multi-boutiques.\n\n"
        "**Hiérarchie des rôles :**\n"
        "- `pdg` — crée les boutiques, assigne les directeurs, voit tout\n"
        "- `directeur` — gère SA boutique (articles, achats, profits, alertes)\n"
        "- `vendeur` — fait des ventes dans SA boutique\n\n"
        "**Démarrage rapide :**\n"
        "1. `POST /auth/creer-premier-compte` → créer le PDG\n"
        "2. `POST /auth/connexion` → obtenir le token\n"
        "3. Cliquer sur **Authorize** ici → coller le token\n"
        "4. `POST /pdg/boutiques` → créer une boutique\n"
        "5. `POST /pdg/boutiques/{id}/ajouter-directeur` → assigner un directeur"
    ),
    version     = "3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# Enregistrement des routes
app.include_router(auth_router.router)   # /auth/*
app.include_router(pdg_router.router)    # /pdg/*
app.include_router(items.router)         # /articles/*


@app.get("/", tags=["Root"])
def accueil():
    return {
        "message"       : "API Gestion de Stock Multi-Boutiques",
        "version"       : "3.0.0",
        "documentation" : "/docs",
        "premier_pas"   : "POST /auth/creer-premier-compte",
    }
