from fastapi import APIRouter, Depends
from app.core.auth import verify_token

router = APIRouter()

@router.get("/health")
async def health(payload=Depends(verify_token)):
    return {
        "status": "ok",
    }
