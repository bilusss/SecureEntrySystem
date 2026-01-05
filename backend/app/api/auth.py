from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import UserLogin
from app.users import get_user_manager, cookie_transport, auth_backend

auth_router = r = APIRouter()

@r.post("/login")
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    user_manager=Depends(get_user_manager)
):
    # Convert UserLogin to OAuth2PasswordRequestForm-like object
    class CredentialsWrapper:
        def __init__(self, email: str, password: str):
            self.username = email
            self.password = password
    
    creds = CredentialsWrapper(credentials.username, credentials.password)
    user = await user_manager.authenticate(creds)
    
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = await auth_backend.get_strategy().write_token(user)
    cookie_response = await cookie_transport.get_login_response(token)
    response = JSONResponse(content={"status": "Logged in"})
    if "set-cookie" in cookie_response.headers:
        response.headers["set-cookie"] = cookie_response.headers["set-cookie"]

    return response

@r.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"detail": "Logged out"}