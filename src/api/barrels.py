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
    barrels = convert_catalog(barrels_delivered)
    # printing the dict version of this for testing later down the road
    for barrel in barrels.values():
        json_string = json.dumps(barrel.__dict__)
        print(json_string)

    for barrel in barrels.values():
        # getting color
        gold_change = -1 * barrel.price * barrel.quantity
        current_gold = db.get_gold()
        if current_gold + gold_change < 0:
            raise "not enough gold to buy barrels"

        query = text(
            "INSERT INTO gold_ledger (change) VALUES (:gold_change)",
        )
        db.execute_with_binds(query, {"gold_change": gold_change})

        ml_gained = barrel.ml_per_barrel * barrel.quantity
        query = text(
            "INSERT INTO fluids_ledger (fluid_id, change) SELECT fluid_id, :ml_gained FROM fluids WHERE fluids.potion_type = :potion_type",
        )
        db.execute_with_binds(
            query, {"ml_gained": ml_gained, "potion_type": barrel.potion_type}
        )
    return "OK"


def balance_barrels(catalog, state):
    # goal is to keep a balance of potion types
    fluid_counts = state.fluid_counts
    gold = state.gold

    i = 0
    purchase_plan = {}

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
        else:
            i += 1

    return purchase_plan


class State(BaseModel):
    fluid_counts: dict
    gold: int


def convert_catalog(barrels: list[Barrel]):
    # converting potions
    for barrel in barrels:
        barrel.potion_type = [100 if x == 1 else x for x in barrel.potion_type]
    return {barrel.sku: barrel for barrel in barrels}


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    print(wholesale_catalog)
    # printing the dict version of this for testing later down the road
    catalog = convert_catalog(wholesale_catalog)
    fluid_counts = db.get_net_fluid_counts()
    gold = db.get_gold()
    state = State(fluid_counts=fluid_counts, gold=gold)
    purchase_plan = balance_barrels(catalog, state)
    print(purchase_plan)
    ans = []
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
