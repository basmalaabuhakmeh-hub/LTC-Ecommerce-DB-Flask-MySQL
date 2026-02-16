# models/dashboard_model.py
from database.db import get_db_connection


def get_total_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Product")
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return count


def get_total_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Users")
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return count


def get_total_categories():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Category")
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return count


def get_total_warehouses():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Warehouse")
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return count


def get_total_orders():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Orders")
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return count


def get_products_by_category():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.category_name, COUNT(p.product_id) as product_count
        FROM Category c
        LEFT JOIN Product p ON c.category_id = p.category_id
        GROUP BY c.category_id, c.category_name
        ORDER BY product_count DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_low_stock_products(threshold=10):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.product_id, p.product_name, 
               COALESCE(SUM(wp.quantity), 0) as total_quantity
        FROM Product p
        LEFT JOIN WarehouseProduct wp ON p.product_id = wp.product_id
        GROUP BY p.product_id, p.product_name
        HAVING total_quantity < %s OR total_quantity IS NULL
        ORDER BY total_quantity ASC
        LIMIT 10
    """, (threshold,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_recent_orders(limit=5):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.order_id, o.order_date, o.delivery_status,
               u.first_name, u.last_name,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price
        FROM Orders o
        JOIN Users u ON o.user_id = u.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        GROUP BY o.order_id, o.order_date, o.delivery_status, u.first_name, u.last_name
        ORDER BY o.order_date DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_warehouse_summary():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT w.warehouse_id,
               COUNT(DISTINCT wp.product_id) as product_count,
               COALESCE(SUM(wp.quantity), 0) as total_quantity
        FROM Warehouse w
        LEFT JOIN WarehouseProduct wp ON w.warehouse_id = wp.warehouse_id
        GROUP BY w.warehouse_id
        ORDER BY w.warehouse_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_best_sellers(limit=10):
    """Get best selling products by total quantity sold"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.product_id, p.product_name, p.price, c.category_name,
               COALESCE(SUM(oi.quantity), 0) as total_sold,
               COUNT(DISTINCT oi.order_id) as order_count
        FROM Product p
        LEFT JOIN Category c ON p.category_id = c.category_id
        LEFT JOIN OrderItem oi ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.product_name, p.price, c.category_name
        ORDER BY total_sold DESC, order_count DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_total_earnings():
    """Get total earnings from all orders"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_earnings
        FROM OrderItem oi
    """)
    (total,) = cur.fetchone()
    cur.close()
    conn.close()
    return float(total) if total else 0.0


def get_orders_by_customer():
    """Get total orders per customer"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.user_id, u.first_name, u.last_name, u.email,
               COUNT(o.order_id) as order_count,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_spent
        FROM Users u
        LEFT JOIN Orders o ON u.user_id = o.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE u.user_type = 'customer'
        GROUP BY u.user_id, u.first_name, u.last_name, u.email
        HAVING order_count > 0
        ORDER BY order_count DESC, total_spent DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_top_customers(limit=5):
    """Get top customers by total spending"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.user_id, u.first_name, u.last_name, u.email,
               COUNT(DISTINCT o.order_id) as order_count,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_spent
        FROM Users u
        JOIN Orders o ON u.user_id = o.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE u.user_type = 'customer'
        GROUP BY u.user_id, u.first_name, u.last_name, u.email
        ORDER BY total_spent DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_highest_order():
    """Get the single highest value order"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.order_id, o.order_date, o.delivery_status,
               u.first_name, u.last_name, u.email,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price
        FROM Orders o
        JOIN Users u ON o.user_id = u.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        GROUP BY o.order_id, o.order_date, o.delivery_status, u.first_name, u.last_name, u.email
        ORDER BY total_price DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_orders_per_day(limit=30):
    """Get orders count per day for the last N days"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT DATE(o.order_date) as order_day,
               COUNT(DISTINCT o.order_id) as order_count,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as daily_earnings
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        GROUP BY DATE(o.order_date)
        ORDER BY order_day DESC
        LIMIT %s
    """, (limit, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_earnings_by_month(limit=12):
    """Get earnings grouped by month"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # Use %Y-%m format in SQL - Python's % needs to be escaped as %%
    cur.execute("""
        SELECT DATE_FORMAT(o.order_date, '%Y-%m') as month,
               COUNT(DISTINCT o.order_id) as order_count,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as monthly_earnings
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
        ORDER BY month DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# =====================================================
# ENHANCED EARNINGS & CHART DATA FUNCTIONS
# =====================================================

def get_daily_earnings():
    """Get today's earnings"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as earnings,
               COUNT(DISTINCT o.order_id) as order_count
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE DATE(o.order_date) = CURDATE()
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        'earnings': float(row['earnings']) if row and row['earnings'] else 0.0,
        'order_count': row['order_count'] if row else 0
    }


