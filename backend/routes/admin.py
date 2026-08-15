from datetime import datetime, date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from database import get_db_connection
from models import UserUpdate, UserCreateAdmin
from auth import get_current_admin, hash_password
from utils import time_to_str

router = APIRouter()

# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================
@router.get("/users")
async def get_all_users(current_user: dict = Depends(get_current_admin)):
    """Получить список всех пользователей (только для админа)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                id,
                email,
                name,
                phone,
                role,
                created_at,
                last_login
            FROM users
            WHERE is_active = 1
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.post("/users")
async def create_user(
    user: UserCreateAdmin,
    current_user: dict = Depends(get_current_admin),
):
    """Создать пользователя от имени администратора."""
    if user.role not in ("user", "admin"):
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    if len(user.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters",
        )

    connection = get_db_connection()

    if connection is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            """,
            (user.email,),
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists",
            )

        hashed_password = hash_password(user.password)

        cursor.execute(
            """
            INSERT INTO users (
                email,
                password_hash,
                name,
                phone,
                role,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, 1)
            """,
            (
                user.email,
                hashed_password,
                user.name,
                user.phone or "",
                user.role,
            ),
        )

        user_id = cursor.lastrowid

        connection.commit()

        return {
            "message": "User created successfully",
            "user_id": user_id,
            "role": user.role,
        }

    except HTTPException:
        raise

    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@router.get("/users/{user_id}/bookings")
