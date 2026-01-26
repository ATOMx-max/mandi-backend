from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def products_test():
    return {"message": "Products route working"}
