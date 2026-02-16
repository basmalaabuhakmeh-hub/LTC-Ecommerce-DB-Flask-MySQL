from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from functools import wraps
from werkzeug.security import generate_password_hash
from models.user_model import (get_user_by_id, get_all_users_with_spending, insert_user, get_user_by_email,
                                get_all_employees)
from models.dashboard_model import (
    get_total_products, get_total_users, get_total_categories,
    get_total_warehouses, get_total_orders, get_total_earnings,
    get_top_customers, get_highest_order, get_orders_per_day,
    get_earnings_by_month, get_daily_earnings, get_weekly_earnings,
    get_monthly_earnings, get_yearly_earnings, get_earnings_by_category,
    get_sales_by_product, get_spending_by_customer_chart, get_low_stock_count,
    get_orders_by_customer,
)
from models.order_model import get_all_orders_for_employee
from database.db import get_db_connection

admin_bp = Blueprint("admin", __name__)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("user.login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_user_by_id(session.get("user_id"))
        if not user or user["email"] != "admin@ltc.com":
            flash("Admin access only.", "error")
            return redirect(url_for("user.customer_dashboard"))
        return view(*args, **kwargs)
    return wrapped

# ---------- ADMIN DASHBOARD ----------
@admin_bp.route("/dashboard/admin")
@login_required
@admin_required
def admin_dashboard():
    """Main admin dashboard with overview statistics"""
    user_id = session.get("user_id")
    
    # Get all dashboard metrics
    total_users = get_total_users()
    total_products = get_total_products()
    total_categories = get_total_categories()
    total_warehouses = get_total_warehouses()
    total_orders = get_total_orders()
    total_earnings = get_total_earnings()
    low_stock_count = get_low_stock_count()
    top_customers = get_top_customers(5)
    # Customer list/filter options (default: spendings)
    customer_filter = request.args.get("customer_filter", "spendings")
    customer_limit = request.args.get("customer_limit", 10, type=int)
    customer_list = []
    try:
        if customer_filter == 'orders':
            # customers ordered by number of orders
            customer_list = get_orders_by_customer()
        elif customer_filter == 'spendings':
            # customers ordered by total spend
            customer_list = get_top_customers(customer_limit)
        elif customer_filter == 'date_registered':
            # If there's no created_at column, use user_id as a proxy for registration order
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute('''
                SELECT u.user_id, u.first_name, u.last_name, u.email,
                       COALESCE(SUM(oi.quantity * oi.price_at_order), 0) as total_spent,
                       COUNT(DISTINCT o.order_id) as order_count
                FROM Users u
                LEFT JOIN Orders o ON u.user_id = o.user_id
                LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
                WHERE u.user_type = 'customer'
                GROUP BY u.user_id, u.first_name, u.last_name, u.email
                ORDER BY u.user_id DESC
                LIMIT %s
            ''', (customer_limit,))
            customer_list = cur.fetchall()
            cur.close()
            conn.close()
        else:
            customer_list = get_top_customers(customer_limit)
    except Exception:
        # Fallback to previously computed top_customers on any error
        customer_list = top_customers
    
    # Get earnings data
    daily_earnings = get_daily_earnings()
    weekly_earnings = get_weekly_earnings()
    monthly_earnings = get_monthly_earnings()
    yearly_earnings = get_yearly_earnings()
    
    # Get sales data
    earnings_by_category = get_earnings_by_category()
    sales_by_product = get_sales_by_product()
    
    return render_template(
        "dashboards/admin.html",
        total_users=total_users,
        total_products=total_products,
        total_categories=total_categories,
        total_warehouses=total_warehouses,
        total_orders=total_orders,
        total_earnings=total_earnings,
        low_stock_count=low_stock_count,
        top_customers=top_customers,
        daily_earnings=daily_earnings,
        weekly_earnings=weekly_earnings,
        monthly_earnings=monthly_earnings,
        yearly_earnings=yearly_earnings,
        earnings_by_category=earnings_by_category,
        sales_by_product=sales_by_product,
        customer_list=customer_list,
        customer_filter=customer_filter,
        customer_limit=customer_limit
    )

# ---------- EMPLOYEES MANAGEMENT ----------
@admin_bp.route("/admin/employees", methods=["GET", "POST"])
@login_required
@admin_required
def employees_list():
    """List all employees and handle adding new employees"""
    if request.method == "POST":
        # Handle adding new employee
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        
        # Validation
        if not all([email, password, first_name, last_name]):
            flash("All fields are required.", "error")
            return redirect(url_for("admin.employees_list"))
        
        # Check if email already exists
        if get_user_by_email(email):
            flash("Email already in use.", "error")
            return redirect(url_for("admin.employees_list"))
        
        # Validate email format
        if not email or "@" not in email:
            flash("Invalid email format.", "error")
            return redirect(url_for("admin.employees_list"))
        
        # Hash password and insert employee
        try:
            password_hash = generate_password_hash(password)
            insert_user(email, password_hash, first_name, last_name, None, "employee")
            flash(f"Employee {first_name} {last_name} created successfully!", "success")
        except Exception as e:
            flash(f"Failed to create employee: {str(e)}", "error")
        
        return redirect(url_for("admin.employees_list"))
    
    # GET request - show employees
    try:
        # Get all employees (users with user_type = 'employee') - exclude admin
        employees = get_all_employees()
        
        return render_template("admin/employees.html", employees=employees)
    except Exception as e:
        flash(f"Error loading employees: {str(e)}", "error")
        return redirect(url_for("user.customer_dashboard"))

# ---------- ADMIN API ENDPOINTS ----------
@admin_bp.route("/api/admin/employees", methods=["GET"])
@login_required
@admin_required
def api_employees():
    """API endpoint to get all employees"""
    try:
        employees = get_all_users_with_spending()
        # Filter only employees
        employees = [emp for emp in employees if emp.get('user_type') == 'employee']
        return jsonify({
            "success": True,
            "data": employees,
            "count": len(employees)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/api/admin/dashboard/stats", methods=["GET"])
@login_required
@admin_required
def api_dashboard_stats():
    """API endpoint to get dashboard statistics"""
    try:
        stats = {
            "total_users": get_total_users(),
            "total_products": get_total_products(),
            "total_categories": get_total_categories(),
            "total_warehouses": get_total_warehouses(),
            "total_orders": get_total_orders(),
            "total_earnings": get_total_earnings(),
            "low_stock_count": get_low_stock_count()
        }
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/api/admin/employees/<int:employee_id>", methods=["GET"])
@login_required
@admin_required
def api_employee_details(employee_id):
    """API endpoint to get employee details"""
    try:
        employee = get_user_by_id(employee_id)
        if not employee or employee.get('user_type') != 'employee':
            return jsonify({
                "success": False,
                "error": "Employee not found"
            }), 404
        
        recent_orders = get_all_orders_for_employee(user_id=employee_id)
        
        return jsonify({
            "success": True,
            "data": {
                "employee": employee,
                "recent_orders": recent_orders
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/api/admin/earnings/by-period", methods=["GET"])
@login_required
@admin_required
def api_earnings_by_period():
    """API endpoint to get earnings by period"""
    try:
        period = request.args.get("period", "monthly")
        
        if period == "daily":
            earnings = get_daily_earnings()
        elif period == "weekly":
            earnings = get_weekly_earnings()
        elif period == "yearly":
            earnings = get_yearly_earnings()
        else:  # monthly
            earnings = get_monthly_earnings()
        
        return jsonify({
            "success": True,
            "period": period,
            "data": earnings
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/api/admin/sales/by-category", methods=["GET"])
@login_required
@admin_required
def api_sales_by_category():
    """API endpoint to get sales by category"""
    try:
        data = get_earnings_by_category()
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/api/admin/sales/by-product", methods=["GET"])
@login_required
@admin_required
def api_sales_by_product():
    """API endpoint to get sales by product"""
    try:
        data = get_sales_by_product()
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/api/admin/top-customers", methods=["GET"])
@login_required
@admin_required
def api_top_customers():
    """API endpoint to get top customers"""
    try:
        limit = request.args.get("limit", 10, type=int)
        data = get_top_customers(limit)
        return jsonify({
            "success": True,
            "data": data,
            "limit": limit
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


