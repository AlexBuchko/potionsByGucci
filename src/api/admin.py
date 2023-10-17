from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src.api import database as db
from sqlalchemy import text

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    # updating gold
    queries = []
    queries.append(text("UPDATE global_inventory SET gold = 100"))
    queries.append(text("TRUNCATE TABLE carts CASCADE"))
    queries.append(text("TRUNCATE TABLE cart_contents"))
    queries.append(text("UPDATE potions SET quantity = 0"))
    queries.append(text("UPDATE fluids SET quantity = 0"))
    for query in queries:
        print(query)
        db.execute(query)


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potions by Gucci",
        "shop_owner": "Alex Buchko",
    }
