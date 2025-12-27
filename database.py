import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_NAME = "gearguard"
DB_USER = "postgres"
DB_PASSWORD = "Admin@123"
DB_HOST = "localhost"
DB_PORT = 5433


def create_database():
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))

    if cursor.fetchone() is None:
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print("Database created:", DB_NAME)
    else:
        print("Database already exists:", DB_NAME)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database()
