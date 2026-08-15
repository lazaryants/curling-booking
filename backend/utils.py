# /var/www/bro/backend/utils.py
from datetime import datetime, time, timedelta
from typing import List, Dict

def time_to_str(time_obj) -> str:
    """Преобразует объект времени в строку формата HH:MM"""
    if time_obj is None:
        return ""
    
    if isinstance(time_obj, timedelta):
        # Преобразуем timedelta в строку
        total_seconds = int(time_obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    elif isinstance(time_obj, time):
        # Если это объект времени
        return time_obj.strftime('%H:%M')
    elif isinstance(time_obj, str):
        # Если это уже строка
        return time_obj[:5] if time_obj else ""
    else:
        return str(time_obj)[:5] if time_obj else ""

def generate_time_slots() -> List[Dict]:
    """Генерирует список временных слотов с 10:00 до 22:00 по 1 часу"""
    slots = []
    for hour in range(10, 22):
        start_time = f"{hour:02d}:00"
        end_time = f"{hour+1:02d}:00"
        slots.append({
            "start_time": start_time,
            "end_time": end_time,
            "id": hour - 9  # Для совместимости со старым фронтендом (id 1-12)
        })
    return slots

def check_time_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """Проверяет пересечение временных интервалов"""
    def to_minutes(t: str) -> int:
        h, m = map(int, t.split(':'))
        return h * 60 + m
    
    s1, e1 = to_minutes(start1), to_minutes(end1)
    s2, e2 = to_minutes(start2), to_minutes(end2)
    
    return not (e1 <= s2 or e2 <= s1)