def get_weekly_earnings():
    """Get this week's earnings"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as earnings,
               COUNT(DISTINCT o.order_id) as order_count
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        'earnings': float(row['earnings']) if row and row['earnings'] else 0.0,
        'order_count': row['order_count'] if row else 0
    }


def get_monthly_earnings():
    """Get this month's earnings"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as earnings,
               COUNT(DISTINCT o.order_id) as order_count
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE MONTH(o.order_date) = MONTH(CURDATE()) AND YEAR(o.order_date) = YEAR(CURDATE())
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        'earnings': float(row['earnings']) if row and row['earnings'] else 0.0,
        'order_count': row['order_count'] if row else 0
    }


def get_yearly_earnings():
    """Get this year's earnings"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as earnings,
               COUNT(DISTINCT o.order_id) as order_count
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE YEAR(o.order_date) = YEAR(CURDATE())
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        'earnings': float(row['earnings']) if row and row['earnings'] else 0.0,
        'order_count': row['order_count'] if row else 0
    }


def get_earnings_by_period(start_date, end_date):
    """Get earnings for a custom date range"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as earnings,
               COUNT(DISTINCT o.order_id) as order_count
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE o.order_date >= %s AND o.order_date <= %s
    """, (start_date, end_date))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        'earnings': float(row['earnings']) if row and row['earnings'] else 0.0,
        'order_count': row['order_count'] if row else 0
    }


def get_earnings_by_category(start_date=None, end_date=None):
    """Get earnings breakdown by product category for pie chart"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    params = []
    
    # Build the ON condition for Orders JOIN with date filtering
    order_join_condition = "oi.order_id = o.order_id"
    if start_date and end_date:
        order_join_condition += " AND o.order_date >= %s AND o.order_date <= %s"
        params.extend([start_date, end_date])
    elif start_date:
        order_join_condition += " AND o.order_date >= %s"
        params.append(start_date)
    elif end_date:
        order_join_condition += " AND o.order_date <= %s"
        params.append(end_date)
    
    query = f"""
        SELECT c.category_id, c.category_name,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as category_earnings,
               COUNT(DISTINCT oi.order_item_id) as items_sold
        FROM Category c
        LEFT JOIN Product p ON c.category_id = p.category_id
        LEFT JOIN OrderItem oi ON p.product_id = oi.product_id
        LEFT JOIN Orders o ON {order_join_condition}
        GROUP BY c.category_id, c.category_name
        ORDER BY category_earnings DESC
    """
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_sales_by_product(limit=10):
    """Get sales data for best sellers chart"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.product_id, p.product_name,
               COALESCE(SUM(oi.quantity), 0) as quantity_sold,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as revenue
        FROM Product p
        LEFT JOIN OrderItem oi ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.product_name
        HAVING quantity_sold > 0
        ORDER BY quantity_sold DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_spending_by_customer_chart(limit=10):
    """Get customer spending data for top customers chart"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.user_id,
               CONCAT(u.first_name, ' ', u.last_name) as customer_name,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_spent,
               COUNT(DISTINCT o.order_id) as order_count
        FROM Users u
        JOIN Orders o ON u.user_id = o.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE u.user_type = 'customer'
        GROUP BY u.user_id, u.first_name, u.last_name
        ORDER BY total_spent DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_earnings_over_time(days=30, start_date=None, end_date=None):
    """Get daily earnings for line chart with all dates in range filled"""
    from datetime import date as date_type, timedelta

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Determine the date range
    if start_date and end_date:
        # Convert string dates to date objects if needed
        if isinstance(start_date, str):
            start_date = date_type.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date_type.fromisoformat(end_date)
        range_start = start_date
        range_end = end_date
    else:
        # Use days interval
        range_end = date_type.today()
        range_start = range_end - timedelta(days=days - 1)

    # Query actual earnings data
    query = """
        SELECT DATE(o.order_date) as date,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as earnings
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE DATE(o.order_date) >= %s AND DATE(o.order_date) <= %s
        GROUP BY DATE(o.order_date)
        ORDER BY date ASC
    """
    cur.execute(query, (range_start, range_end))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Create a dictionary of existing earnings by date
    earnings_by_date = {}
    for row in rows:
        date_key = row['date']
        if hasattr(date_key, 'isoformat'):
            date_key = date_key.isoformat()
        earnings_by_date[date_key] = float(row['earnings']) if row['earnings'] else 0.0

    # Fill in all dates in the range with 0 for missing dates
    result = []
    current_date = range_start
    while current_date <= range_end:
        date_str = current_date.isoformat()
        result.append({
            'date': date_str,
            'earnings': earnings_by_date.get(date_str, 0.0)
        })
        current_date += timedelta(days=1)

    return result


def get_low_stock_count(threshold=10):
    """Get count of low stock items"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT p.product_id
            FROM Product p
            LEFT JOIN WarehouseProduct wp ON p.product_id = wp.product_id
            GROUP BY p.product_id
            HAVING COALESCE(SUM(wp.quantity), 0) <= %s
        ) as low_stock_items
    """, (threshold,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

