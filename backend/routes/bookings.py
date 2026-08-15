# /var/www/bro/backend/routes/bookings.py
from mysql.connector import IntegrityError
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, date, timedelta
import database
import models
import auth
import utils
from zoneinfo import ZoneInfo

router = APIRouter()

@router.get("/schedule/week")
async def get_week_schedule(
    start_date: str,
    current_user: dict = Depends(auth.get_current_user)
):
    """Получить расписание на неделю (только для админа)"""
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только для администратора")
    
    from datetime import datetime, timedelta
    
    # Парсим start_date
    try:
        current = datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")
    
    # Сдвигаем на ближайший понедельник
    days_to_monday = current.weekday()  # 0 = понедельник, 6 = воскресенье
    monday = current - timedelta(days=days_to_monday)
    
    connection = database.get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Ошибка подключения к БД")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Начало недели (понедельник 00:00)
        week_start = monday.strftime('%Y-%m-%d')
        # Конец недели (воскресенье 23:59)
        week_end = (monday + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Получаем все бронирования на неделю
        cursor.execute("""
            SELECT 
                b.id,
                b.lane_id,
                l.name as lane_name,
                b.booking_date,
                DATE_FORMAT(b.start_time, '%H:%i') as start_time,
                DATE_FORMAT(b.end_time, '%H:%i') as end_time,
                b.status,
                u.name as user_name,
                u.phone as user_phone
            FROM bookings b
            JOIN lanes l ON b.lane_id = l.id
            JOIN users u ON b.user_id = u.id
            WHERE b.booking_date >= %s 
            AND b.booking_date < %s
            AND b.status IN ('pending', 'confirmed')
            ORDER BY b.booking_date ASC, b.start_time ASC
        """, (week_start, week_end))
        
        bookings = cursor.fetchall()
        
        # Группируем по дням недели (пн-вс)
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        weekdays_short = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        
        week_schedule = []
        
        for i in range(7):
            day_date = monday + timedelta(days=i)
            date_str = day_date.strftime('%Y-%m-%d')
            day_bookings = []
            
            for booking in bookings:
                booking_date = booking['booking_date']
                if isinstance(booking_date, datetime):
                    booking_date_str = booking_date.strftime('%Y-%m-%d')
                else:
                    booking_date_str = str(booking_date)
                
                if booking_date_str == date_str:
                    day_bookings.append(booking)
            
            week_schedule.append({
                "date": date_str,
                "day_of_week": weekdays[i],
                "day_of_week_short": weekdays_short[i],
                "day_number": day_date.strftime('%d'),
                "month": day_date.strftime('%m'),
                "bookings": day_bookings,
                "has_bookings": len(day_bookings) > 0
            })
        
        return {
            "week_start": week_start,
            "week_end": (monday + timedelta(days=6)).strftime('%Y-%m-%d'),
            "schedule": week_schedule
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# ==================== ПОЛУЧЕНИЕ РАСПИСАНИЯ ====================
@router.get("/schedule/{date_str}")
async def get_schedule(
    date_str: str,
    current_user: Optional[dict] = Depends(auth.get_current_user),
):
    """
    Получить расписание на указанную дату.

    Публично раскрывается только занятость слота.
    Владелец бронирования получает данные своей брони.
    Администратор получает служебные данные всех активных броней.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат даты. Используйте ГГГГ-ММ-ДД",
        )

    connection = database.get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=500,
            detail="Ошибка подключения к БД",
        )

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name
            FROM lanes
            WHERE status = 'active'
            ORDER BY number
            """
        )
        lanes = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                b.id AS booking_id,
                b.lane_id,
                b.user_id,
                DATE_FORMAT(b.start_time, '%H:%i') AS start_time,
                DATE_FORMAT(b.end_time, '%H:%i') AS end_time,
                b.status,
                u.name AS user_name,
                u.phone AS user_phone
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            WHERE b.booking_date = %s
              AND b.status IN ('pending', 'confirmed')
            ORDER BY b.start_time
            """,
            (date_str,),
        )

        bookings = cursor.fetchall()
        time_slots = utils.generate_time_slots()

        current_user_id = (
            current_user.get("user_id")
            if current_user
            else None
        )

        is_admin = bool(
            current_user
            and current_user.get("role") == "admin"
        )

        schedule = []

        for lane in lanes:
            lane_schedule = {
                "lane_id": lane["id"],
                "lane_name": lane["name"],
                "slots": [],
            }

            for slot in time_slots:
                booking = None

                for candidate in bookings:
                    if candidate["lane_id"] != lane["id"]:
                        continue

                    if (
                        candidate["start_time"] == slot["start_time"]
                        and candidate["end_time"] == slot["end_time"]
                    ):
                        booking = candidate
                        break

                slot_info = {
                    "id": slot["id"],
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "is_booked": booking is not None,
                }

                if booking:
                    is_owner = (
                        current_user_id is not None
                        and booking["user_id"] == current_user_id
                    )

                    if is_admin or is_owner:
                        slot_info["booking_id"] = booking["booking_id"]
                        slot_info["status"] = booking["status"]

                    if is_admin:
                        slot_info["user_name"] = booking["user_name"]
                        slot_info["user_phone"] = booking["user_phone"]

                lane_schedule["slots"].append(slot_info)

            schedule.append(lane_schedule)

        return {
            "date": date_str,
            "schedule": schedule,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка базы данных: {str(e)}",
        )

    finally:
        if connection.is_connected():
            if cursor is not None:
                cursor.close()
            connection.close()


# ==================== СОЗДАНИЕ БРОНИРОВАНИЯ ====================
@router.post("/bookings")
async def create_booking(
    booking: models.BookingCreate,
    current_user: dict = Depends(auth.get_current_user)
):
    """Создать новое бронирование"""

    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    connection = database.get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Ошибка подключения к БД")
    
    try:
        cursor = connection.cursor()
        
        # Проверяем дату и время относительно Москвы.
        moscow_tz = ZoneInfo("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)
        today = now_moscow.date()

        booking_date = datetime.strptime(
            booking.booking_date,
            '%Y-%m-%d'
        ).date()

        if booking_date < today:
            raise HTTPException(
                status_code=400,
                detail="Нельзя бронировать прошедшие даты"
            )

        if booking_date == today:
            start_hour, start_minute = map(
                int,
                booking.start_time.split(':')
            )

            slot_start = datetime(
                booking_date.year,
                booking_date.month,
                booking_date.day,
                start_hour,
                start_minute,
                tzinfo=moscow_tz,
            )

            if slot_start <= now_moscow:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Нельзя бронировать уже начавшийся "
                        "или прошедший временной интервал"
                    )
                )
        
        # Проверяем, что время начала раньше времени окончания
        if booking.start_time >= booking.end_time:
            raise HTTPException(status_code=400, detail="Время начала должно быть раньше времени окончания")
        
        # Проверяем, что слот длится ровно 1 час
        start_dt = datetime.strptime(booking.start_time, '%H:%M')
        end_dt = datetime.strptime(booking.end_time, '%H:%M')
        if (end_dt - start_dt).seconds != 3600:
            raise HTTPException(status_code=400, detail="Длительность бронирования должна быть 1 час")
        
        # Проверяем, что время в пределах рабочего дня (10:00-22:00)
        if booking.start_time < "10:00" or booking.end_time > "22:00":
            raise HTTPException(status_code=400, detail="Бронирование возможно только с 10:00 до 22:00")
        
        # Проверяем, что дорожка существует и активна
        cursor.execute("SELECT id FROM lanes WHERE id = %s AND status = 'active'", (booking.lane_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Дорожка не найдена или неактивна")
        
        # Проверяем, нет ли уже бронирования на это время
        cursor.execute("""
            SELECT id FROM bookings 
            WHERE lane_id = %s 
            AND booking_date = %s 
            AND start_time = %s 
            AND end_time = %s
            AND status IN ('pending', 'confirmed')
        """, (
            booking.lane_id,
            booking.booking_date,
            booking.start_time + ":00",
            booking.end_time + ":00"
        ))
        
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Это время уже занято")
        
        # Определяем статус: админ сразу подтверждается
        if current_user.get("role") == "admin":
            status = "confirmed"
        else:
            status = "pending"
        
        # Создаем бронирование
        cursor.execute("""
            INSERT INTO bookings (lane_id, user_id, booking_date, start_time, end_time, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            booking.lane_id,
            current_user["user_id"],
            booking.booking_date,
            booking.start_time + ":00",
            booking.end_time + ":00",
            status
        ))
        
        booking_id = cursor.lastrowid
        connection.commit()
        
        return {
            "message": "Бронирование создано",
            "booking_id": booking_id,
            "status": status
        }
        
    except HTTPException:
        raise
    except IntegrityError as e:
        connection.rollback()

        if getattr(e, "errno", None) == 1062:
            raise HTTPException(
                status_code=409,
                detail="Это время уже занято",
            )

        raise HTTPException(
            status_code=500,
            detail="Ошибка ограничения базы данных",
        )
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка базы данных: {str(e)}",
        )
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== МОИ БРОНИРОВАНИЯ ====================
@router.get("/my-bookings")
async def get_my_bookings(current_user: dict = Depends(auth.get_current_user)):
    """Получить бронирования текущего пользователя"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    connection = database.get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Ошибка подключения к БД")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                b.id,
                b.lane_id,
                l.name as lane_name,
                b.user_id,
                u.name as user_name,
                u.phone as user_phone,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                b.comment,
                b.created_at
            FROM bookings b
            JOIN lanes l ON b.lane_id = l.id
            JOIN users u ON b.user_id = u.id
            WHERE b.user_id = %s
            ORDER BY b.booking_date DESC, b.start_time DESC
        """, (current_user["user_id"],))
        
        bookings = cursor.fetchall()
        
        # Форматируем время
        for booking in bookings:
            booking["start_time"] = utils.time_to_str(booking["start_time"])
            booking["end_time"] = utils.time_to_str(booking["end_time"])
            booking["created_at"] = booking["created_at"].isoformat()
        
        return {"bookings": bookings}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== ОТМЕНА БРОНИРОВАНИЯ ====================
