import os
import dotenv
from sqlalchemy import create_engine, text
from src.api import colors


def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("CONNECTION_URI")


engine = create_engine(database_connection_url(), pool_pre_ping=True)


def get_global_inventory():
    with engine.begin() as connection:
        select_statement = text(
            "SELECT num_red_potions, num_red_ml, num_green_potions, num_green_ml, num_blue_potions, num_blue_ml, gold from global_inventory"
        )
        current_inventory = connection.execute(select_statement)
        current_inventory = current_inventory.first()._asdict()
        return current_inventory


def get_net_potion_counts():
    inventory = get_global_inventory()
    potion_counts = {
        color: inventory[f"num_{color}_potions"] for color in colors.colors
    }
    fluid_counts = {color: inventory[f"num_{color}_ml"] for color in colors.colors}

    # if we have have 350ml of red fluid, we might as well have 3.5 red potions
    for color, num_ml in fluid_counts.items():
        potion_counts[color] += num_ml / 100
    return potion_counts


def execute(command):
    with engine.begin() as connection:
        connection.execute(text(command))
