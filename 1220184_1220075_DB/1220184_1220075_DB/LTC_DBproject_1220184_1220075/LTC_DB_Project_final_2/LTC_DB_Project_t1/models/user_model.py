from database.db import get_db_connection

def get_user_by_email(email):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Users WHERE email = %s", (email.lower().strip(),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Users WHERE user_id = %s", (int(user_id),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def insert_user(email, password_hash, first_name, last_name, date_of_birth, user_type):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Users (email, user_password, first_name, last_name, date_of_birth, user_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (email.lower().strip(), password_hash, first_name, last_name, date_of_birth, user_type))
    conn.commit()
    user_id = cur.lastrowid
    cur.close()
    conn.close()
    return user_id


def update_user_profile(user_id, first_name=None, last_name=None, date_of_birth=None, email=None):
    """Update user profile information"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        fields = []
        values = []
        
        if first_name is not None:
            fields.append("first_name = %s")
            values.append(first_name)
        
        if last_name is not None:
            fields.append("last_name = %s")
            values.append(last_name)
        
        if date_of_birth is not None:
            fields.append("date_of_birth = %s")
            values.append(date_of_birth if date_of_birth else None)
        
        if email is not None:
            fields.append("email = %s")
            values.append(email.lower().strip())
        
        if not fields:
            return 0
        
        values.append(int(user_id))
        
        cur.execute(f"UPDATE Users SET {', '.join(fields)} WHERE user_id = %s", tuple(values))
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


def update_user_password(user_id, password_hash):
    """Update user password"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Users SET user_password = %s WHERE user_id = %s", (password_hash, int(user_id)))
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


# =====================================================
# EMPLOYEE USER MANAGEMENT FUNCTIONS
# =====================================================

