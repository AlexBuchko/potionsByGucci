import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src.api import database as db
from src.api import potionUtils
from sqlalchemy import text

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


sizes = ["MINI", "SMALL", "MEDIUM", "LARGE"]


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)
    # printing the dict version of this for testing later down the road
    for barrel in barrels_delivered:
        json_string = json.dumps(barrel.__dict__)
        print(json_string)

    for barrel in barrels_delivered:
        # getting color
        color = potionUtils.get_color_from_barrel_type(barrel.potion_type)
        gold_spent = barrel.price * barrel.quantity
        query = text(
            "UPDATE global_inventory SET gold = gold - :gold_spent",
        )
        db.execute_with_binds(query, {"gold_spent": gold_spent})

        ml_gained = barrel.ml_per_barrel * barrel.quantity
        query = text(
            "UPDATE fluids SET quantity = quantity + :ml_gained WHERE color = :color",
        )
        db.execute_with_binds(query, {"ml_gained": ml_gained, "color": color})
    return "OK"


def balance_barrels(catalog):
    # goal is to keep a balance of potion types

    fluid_counts = db.get_net_fluid_counts()
    i = 0
    gold = db.get_gold()
    purchase_plan = {}
    print(fluid_counts)

    # buying the most of the potion we have the least of till we're out of money

    while i < len(potionUtils.colors):
        if i == 0:  # recomputing the order when we reset
            buying_order = sorted(
                potionUtils.colors, key=lambda color: fluid_counts[color]
            )
        color_to_buy = buying_order[i]
        for size in reversed(sizes):
            sku = f"{size}_{color_to_buy.upper()}_BARREL"
            if sku not in catalog:
                continue
            barrel = catalog[sku]
            can_afford = gold >= barrel.price
            current_amount = purchase_plan.get(sku, 0)
            any_barrels_left = current_amount < barrel.quantity
            if can_afford and any_barrels_left:
                # adding to purchase plan
                fluid_counts[color_to_buy] += barrel.ml_per_barrel
                purchase_plan[sku] = current_amount + 1
                gold -= barrel.price
                i = 0
                break
        i += 1

    return purchase_plan


def one_of_each(catalog):
    # NOTE: probably outdated lol
    # buying the smallest amount of a each color we don't have that's for sale
    inventory = db.get_gold()
    gold = inventory["gold"]
    potion_counts = db.get_net_fluid_counts()
    purchase_plan = {}
    for color in potionUtils.colors:
        if potion_counts[color] > 0:
            continue
        for size in sizes_to_buy:
            sku = f"{size}_{color.upper()}_BARREL"
            if sku in catalog:
                barrel = catalog[sku]
                if barrel.price <= gold:
                    gold -= barrel.price
                    purchase_plan[sku] = 1
                    break
    return purchase_plan


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    print(wholesale_catalog)
    # printing the dict version of this for testing later down the road
    catalog = {barrel.sku: barrel for barrel in wholesale_catalog}
    ans = []
    purchase_plan = balance_barrels(catalog)
    print(purchase_plan)
    for sku, count in purchase_plan.items():
        barrel = catalog[sku]
        print(f"purchasing {count} of {sku} for {count * barrel.price}")
        ans.append(
            {
                "sku": sku,
                "quantity": count,
            }
        )

    return ans
