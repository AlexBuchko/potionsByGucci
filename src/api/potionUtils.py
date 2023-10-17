from sqlalchemy import text
from src.api import database as db

colors = ["red", "green", "blue", "dark"]


def get_potion_type(sku):
    query = text("SELECT potion_type from potions where sku = :sku")
    result = db.execute_with_binds(query, {"sku": sku})
    return result.scalar_one()


def get_sku_from_potion_type(potion_type):
    query = text("SELECT sku from potions WHERE potion_type = :type")
    result = db.execute_with_binds(query, {"type": potion_type})
    return result.scalar_one()


def get_color_from_barrel_type(barrel_type):
    for i, color in enumerate(colors):
        if barrel_type[i] >= 1:
            return color
    raise Exception(f"could not find color from {barrel_type}")


def potion_type_to_dict(potion_type):
    return {colors[i]: potion_type[i] for i in range(len(potion_type))}


def have_needed_fluids(fluids, potion_type):
    potion_type = potion_type_to_dict(potion_type)
    for color in fluids.keys():
        if fluids[color] < potion_type[color]:
            return False
    return True
