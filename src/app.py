from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data import Base, engine
from .routers import items

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title       = "API Gestion de Stock",
    description = "API REST de gestion de stock avec mouvements, alertes et calcul de bénéfices.",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],   # Restreindre en production (ex: ["https://monsite.com"])
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(items.router)


@app.get("/", tags=["Root"])
def home():
    return {"message": "API Stock OK", "docs": "/docs"}
