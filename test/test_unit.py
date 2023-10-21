from src.api.barrels import Barrel, State, balance_barrels
import pytest


@pytest.fixture
def catalog():
    catalog = [
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=500,
            potion_type=[1, 0, 0, 0],
            price=100,
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
            sku="SMALL_BLUE_BARREL",
            ml_per_barrel=500,
            potion_type=[0, 0, 1, 0],
            price=120,
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
    return catalog


def test_balance_barrels(catalog):
    catalog = {barrel.sku: barrel for barrel in catalog}

    state = State(fluid_counts={"red": 0, "blue": 0, "green": 0, "dark": 0}, gold=1000)
    result = balance_barrels(catalog, state)
    print(result)
    assert result == result


def test_balance_barrels_too_much_of_one(catalog):
    catalog = {barrel.sku: barrel for barrel in catalog}

    state = State(
        fluid_counts={"red": 2000, "blue": 0, "green": 0, "dark": 0}, gold=1000
    )
    result = balance_barrels(catalog, state)
    print(result)
    assert result == result
