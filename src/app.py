from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data import Base, engine
from .routers import items
from .routers import auth as auth_router

# Création automatique des tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title       = "API Gestion de Stock",
    description = (
        "API REST de gestion de stock avec authentification JWT.\n\n"
        "**Rôles :**\n"
        "- `vendeur` — ventes, consultation articles et mouvements\n"
        "- `directeur` — tout + achats, profits, alertes, création d'articles\n\n"
        "**Connexion :** `POST /auth/connexion` → copier le token → cliquer 'Authorize' en haut"
    ),
    version     = "2.0.0",
)

# Autoriser les requêtes depuis n'importe quelle origine
# (à restreindre en production : allow_origins=["https://monsite.com"])
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# Enregistrement des routes
app.include_router(auth_router.router)   # /auth/*
app.include_router(items.router)         # /articles/*


@app.get("/", tags=["Root"])
def accueil():
    return {
        "message"      : "API Gestion de Stock — OK",
        "documentation": "/docs",
        "connexion"    : "POST /auth/connexion",
    }
