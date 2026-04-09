from fastapi import APIRouter
from starlette import status

router = APIRouter()

@router.get(
    path="/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    tags=["Health"]
)
async def health_check():
    return {
        "status": "ok",
    }


