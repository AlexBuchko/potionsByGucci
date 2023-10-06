from fastapi import APIRouter
import sqlalchemy
from src.api import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    inventory = db.get_global_inventory()
    if (inventory["num_red_potions"]) <= 0:
        print("no potions to sell, returning")
        return
    ans = []
    colors = ["red", "green", "blue"]
    for color in colors:
        key = f"num_{color}_potions"
        num_potions = inventory[key]
        if num_potions >= 1:
            ans.append(
                {
                    "sku": f"{color.upper()}_POTION_0",
                    "name": "{color} potion",
                    "price": 50,
                    "potion_type": colorUtils.get_base_potion_type(color),
                    "quantity": 1,
                }
            )

    # Can return a max of 20 items.
    response = {
        "sku": "RED_POTION_0",
        "name": "red potion",
        "price": 50,
        "potion_type": [100, 0, 0, 0],
        "quantity": 1,
    }
    return response
