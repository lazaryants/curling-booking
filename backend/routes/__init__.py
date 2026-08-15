from .auth import router as auth
from .bookings import router as bookings
from .admin import router as admin  # Пока закомментируем
# from .lanes import router as lanes  # Пока закомментируем

__all__ = ["auth", "bookings" , "admin"] #, "lanes"]
