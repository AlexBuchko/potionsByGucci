import os

cwd = os.getcwd()
print(cwd)
from src.api import potionUtils as pu

import pytest
from fastapi import Security, Request
from fastapi.testclient import TestClient
from fastapi.security.api_key import APIKeyHeader
from src.api.server import app
from src.api.auth import get_api_key
from src.api import barrels
from src.api.barrels import Barrel
from sqlalchemy import text
from src.api import database as db
from test.factories import barrel_factory
from src.api.bottler import (
    PotionInventory,
    BottlerState,
    get_bottle_plan,
    post_deliver_bottles,
)
from src.api.carts import checkout, CartCheckout, set_item_quantity, CartItem, get_cart
from src.api.audit import get_inventory
from src.api.catalog import get_catalog


def convert_list_of_dicts(dicts):
    ans = set()
    for dict in dicts:
        sub_ans = set()
        for key, value in dict.items():
            if type(value) is list:
                sub_ans.add((key, tuple(value)))
            else:
                sub_ans.add((key, value))
        ans.add(frozenset(sub_ans))
    return ans


class TestsStateless:
    @staticmethod
    def test_get_color_from_barrel_type():
        type = [100, 0, 0, 0]
        assert pu.get_color_from_barrel_type(type) == "red"

    @staticmethod
    def test_get_potion_type():
        sku = "red"
        assert pu.get_potion_type(sku) == [100, 0, 0, 0]

    @staticmethod
    def test_get_sku_from_potion_type():
        type = [100, 0, 0, 0]
        assert pu.get_sku_from_potion_type(type) == "red"

    @staticmethod
    def test_potion_type_to_dict():
        type = [20, 30, 0, 50]
        answer = pu.potion_type_to_dict(type)
        expected = {"red": 20, "green": 30, "blue": 0, "dark": 50}
        assert answer == expected


client = TestClient(app)
api_key_header = APIKeyHeader(name="access_token", auto_error=False)


async def get_api_key_override(
    request: Request, api_key_header: str = Security(api_key_header)
):
    return api_key_header


app.dependency_overrides[get_api_key] = get_api_key_override


@pytest.fixture(autouse=True)
def admin_reset():
    response = client.post("/admin/reset")


@pytest.fixture
def test_data():
    queries = []
    queries.append(
        """INSERT INTO potions_ledger (potion_id, change) VALUES 
                 (1, 3),
                 (1, -2),
                 (5, 5),
                 (2, 2),
                 (3, 3)"""
    )
    queries.append(
        """
    INSERT INTO fluids_ledger (fluid_id, change) VALUES
         (1, 500),
         (2, 200),
         (1, -200),
         (4, 300),
         (4, -100),
         (4, 200)
                 """
    )

    queries.append("INSERT INTO carts (cart_id, customer_name) VALUES (1, 'Bob')")
    queries.append(
        "INSERT INTO cart_contents (cart_id, potion_id, amount) VALUES (1, 1, 1), (1, 5, 3)"
    )

    queries.append("INSERT INTO gold_ledger (change) VALUES (1000)")
    for query in queries:
        db.execute(text(query))


def test_get_gold():
    # arranging
    query = text("INSERT INTO gold_ledger (change) VALUES (100), (-50), (25)")
    db.execute(query)

    result = db.get_gold()
    assert result == 175


def test_get_potion_counts(test_data):
    result = db.get_potion_counts()
    assert result["red"] == 1
    assert result["purple"] == 5
    assert result["dark green"] == 0


def test_get_fluid_counts(test_data):
    result = db.get_fluid_counts()
    assert result == {"red": 300, "green": 200, "blue": 0, "dark": 400}


def test_get_net_fluid_counts(test_data):
    result = db.get_net_fluid_counts()
    assert result == {"red": 650, "green": 400, "blue": 250, "dark": 400}


def test_deliver_barrels(test_data):
    initial = db.get_fluid_counts()
    initial_gold = db.get_gold()
    input_barrels = [
        barrel_factory(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": 1,
                "ml_per_barrel": 500,
                "price": 50,
                "sku": "small_red",
            },
        ),
        barrel_factory(
            {
                "potion_type": [0, 100, 0, 0],
                "ml_per_barrel": 300,
                "quantity": 3,
                "price": 100,
                "sku": "small_blue",
            }
        ),
    ]

    barrels.post_deliver_barrels(input_barrels)
    new_fluid_counts = db.get_fluid_counts()
    assert new_fluid_counts["red"] == initial["red"] + 500
    assert new_fluid_counts["green"] == initial["green"] + 900
    new_gold = db.get_gold()
    assert new_gold == initial_gold - 350


def test_brewing_plan(test_data):
    result = get_bottle_plan()
    expected = [
        {"potion_type": [0, 0, 0, 100], "quantity": 2},
        {"potion_type": [50, 0, 0, 50], "quantity": 2},
        {"potion_type": [0, 50, 0, 50], "quantity": 2},
        {"potion_type": [100, 0, 0, 0], "quantity": 2},
        {"potion_type": [0, 100, 0, 0], "quantity": 1},
    ]
    assert convert_list_of_dicts(result) == convert_list_of_dicts(expected)


