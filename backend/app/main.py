from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.users import fastapi_users, auth_backend
from contextlib import asynccontextmanager
import uvicorn
import os
from app import settings
from app.api.employees import employees_router
from app.api.entries import entries_router
from app.api.auth import auth_router
from app.db import init_db
from app.schemas import UserRead, UserCreate


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

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://172.18.0.3:5173",  # Docker network
        "http://0.0.0.0:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["set-cookie"],
)

# Serve uploaded photos
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


app.include_router(router=employees_router, prefix="/api", tags=["employees"])
app.include_router(router=entries_router, prefix="/api", tags=["entries"])

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)


app.include_router(
    fastapi_users.get_register_router(
        user_schema=UserRead,
        user_create_schema=UserCreate
    ),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", reload=True, port=8888)
