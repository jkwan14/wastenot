from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import FoodIn, FoodOut, FoodUpdate, NotificationOut
from models import DBFood, DBNotification
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from schema import UserPublicDetails
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")


engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_food_items() -> list[FoodOut]:
    db = SessionLocal()
    db_items = db.query(DBFood).order_by(DBFood.name).all()
    items = []
    for db_item in db_items:
        items.append(FoodOut(
            id=db_item.id,
            name=db_item.name,
            expiration_date=db_item.expiration_date,
            category_id=db_item.category_id
        ))
    db.close()
    return items


def create_food_item(item: FoodIn) -> FoodOut:
    db = SessionLocal()
    db_item = DBFood(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    item = FoodOut(
        id=db_item.id,
        name=db_item.name,
        expiration_date=db_item.expiration_date,
        category_id=db_item.category_id
    )
    db.close()
    return item


def update_food_item(id: int, item: FoodUpdate) -> FoodOut:
    db = SessionLocal()
    db_item = db.query(DBFood).filter(DBFood.id == id).first()
    if item.name is not None:
        db_item.name = item.name
    if item.expiration_date is not None:
        db_item.expiration_date = item.expiration_date

    if item.category_id is not None:
        db_item.category_id = item.category_id

    db.commit()
    db.refresh(db_item)
    db.close()

    return FoodOut(
        id=db_item.id,
        name=db_item.name,
        expiration_date=db_item.expiration_date,
        category_id=db_item.category_id
        )


def delete_food_item(id: int) -> bool:
    db = SessionLocal()
    db_item = db.query(DBFood).filter(DBFood.id == id).first()
    db.delete(db_item)
    db.commit()
    db.close()
    return True


def get_food_item(id: int) -> FoodOut:
    db = SessionLocal()
    db_item = db.query(DBFood).filter(DBFood.id == id).first()
    db.close()
    return FoodOut(
        id=db_item.id,
        name=db_item.name,
        expiration_date=db_item.expiration_date,
        category_id=db_item.category_id

    )


def check_expiring_items():
    db = SessionLocal()
    today = datetime.now(ZoneInfo("America/New_York")).date()
    db_food_items = db.query(DBFood).all()

    for db_food_item in db_food_items:
        days_diff = (db_food_item.expiration_date - today).days

        if days_diff > 2:
            existing = db.query(DBNotification).filter(DBNotification.food_id == db_food_item.id).first()
            if existing:
                db.delete(existing)
            continue

        if days_diff == 2:
            message = f"{db_food_item.name} expires in 2 days!"
        elif days_diff == 1:
            message = f"{db_food_item.name} expires in 1 day!"
        elif days_diff == 0:
            message = f"{db_food_item.name} expires today!"
        elif days_diff == -1:
            message = f"{db_food_item.name} expired 1 day ago!"
        elif days_diff < -1:
            message = f"{db_food_item.name} expired {abs(days_diff)} days ago!"

        db_notification = db.query(DBNotification).filter(DBNotification.food_id == db_food_item.id).first()
        if db_notification:
            db_notification.message = message
            db_notification.created_at = datetime.now(timezone.utc)
        else:
            db.add(DBNotification(message=message, food_id=db_food_item.id))
    db.commit()
    db.close()


def get_notifications() -> list[NotificationOut]:
    db = SessionLocal()
    db_notifications = db.query(DBNotification).order_by(DBNotification.created_at.desc()).all()
    notifications = []
    for db_notification in db_notifications:
        notifications.append(NotificationOut(
            notification_id=db_notification.notification_id,
            message=db_notification.message,
            created_at=db_notification.created_at,
            food_id=db_notification.food_id
        ))
    db.close()
    return notifications


def validate_username_password(username: str, password: str) -> str | None:
    with SessionLocal() as db:
        account = (
            db.query(DBAccount).filter(DBAccount.username == username).first()
        )
        if not account:
            return None
        valid_credentials = bcrypt.checkpw(
            password.encode(), account.hashed_password.encode()
        )
        if not valid_credentials:
            return None
        session_token = token_urlsafe()
        account.session_token = session_token
        expires = datetime.now() + timedelta(minutes=SESSION_LIFE_MINUTES)
        account.session_expires_at = expires
        db.commit()
        return session_token


def validate_session(username: str, session_token: str) -> bool:
    with SessionLocal() as db:
        account = (
            db.query(DBAccount)
            .filter(
                DBAccount.username == username,
                DBAccount.session_token == session_token,
            )
            .first()
        )
        if not account:
            return False
        if datetime.now() >= account.session_expires_at:
            return False
        expires = datetime.now() + timedelta(minutes=SESSION_LIFE_MINUTES)
        account.session_expires_at = expires
        db.commit()
        return True


def invalidate_session(username: str, session_token: str) -> None:
    with SessionLocal() as db:
        account = (
            db.query(DBAccount)
            .filter(
                DBAccount.username == username,
                DBAccount.session_token == session_token,
            )
            .first()
        )
        if not account:
            return
        account.session_token = f"expired-{token_urlsafe()}"
        db.commit()


def create_user_account(username: str, password: str) -> bool:
    with SessionLocal() as db:
        if db.query(DBAccount).filter(DBAccount.username == username).first():
            return False
        hashed_password = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()
        ).decode()
        account = DBAccount(
            username=username,
            hashed_password=hashed_password,
            session_token=None,
            session_expires_at=None,
        )
        db.add(account)
        db.commit()
        return True


def get_user_public_details(username: str):
    with SessionLocal() as db:
        account = (
            db.query(DBAccount).filter(DBAccount.username == username).first()
        )
        if not account:
            return None
        return UserPublicDetails(username=account.username)


def get_auth_user(request: Request):
    username = request.session.get("username")
    if not username and not isinstance(username, str):
        raise HTTPException(status_code=401)
    session_token = request.session.get("session_token")
    if not session_token and not isinstance(session_token, str):
        raise HTTPException(status_code=401)
    if not validate_session(username, session_token):
        raise HTTPException(status_code=403)
    return True
