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
        "SELECT sku, potion_type, price, quantity FROM potions WHERE quantity >= 1"
    )
    result = db.execute(query)
    ans = [
        {
            "sku": row.sku,
            "name": row.sku,
            "price": row.price,
            "potion_type": row.potion_type,
            "quantity": row.quantity,
        }
        for row in result
    ]
    return ans
    ans = []
    for color in colorUtils.colors:
        key = f"num_{color}_potions"
        num_potions = inventory[key]
        if num_potions >= 1:
            ans.append(
                {
                    "sku": f"{color.upper()}_POTION_0",
                    "name": "{color} potion",
                    "price": 50,
                    "potion_type": colorUtils.get_potion_type(color),
                    "quantity": 1,
                }
            )

    return ans
