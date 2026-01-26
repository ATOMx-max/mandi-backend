from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def prices_test():
    return {"message": "Prices route working"}
