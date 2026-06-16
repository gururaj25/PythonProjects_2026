from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    return {"message": "OAuth integration coming in Step 2"}