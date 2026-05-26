from fastapi import FastAPI

from api.router import router
from core.config import settings

app = FastAPI(title=settings.project_name)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
