from pydantic import BaseModel


# =========================
# ARTICLE
# =========================

class ArticleBase(BaseModel):
    name: str
    description: str | None = None

    price_achat: float
    price_vente: float

    low_stock_threshold: int = 5


class ArticleCreate(ArticleBase):
    pass


class ArticleResponse(ArticleBase):
    id: int
    quantity: int

    class Config:
        from_attributes = True


# =========================
# MOVEMENT
# =========================

class MovementResponse(BaseModel):
    id: int
    article_id: int
    type: str
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True