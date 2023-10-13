import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src.api import database as db
from src.api import colors

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
        color = colors.get_color_from_potion_type(barrel.potion_type)

        inventory = db.get_global_inventory()
        money_spent = barrel.price * barrel.quantity
        ml_gained = barrel.ml_per_barrel * barrel.quantity
        new_gold = inventory["gold"] - money_spent
        new_ml = inventory[f"num_{color}_ml"] + ml_gained
        update_command = f"UPDATE global_inventory SET gold = {new_gold}, num_{color}_ml = {new_ml} WHERE id = 1"
        db.execute(update_command)

    return "OK"


def balance_barrels(catalog):
    # goal is to keep a balance of potion types

    inventory = db.get_global_inventory()
    # getting a count of how many potions we have
    colors = ["red", "green", "blue"]
    colors = list(
        filter(lambda color: f"SMALL_{color.upper()}_BARREL" in catalog, colors)
    )
    potion_counts = {color: inventory[f"num_{color}_potions"] for color in colors}
    fluid_counts = {color: inventory[f"num_{color}_ml"] for color in colors}

    # if we have have 350ml of red fluid, we might as well have 3.5 red potions
    for color, num_ml in fluid_counts.items():
        potion_counts[color] += num_ml / 100

    # buying the potion we have the least of till we're out of money
    i = 0
    gold = inventory["gold"]
    purchase_plan = {}

    while i < len(colors):
        if i == 0:  # recomputing the order when we reset
            buying_order = sorted(colors, key=lambda color: potion_counts[color])
        color_to_buy = buying_order[i]
        sku = f"SMALL_{color_to_buy.upper()}_BARREL"
        barrel = catalog[sku]
        can_afford = gold >= barrel.price
        if can_afford:
            # adding to purchase plan
            potion_counts[color_to_buy] += barrel.ml_per_barrel / 100
            purchase_plan[sku] = purchase_plan.get(sku, 0) + 1
            gold -= barrel.price
            i = 0
        else:
            i += 1

    # getting a return value
    return purchase_plan


sizes = ["MINI", "SMALL", "MEDIUM", "LARGE"]
sizes_to_buy = ["MINI", "SMALL"]


def one_of_each(catalog):
    # buying the smallest amount of a each color we don't have that's for sale
    inventory = db.get_global_inventory()
    gold = inventory["gold"]
    potion_counts = db.get_net_potion_counts()
    purchase_plan = {}
    for color in colors.colors:
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
    for barrel in wholesale_catalog:
        json_string = json.dumps(barrel.__dict__)
        print(json_string)

    catalog = {barrel.sku: barrel for barrel in wholesale_catalog}
    ans = []
    purchase_plan = balance_barrels(catalog)
    print(purchase_plan)
    for sku, count in purchase_plan.items():
        barrel = catalog[sku]
        print(f"purchasing {sku} at {barrel.price}")
        ans.append(
            {
                "sku": sku,
                "quantity": count,
            }
        )

    return ans
