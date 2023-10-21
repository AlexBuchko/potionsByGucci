from src.api.barrels import Barrel


def barrel_factory(params):
    # quantity and potion type are required
    sku = params.get("sku", "foo")
    ml_per_barrel = params.get("ml_per_barrel", 500)
    potion_type = params["potion_type"]
    price = params.get("price", 50)
    quantity = params["quantity"]

    return Barrel(
        sku=sku,
        ml_per_barrel=ml_per_barrel,
        potion_type=potion_type,
        price=price,
        quantity=quantity,
    )
