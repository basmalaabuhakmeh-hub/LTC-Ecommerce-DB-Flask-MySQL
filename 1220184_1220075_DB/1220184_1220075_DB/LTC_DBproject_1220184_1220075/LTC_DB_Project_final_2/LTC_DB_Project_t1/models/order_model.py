# models/order_model.py
from database.db import get_db_connection
from datetime import datetime, timedelta


def get_customer_orders(user_id, period=None, status=None, start_date=None, end_date=None):
    """
    Get orders for a specific customer with optional filters.

    Args:
        user_id: The customer's user ID
        period: 'weekly', 'monthly', 'yearly', or None for all
        status: Filter by delivery_status, or None for all
        start_date: Custom start date (YYYY-MM-DD)
        end_date: Custom end date (YYYY-MM-DD)
    """
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT o.order_id, o.order_date, o.receive_date, o.delivery_status,
               a.country, a.city, a.street_no, a.building, a.apartment_no,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price,
               COUNT(DISTINCT oi.product_id) as item_count
        FROM Orders o
        LEFT JOIN Address a ON o.address_id = a.address_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE o.user_id = %s
    """
    params = [user_id]

    # Apply period filter
    if period == 'weekly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    elif period == 'monthly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
    elif period == 'yearly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"

    # Apply custom date range
    if start_date:
        query += " AND o.order_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND o.order_date <= %s"
        params.append(end_date)

    # Apply status filter
    if status:
        query += " AND o.delivery_status = %s"
        params.append(status)

    query += """
        GROUP BY o.order_id, o.order_date, o.receive_date, o.delivery_status,
                 a.country, a.city, a.street_no, a.building, a.apartment_no
        ORDER BY o.order_date DESC
    """

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_order_items(order_id):
    """Get all items in an order with product details"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT oi.order_item_id, oi.quantity, oi.price_at_order,
               p.product_id, p.product_name, p.product_description,
               c.category_id, c.category_name
        FROM OrderItem oi
        JOIN Product p ON oi.product_id = p.product_id
        LEFT JOIN Category c ON p.category_id = c.category_id
        WHERE oi.order_id = %s
        ORDER BY oi.order_item_id
    """, (int(order_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_order_by_id(order_id, user_id=None):
    """Get a single order by ID, optionally verifying ownership"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT o.order_id, o.user_id, o.order_date, o.receive_date, o.delivery_status,
               a.address_id, a.country, a.city, a.street_no, a.building, a.apartment_no,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price,
               COUNT(DISTINCT oi.product_id) as item_count
        FROM Orders o
        LEFT JOIN Address a ON o.address_id = a.address_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE o.order_id = %s
    """
    params = [int(order_id)]

    if user_id:
        query += " AND o.user_id = %s"
        params.append(int(user_id))

    query += " GROUP BY o.order_id, a.address_id"

    cur.execute(query, tuple(params))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_customer_order_stats(user_id, period=None, start_date=None, end_date=None):
    """Get order statistics for a customer"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT
            COUNT(DISTINCT o.order_id) as total_orders,
            COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_spent,
            COALESCE(AVG(sub.order_total), 0) as avg_order_value
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        LEFT JOIN (
            SELECT o2.order_id, SUM(oi2.quantity * oi2.price_at_order) as order_total
            FROM Orders o2
            JOIN OrderItem oi2 ON o2.order_id = oi2.order_id
            WHERE o2.user_id = %s
            GROUP BY o2.order_id
        ) sub ON o.order_id = sub.order_id
        WHERE o.user_id = %s
    """
    params = [user_id, user_id]

    if period == 'weekly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    elif period == 'monthly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
    elif period == 'yearly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"

    if start_date:
        query += " AND o.order_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND o.order_date <= %s"
        params.append(end_date)

    cur.execute(query, tuple(params))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_spending_by_category(user_id, period=None, start_date=None, end_date=None):
    """Get spending breakdown by category for a customer"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT c.category_id, c.category_name,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as category_spent,
               COUNT(DISTINCT oi.order_item_id) as items_bought
        FROM Orders o
        JOIN OrderItem oi ON o.order_id = oi.order_id
        JOIN Product p ON oi.product_id = p.product_id
        JOIN Category c ON p.category_id = c.category_id
        WHERE o.user_id = %s
    """
    params = [user_id]

    if period == 'weekly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    elif period == 'monthly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
    elif period == 'yearly':
        query += " AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"

    if start_date:
        query += " AND o.order_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND o.order_date <= %s"
        params.append(end_date)

    query += """
        GROUP BY c.category_id, c.category_name
        ORDER BY category_spent DESC
    """

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_customer_orders_summary(user_id):
    """Get a quick summary for dashboard - recent orders and basic stats"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Get recent orders (last 5)
    cur.execute("""
        SELECT o.order_id, o.order_date, o.delivery_status,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price,
               COUNT(DISTINCT oi.product_id) as item_count
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE o.user_id = %s
        GROUP BY o.order_id, o.order_date, o.delivery_status
        ORDER BY o.order_date DESC
        LIMIT 5
    """, (user_id,))
    recent_orders = cur.fetchall()

    # Get counts by status
    cur.execute("""
        SELECT delivery_status, COUNT(*) as count
        FROM Orders
        WHERE user_id = %s
        GROUP BY delivery_status
    """, (user_id,))
    status_counts = {row['delivery_status'] or 'Pending': row['count'] for row in cur.fetchall()}

    # Get total orders and spending
    cur.execute("""
        SELECT COUNT(DISTINCT o.order_id) as total_orders,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_spent
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE o.user_id = %s
    """, (user_id,))
    totals = cur.fetchone()

    cur.close()
    conn.close()

    return {
        'recent_orders': recent_orders,
        'status_counts': status_counts,
        'total_orders': totals['total_orders'] if totals else 0,
        'total_spent': float(totals['total_spent']) if totals and totals['total_spent'] else 0.0
    }