def test_deliver_bottles(test_data):
    initial_fluids = db.get_fluid_counts()
    initial_potions = db.get_potions()

    delivered_potions = [
        PotionInventory(potion_type=[0, 50, 0, 50], quantity=2),
        PotionInventory(potion_type=[0, 100, 0, 0], quantity=1),
    ]
    post_deliver_bottles(delivered_potions)

    fluids = db.get_fluid_counts()
    potions = db.get_potions()
    assert (
        potions["dark green"]["amount"] == initial_potions["dark green"]["amount"] + 2
    )
    assert potions["green"]["amount"] == initial_potions["green"]["amount"] + 1

    assert fluids["green"] == initial_fluids["green"] - 200
    assert fluids["dark"] == initial_fluids["dark"] - 100


def test_checkout(test_data):
    initial_potions = db.get_potion_counts()
    initial_gold = db.get_gold()

    result = checkout(1, CartCheckout(payment="credit"))

    assert result["total_potions_bought"] == 4
    assert result["total_gold_paid"] == 200

    new_potions = db.get_potion_counts()
    new_gold = db.get_gold()

    assert new_potions["purple"] == initial_potions["purple"] - 3
    assert new_potions["red"] == initial_potions["red"] - 1

    assert new_gold == initial_gold + 200


def test_audit(test_data):
    result = get_inventory()
    expected = {"gold": 1100, "ml_in_barrels": 900, "number_of_potions": 8}
    assert result == expected


def test_catalog(test_data):
    result = get_catalog()
    expected = [
        {
            "sku": "red",
            "name": "red",
            "price": 50,
            "potion_type": [100, 0, 0, 0],
            "quantity": 1,
        },
        {
            "sku": "green",
            "name": "green",
            "price": 50,
            "potion_type": [0, 100, 0, 0],
            "quantity": 2,
        },
        {
            "sku": "purple",
            "name": "purple",
            "price": 50,
            "potion_type": [50, 0, 50, 0],
            "quantity": 5,
        },
    ]
    assert result == expected


def test_empty_barrels():
    catalog = [
        Barrel(
            sku="LARGE_RED_BARREL",
            ml_per_barrel=10000,
            potion_type=[1, 0, 0, 0],
            price=500,
            quantity=30,
        ),
        Barrel(
            sku="MEDIUM_RED_BARREL",
            ml_per_barrel=2500,
            potion_type=[1, 0, 0, 0],
            price=250,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=500,
            potion_type=[1, 0, 0, 0],
            price=100,
            quantity=10,
        ),
        Barrel(
            sku="LARGE_GREEN_BARREL",
            ml_per_barrel=10000,
            potion_type=[0, 1, 0, 0],
            price=400,
            quantity=30,
        ),
        Barrel(
            sku="MEDIUM_GREEN_BARREL",
            ml_per_barrel=2500,
            potion_type=[0, 1, 0, 0],
            price=250,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_GREEN_BARREL",
            ml_per_barrel=500,
            potion_type=[0, 1, 0, 0],
            price=100,
            quantity=10,
        ),
        Barrel(
            sku="LARGE_BLUE_BARREL",
            ml_per_barrel=10000,
            potion_type=[0, 0, 1, 0],
            price=600,
            quantity=30,
        ),
        Barrel(
            sku="MEDIUM_BLUE_BARREL",
            ml_per_barrel=2500,
            potion_type=[0, 0, 1, 0],
            price=300,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_BLUE_BARREL",
            ml_per_barrel=500,
            potion_type=[0, 0, 1, 0],
            price=120,
            quantity=10,
        ),
        Barrel(
            sku="LARGE_DARK_BARREL",
            ml_per_barrel=10000,
            potion_type=[0, 0, 0, 1],
            price=750,
            quantity=10,
        ),
        Barrel(
            sku="MINI_RED_BARREL",
            ml_per_barrel=200,
            potion_type=[1, 0, 0, 0],
            price=60,
            quantity=1,
        ),
        Barrel(
            sku="MINI_GREEN_BARREL",
            ml_per_barrel=200,
            potion_type=[0, 1, 0, 0],
            price=60,
            quantity=1,
        ),
        Barrel(
            sku="MINI_BLUE_BARREL",
            ml_per_barrel=200,
            potion_type=[0, 0, 1, 0],
            price=60,
            quantity=1,
        ),
    ]

    result = barrels.get_wholesale_purchase_plan(catalog)
    expected = [{"quantity": 1, "sku": "SMALL_RED_BARREL"}]
    assert result == expected


def test_add_to_cart(test_data):
    set_item_quantity(1, "green", CartItem(quantity=2))
    # getting the cart's concent
    query = text("SELECT amount from cart_contents WHERE cart_id=1 AND potion_id = 2")
    result = db.execute(query).scalar_one()
    assert result == 2


def test_get_cart(test_data):
    result = get_cart(1)
    expected = [{"potion_id": 1, "amount": 1}, {"potion_id": 5, "amount": 3}]
    assert convert_list_of_dicts(result) == convert_list_of_dicts(expected)