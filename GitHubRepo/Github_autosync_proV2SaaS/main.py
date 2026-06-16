from fastapi import FastAPI
from api.routes_sync import router as sync_router
from api.routes_health import router as health_router
from api.routes_auth import router as auth_router

app = FastAPI(
    title="GitHub AutoSync SaaS",
    version="1.0.0"
)

app.include_router(sync_router, prefix="/sync")
app.include_router(auth_router, prefix="/auth")
app.include_router(health_router, prefix="/health")


@app.get("/")
def home():
    return {"message": "GitHub AutoSync SaaS is running 🚀"}