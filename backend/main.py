from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, bookings, admin  # lanes пока закомментируем

app = FastAPI(title="Bro Curling API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bro.curling76.ru"],  # Пока для теста разрешаем все
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(auth, prefix="/api", tags=["auth"])
app.include_router(bookings, prefix="/api", tags=["bookings"])
app.include_router(admin, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "Bro Curling API"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