@router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    current_user: dict = Depends(auth.get_current_user)
):
    """Отменить бронирование."""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Не авторизован",
        )

    connection = database.get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=500,
            detail="Ошибка подключения к БД",
        )

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                user_id,
                booking_date,
                start_time,
                status
            FROM bookings
            WHERE id = %s
        """, (booking_id,))

        booking = cursor.fetchone()

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Бронирование не найдено",
            )

        is_admin = current_user.get("role") == "admin"
        is_owner = booking[1] == current_user["user_id"]

        if not (is_admin or is_owner):
            raise HTTPException(
                status_code=403,
                detail="Нет прав для отмены этого бронирования",
            )

        if booking[4] not in ("pending", "confirmed"):
            raise HTTPException(
                status_code=400,
                detail="Это бронирование уже не активно",
            )

        if not is_admin:
            booking_date = booking[2]
            start_time_str = utils.time_to_str(booking[3])

            moscow_tz = ZoneInfo("Europe/Moscow")

            booking_datetime = datetime.strptime(
                f"{booking_date} {start_time_str}",
                "%Y-%m-%d %H:%M",
            ).replace(tzinfo=moscow_tz)

            now = datetime.now(moscow_tz)

            if (
                booking_datetime - now
            ).total_seconds() < 7200:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Нельзя отменить бронирование "
                        "менее чем за 2 часа до начала"
                    ),
                )

            cursor.execute(
                """
                UPDATE bookings
                SET status = 'cancelled_by_user'
                WHERE id = %s
                  AND status IN ('pending', 'confirmed')
                """,
                (booking_id,),
            )

            if cursor.rowcount != 1:
                connection.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="Статус бронирования уже изменился",
                )

        else:
            cursor.execute(
                """
                UPDATE bookings
                SET status = 'cancelled_by_admin'
                WHERE id = %s
                  AND status IN ('pending', 'confirmed')
                """,
                (booking_id,),
            )

            if cursor.rowcount != 1:
                connection.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="Статус бронирования уже изменился",
                )

        connection.commit()

        return {
            "message": "Бронирование отменено"
        }

    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка базы данных: {str(e)}",
        )
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

