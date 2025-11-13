import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Account, Order

app = FastAPI(title="MLBB Account Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class ObjectIdStr(BaseModel):
    id: str


def to_serializable(doc: dict):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # convert datetime to isoformat if present
    for k, v in list(doc.items()):
        try:
            import datetime as _dt
            if isinstance(v, (_dt.datetime, _dt.date)):
                doc[k] = v.isoformat()
        except Exception:
            pass
    return doc


@app.get("/")
def read_root():
    return {"message": "MLBB Account Store API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "N/A"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Accounts
@app.post("/api/accounts", response_model=dict)
def create_account(account: Account):
    try:
        new_id = create_document("account", account)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts", response_model=List[dict])
def list_accounts(q: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, rank: Optional[str] = None):
    try:
        filter_q = {"is_available": True}
        if q:
            filter_q["title"] = {"$regex": q, "$options": "i"}
        if rank:
            filter_q["rank"] = {"$regex": f"^{rank}$", "$options": "i"}
        if min_price is not None or max_price is not None:
            price = {}
            if min_price is not None:
                price["$gte"] = float(min_price)
            if max_price is not None:
                price["$lte"] = float(max_price)
            filter_q["price"] = price
        docs = get_documents("account", filter_q)
        return [to_serializable(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/{account_id}", response_model=dict)
def get_account(account_id: str):
    try:
        doc = db["account"].find_one({"_id": ObjectId(account_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Account not found")
        return to_serializable(doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Orders
@app.post("/api/orders", response_model=dict)
def create_order(order: Order):
    try:
        # make sure account exists and available
        acc = db["account"].find_one({"_id": ObjectId(order.account_id), "is_available": True})
        if not acc:
            raise HTTPException(status_code=404, detail="Account not available")
        new_id = create_document("order", order)
        # mark account not available
        db["account"].update_one({"_id": ObjectId(order.account_id)}, {"$set": {"is_available": False}})
        return {"id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders", response_model=List[dict])
def list_orders(status: Optional[str] = None):
    try:
        filter_q = {}
        if status:
            filter_q["status"] = status
        docs = get_documents("order", filter_q)
        return [to_serializable(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
