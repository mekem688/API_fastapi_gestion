from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data import Base, engine
from .routers import items
from .routers import auth as auth_router
from .routers import pdg as pdg_router
from .routers import credits as credits_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title       = "API Gestion de Stock Multi-Boutiques",
    description = (
        "API REST — Gestion de stock, crédits, journal d'activité.\n\n"
        "**Hiérarchie :**\n"
        "- `pdg` — vue entreprise, permissions, crédits toutes boutiques, journal global\n"
        "- `directeur` — gère SA boutique, crédits, journal boutique\n"
        "- `vendeur` — ventes et consultation de SA boutique\n\n"
        "**Démarrage :**\n"
        "1. `POST /auth/creer-premier-compte` → créer le PDG\n"
        "2. `POST /auth/connexion` → token → **Authorize**\n"
        "3. `POST /pdg/boutiques` → créer une boutique\n"
        "4. `POST /pdg/boutiques/{id}/ajouter-directeur`\n"
        "5. `PUT /pdg/directeurs/{id}/permissions` → accorder les droits"
    ),
    version = "4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(pdg_router.router)
app.include_router(items.router)
app.include_router(credits_router.router)


@app.get("/", tags=["Root"])
def accueil():
    return {
        "message"    : "API Gestion de Stock Multi-Boutiques v4",
        "docs"       : "/docs",
        "premier_pas": "POST /auth/creer-premier-compte",
    }
