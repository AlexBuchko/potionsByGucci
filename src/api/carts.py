from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import logging
from src.api import database as db
from sqlalchemy import text

logger = logging.getLogger("potions")
router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    query = text("INSERT INTO carts (customer_name) VALUES (:name) RETURNING cart_id")
    id = db.execute_with_binds(query, {"name": new_cart.customer}).scalar_one()
    """ """
    return {"cart_id": id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    query = text(
        "SELECT potion_id, quantity from cart_contents WHERE cart_id = :cart_id"
    )
    result = db.execute_with_binds(query, {"cart_id": cart_id})
    result = result.fetchall()
    result = [row._asdict() for row in result]
    return result


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    try:
        # getting potion ID from sku
        query = text(
            """
            INSERT INTO cart_contents (cart_id, potion_id, quantity)
            SELECT  :cart_id, potions.potion_id, :quantity
            FROM potions WHERE potions.sku = :item_sku
            """
        )
        db.execute_with_binds(
            query,
            {"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity},
        )
        return {"success": True}
    except Exception as error:
        print(error)
        return {"success": False}


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    logger.info("checkout")

    # checking that we have enough potions
    query = text(
        """
        SELECT
            CASE WHEN exists 
            (
            SELECT * from
            potions join cart_contents on potions.potion_id = cart_contents.potion_id
            WHERE cart_contents.cart_id = :cart_id AND potions.quantity < cart_contents.quantity
            )
            THEN 'TRUE'
            ELSE 'FALSE'
        END
        """
    )
    not_enough_potions = db.execute_with_binds(query, {"cart_id": cart_id}).scalar_one()
    if not_enough_potions == "TRUE":
        print("not enough potions to check out, failing")
        return {"success": False}

    # getting gold paid
    query = text(
        """
        SELECT sum(cart_contents.quantity * potions.price) 
        FROM cart_contents JOIN potions ON cart_contents.potion_id = potions.potion_id 
        WHERE cart_contents.cart_id = :cart_id
        """
    )
    gold_paid = db.execute_with_binds(query, {"cart_id": cart_id}).scalar_one()

    # updating gold
    query = text("UPDATE global_inventory SET gold = gold + :gold_gained")
    db.execute_with_binds(query, {"gold_gained": gold_paid})

    # getting sum of potions bought
    query = text(
        "select SUM(quantity) FROM cart_contents WHERE cart_contents.cart_id = :cart_id"
    )
    num_potions_bought = db.execute_with_binds(query, {"cart_id": cart_id}).scalar_one()
    # updating potion inventory
    query = text(
        """
        UPDATE potions
        SET quantity = potions.quantity - cart_contents.quantity
        FROM cart_contents
        WHERE cart_contents.potion_id = potions.potion_id and cart_id = :cart_id
        """
    )
    db.execute_with_binds(query, {"cart_id": cart_id})

    return {
        "total_potions_bought": num_potions_bought,
        "total_gold_paid": gold_paid,
    }

    POTION_PRICE = 1
    TABLE_NAME = "global_inventory"
    cart = carts[cart_id]
    inventory = db.get_gold()

    gold_count = inventory["gold"]
    potions_bought = 0
    gold_paid = 0
    print(cart)
    for sku, quantity in cart.items():
        print("iter 1", sku, quantity)
        color = sku.split("_")[0].lower()

        potion_count = inventory[f"num_{color}_potions"]

        if quantity > potion_count:
            print(
                f"ordered {quantity} {color} potions but we only have {potion_count} in stock"
            )
            continue

        revenue = POTION_PRICE * quantity
        gold_count += revenue
        potion_count -= quantity

        # logic to update database
        update_command = (
            f"UPDATE {TABLE_NAME} SET num_{color}_potions = {potion_count} WHERE id = 1"
        )
        db.execute_with_binds(update_command)

        gold_paid += revenue
        potions_bought += quantity

    update_command = f"UPDATE {TABLE_NAME} SET gold = {gold_count} WHERE id = 1"
    db.execute_with_binds(update_command)
    del carts[cart_id]

    return {
        "total_potions_bought": potions_bought,
        "total_gold_paid": gold_paid,
    }
