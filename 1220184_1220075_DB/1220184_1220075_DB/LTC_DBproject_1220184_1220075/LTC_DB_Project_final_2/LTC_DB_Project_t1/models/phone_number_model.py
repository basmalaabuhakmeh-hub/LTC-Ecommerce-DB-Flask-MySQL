# models/phone_number_model.py
from database.db import get_db_connection


def get_phone_numbers_by_user_id(user_id: int):
    """Get all phone numbers for a specific user"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM Phone_Number 
        WHERE user_id = %s 
        ORDER BY number_id ASC
    """, (int(user_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_phone_number_by_id(number_id: int):
    """Get a phone number by its ID"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Phone_Number WHERE number_id = %s", (int(number_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def insert_phone_number(user_id: int, phone_number: str):
    """Add a new phone number for a user"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Phone_Number (user_id, phone_number)
            VALUES (%s, %s)
        """, (int(user_id), phone_number.strip()))
        conn.commit()
        new_id = cur.lastrowid
        return new_id
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def update_phone_number(number_id: int, phone_number: str):
    """Update a phone number"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Phone_Number
            SET phone_number = %s
            WHERE number_id = %s
        """, (phone_number.strip(), int(number_id)))
        conn.commit()
        updated = cur.rowcount
        return updated
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def delete_phone_number(number_id: int):
    """Delete a phone number"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Phone_Number WHERE number_id = %s", (int(number_id),))
        conn.commit()
        deleted = cur.rowcount
        return deleted
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def count_phone_numbers_by_user(user_id: int):
    """Count phone numbers for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Phone_Number WHERE user_id = %s", (int(user_id),))
    (cnt,) = cur.fetchone()
    cur.close()
    conn.close()
    return cnt

