from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def negotiations_test():
    return {"message": "Negotiations route working"}
