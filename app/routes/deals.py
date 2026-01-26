from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def deals_test():
    return {"message": "Deals route working"}
