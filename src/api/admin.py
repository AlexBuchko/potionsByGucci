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
    queries.append(text("TRUNCATE TABLE gold_ledger CASCADE"))
    queries.append(text("INSERT INTO gold_ledger (change) VALUES (100)"))
    queries.append(text("TRUNCATE TABLE carts CASCADE"))
    queries.append(text("TRUNCATE TABLE cart_contents"))
    queries.append(text("TRUNCATE TABLE fluids_ledger"))
    queries.append(text("TRUNCATE TABLE potions_ledger"))
    for query in queries:
        print(query)
        db.execute(query)


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Potions by Gucci",
        "shop_owner": "Alex Buchko",
    }
