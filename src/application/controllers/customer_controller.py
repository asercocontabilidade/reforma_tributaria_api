from fastapi import APIRouter


router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/register")
def register_customer():
    ...