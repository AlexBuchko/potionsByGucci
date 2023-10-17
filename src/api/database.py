import os
import dotenv
from sqlalchemy import create_engine, text
from src.api import potionUtils


def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("CONNECTION_URI")


engine = create_engine(database_connection_url(), pool_pre_ping=True)


def execute(command):
    # command should be a sql alchemy text type
    with engine.begin() as connection:
        result = connection.execute(command)
        return result


def execute_with_binds(command, binds):
    # command should be a sql alchemy text type
    with engine.begin() as connection:
        result = connection.execute(command, binds)
        return result


def get_gold():
    with engine.begin() as connection:
        select_statement = text("SELECT gold from global_inventory")
        gold = connection.execute(select_statement).scalar_one()
        return gold


def get_potions():
    query = "SELECT sku, potion_type, price, quantity FROM potions"
    result = execute(text(query))
    ans = {}
    for row in result:
        row_as_dict = row._asdict()
        sku = row_as_dict["sku"]
        ans[sku] = row_as_dict
    return ans


def get_potion_counts():
    query = "SELECT sku, quantity FROM potions"
    result = execute(text(query))
    return {row.sku: row.quantity for row in result}


def get_fluid_counts():
    query = "SELECT color, quantity from fluids"
    result = execute(text(query))
    return {row.color: row.quantity for row in result}


def get_net_fluid_counts():
    potions = get_potions()
    fluid_counts = get_fluid_counts()
    for potion in potions.values():
        fluid_makeup = potions.potion_type_to_dict(potion["potion_type"])
        for color, amount in fluid_makeup.items():
            fluid_counts[color] += amount
    return fluid_counts
    # if we have 3 red potions, we basically have an extra 300ml of fluid
