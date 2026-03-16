import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
    except psycopg2.Error as e:
        print("Database connection error:", e)
        return None


def get_memories():
    conn = get_connection()

    if conn is None:
        return []

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM memory ORDER BY id DESC LIMIT 10")
                rows = cursor.fetchall()
                return rows

    except psycopg2.Error as e:
        print("Database query error:", e)
        return []


def clear_whole_database():
    conn = get_connection()

    if conn is None:
        return []
    
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE memory")
    
    except psycopg2.Error as e:
        print("Database query error:", e)
        return []
    

def store_memory(text):
    conn = get_connection()

    if conn is None:
        return False

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO memory (content) VALUES (%s)",
                    (text,)
                )
        return True

    except psycopg2.Error as e:
        print("Database insert error:", e)
        return False

clear_whole_database()