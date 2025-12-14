from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from app.schemas import UserLogin, UserRead
from app.users import get_user_manager, cookie_transport, auth_backend

auth_router = r = APIRouter()

@r.post("/login", response_model=UserRead)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    user_manager=Depends(get_user_manager)
):
    user = await user_manager.authenticate(credentials)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = await auth_backend.get_strategy().write_token(user)
    cookie_response = await cookie_transport.get_login_response(token)
    response = await cookie_transport.get_login_response(token)
    response = JSONResponse(content={"status": "Logged in"})
    if "set-cookie" in cookie_response.headers:
        response.headers["set-cookie"] = cookie_response.headers["set-cookie"]

    return response

@r.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"detail": "Logged out"}