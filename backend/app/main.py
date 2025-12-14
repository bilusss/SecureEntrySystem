from fastapi import FastAPI
from contextlib import asynccontextmanager
from app import settings
import uvicorn
from app.api.employees import employees_router
from app.api.entries import entries_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    yield


app = FastAPI(
    title="SecureEntryBackend",
    docs_url="/api/docs",
    openapi_url="/api",
    lifespan=lifespan,
)


app.include_router(router=employees_router, prefix="/api", tags=["employees"])
app.include_router(router=entries_router, prefix="/api", tags=["entries"])


@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", reload=True, port=8888)