async def get_user_bookings(user_id: int, current_user: dict = Depends(get_current_admin)):
    """Получить активные бронирования пользователя (только для админа)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                b.id,
                b.lane_id,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                l.name as lane_name
            FROM bookings b
            JOIN lanes l ON b.lane_id = l.id
            WHERE b.user_id = %s
            ORDER BY b.booking_date DESC, b.start_time DESC
        """, (user_id,))
        
        bookings = cursor.fetchall()
        
        # Форматируем время
        for booking in bookings:
            booking["start_time"] = time_to_str(booking["start_time"])
            booking["end_time"] = time_to_str(booking["end_time"])
        
        return {"bookings": bookings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.put("/users/{user_id}")
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    current_user: dict = Depends(get_current_admin)
):
    """Обновить данные пользователя (только для админа)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        # Редактировать можно только активного пользователя.
        cursor.execute(
            """
            SELECT id, role
            FROM users
            WHERE id = %s
              AND is_active = 1
            """,
            (user_id,),
        )
        existing_user = cursor.fetchone()

        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail="Active user not found",
            )
        
        updates = []
        values = []
        
        if user_update.name is not None:
            updates.append("name = %s")
            values.append(user_update.name)
        
        if user_update.phone is not None:
            updates.append("phone = %s")
            values.append(user_update.phone)
        
        if user_update.email is not None:
            # Проверяем, не занят ли новый email
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", 
                         (user_update.email, user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already in use")
            
            updates.append("email = %s")
            values.append(user_update.email)
        
        if user_update.password is not None:
            if len(user_update.password) < 6:
                raise HTTPException(
                    status_code=400,
                    detail="Password must contain at least 6 characters",
                )

            hashed_password = hash_password(user_update.password)
            updates.append("password_hash = %s")
            values.append(hashed_password)
        
        if user_update.role is not None:
            if user_update.role not in ('user', 'admin'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid role",
                )

            # Администратор не может снять права администратора
            # со своей собственной учётной записи.
            if (
                user_id == current_user["user_id"]
                and existing_user[1] == "admin"
                and user_update.role != "admin"
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Cannot remove your own admin role",
                )

            updates.append("role = %s")
            values.append(user_update.role)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        
        connection.commit()
        return {"message": "User updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_admin)):
    """Удалить пользователя (только для админа)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Запрещаем удалять самого себя
        if user[0] == current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Cannot delete yourself")
        
        # Архивируем пользователя вместо физического удаления.
        # Исходный email освобождаем, чтобы его можно было
        # использовать для новой регистрации.
        archived_email = (
            f"deleted-{user_id}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            "@bro.invalid"
        )

        cursor.execute(
            """
            UPDATE users
            SET
                email = %s,
                is_active = 0,
                deleted_at = NOW()
            WHERE id = %s
            AND is_active = 1
            """,
            (archived_email, user_id),
        )

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Active user not found",
            )

        connection.commit()

        return {
            "message": "User archived successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== УПРАВЛЕНИЕ БРОНИРОВАНИЯМИ ====================
@router.get("/bookings")
async def get_all_bookings(
    current_user: dict = Depends(get_current_admin),
    date: Optional[str] = None,
    status: Optional[str] = None
):
    """Получить все бронирования (только для админа)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT 
                b.id,
                b.lane_id,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                l.name as lane_name,
                u.name as user_name,
                u.phone as user_phone,
                u.email as user_email,
                b.user_id
            FROM bookings b
            JOIN lanes l ON b.lane_id = l.id
            JOIN users u ON b.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if date:
            query += " AND b.booking_date = %s"
            params.append(date)
        
        if status:
            query += " AND b.status = %s"
            params.append(status)
        else:
            query += " AND b.status IN ('pending', 'confirmed')"
        
        query += " ORDER BY b.booking_date DESC, b.start_time DESC"
        
        cursor.execute(query, params)
        bookings = cursor.fetchall()
        
        # Форматируем время
        for booking in bookings:
            booking['start_time'] = time_to_str(booking['start_time'])
            booking['end_time'] = time_to_str(booking['end_time'])
        
        return {"bookings": bookings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.put("/bookings/{booking_id}/confirm")
async def confirm_booking(booking_id: int, current_user: dict = Depends(get_current_admin)):
    """Подтвердить бронирование (только для админа)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        # Проверяем, существует ли бронирование и имеет статус 'pending'
        cursor.execute("SELECT id, status FROM bookings WHERE id = %s", (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking[1] != 'pending':
            raise HTTPException(status_code=400, detail="Booking is not pending confirmation")
        
        # Подтверждаем бронирование
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'confirmed'
            WHERE id = %s
              AND status = 'pending'
            """,
            (booking_id,),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            raise HTTPException(
                status_code=409,
                detail="Booking status changed concurrently",
            )
        connection.commit()
        
        return {"message": "Booking confirmed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.put("/bookings/{booking_id}/reject")
async def reject_booking(booking_id: int, current_user: dict = Depends(get_current_admin)):
    """Отклонить бронирование (только для админа)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        # Проверяем, существует ли бронирование и имеет статус 'pending'
        cursor.execute("SELECT id, status FROM bookings WHERE id = %s", (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking[1] != 'pending':
            raise HTTPException(status_code=400, detail="Booking is not pending confirmation")
        
        # Отклоняем бронирование
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'rejected_by_admin'
            WHERE id = %s
              AND status = 'pending'
            """,
            (booking_id,),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            raise HTTPException(
                status_code=409,
                detail="Booking status changed concurrently",
            )
        connection.commit()
        
        return {"message": "Booking rejected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.delete("/cleanup-expired-bookings")
async def cleanup_expired_bookings(
    current_user: dict = Depends(get_current_admin)
):
    """Обновить статусы фактически прошедших бронирований."""
    connection = get_db_connection()

    if not connection:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )

    try:
        cursor = connection.cursor()

        moscow_tz = ZoneInfo("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)
        now_db = now_moscow.replace(tzinfo=None)

        cursor.execute(
            """
            UPDATE bookings
            SET status = 'rejected_by_admin'
            WHERE status = 'pending'
              AND TIMESTAMP(booking_date, start_time) <= %s
            """,
            (now_db,),
        )

        rejected_pending = cursor.rowcount

        cursor.execute(
            """
            UPDATE bookings
            SET status = 'completed'
            WHERE status = 'confirmed'
              AND TIMESTAMP(booking_date, end_time) <= %s
            """,
            (now_db,),
        )

        updated_completed = cursor.rowcount

        connection.commit()

        return {
            "message": "Cleanup completed",
            "rejected_pending": rejected_pending,
            "updated_to_completed": updated_completed,
            "now": now_moscow.isoformat(),
        }

    except Exception as e:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

