# models/sale_model.py
from database.db import get_db_connection
from datetime import datetime, date
from models.product_model import get_product_total_stock


def get_all_sales(include_inactive=False):
    """Get all sales, optionally including inactive ones"""
    conn = get_db_connection()
    
    # Use regular cursor for column check
    check_cur = conn.cursor()
    check_cur.execute("""
        SELECT COUNT(*) as col_count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'Sale'
          AND COLUMN_NAME = 'is_active'
    """)
    has_is_active = check_cur.fetchone()[0] > 0
    check_cur.close()
    
    # Use dictionary cursor for main query
    cur = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM Sale"
    if has_is_active and not include_inactive:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY start_date DESC, sale_id DESC"
    
    cur.execute(query)
    rows = cur.fetchall()
    
    today = date.today()
    
    # Add default values if columns don't exist and calculate effective status
    for row in rows:
        if 'is_active' not in row:
            row['is_active'] = True
        
        # Override is_active if sale has expired (end_date < today)
        # This ensures expired sales always show as inactive, even if flag hasn't been updated
        if row.get('end_date'):
            if isinstance(row['end_date'], str):
                from datetime import datetime
                end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()
            else:
                end_date = row['end_date']
            
            if end_date < today:
                row['is_active'] = False
        
        if 'sale_name' not in row:
            row['sale_name'] = 'Sale'
        if 'sale_type' not in row:
            row['sale_type'] = 'percentage'
        if 'discount_value' not in row:
            row['discount_value'] = row.get('sale_amount', 0)
    
    cur.close()
    conn.close()
    return rows


