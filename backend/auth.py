from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt

from database import get_db_connection


SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        salt,
    )
    return hashed.decode("utf-8")


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire,
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        return None


def authenticate_user(
    email: str,
    password: str,
):
    connection = get_db_connection()

    if connection is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )

    try:
        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            AND is_active = 1
            """,
            (email,),
        )

        user = cursor.fetchone()

        if not user:
            return None

        if not verify_password(
            password,
            user["password_hash"],
        ):
            return None

        cursor.execute(
            """
            UPDATE users
            SET last_login = NOW()
            WHERE id = %s
            """,
            (user["id"],),
        )

        connection.commit()

        return user

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


async def get_current_user(
    authorization: Optional[str] = Header(None),
):
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        return None

    payload = verify_token(token)

    if not payload:
        return None

    user_id = payload.get("user_id")

    if not user_id:
        return None

    connection = get_db_connection()

    if connection is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )

    try:
        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                id,
                email,
                name,
                phone,
                role
            FROM users
            WHERE id = %s
            AND is_active = 1
            """,
            (user_id,),
        )

        user = cursor.fetchone()

        if not user:
            return None

        return {
            "user_id": user["id"],
            "sub": user["email"],
            "email": user["email"],
            "name": user["name"],
            "phone": user["phone"],
            "role": user["role"],
        }

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


async def get_current_admin(
    current_user: dict = Depends(
        get_current_user
    ),
):
    if (
        not current_user
        or current_user.get("role") != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized",
        )

    return current_user
