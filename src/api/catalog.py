from fastapi import APIRouter
from sqlalchemy import text
from src.api import database as db
from src.api import potionUtils as colorUtils

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    query = text(
        """
         SELECT potions.potion_id, potion_type, sku, price, amount FROM potions JOIN 
            (SELECT potion_id, sum(change) as amount FROM potions_ledger GROUP BY potion_id) ledger 
            on ledger.potion_id = potions.potion_id
            WHERE amount > 0
        """
    )

    result = db.execute(query)
    ans = [
        {
            "sku": row.sku,
            "name": row.sku,
            "price": row.price,
            "potion_type": row.potion_type,
            "quantity": row.amount,
        }
        for row in result
    ]
    return ans