def get_order_statuses():
    """Get all distinct order statuses"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT delivery_status FROM Orders WHERE delivery_status IS NOT NULL ORDER BY delivery_status")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]


# =====================================================
# EMPLOYEE ORDER MANAGEMENT FUNCTIONS
# =====================================================

def get_all_orders_for_employee(user_id=None, status=None, city=None, country=None,
                                 min_price=None, max_price=None, start_date=None, end_date=None):
    """
    Get all orders for employee management with optional filters.

    Args:
        user_id: Filter by specific customer
        status: Filter by delivery_status
        city: Filter by delivery city
        country: Filter by delivery country
        min_price: Minimum order total
        max_price: Maximum order total
        start_date: Filter orders from this date
        end_date: Filter orders until this date
    """
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT o.order_id, o.user_id, o.order_date, o.receive_date, o.delivery_status,
               u.first_name, u.last_name, u.email,
               a.country, a.city, a.street_no, a.building, a.apartment_no,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price,
               COUNT(DISTINCT oi.product_id) as item_count
        FROM Orders o
        LEFT JOIN Users u ON o.user_id = u.user_id
        LEFT JOIN Address a ON o.address_id = a.address_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE 1=1
    """
    params = []

    if user_id:
        query += " AND o.user_id = %s"
        params.append(int(user_id))

    if status:
        query += " AND o.delivery_status = %s"
        params.append(status)

    if city:
        query += " AND a.city LIKE %s"
        params.append(f"%{city}%")

    if country:
        query += " AND a.country LIKE %s"
        params.append(f"%{country}%")

    if start_date:
        query += " AND o.order_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND o.order_date <= %s"
        params.append(end_date)

    query += """
        GROUP BY o.order_id, o.user_id, o.order_date, o.receive_date, o.delivery_status,
                 u.first_name, u.last_name, u.email,
                 a.country, a.city, a.street_no, a.building, a.apartment_no
    """

    # Apply price filters after grouping using HAVING
    if min_price is not None:
        query += " HAVING total_price >= %s"
        params.append(float(min_price))
        if max_price is not None:
            query += " AND total_price <= %s"
            params.append(float(max_price))
    elif max_price is not None:
        query += " HAVING total_price <= %s"
        params.append(float(max_price))

    query += " ORDER BY o.order_date DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def update_order_status(order_id, new_status, employee_id=None):
    """
    Update an order's delivery status.
    Valid statuses: Pending, Processing, Shipped, In Transit, Delivered

    When status changes to 'Processing', automatically deducts items from warehouse inventory.
    """
    from models.warehouse_model import deduct_product_from_warehouse

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Get current status to check if we're transitioning to Processing
    cur.execute("SELECT delivery_status FROM Orders WHERE order_id = %s", (int(order_id),))
    current = cur.fetchone()
    current_status = current['delivery_status'] if current else None

    # If transitioning to Processing, deduct inventory
    if new_status == 'Processing' and current_status != 'Processing':
        # Get all order items
        cur.execute("""
            SELECT product_id, quantity
            FROM OrderItem
            WHERE order_id = %s
        """, (int(order_id),))
        order_items = cur.fetchall()

        # Deduct each product from warehouse
        for item in order_items:
            success = deduct_product_from_warehouse(
                product_id=item['product_id'],
                quantity=item['quantity'],
                employee_id=employee_id,
                order_id=order_id
            )
            if not success:
                # Insufficient stock - rollback and return False
                cur.close()
                conn.close()
                return False, f"Insufficient stock for product ID {item['product_id']}"

    # Update the order status
    cur = conn.cursor()  # Get a fresh cursor
    if new_status == 'Delivered':
        cur.execute("""
            UPDATE Orders
            SET delivery_status = %s, receive_date = CURDATE()
            WHERE order_id = %s
        """, (new_status, int(order_id)))
    else:
        cur.execute("""
            UPDATE Orders
            SET delivery_status = %s
            WHERE order_id = %s
        """, (new_status, int(order_id)))

    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return affected > 0, None


