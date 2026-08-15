from datetime import datetime
from zoneinfo import ZoneInfo

from database import get_db_connection


MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def main():
    connection = get_db_connection()

    if not connection:
        raise SystemExit("Database connection failed")

    try:
        cursor = connection.cursor()

        now_moscow = datetime.now(MOSCOW_TZ)

        # Передаём в MySQL локальное московское время без tzinfo,
        # потому что booking_date/start_time/end_time хранятся
        # как DATE/TIME без часового пояса.
        now_db = now_moscow.replace(tzinfo=None)

        # Неподтверждённая заявка теряет смысл после начала слота.
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

        # Подтверждённая бронь считается завершённой
        # после окончания временного интервала.
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

        print(
            "Cleanup completed: "
            f"rejected_pending={rejected_pending}, "
            f"updated_completed={updated_completed}, "
            f"now={now_moscow.isoformat()}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    main()