def get_all_users_with_spending(search=None):
    """
    Get all customers with their total spending for employee view.
    Excludes employees from the list.
    """
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.date_of_birth,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_spent,
               COUNT(DISTINCT o.order_id) as total_orders
        FROM Users u
        LEFT JOIN Orders o ON u.user_id = o.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        WHERE u.user_type = 'customer'
    """
    params = []

    if search:
        query += """ AND (u.first_name LIKE %s OR u.last_name LIKE %s OR u.email LIKE %s)"""
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    query += """
        GROUP BY u.user_id, u.first_name, u.last_name, u.email, u.date_of_birth
        ORDER BY total_spent DESC
    """

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_user_contact_details(user_id):
    """Get user's email and phone numbers for employee view"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Get user email
    cur.execute("""
        SELECT user_id, first_name, last_name, email
        FROM Users
        WHERE user_id = %s
    """, (int(user_id),))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return None

    # Get user phone numbers (Phone_Number table)
    cur.execute("""
        SELECT number_id AS phone_id, phone_number, NULL AS phone_type
        FROM Phone_Number
        WHERE user_id = %s
        ORDER BY number_id
    """, (int(user_id),))
    phones = cur.fetchall()

    cur.close()
    conn.close()

    return {
        'user_id': user['user_id'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'email': user['email'],
        'phones': phones
    }


def get_total_customers():
    """Get total count of customers (not employees)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Users WHERE user_type = 'customer'")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


def get_employee_statistics(employee_id):
    """Get warehouse transaction statistics for a specific employee"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT COUNT(*) as total_transactions,
               SUM(quantity) as total_quantity,
               COUNT(DISTINCT warehouse_id) as unique_warehouses,
               COUNT(DISTINCT product_id) as unique_products
        FROM WarehouseProduct
    """)
    warehouse_stats = cur.fetchone()

    cur.close()
    conn.close()

    return {
        'total_transactions': warehouse_stats.get('total_transactions', 0) if warehouse_stats else 0,
        'total_quantity': warehouse_stats.get('total_quantity', 0) or 0 if warehouse_stats else 0,
        'unique_warehouses': warehouse_stats.get('unique_warehouses', 0) if warehouse_stats else 0,
        'unique_products': warehouse_stats.get('unique_products', 0) if warehouse_stats else 0
    }


def get_detailed_warehouse_activity(employee_id=None):
    """Get detailed warehouse activity for reports, optionally filtered by employee"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT wp.warehouse_id, wp.product_id, wp.quantity,
               p.product_name, p.price, c.category_name
        FROM WarehouseProduct wp
        JOIN Product p ON wp.product_id = p.product_id
        LEFT JOIN Category c ON p.category_id = c.category_id
        ORDER BY wp.warehouse_id, p.product_name
        LIMIT 50
    """)
    transactions = cur.fetchall()

    cur.close()
    conn.close()

    # Convert Decimal to float for JSON serialization
    for t in transactions:
        if t.get('price'):
            t['price'] = float(t['price'])

    return transactions


def get_detailed_order_activity():
    """Get detailed order activity for reports"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Get orders with customer details
    cur.execute("""
        SELECT o.order_id, o.order_date, o.delivery_status, o.receive_date,
               u.first_name as customer_first_name, u.last_name as customer_last_name,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price
        FROM Orders o
        JOIN Users u ON o.user_id = u.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        GROUP BY o.order_id, o.order_date, o.delivery_status, o.receive_date,
                 u.first_name, u.last_name
        ORDER BY o.order_date DESC
        LIMIT 50
    """)
    orders = cur.fetchall()

    # Get order status breakdown
    cur.execute("""
        SELECT delivery_status, COUNT(*) as count
        FROM Orders
        GROUP BY delivery_status
    """)
    status_breakdown = {row['delivery_status'] or 'Pending': row['count'] for row in cur.fetchall()}

    cur.close()
    conn.close()

    # Convert date and Decimal to serializable format
    for order in orders:
        if order.get('order_date'):
            order['order_date'] = str(order['order_date'])
        if order.get('receive_date'):
            order['receive_date'] = str(order['receive_date'])
        if order.get('total_price'):
            order['total_price'] = float(order['total_price'])

    return {'orders': orders, 'status_breakdown': status_breakdown}


def deactivate_employee(employee_id):
    """Deactivate an employee"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Get employee details
        employee = get_user_by_id(employee_id)
        if not employee:
            cur.close()
            conn.close()
            print(f"Employee {employee_id} not found")
            return False
        
        # Verify employee is actually an employee (not admin or inactive)
        if employee.get('user_type') != 'employee':
            cur.close()
            conn.close()
            print(f"User {employee_id} is not an employee (type: {employee.get('user_type')})")
            return False

        # Mark the employee as inactive.
        cur.execute("UPDATE Users SET user_type = %s WHERE user_id = %s AND user_type = %s",
                    ('inactive_employee', int(employee_id), 'employee'))
        conn.commit()
        affected = cur.rowcount
        if affected == 0:
            # Employee might already be inactive or not found
            cur.close()
            conn.close()
            print(f"Warning: No rows updated for employee {employee_id} - may already be inactive")
            return False
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"Error deactivating employee: {str(e)}")
        return False


# =====================================================
# ADMIN FUNCTIONS
# =====================================================

def get_all_employees(search=None):
    """Get all employees for admin view - excludes admin user"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.date_of_birth,
               u.user_type
        FROM Users u
        WHERE u.user_type = 'employee' AND u.email != 'admin@ltc.com'
    """
    params = []

    if search:
        query += """ AND (u.first_name LIKE %s OR u.last_name LIKE %s OR u.email LIKE %s)"""
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    query += " ORDER BY u.first_name, u.last_name"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows


def get_employee_with_stats(employee_id):
    """Get employee details with statistics for profile view"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Get employee details
    cur.execute("""
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.date_of_birth,
               u.user_type
        FROM Users u
        WHERE u.user_id = %s AND u.user_type = 'employee'
    """, (int(employee_id),))
    employee = cur.fetchone()

    if not employee:
        cur.close()
        conn.close()
        return None

    # Get phone numbers from Phone_Number (use empty list if none)
    try:
        cur.execute("""
            SELECT number_id AS phone_id, phone_number, NULL AS phone_type
            FROM Phone_Number
            WHERE user_id = %s
            ORDER BY number_id
        """, (int(employee_id),))
        phones = cur.fetchall() or []
    except Exception:
        phones = []
    employee['phones'] = phones

    # Get statistics
    stats = get_employee_statistics(employee_id)
    employee['stats'] = stats

    cur.close()
    conn.close()
    return employee


def get_employee_order_transactions(employee_id, limit=50):
    """Get orders processed by employee - for now returns recent orders"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Since we don't track which employee processed which order, return recent orders
    cur.execute("""
        SELECT o.order_id, o.order_date, o.delivery_status, o.receive_date,
               u.first_name as customer_first_name, u.last_name as customer_last_name,
               COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_price
        FROM Orders o
        JOIN Users u ON o.user_id = u.user_id
        LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
        GROUP BY o.order_id, o.order_date, o.delivery_status, o.receive_date,
                 u.first_name, u.last_name
        ORDER BY o.order_date DESC
        LIMIT %s
    """, (limit,))

    orders = cur.fetchall()
    cur.close()
    conn.close()
    return orders


def create_employee(email, password_hash, first_name, last_name, date_of_birth=None):
    """Create a new employee account"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Users (email, user_password, first_name, last_name, date_of_birth, user_type)
        VALUES (%s, %s, %s, %s, %s, 'employee')
    """, (email.lower().strip(), password_hash, first_name, last_name, date_of_birth))
    conn.commit()
    user_id = cur.lastrowid
    cur.close()
    conn.close()
    return user_id


def get_total_employees():
    """Get total count of employees"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Users WHERE user_type = 'employee'")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


def reactivate_employee(employee_id):
    """Reactivate a deactivated employee by changing user_type back to employee"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Change user_type back to 'employee'
        cur.execute("""
            UPDATE Users 
            SET user_type = %s 
            WHERE user_id = %s AND user_type = %s
        """, ('employee', int(employee_id), 'inactive_employee'))
        conn.commit()
        affected = cur.rowcount
        cur.close()
        conn.close()
        return affected > 0
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"Error reactivating employee: {str(e)}")
        return False