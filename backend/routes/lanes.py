from fastapi import APIRouter, HTTPException
from database import get_db_connection
from utils import time_to_str

router = APIRouter()

@router.get("/lanes")
async def get_lanes():
    """Получить список всех дорожек"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, number, status FROM lanes ORDER BY number")
        lanes = cursor.fetchall()
        return {"lanes": lanes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.get("/schedule/{date}")
async def get_schedule(date: str):
    """Получить расписание для указанной даты (только активные и ожидающие бронирования)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Получаем все временные слоты
        cursor.execute("SELECT id, start_time, end_time FROM time_slots ORDER BY start_time")
        time_slots = cursor.fetchall()
        
        # Получаем все дорожки
        cursor.execute("SELECT id, name, number FROM lanes ORDER BY number")
        lanes = cursor.fetchall()
        
        # Получаем ТОЛЬКО активные и ожидающие бронирования на указанную дату
        cursor.execute("""
            SELECT 
                b.lane_id,
                b.time_slot_id,
                b.id,
                b.status,
                b.user_name,
                b.user_phone
            FROM bookings b
            WHERE b.booking_date = %s 
            AND b.status IN ('pending', 'confirmed')
        """, (date,))
        
        bookings = cursor.fetchall()
        
        # Создаём словарь для быстрого поиска
        bookings_dict = {}
        for booking in bookings:
            key = (booking['lane_id'], booking['time_slot_id'])
            bookings_dict[key] = booking
        
        # Формируем расписание
        schedule = []
        for lane in lanes:
            lane_schedule = {
                "lane_id": lane["id"],
                "lane_name": lane["name"],
                "slots": []
            }
            
            for slot in time_slots:
                key = (lane["id"], slot["id"])
                booking = bookings_dict.get(key)
                
                slot_info = {
                    "id": slot["id"],
                    "start_time": time_to_str(slot["start_time"]),
                    "end_time": time_to_str(slot["end_time"]),
                    "is_booked": booking is not None,
                    "booking_id": booking["id"] if booking else None,
                    "status": booking["status"] if booking else None,
                    "user_name": booking["user_name"] if booking else None,
                    "user_phone": booking["user_phone"] if booking else None
                }
                
                lane_schedule["slots"].append(slot_info)
            
            schedule.append(lane_schedule)
        
        return {"date": date, "schedule": schedule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@router.get("/schedule/week")
async def get_week_schedule(start_date: str):
    """Получить расписание на неделю (7 дней)"""
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Получаем все временные слоты
        cursor.execute("SELECT id, start_time, end_time FROM time_slots ORDER BY start_time")
        time_slots = cursor.fetchall()
        
        # Получаем все дорожки
        cursor.execute("SELECT id, name, number FROM lanes ORDER BY number")
        lanes = cursor.fetchall()
        
        # Формируем список дат недели
        dates = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        for i in range(7):
            dates.append((current_date + timedelta(days=i)).strftime('%Y-%m-%d'))
        
        # Получаем все бронирования за неделю
        placeholders = ','.join(['%s'] * len(dates))
        query = f"""
            SELECT 
                b.lane_id,
                b.time_slot_id,
                b.booking_date,
                b.id,
                b.status,
                b.user_name,
                b.user_phone
            FROM bookings b
            WHERE b.booking_date IN ({placeholders})
            AND b.status IN ('pending', 'confirmed')
        """
        cursor.execute(query, dates)
        
        bookings = cursor.fetchall()
        
        # Создаём словарь для быстрого поиска
        bookings_dict = {}
        for booking in bookings:
            key = (booking['lane_id'], booking['time_slot_id'], booking['booking_date'])
            bookings_dict[key] = booking
        
        # Формируем расписание на неделю
        week_schedule = []
        for lane in lanes:
            lane_schedule = {
                "lane_id": lane["id"],
                "lane_name": lane["name"],
                "slots": []
            }
            
            for slot in time_slots:
                slot_info = {
                    "id": slot["id"],
                    "start_time": time_to_str(slot["start_time"]),
                    "end_time": time_to_str(slot["end_time"]),
                    "bookings": []
                }
                
                # Для каждого дня недели
                for date in dates:
                    key = (lane["id"], slot["id"], date)
                    booking = bookings_dict.get(key)
                    
                    slot_info["bookings"].append({
                        "date": date,
                        "is_booked": booking is not None,
                        "booking_id": booking["id"] if booking else None,
                        "status": booking["status"] if booking else None,
                        "user_name": booking["user_name"] if booking else None,
                        "user_phone": booking["user_phone"] if booking else None
                    })
                
                lane_schedule["slots"].append(slot_info)
            
            week_schedule.append(lane_schedule)
        
        return {"start_date": start_date, "dates": dates, "schedule": week_schedule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