def get_sale_by_id(sale_id):
    """Get a specific sale by ID"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Sale WHERE sale_id = %s", (int(sale_id),))
    row = cur.fetchone()
    
    if row:
        # Add default values if columns don't exist
        if 'is_active' not in row:
            row['is_active'] = True
        if 'sale_name' not in row:
            row['sale_name'] = 'Sale'
        if 'sale_type' not in row:
            row['sale_type'] = 'percentage'
        if 'discount_value' not in row:
            row['discount_value'] = row.get('sale_amount', 0)
    
    cur.close()
    conn.close()
    return row


def get_active_sales_for_product(product_id):
    """Get all active sales for a specific product"""
    conn = get_db_connection()
    
    # Use regular cursor for column checks
    check_cur = conn.cursor()
    
    # Check if is_active column exists
    check_cur.execute("""
        SELECT COUNT(*) as col_count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'Sale'
          AND COLUMN_NAME = 'is_active'
    """)
    has_is_active = check_cur.fetchone()[0] > 0
    
    # Check which discount column exists
    check_cur.execute("""
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'Sale'
          AND COLUMN_NAME IN ('discount_value', 'sale_amount')
    """)
    discount_cols = [row[0] for row in check_cur.fetchall()]
    check_cur.close()
    
    # Use dictionary cursor for main query
    cur = conn.cursor(dictionary=True)
    today = date.today()
    
    query = """
        SELECT s.*, ps.product_id
        FROM Sale s
        JOIN ProductSale ps ON s.sale_id = ps.sale_id
        WHERE ps.product_id = %s
          AND s.start_date <= %s
          AND s.end_date >= %s
    """
    params = [int(product_id), today, today]
    
    if has_is_active:
        query += " AND s.is_active = TRUE"
    
    if 'discount_value' in discount_cols:
        query += " ORDER BY s.discount_value DESC LIMIT 1"
    elif 'sale_amount' in discount_cols:
        query += " ORDER BY s.sale_amount DESC LIMIT 1"
    else:
        query += " LIMIT 1"
    
    cur.execute(query, tuple(params))
    row = cur.fetchone()
    
    if row:
        # Add default values if columns don't exist
        if 'sale_type' not in row:
            row['sale_type'] = 'percentage'
        if 'discount_value' not in row:
            row['discount_value'] = row.get('sale_amount', 0)
        if 'sale_name' not in row:
            row['sale_name'] = 'Sale'
    
    cur.close()
    conn.close()
    return row


def create_sale(sale_name, sale_type, discount_value, start_date, end_date, product_ids=None):
    """Create a new sale and optionally assign products"""
    conn = get_db_connection()
    
    # Check which columns exist using a separate cursor
    check_cur = conn.cursor()
    check_cur.execute("""
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'Sale'
    """)
    existing_columns = [row[0] for row in check_cur.fetchall()]
    check_cur.close()
    
    # Use main cursor for inserts
    cur = conn.cursor()
    
    try:
        
        # Build insert query based on available columns
        if 'sale_name' in existing_columns and 'sale_type' in existing_columns and 'discount_value' in existing_columns:
            # New schema
            cur.execute("""
                INSERT INTO Sale (sale_name, sale_type, discount_value, start_date, end_date, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
            """, (sale_name, sale_type, float(discount_value), start_date, end_date))
        else:
            # Old schema - use sale_amount
            cur.execute("""
                INSERT INTO Sale (sale_amount, start_date, end_date)
                VALUES (%s, %s, %s)
            """, (float(discount_value), start_date, end_date))
        
        sale_id = cur.lastrowid
        
        # Assign products if provided
        if product_ids:
            for product_id in product_ids:
                cur.execute("""
                    INSERT INTO ProductSale (product_id, sale_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE product_id = product_id
                """, (int(product_id), sale_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return sale_id
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise e


def update_sale(sale_id, sale_name=None, sale_type=None, discount_value=None, 
                start_date=None, end_date=None, is_active=None):
    """Update sale fields"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check which columns exist
    cur.execute("""
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'Sale'
    """)
    existing_columns = [row[0] for row in cur.fetchall()]
    
    updates = []
    params = []
    
    if sale_name is not None and 'sale_name' in existing_columns:
        updates.append("sale_name = %s")
        params.append(sale_name)
    if sale_type is not None and 'sale_type' in existing_columns:
        updates.append("sale_type = %s")
        params.append(sale_type)
    if discount_value is not None:
        if 'discount_value' in existing_columns:
            updates.append("discount_value = %s")
            params.append(float(discount_value))
        elif 'sale_amount' in existing_columns:
            updates.append("sale_amount = %s")
            params.append(float(discount_value))
    if start_date is not None:
        updates.append("start_date = %s")
        params.append(start_date)
    if end_date is not None:
        updates.append("end_date = %s")
        params.append(end_date)
    if is_active is not None and 'is_active' in existing_columns:
        updates.append("is_active = %s")
        params.append(bool(is_active))
    
    if not updates:
        cur.close()
        conn.close()
        return False
    
    params.append(int(sale_id))
    query = f"UPDATE Sale SET {', '.join(updates)} WHERE sale_id = %s"
    
    cur.execute(query, tuple(params))
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return affected > 0


def delete_sale(sale_id):
    """Delete a sale (cascade will remove ProductSale entries)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Sale WHERE sale_id = %s", (int(sale_id),))
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return affected > 0


def assign_products_to_sale(sale_id, product_ids):
    """Assign products to a sale"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Remove existing assignments
        cur.execute("DELETE FROM ProductSale WHERE sale_id = %s", (int(sale_id),))
        
        # Add new assignments
        for product_id in product_ids:
            cur.execute("""
                INSERT INTO ProductSale (product_id, sale_id)
                VALUES (%s, %s)
            """, (int(product_id), int(sale_id)))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise e


def get_products_in_sale(sale_id):
    """Get all products assigned to a sale"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        JOIN ProductSale ps ON p.product_id = ps.product_id
        LEFT JOIN Category c ON p.category_id = c.category_id
        WHERE ps.sale_id = %s
        ORDER BY p.product_name
    """, (int(sale_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def calculate_sale_price(original_price, sale):
    """Calculate the sale price based on sale type"""
    if not sale:
        return original_price
    
    # Convert discount_value to float to avoid Decimal/float mixing issues
    discount_value = float(sale['discount_value']) if sale.get('discount_value') is not None else 0
    
    if sale['sale_type'] == 'percentage':
        discount = original_price * (discount_value / 100)
        return round(original_price - discount, 2)
    elif sale['sale_type'] == 'fixed':
        return round(max(0, original_price - discount_value), 2)
    else:
        return original_price


def get_product_with_sale_price(product_id):
    """Get product with calculated sale price if applicable"""
    from models.product_model import get_product_by_id
    
    product = get_product_by_id(product_id)
    if not product:
        return None
    
    original_price = float(product['price'])
    
    # Check if product has active sale and is in stock
    sale = get_active_sales_for_product(product_id)
    stock = get_product_total_stock(product_id)
    
    sale_price = original_price
    discount_percentage = 0
    is_on_sale = False
    
    if sale and stock > 0:
        # Check if sale is still valid (date and stock)
        today = date.today()
        if sale['start_date'] <= today <= sale['end_date']:
            sale_price = calculate_sale_price(original_price, sale)
            # Convert discount_value to float to avoid Decimal/float mixing issues
            discount_value = float(sale['discount_value']) if sale.get('discount_value') is not None else 0
            if sale['sale_type'] == 'percentage':
                discount_percentage = discount_value
            else:
                discount_percentage = (discount_value / original_price) * 100
            is_on_sale = True
    
    product['original_price'] = original_price
    product['sale_price'] = sale_price
    product['discount_percentage'] = discount_percentage
    product['is_on_sale'] = is_on_sale
    product['sale_info'] = sale if is_on_sale else None
    
    return product


def check_and_deactivate_expired_sales():
    """Automatically deactivate sales that have ended or products out of stock"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if is_active column exists
        cur.execute("""
            SELECT COUNT(*) as col_count
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'Sale'
              AND COLUMN_NAME = 'is_active'
        """)
        has_is_active = cur.fetchone()[0] > 0
        
        today = date.today()
        
        if has_is_active:
            # Deactivate sales past end date
            cur.execute("""
                UPDATE Sale
                SET is_active = FALSE
                WHERE is_active = TRUE AND end_date < %s
            """, (today,))
            
            # Deactivate sales for products with zero stock
            cur.execute("""
                UPDATE Sale s
                JOIN ProductSale ps ON s.sale_id = ps.sale_id
                LEFT JOIN (
                    SELECT product_id, SUM(quantity) as total_stock
                    FROM WarehouseProduct
                    GROUP BY product_id
                ) wp ON ps.product_id = wp.product_id
                SET s.is_active = FALSE
                WHERE s.is_active = TRUE
                  AND (wp.total_stock IS NULL OR wp.total_stock = 0)
            """)
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # Silently fail if there's an issue - schema might not be updated yet
        pass


def get_sales_statistics():
    """Get statistics about sales"""
    conn = get_db_connection()
    
    # Use regular cursor for column check
    check_cur = conn.cursor()
    check_cur.execute("""
        SELECT COUNT(*) as col_count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'Sale'
          AND COLUMN_NAME = 'is_active'
    """)
    has_is_active = check_cur.fetchone()[0] > 0
    check_cur.close()
    
    # Use dictionary cursor for main queries
    cur = conn.cursor(dictionary=True)
    
    today = date.today()
    
    # Active sales count
    if has_is_active:
        cur.execute("""
            SELECT COUNT(*) as active_count
            FROM Sale
            WHERE is_active = TRUE
              AND start_date <= %s
              AND end_date >= %s
        """, (today, today))
    else:
        cur.execute("""
            SELECT COUNT(*) as active_count
            FROM Sale
            WHERE start_date <= %s
              AND end_date >= %s
        """, (today, today))
    active = cur.fetchone()
    
    # Total sales count
    cur.execute("SELECT COUNT(*) as total_count FROM Sale")
    total = cur.fetchone()
    
    # Upcoming sales
    if has_is_active:
        cur.execute("""
            SELECT COUNT(*) as upcoming_count
            FROM Sale
            WHERE is_active = TRUE AND start_date > %s
        """, (today,))
    else:
        cur.execute("""
            SELECT COUNT(*) as upcoming_count
            FROM Sale
            WHERE start_date > %s
        """, (today,))
    upcoming = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        'active': active['active_count'] if active else 0,
        'total': total['total_count'] if total else 0,
        'upcoming': upcoming['upcoming_count'] if upcoming else 0
    }

