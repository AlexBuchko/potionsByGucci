import os

cwd = os.getcwd()
print(cwd)
from src.api import potionUtils as pu

print("hi")


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
