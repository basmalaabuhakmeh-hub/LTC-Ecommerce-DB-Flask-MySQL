# models/warehouse_model.py
from database.db import get_db_connection


def get_all_warehouses():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT w.*,
               COUNT(DISTINCT wp.product_id) AS product_count,
               COALESCE(SUM(wp.quantity), 0) AS total_quantity
        FROM Warehouse w
        LEFT JOIN WarehouseProduct wp ON w.warehouse_id = wp.warehouse_id
        GROUP BY w.warehouse_id
        ORDER BY w.warehouse_id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_warehouse_by_id(warehouse_id: int):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Warehouse WHERE warehouse_id = %s", (int(warehouse_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def insert_warehouse():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Warehouse () VALUES ()")
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return new_id


def delete_warehouse(warehouse_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Warehouse WHERE warehouse_id = %s", (int(warehouse_id),))
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()
    return deleted


def count_warehouses():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Warehouse")
    (cnt,) = cur.fetchone()
    cur.close()
    conn.close()
    return cnt


# Warehouse Product operations
def get_warehouse_products(warehouse_id: int):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT wp.*, p.product_name, p.price, c.category_name
        FROM WarehouseProduct wp
        JOIN Product p ON wp.product_id = p.product_id
        LEFT JOIN Category c ON p.category_id = c.category_id
        WHERE wp.warehouse_id = %s
        ORDER BY p.product_name ASC
    """, (int(warehouse_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_warehouse_product(warehouse_id: int, product_id: int):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT wp.*, p.product_name, p.price, c.category_name
        FROM WarehouseProduct wp
        JOIN Product p ON wp.product_id = p.product_id
        LEFT JOIN Category c ON p.category_id = c.category_id
        WHERE wp.warehouse_id = %s AND wp.product_id = %s
    """, (int(warehouse_id), int(product_id)))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def add_product_to_warehouse(warehouse_id: int, product_id: int, quantity: int, employee_id: int = None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO WarehouseProduct (warehouse_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = quantity + %s
    """, (int(warehouse_id), int(product_id), int(quantity), int(quantity)))
    updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    return updated


def update_warehouse_product_quantity(warehouse_id: int, product_id: int, quantity: int, employee_id: int = None):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get current quantity for calculating the change
    cur.execute("""
        SELECT quantity FROM WarehouseProduct
        WHERE warehouse_id = %s AND product_id = %s
    """, (int(warehouse_id), int(product_id)))
    current = cur.fetchone()
    old_quantity = current[0] if current else 0

    cur.execute("""
        UPDATE WarehouseProduct
        SET quantity = %s
        WHERE warehouse_id = %s AND product_id = %s
    """, (int(quantity), int(warehouse_id), int(product_id)))
    updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    return updated


def remove_product_from_warehouse(warehouse_id: int, product_id: int, employee_id: int = None):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get current quantity for logging
    cur.execute("""
        SELECT quantity FROM WarehouseProduct
        WHERE warehouse_id = %s AND product_id = %s
    """, (int(warehouse_id), int(product_id)))
    current = cur.fetchone()
    old_quantity = current[0] if current else 0

    cur.execute("""
        DELETE FROM WarehouseProduct
        WHERE warehouse_id = %s AND product_id = %s
    """, (int(warehouse_id), int(product_id)))
    deleted = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    return deleted


def get_all_products_for_warehouse():
    """Get all products available to add to warehouse"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        LEFT JOIN Category c ON p.category_id = c.category_id
        ORDER BY p.product_name ASC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_low_stock_items_detailed(threshold=10):
    """
    Get items with low stock including warehouse details.
    Returns products with total quantity <= threshold across all warehouses.
    """
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.product_id, p.product_name, p.price,
               c.category_id, c.category_name,
               COALESCE(SUM(wp.quantity), 0) as total_quantity,
               GROUP_CONCAT(
                   CONCAT(w.warehouse_id, ':', COALESCE(wp.quantity, 0))
                   ORDER BY w.warehouse_id
                   SEPARATOR ','
               ) as warehouse_quantities
        FROM Product p
        LEFT JOIN Category c ON p.category_id = c.category_id
        LEFT JOIN WarehouseProduct wp ON p.product_id = wp.product_id
        LEFT JOIN Warehouse w ON wp.warehouse_id = w.warehouse_id
        GROUP BY p.product_id, p.product_name, p.price, c.category_id, c.category_name
        HAVING total_quantity <= %s
        ORDER BY total_quantity ASC, p.product_name ASC
    """, (threshold,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Parse warehouse quantities into a more usable format
    for row in rows:
        if row['warehouse_quantities']:
            quantities = {}
            for pair in row['warehouse_quantities'].split(','):
                wh_id, qty = pair.split(':')
                quantities[int(wh_id)] = int(qty)
            row['warehouse_breakdown'] = quantities
        else:
            row['warehouse_breakdown'] = {}

    return rows


def get_all_warehouse_ids():
    """Get list of all warehouse IDs for column headers"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT warehouse_id FROM Warehouse ORDER BY warehouse_id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]


def get_employee_warehouse_activity(employee_id: int, limit: int = 50):
    """Get warehouse transactions made by a specific employee"""
    # Since WarehouseTransaction is removed, return empty list
    return []


def get_employee_warehouse_stats(employee_id: int):
    """Get warehouse statistics for a specific employee"""
    # Since WarehouseTransaction is removed, return empty stats
    return {
        'total_transactions': 0,
        'total_products_added': 0,
        'unique_warehouses': 0,
        'unique_products': 0
    }


def deduct_product_from_warehouse(product_id: int, quantity: int, employee_id: int = None, order_id: int = None):
    """
    Deduct product quantity from warehouses for order processing.
    Deducts from warehouses with available stock, starting from lowest warehouse_id.
    Returns True if successful, False if insufficient stock.
    """
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Get available stock from warehouses (ordered by warehouse_id)
        cur.execute("""
            SELECT warehouse_id, quantity
            FROM WarehouseProduct
            WHERE product_id = %s AND quantity > 0
            ORDER BY warehouse_id
        """, (int(product_id),))
        warehouses = cur.fetchall()

        # Calculate total available
        total_available = sum(w['quantity'] for w in warehouses)
        if total_available < quantity:
            cur.close()
            conn.close()
            return False  # Insufficient stock

        remaining_to_deduct = quantity
        for warehouse in warehouses:
            if remaining_to_deduct <= 0:
                break

            wh_id = warehouse['warehouse_id']
            wh_qty = warehouse['quantity']

            if wh_qty >= remaining_to_deduct:
                # This warehouse has enough
                new_qty = wh_qty - remaining_to_deduct
                deducted = remaining_to_deduct
                remaining_to_deduct = 0
            else:
                # Use all from this warehouse and continue
                new_qty = 0
                deducted = wh_qty
                remaining_to_deduct -= wh_qty

            # Update warehouse quantity
            if new_qty > 0:
                cur.execute("""
                    UPDATE WarehouseProduct
                    SET quantity = %s
                    WHERE warehouse_id = %s AND product_id = %s
                """, (new_qty, wh_id, int(product_id)))
            else:
                # Remove the entry if quantity is 0
                cur.execute("""
                    DELETE FROM WarehouseProduct
                    WHERE warehouse_id = %s AND product_id = %s
                """, (wh_id, int(product_id)))


        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"Error deducting product: {str(e)}")
        return False


def get_total_product_stock(product_id: int):
    """Get total stock of a product across all warehouses"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM WarehouseProduct
        WHERE product_id = %s
    """, (int(product_id),))
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total

