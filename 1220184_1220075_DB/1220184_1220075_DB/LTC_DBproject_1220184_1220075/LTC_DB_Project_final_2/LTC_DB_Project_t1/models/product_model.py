# models/product_model.py
from database.db import get_db_connection


def get_all_products():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # Use subquery to get latest warranty for each product
    cur.execute("""
        SELECT p.*, c.category_name,
               w.warranty_months, w.warranty_provider
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        LEFT JOIN (
            SELECT w1.product_id, w1.warranty_months, w1.warranty_provider
            FROM Warranty w1
            INNER JOIN (
                SELECT product_id, MAX(warranty_id) as max_warranty_id
                FROM Warranty
                GROUP BY product_id
            ) w2 ON w1.product_id = w2.product_id AND w1.warranty_id = w2.max_warranty_id
        ) w ON p.product_id = w.product_id
        ORDER BY p.product_id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_product_by_id(product_id: int):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name,
               w.warranty_months, w.warranty_provider
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        LEFT JOIN Warranty w ON p.product_id = w.product_id
        WHERE p.product_id = %s
        ORDER BY w.warranty_id DESC
        LIMIT 1
    """, (int(product_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def insert_product(category_id, product_name, product_description, price):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Product (category_id, product_name, product_description, price)
            VALUES (%s, %s, %s, %s)
            """,
            (int(category_id), product_name, product_description, float(price)),
        )
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


def update_product_full(product_id, category_id, product_name, product_description, price):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE Product
            SET category_id = %s,
                product_name = %s,
                product_description = %s,
                price = %s
            WHERE product_id = %s
            """,
            (int(category_id), product_name, product_description, float(price), int(product_id)),
        )
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


def update_product_partial(product_id, category_id=None, product_name=None, product_description=None, price=None):
    fields = []
    values = []

    if category_id is not None:
        fields.append("category_id = %s")
        values.append(int(category_id))

    if product_name is not None:
        fields.append("product_name = %s")
        values.append(product_name)

    if product_description is not None:
        fields.append("product_description = %s")
        values.append(product_description)

    if price is not None:
        fields.append("price = %s")
        values.append(float(price))

    if not fields:
        return 0

    values.append(int(product_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE Product SET {', '.join(fields)} WHERE product_id = %s", tuple(values))
    conn.commit()
    updated = cur.rowcount
    cur.close()
    conn.close()
    return updated


def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Product WHERE product_id = %s", (int(product_id),))
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()
    return deleted


def count_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Product")
    (cnt,) = cur.fetchone()
    cur.close()
    conn.close()
    return cnt


def search_products_by_name(q):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        WHERE p.product_name LIKE %s
        ORDER BY p.product_id DESC
    """, (f"%{q}%",))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def filter_products_by_price(min_price, max_price):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        WHERE p.price BETWEEN %s AND %s
        ORDER BY p.product_id DESC
    """, (float(min_price), float(max_price)))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_products_by_category(category_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        WHERE p.category_id = %s
        ORDER BY p.product_id DESC
    """, (int(category_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_similar_products(product_id, category_id, limit=4):
    """Get similar products from the same category, excluding the current product"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        WHERE p.category_id = %s AND p.product_id != %s
        ORDER BY RAND()
        LIMIT %s
    """, (int(category_id), int(product_id), int(limit)))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_filtered_products(q=None, category_id=None, min_price=None, max_price=None, sort_by='newest'):
    """Get products with multiple filters applied - word by word search"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT p.*, c.category_name
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        WHERE 1=1
    """
    params = []

    if q:
        # Word by word search - split query into words and match each
        words = q.strip().split()
        for word in words:
            query += " AND (p.product_name LIKE %s OR p.product_description LIKE %s)"
            params.extend([f"%{word}%", f"%{word}%"])

    if category_id:
        query += " AND p.category_id = %s"
        params.append(int(category_id))

    if min_price is not None:
        query += " AND p.price >= %s"
        params.append(float(min_price))

    if max_price is not None:
        query += " AND p.price <= %s"
        params.append(float(max_price))

    # Sorting
    if sort_by == 'price_asc':
        query += " ORDER BY p.price ASC"
    elif sort_by == 'price_desc':
        query += " ORDER BY p.price DESC"
    elif sort_by == 'name_asc':
        query += " ORDER BY p.product_name ASC"
    elif sort_by == 'name_desc':
        query += " ORDER BY p.product_name DESC"
    else:
        query += " ORDER BY p.product_id DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_price_range():
    """Get min and max prices from all products"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT MIN(price) as min_price, MAX(price) as max_price FROM Product")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_product_total_stock(product_id):
    """Get total stock quantity for a product across all warehouses"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COALESCE(SUM(wp.quantity), 0) as total_stock
        FROM WarehouseProduct wp
        WHERE wp.product_id = %s
    """, (int(product_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['total_stock'] if row else 0


def get_product_with_stock(product_id):
    """Get product details including total stock from all warehouses"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name,
               COALESCE(SUM(wp.quantity), 0) as total_stock,
               w.warranty_months, w.warranty_provider
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        LEFT JOIN WarehouseProduct wp ON p.product_id = wp.product_id
        LEFT JOIN Warranty w ON p.product_id = w.product_id
        WHERE p.product_id = %s
        GROUP BY p.product_id, c.category_name, p.category_id, p.product_name, p.product_description, p.price, w.warranty_months, w.warranty_provider
        ORDER BY w.warranty_id DESC
        LIMIT 1
    """, (int(product_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_product_warehouse_breakdown(product_id):
    """Get stock breakdown by warehouse for a product"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT wp.warehouse_id, wp.quantity
        FROM WarehouseProduct wp
        WHERE wp.product_id = %s
        ORDER BY wp.warehouse_id ASC
    """, (int(product_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_filtered_products_with_stock(q=None, category_id=None, min_price=None, max_price=None, sort_by='newest'):
    """Get products with filters and total stock included, with sale prices"""
    from models.sale_model import get_active_sales_for_product, calculate_sale_price
    from datetime import date

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT p.*, c.category_name,
               COALESCE(SUM(wp.quantity), 0) as total_stock,
               MAX(w.warranty_months) as warranty_months,
               MAX(w.warranty_provider) as warranty_provider
        FROM Product p
        JOIN Category c ON c.category_id = p.category_id
        LEFT JOIN WarehouseProduct wp ON p.product_id = wp.product_id
        LEFT JOIN Warranty w ON p.product_id = w.product_id
        WHERE 1=1
    """
    params = []

    if q:
        words = q.strip().split()
        for word in words:
            query += " AND (p.product_name LIKE %s OR p.product_description LIKE %s)"
            params.extend([f"%{word}%", f"%{word}%"])

    if category_id:
        query += " AND p.category_id = %s"
        params.append(int(category_id))

    if min_price is not None:
        query += " AND p.price >= %s"
        params.append(float(min_price))

    if max_price is not None:
        query += " AND p.price <= %s"
        params.append(float(max_price))

    query += " GROUP BY p.product_id, c.category_name, p.category_id, p.product_name, p.product_description, p.price"

    # Sorting
    if sort_by == 'price_asc':
        query += " ORDER BY p.price ASC"
    elif sort_by == 'price_desc':
        query += " ORDER BY p.price DESC"
    elif sort_by == 'name_asc':
        query += " ORDER BY p.product_name ASC"
    elif sort_by == 'name_desc':
        query += " ORDER BY p.product_name DESC"
    else:
        query += " ORDER BY p.product_id DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Add sale price information
    today = date.today()
    for product in rows:
        original_price = float(product['price'])
        stock = product.get('total_stock', 0) or 0
        
        # Check for active sale
        sale = get_active_sales_for_product(product['product_id'])
        sale_price = original_price
        discount_percentage = 0
        is_on_sale = False
        
        if sale and stock > 0:
            if sale['start_date'] <= today <= sale['end_date']:
                sale_price = calculate_sale_price(original_price, sale)
                # Convert discount_value to float to avoid Decimal/float mixing issues
                discount_value = float(sale['discount_value']) if sale.get('discount_value') is not None else 0
                if sale['sale_type'] == 'percentage':
                    discount_percentage = discount_value
                else:
                    discount_percentage = (discount_value / original_price) * 100
                is_on_sale = True
                product['sale_name'] = sale.get('sale_name', 'Sale')
        
        product['original_price'] = original_price
        product['sale_price'] = sale_price
        product['discount_percentage'] = discount_percentage
        product['is_on_sale'] = is_on_sale
    
    return rows
