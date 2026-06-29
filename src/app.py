from fastapi import FastAPI

from .data import Base, engine
from .routers import items

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Gestion de Stock Avancée")

app.include_router(items.router)


@app.get("/")
def home():
    return {"message": "API Stock ERP OK"}