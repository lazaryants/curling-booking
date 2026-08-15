import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        port=os.getenv('DB_PORT', 3306)
    )
    
    if connection.is_connected():
        print("✅ Успешное подключение к MySQL")
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        print("Текущая база данных:", cursor.fetchone())
        cursor.execute("SELECT * FROM lanes LIMIT 1")
        print("Первая запись в таблице lanes:", cursor.fetchone())
        cursor.close()
        connection.close()
    else:
        print("❌ Не удалось подключиться к MySQL")
except Exception as e:
    print("❌ Ошибка подключения:", str(e))
