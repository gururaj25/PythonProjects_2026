from fastapi import APIRouter
from core.sync_engine import SyncEngine

router = APIRouter()

@router.post("/run")
def run_sync(payload: dict):

    engine = SyncEngine(token=payload["token"])

    result = engine.run_sync(
        folder=payload["folder"],
        repo_name=payload["repo_name"],
        branch="main"
    )

    return result