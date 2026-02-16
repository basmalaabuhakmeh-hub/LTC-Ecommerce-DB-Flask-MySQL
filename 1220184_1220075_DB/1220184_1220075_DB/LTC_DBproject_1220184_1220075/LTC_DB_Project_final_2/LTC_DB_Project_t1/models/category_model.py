# models/category_model.py
from database.db import get_db_connection


def get_all_categories():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Category ORDER BY category_name ASC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_category_by_id(category_id: int):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Category WHERE category_id = %s", (int(category_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def insert_category(category_name: str, category_description: str = None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Category (category_name, category_description)
        VALUES (%s, %s)
        """,
        (category_name, category_description),
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return new_id


def update_category_full(category_id: int, category_name: str, category_description: str = None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE Category
        SET category_name = %s, category_description = %s
        WHERE category_id = %s
        """,
        (category_name, category_description, int(category_id)),
    )
    conn.commit()
    updated = cur.rowcount
    cur.close()
    conn.close()
    return updated


def update_category_partial(category_id: int, category_name=None, category_description=None):
    fields = []
    values = []

    if category_name is not None:
        fields.append("category_name = %s")
        values.append(category_name)

    if category_description is not None:
        fields.append("category_description = %s")
        values.append(category_description)

    if not fields:
        return 0

    values.append(int(category_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE Category SET {', '.join(fields)} WHERE category_id = %s", tuple(values))
    conn.commit()
    updated = cur.rowcount
    cur.close()
    conn.close()
    return updated


def delete_category(category_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Category WHERE category_id = %s", (int(category_id),))
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()
    return deleted


def count_categories():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Category")
    (cnt,) = cur.fetchone()
    cur.close()
    conn.close()
    return cnt


def search_categories_by_name(q: str):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Category WHERE category_name LIKE %s ORDER BY category_name ASC", (f"%{q}%",))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_categories_with_product_count():
    """Get all categories with their product counts"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, COUNT(p.product_id) as product_count
        FROM Category c
        LEFT JOIN Product p ON c.category_id = p.category_id
        GROUP BY c.category_id
        ORDER BY c.category_name ASC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_top_products_by_category(category_id, limit=3):
    """Get top selling products for a category"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        WHERE p.category_id = %s
        ORDER BY p.product_id DESC
        LIMIT %s
    """, (int(category_id), int(limit)))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
