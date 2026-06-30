from pydantic import BaseModel, Field
from datetime import datetime


# =========================
# ARTICLE
# =========================

class ArticleBase(BaseModel):
    name                : str
    description         : str | None = None
    price_achat         : float = Field(gt=0)
    price_vente         : float = Field(gt=0)
    low_stock_threshold : int   = Field(default=5, ge=0)


class ArticleCreate(ArticleBase):
    pass


class ArticleResponse(ArticleBase):
    id       : int
    quantity : int

    class Config:
        from_attributes = True


# =========================
# MOVEMENT
# =========================

class MovementResponse(BaseModel):
    id            : int
    article_id    : int
    movement_type : str
    quantity      : int
    unit_price    : float
    created_at    : datetime

    class Config:
        from_attributes = True
