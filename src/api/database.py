import os
import dotenv
from sqlalchemy import create_engine, text
from src.api import potionUtils


def database_connection_url():
    dotenv.load_dotenv()

    deployment_type = os.environ.get("DEPLOYMENT_TYPE")
    if deployment_type == "development":
        return os.environ.get("DEVELOPMENT_CONNECTION_URI")
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
        select_statement = text("SELECT SUM(change) from gold_ledger")
        gold = connection.execute(select_statement).scalar_one()
        return gold


def get_potions():
    query = """
        SELECT sku, coalesce(amount, 0) as amount, potion_type, price FROM 
            potions LEFT JOIN
            (SELECT potion_id, SUM(change) as amount from potions_ledger GROUP by potion_id) ledger
            ON potions.potion_id = ledger.potion_id  
    """
    result = execute(text(query))
    return {row.sku: row._asdict() for row in result}


def get_potion_counts():
    query = """
        SELECT sku, coalesce(amount, 0) as amount FROM 
            potions LEFT JOIN
            (SELECT potion_id, SUM(change) as amount from potions_ledger GROUP by potion_id) ledger
            ON potions.potion_id = ledger.potion_id  
    """
    result = execute(text(query))
    return {row.sku: row.amount for row in result}


def get_fluid_counts():
    query = text(
        """
        SELECT color, coalesce(sum, 0) as amount FROM 
            fluids LEFT JOIN
            (SELECT fluid_id, SUM(change) as sum from fluids_ledger GROUP by fluid_id) ledger
            ON fluids.fluid_id = ledger.fluid_id
    """
    )
    result = execute(query)
    return {row.color: row.amount for row in result}


def get_net_fluid_counts():
    potions = get_potions()
    fluid_counts = get_fluid_counts()
    for potion in potions.values():
        fluid_makeup = potionUtils.potion_type_to_dict(potion["potion_type"])
        for color, amount in fluid_makeup.items():
            fluid_counts[color] += amount * potion["amount"]
    return fluid_counts
    # if we have 3 red potions, we basically have an extra 300ml of fluid
