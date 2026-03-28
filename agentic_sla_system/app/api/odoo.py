from fastapi import APIRouter
from app.services.odoo_sync import sync_odoo_tickets

router = APIRouter()

@router.post("/odoo/sync")
def sync():
    sync_odoo_tickets()
    return {"message": "Odoo tickets synced"}