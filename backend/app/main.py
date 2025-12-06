from fastapi import FastAPI
import uvicorn
from app.api.employees import employees_router
from app.db import init_db

app = FastAPI(title="SecureEntryBackend", docs_url="/api/docs", openapi_url="/api")


app.include_router(router=employees_router, prefix="/api", tags=["employees"])

@app.on_event("startup")
def init():
    init_db()

@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", reload=True, port=8888)
