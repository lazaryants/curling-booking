# /var/www/bro/backend/routes/auth.py - ТОЛЬКО роутер
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from database import get_db_connection
from models import UserRegister, UserLogin, ProfileUpdate
from auth import (
    authenticate_user, 
    create_access_token, 
    hash_password,
    get_current_user
)

router = APIRouter()

@router.post("/register")
async def register_user(user: UserRegister):
    """Регистрация нового пользователя"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        # Проверяем, существует ли пользователь с таким email
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Хешируем пароль
        hashed_password = hash_password(user.password)
        
        # Создаем пользователя
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, phone, role)
            VALUES (%s, %s, %s, %s, 'user')
        """, (
            user.email,
            hashed_password,
            user.name,
            user.phone or "",
        ))
        
        connection.commit()
        return {"message": "User registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.post("/login")
async def login_user(user: UserLogin):
    """Вход в систему"""
    authenticated_user = authenticate_user(user.email, user.password)
    
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Создаем токен
    access_token = create_access_token(
        {
            "sub": authenticated_user["email"],
            "user_id": authenticated_user["id"],
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": authenticated_user["id"],
            "email": authenticated_user["email"],
            "name": authenticated_user["name"],
            "phone": authenticated_user["phone"],
            "role": authenticated_user["role"]
        }
    }

@router.put("/profile")
async def update_profile(
    profile: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить профиль текущего пользователя"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        updates = []
        values = []
        
        if profile.name is not None:
            updates.append("name = %s")
            values.append(profile.name)
        
        if profile.phone is not None:
            updates.append("phone = %s")
            values.append(profile.phone)
        
        if profile.email is not None:
            # Проверяем, не занят ли новый email
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (profile.email, current_user["user_id"]))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already in use")
            
            updates.append("email = %s")
            values.append(profile.email)
        
        if profile.password is not None:
            if len(profile.password) < 6:
                raise HTTPException(
                    status_code=400,
                    detail="Password must contain at least 6 characters",
                )

            hashed_password = hash_password(profile.password)
            updates.append("password_hash = %s")
            values.append(hashed_password)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(current_user["user_id"])
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        
        connection.commit()
        
        return {"message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