def get_order_statistics_for_employee():
    """Get order statistics for employee dashboard"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Get counts by status
    cur.execute("""
        SELECT
            COALESCE(delivery_status, 'Pending') as status,
            COUNT(*) as count
        FROM Orders
        GROUP BY delivery_status
    """)
    status_counts = {row['status']: row['count'] for row in cur.fetchall()}

    # Get total orders and revenue
    cur.execute("""
        SELECT
            COUNT(DISTINCT o.order_id) as total_orders,
            COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_revenue,
            COALESCE(AVG(sub.order_total), 0) as avg_order_value
        FROM Orders o
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        LEFT JOIN (
            SELECT order_id, SUM(quantity * price_at_order) as order_total
            FROM OrderItem
            GROUP BY order_id
        ) sub ON o.order_id = sub.order_id
    """)
    totals = cur.fetchone()

    # Get today's orders
    cur.execute("""
        SELECT COUNT(*) as today_orders
        FROM Orders
        WHERE DATE(order_date) = CURDATE()
    """)
    today = cur.fetchone()

    # Get pending orders count (needs attention)
    pending_count = status_counts.get('Pending', 0)

    cur.close()
    conn.close()

    return {
        'status_counts': status_counts,
        'total_orders': totals['total_orders'] if totals else 0,
        'total_revenue': float(totals['total_revenue']) if totals and totals['total_revenue'] else 0.0,
        'avg_order_value': float(totals['avg_order_value']) if totals and totals['avg_order_value'] else 0.0,
        'today_orders': today['today_orders'] if today else 0,
        'pending_orders': pending_count
    }


def get_all_customers_for_filter():
    """Get all customers for the filter dropdown"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT DISTINCT u.user_id, u.first_name, u.last_name
        FROM Users u
        JOIN Orders o ON u.user_id = o.user_id
        ORDER BY u.first_name, u.last_name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# =====================================================
# ORDER CREATION FUNCTIONS
# =====================================================

def insert_address(country, city, street_no, building=None, apartment_no=None):
    """Insert a new address and return address_id"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO Address (country, city, street_no, building, apartment_no)
        VALUES (%s, %s, %s, %s, %s)
    """, (country, city, int(street_no), building, int(apartment_no) if apartment_no else None))
    
    address_id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return address_id


def create_order(user_id, address_id, delivery_status='Pending'):
    """Create a new order and return order_id"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO Orders (user_id, address_id, order_date, delivery_status)
        VALUES (%s, %s, CURDATE(), %s)
    """, (int(user_id), int(address_id), delivery_status))
    
    order_id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return order_id


def create_order_item(order_id, product_id, quantity, price_at_order):
    """Create an order item"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO OrderItem (order_id, product_id, quantity, price_at_order)
        VALUES (%s, %s, %s, %s)
    """, (int(order_id), int(product_id), int(quantity), float(price_at_order)))
    
    conn.commit()
    cur.close()
    conn.close()
    return True


def create_payment(order_id, method, payed_amount, payment_status='Pending'):
    """Create a payment record for an order"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO Payment (order_id, method, payed_amount, payment_status)
        VALUES (%s, %s, %s, %s)
    """, (int(order_id), method, float(payed_amount), payment_status))
    
    payment_id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return payment_id