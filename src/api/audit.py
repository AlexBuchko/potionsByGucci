from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from sqlalchemy import text
from src.api import database as db
from src.api import potionUtils

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.get("/inventory")
def get_inventory():
    """ """

    gold = db.get_gold()
    query = """
        SELECT
            (SELECT sum(change)::int from potions_ledger) as sum_potions,
            (SELECT sum(change)::int from fluids_ledger) as sum_fluids
    """
    [num_potions, num_fluids] = db.execute(text(query)).first()
    return {"number_of_potions": num_potions, "ml_in_barrels": num_fluids, "gold": gold}


class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool


# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
