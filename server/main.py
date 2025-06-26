import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from schema import FoodIn, FoodOut, FoodUpdate, NotificationOut, SuccessResponse, LoginCredentials, UserPublicDetails, SecretResponse
import db
from recipes import fetch_recipes
from starlette.middleware.sessions import SessionMiddleware



app = FastAPI()

origins = ["http://localhost:5173", "dpg-d108v4e3jp1c739o6pp0-a", "https://wastenot-frontend-e09l.onrender.com", "https://www.wastenotkitchen.com", "https://wastenotkitchen.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret"),
    session_cookie="session",
    max_age=60 * 60 * 2
)


@app.get("/api/food-items", response_model=list[FoodOut])
async def get_food_items() -> list[FoodOut]:
    return db.get_food_items()


@app.post("/api/food-items", response_model=FoodOut)
async def create_food_item(item: FoodIn) -> FoodOut:
    item = db.create_food_item(item)
    return item


@app.get("/api/food-items/{id}", response_model=FoodOut)
async def get_food_item(id: int) -> FoodOut:
    return db.get_food_item(id)


@app.put("/api/food-items/{id}", response_model=FoodOut)
async def update_food_item(id: int, item: FoodUpdate) -> FoodOut:
    updated_item = db.update_food_item(id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@app.delete("/api/food-items/{id}")
async def delete_food_item(id: int):
    deleted_item = db.delete_food_item(id)
    if not deleted_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return True


@app.get("/api/recipes")
def get_recipes(ingredients: str):
    recipes = fetch_recipes(ingredients)
    if not recipes:
        raise HTTPException(status_code=404, detail="Recipes not found")
    return recipes


@app.get("/api/notifications", response_model=list[NotificationOut])
def get_notifications() -> list[NotificationOut]:
    db.check_expiring_items()
    return db.get_notifications()


@app.post("/api/login", response_model=SuccessResponse)
async def session_login(
    credentials: LoginCredentials, request: Request) -> SuccessResponse:
    username = credentials.username
    password = credentials.password
    new_session_token = validate_username_password(username, password)
    if not new_session_token:
        raise HTTPException(status_code=401)
    request.session["username"] = username
    request.session["session_token"] = new_session_token
    return SuccessResponse(success=True)


@app.get("/api/logout", response_model=SuccessResponse)
async def session_logout(request: Request) -> SuccessResponse:
    username = request.session.get("username")
    if not username and not isinstance(username, str):
        return SuccessResponse(success=False)
    session_token = request.session.get("session_token")
    if not session_token and not isinstance(session_token, str):
        return SuccessResponse(success=False)
    invalidate_session(username, session_token)
    request.session.clear()
    return SuccessResponse(success=True)


@app.post("/api/signup", response_model=SuccessResponse)
async def signup(
    credentials: LoginCredentials, request: Request) -> SuccessResponse:
    username = credentials.username
    password = credentials.password
    if not username or not password:
        raise HTTPException(
            status_code=400, detail="Username and password required"
        )
    success = create_user_account(username, password)
    if not success:
        raise HTTPException(status_code=409, detail="Username already exists")
    new_session_token = validate_username_password(username, password)
    request.session["username"] = username
    request.session["session_token"] = new_session_token
    return SuccessResponse(success=True)


@app.get("/api/me", response_model=UserPublicDetails, dependencies=[Depends(db.get_auth_user)])
async def get_me(request: Request) -> UserPublicDetails:
    username = request.session.get("username")
    if not isinstance(username, str):
        raise HTTPException(status_code=404, detail="User not found")
    user_details = get_user_public_details(username)
    if not user_details:
        raise HTTPException(status_code=404, detail="User not found")
    return user_details


@app.get("/api/secret", response_model=SecretResponse, dependencies=[Depends(db.get_auth_user)])
async def secret() -> SecretResponse:
    return SecretResponse(secret="info")
