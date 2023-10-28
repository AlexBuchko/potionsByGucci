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
    query = text("SELECT potion_id, amount from cart_contents WHERE cart_id = :cart_id")
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
            INSERT INTO cart_contents (cart_id, potion_id, amount)
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
            SELECT * FROM cart_contents left join 
                (SELECT potion_id, sum(change) as inventory FROM potions_ledger GROUP BY potion_id) ledger
                ON cart_contents.potion_id = ledger.potion_id
                WHERE cart_id = :cart_id AND cart_contents.amount > ledger.inventory
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
        SELECT sum(cart_contents.amount * potions.price) 
        FROM cart_contents JOIN potions ON cart_contents.potion_id = potions.potion_id 
        WHERE cart_contents.cart_id = :cart_id
        """
    )
    gold_paid = db.execute_with_binds(query, {"cart_id": cart_id}).scalar_one()

    # updating gold
    query = text("INSERT INTO gold_ledger (change) VALUES (:gold_gained)")
    db.execute_with_binds(query, {"gold_gained": gold_paid})

    # getting sum of potions bought
    query = text(
        "select SUM(amount) FROM cart_contents WHERE cart_contents.cart_id = :cart_id"
    )
    num_potions_bought = db.execute_with_binds(query, {"cart_id": cart_id}).scalar_one()

    # updating potion inventory
    query = text(
        """
        INSERT INTO potions_ledger (potion_id, change)
        SELECT cart_contents.potion_id, -1 * cart_contents.amount
        FROM cart_contents
        WHERE cart_id = :cart_id       
    """
    )
    db.execute_with_binds(query, {"cart_id": cart_id})

    return {
        "total_potions_bought": num_potions_bought,
        "total_gold_paid": gold_paid,
    }
