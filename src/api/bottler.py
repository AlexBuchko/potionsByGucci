from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
from src.api import database as db
from src.api import potionUtils
from sqlalchemy import text

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)
    for potion in potions_delivered:
        # increase the number of potions by quantity
        query = text(
            "UPDATE potions SET quantity = quantity + :brewed WHERE potion_type = :potion_type"
        )
        db.execute_with_binds(
            query, {"brewed": potion.quantity, "potion_type": potion.potion_type}
        )
        # decrease the number of fluids by the fluid amount
        fluid_types = potionUtils.potion_type_to_dict(potion.potion_type)
        for color, amount in fluid_types.items():
            if amount == 0:
                continue
            query = text(
                "UPDATE fluids SET quantity = quantity - :spent WHERE color = :color"
            )
            db.execute_with_binds(
                query, {"spent": amount * potion.quantity, "color": color}
            )

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # iteratively brewing the potion we have the least of and we have the ingredients for
    # until we hit the max potions
    MAX_POTIONS = 300

    query = text("(SELECT sum(quantity)::int from potions)")
    total_potions = db.execute(query).scalar_one()
    fluids = db.get_fluid_counts()
    potions = db.get_potions()
    brewing_plan = {}

    while total_potions < MAX_POTIONS:
        brewing_order = sorted(potions.values(), key=lambda potion: potion["quantity"])
        for potion in brewing_order:
            can_brew = potionUtils.have_needed_fluids(fluids, potion["potion_type"])
            if not can_brew:
                continue

            sku = potion["sku"]
            potions[sku]["quantity"] += 1
            brewing_plan[sku] = brewing_plan.get(sku, 0) + 1
            total_potions += 1

            this_potion_type = potionUtils.potion_type_to_dict(
                potion["potion_type"]
            ).items()
            for color, amount in this_potion_type:
                fluids[color] -= int(amount)
            break
        else:
            # only gets triggered if we get through the sorted order
            break

    return [
        {"potion_type": potions[sku]["potion_type"], "quantity": amount}
        for sku, amount in brewing_plan.items()
    ]
