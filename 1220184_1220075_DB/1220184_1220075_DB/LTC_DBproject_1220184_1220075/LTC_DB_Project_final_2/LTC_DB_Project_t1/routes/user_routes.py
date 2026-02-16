import re
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models.user_model import get_user_by_email, insert_user, get_user_by_id, update_user_profile, update_user_password
from models.phone_number_model import get_phone_numbers_by_user_id
from models.dashboard_model import (
    get_total_products, get_total_users, get_total_categories,
    get_total_warehouses, get_total_orders, get_products_by_category,
    get_low_stock_products, get_recent_orders, get_best_sellers,
    get_total_earnings, get_orders_by_customer, get_top_customers,
    get_highest_order, get_orders_per_day, get_earnings_by_month,
    get_daily_earnings, get_weekly_earnings, get_monthly_earnings,
    get_yearly_earnings, get_earnings_by_period, get_earnings_by_category,
    get_sales_by_product, get_spending_by_customer_chart, get_earnings_over_time,
    get_low_stock_count
)
from models.order_model import (
    get_customer_orders_summary, get_spending_by_category,
    get_all_orders_for_employee, update_order_status, get_order_statistics_for_employee,
    get_all_customers_for_filter, get_order_by_id, get_order_items
)
from models.user_model import (
    get_all_users_with_spending, get_user_contact_details, get_total_customers,
    get_all_employees, get_employee_with_stats,
    get_employee_order_transactions, create_employee, get_total_employees,
    deactivate_employee, reactivate_employee
)
from models.warehouse_model import get_low_stock_items_detailed, get_all_warehouse_ids
from functools import wraps

user_bp = Blueprint("user", __name__)

# ---------- HELPERS ----------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("user.login"))
        return view(*args, **kwargs)
    return wrapped

def employee_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_type") not in ["employee", "admin"]:
            flash("Employees only.", "error")
            return redirect(url_for("user.customer_dashboard"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_type") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("user.employee_dashboard"))
        return view(*args, **kwargs)
    return wrapped

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Validate password strength. Returns (is_valid, error_message).
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    return True, None


# ---------- AUTH CHOICE PAGE (FIX) ----------
# ✅ This route makes /auth work (Login / Sign Up choice)
@user_bp.route("/auth", methods=["GET"])
def auth_choice():
    return render_template("auth/choose.html")


# ---------- AUTH PAGES ----------
@user_bp.route("/auth/signup", methods=["GET", "POST"])
def signup():
    form_data = {}

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        date_of_birth = request.form.get("date_of_birth")
        user_type = request.form.get("user_type", "customer")

        # Store form data to preserve on errors (user_type omitted; default is customer)
        form_data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }

        # Validate required fields
        if not email or not password or not first_name or not last_name:
            flash("All fields are required", "error")
            return render_template("users/signup.html", form_data=form_data)

        # Validate email format
        if not is_valid_email(email):
            flash("Please enter a valid email address", "error")
            return render_template("users/signup.html", form_data=form_data)

        # Validate password strength
        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message, "error")
            return render_template("users/signup.html", form_data=form_data)

        # Check if email already exists
        if get_user_by_email(email):
            flash("Email already exists", "error")
            return render_template("users/signup.html", form_data=form_data)

        try:
            password_hash = generate_password_hash(password)
            insert_user(email, password_hash, first_name, last_name, date_of_birth, user_type)
            flash("Account created. Please log in.", "success")
            return redirect(url_for("user.login"))
        except Exception:
            flash("An error occurred during signup. Please try again later.", "error")
            return render_template("users/signup.html", form_data=form_data)

    return render_template("users/signup.html", form_data=form_data)


@user_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        remember_me = request.form.get("remember_me") == "on"

        user = get_user_by_email(email)
        if not user or not check_password_hash(user["user_password"], password):
            flash("Invalid email or password", "error")
            return redirect(url_for("user.login"))

        # Prevent inactive/deactivated employees from logging in
        if user.get('user_type') == 'inactive_employee':
            flash("Account is deactivated. Contact an administrator to reactivate.", "error")
            return redirect(url_for("user.login"))

        # Set session permanence based on "Remember Me" checkbox
        session.permanent = remember_me

        session["user_id"] = user["user_id"]
        session["user_type"] = user["user_type"]
        session["user_name"] = user["first_name"]

        # Check if user is admin (admin@ltc.com)
        if user["email"].lower() == "admin@ltc.com":
            session["user_type"] = "admin"
            return redirect(url_for("user.admin_dashboard"))
        elif user["user_type"] == "employee":
            return redirect(url_for("user.employee_dashboard"))
        return redirect(url_for("user.customer_dashboard"))

    return render_template("users/login.html")


@user_bp.route("/auth/logout")
def logout():
    session.clear()
    return redirect(url_for("user.login"))


# ---------- DASHBOARDS ----------
@user_bp.route("/dashboard/customer")
@login_required
def customer_dashboard():
    user_id = session.get("user_id")

    # Get orders summary for dashboard
    orders_summary = get_customer_orders_summary(user_id)

    # Get spending by category (last 30 days for dashboard)
    spending_by_category = get_spending_by_category(user_id, period='monthly')

    return render_template(
        "dashboards/customer.html",
        orders_summary=orders_summary,
        spending_by_category=spending_by_category
    )


# ---------- PROFILE SETTINGS ----------
@user_bp.route("/settings", methods=["GET", "POST"])
@user_bp.route("/profile/settings", methods=["GET", "POST"])
@login_required
def profile_settings():
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    
    if not user:
        flash("User not found", "error")
        return redirect(url_for("user.customer_dashboard"))
    
    # Get user's phone numbers
    phone_numbers = get_phone_numbers_by_user_id(user_id)
    
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        date_of_birth = request.form.get("date_of_birth") or None
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        # Update profile info
        update_data = {}
        if first_name and first_name != user["first_name"]:
            update_data["first_name"] = first_name
        if last_name and last_name != user["last_name"]:
            update_data["last_name"] = last_name
        if email and email != user["email"]:
            # Check if email is already taken
            existing_user = get_user_by_email(email)
            if existing_user and existing_user["user_id"] != user_id:
                flash("Email already in use", "error")
                return redirect(url_for("user.profile_settings"))
            update_data["email"] = email
        
        # Handle date of birth (can be empty)
        if date_of_birth != (user.get("date_of_birth") or ""):
            update_data["date_of_birth"] = date_of_birth if date_of_birth else None
        
        # Update profile if there are changes
        if update_data:
            try:
                update_user_profile(user_id, **update_data)
                flash("Profile updated successfully", "success")
                # Update session if name or email changed
                if "first_name" in update_data:
                    session["user_name"] = update_data["first_name"]
                if "email" in update_data:
                    session["user_email"] = update_data["email"]
                # Reload user to show updated data
                user = get_user_by_id(user_id)
            except Exception as e:
                flash("Failed to update profile", "error")
        
        # Handle password change
        if current_password and new_password and confirm_password:
            if not check_password_hash(user["user_password"], current_password):
                flash("Current password is incorrect", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match", "error")
            elif len(new_password) < 6:
                flash("Password must be at least 6 characters", "error")
            else:
                try:
                    password_hash = generate_password_hash(new_password)
                    update_user_password(user_id, password_hash)
                    flash("Password updated successfully", "success")
                except Exception:
                    flash("Failed to update password", "error")
        
        return redirect(url_for("user.profile_settings"))
    
    # Reload phone numbers after potential updates
    phone_numbers = get_phone_numbers_by_user_id(user_id)
    return render_template("users/profile_settings.html", user=user, phone_numbers=phone_numbers)


@user_bp.route("/dashboard/employee")
@login_required
@employee_required
def employee_dashboard():
    # Gather statistics
    low_stock = get_low_stock_products()
    stats = {
        'total_products': get_total_products(),
        'total_users': get_total_users(),
        'total_categories': get_total_categories(),
        'total_warehouses': get_total_warehouses(),
        'total_orders': get_total_orders(),
        'total_earnings': get_total_earnings(),
        'low_stock_count': len(low_stock),
        'low_stock_products': low_stock[:5],  # Limit to 5 for display
        'products_by_category': get_products_by_category(),
        'recent_orders': get_recent_orders(5),
        'best_sellers': get_best_sellers(10),
        'top_customers': get_top_customers(5),
        'orders_by_customer': get_orders_by_customer(),
        'highest_order': get_highest_order(),
        'orders_per_day': get_orders_per_day(30),
        'earnings_by_month': get_earnings_by_month(12)
    }
    return render_template("dashboards/employee.html", stats=stats)


# =====================================================
# EMPLOYEE MANAGEMENT PAGES
# =====================================================

# ---------- ORDER MANAGEMENT ----------
@user_bp.route("/employee/orders")
@login_required
@employee_required
def employee_orders():
    """Order management page for employees"""
    # Get filter parameters
    user_id = request.args.get("user_id", "").strip()
    status = request.args.get("status", "").strip()
    city = request.args.get("city", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Convert empty strings to None
    user_id = int(user_id) if user_id else None
    min_price = float(min_price) if min_price else None
    max_price = float(max_price) if max_price else None

    # Get filtered orders
    orders = get_all_orders_for_employee(
        user_id=user_id,
        status=status if status else None,
        city=city if city else None,
        min_price=min_price,
        max_price=max_price,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None
    )

    # Get statistics
    stats = get_order_statistics_for_employee()

    # Get customers for filter dropdown
    customers = get_all_customers_for_filter()

    # Define status options
    status_options = ['Pending', 'Processing', 'Shipped', 'In Transit', 'Delivered']

    return render_template(
        "employee/orders.html",
        orders=orders,
        stats=stats,
        customers=customers,
        status_options=status_options,
        filters={
            'user_id': user_id,
            'status': status,
            'city': city,
            'min_price': min_price,
            'max_price': max_price,
            'start_date': start_date,
            'end_date': end_date
        }
    )


@user_bp.route("/employee/orders/<int:order_id>/status", methods=["POST"])
@login_required
@employee_required
def update_order_status_route(order_id):
    """Update order status"""
    new_status = request.form.get("status")
    valid_statuses = ['Pending', 'Processing', 'Shipped', 'In Transit', 'Delivered']

    if new_status not in valid_statuses:
        flash("Invalid status.", "error")
        return redirect(url_for("user.employee_orders"))

    employee_id = session.get("user_id")
    result = update_order_status(order_id, new_status, employee_id)

    # Handle both old (bool) and new (tuple) return formats
    if isinstance(result, tuple):
        updated, error_msg = result
    else:
        updated, error_msg = result, None

    if updated:
        flash(f"Order #{order_id} status updated to {new_status}.", "success")
    else:
        if error_msg:
            flash(f"Failed to update order status: {error_msg}", "error")
        else:
            flash("Failed to update order status.", "error")

    return redirect(url_for("user.employee_orders"))


@user_bp.route("/employee/orders/<int:order_id>")
@login_required
@employee_required
def employee_order_details(order_id):
    """View order details for employees"""
    order = get_order_by_id(order_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("user.employee_orders"))

    items = get_order_items(order_id)

    # Get primary image for each item
    from models.image_model import get_primary_image
    for item in items:
        img = get_primary_image(item['product_id'])
        item['primary_image'] = img['image_url'] if img else None

    status_options = ['Pending', 'Processing', 'Shipped', 'In Transit', 'Delivered']

    return render_template(
        "employee/order_details.html",
        order=order,
        items=items,
        status_options=status_options
    )


# ---------- USER MANAGEMENT ----------
@user_bp.route("/employee/users")
@login_required
@employee_required
def employee_users():
    """Users management page for employees"""
    search = request.args.get("search", "").strip()

    users = get_all_users_with_spending(search if search else None)
    total_customers = get_total_customers()

    return render_template(
        "employee/users.html",
        users=users,
        total_customers=total_customers,
        search=search
    )


@user_bp.route("/employee/users/<int:user_id>/contacts")
@login_required
@employee_required
def employee_user_contacts(user_id):
    """AJAX endpoint to get user contact details"""
    contacts = get_user_contact_details(user_id)
    if not contacts:
        return jsonify({"error": "User not found"}), 404

    return jsonify(contacts)


# ---------- LOW STOCK MANAGEMENT ----------
@user_bp.route("/employee/low-stock")
@login_required
@employee_required
def employee_low_stock():
    """Low stock items page for employees"""
    threshold = request.args.get("threshold", "10")
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 10

    items = get_low_stock_items_detailed(threshold)
    warehouse_ids = get_all_warehouse_ids()

    return render_template(
        "employee/low_stock.html",
        items=items,
        warehouse_ids=warehouse_ids,
        threshold=threshold
    )


# ---------- EARNINGS STATISTICS (ADMIN ONLY) ----------
@user_bp.route("/employee/earnings")
@login_required
@admin_required
def employee_earnings():
    """Earnings statistics page for employees"""
    from datetime import date, timedelta
    
    period = request.args.get("period", "month")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    # Calculate date range based on period
    today = date.today()
    filter_start_date = None
    filter_end_date = None
    
    if period == "day":
        filter_start_date = today
        filter_end_date = today
        earnings_data = get_daily_earnings()
    elif period == "week":
        filter_start_date = today - timedelta(days=6)  # Last 7 days including today
        filter_end_date = today
        earnings_data = get_weekly_earnings()
    elif period == "year":
        filter_start_date = date(today.year, 1, 1)  # First day of current year
        filter_end_date = today
        earnings_data = get_yearly_earnings()
    elif period == "custom" and start_date and end_date:
        filter_start_date = start_date
        filter_end_date = end_date
        earnings_data = get_earnings_by_period(start_date, end_date)
    else:
        # Month - first day of current month to today
        filter_start_date = date(today.year, today.month, 1)
        filter_end_date = today
        earnings_data = get_monthly_earnings()
        period = "month"

    # Get category earnings for pie chart - filtered by period
    category_earnings = get_earnings_by_category(filter_start_date, filter_end_date)

    # Get earnings over time for line chart - filtered by period
    earnings_over_time = get_earnings_over_time(days=None, start_date=filter_start_date, end_date=filter_end_date)

    # Total earnings should be the filtered period total, not all-time
    # Use earnings_data for the filtered period total
    total_earnings = earnings_data['earnings']

    return render_template(
        "employee/earnings.html",
        earnings_data=earnings_data,
        category_earnings=category_earnings,
        earnings_over_time=earnings_over_time,
        total_earnings=total_earnings,
        period=period,
        start_date=start_date,
        end_date=end_date
    )


@user_bp.route("/employee/earnings/data")
@login_required
@admin_required
def employee_earnings_data():
    """AJAX endpoint for earnings chart data"""
    data_type = request.args.get("type", "category")

    if data_type == "category":
        data = get_earnings_by_category()
    elif data_type == "time":
        days = request.args.get("days", "30")
        try:
            days = int(days)
        except ValueError:
            days = 30
        data = get_earnings_over_time(days)
    elif data_type == "best_sellers":
        data = get_sales_by_product(10)
    elif data_type == "top_customers":
        data = get_spending_by_customer_chart(10)
    else:
        data = []

    return jsonify(data)


# =====================================================
# ADMIN MANAGEMENT PAGES
# =====================================================

@user_bp.route("/dashboard/admin")
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard - same as employee but with admin access"""
    low_stock = get_low_stock_products()
    stats = {
        'total_products': get_total_products(),
        'total_users': get_total_users(),
        'total_categories': get_total_categories(),
        'total_warehouses': get_total_warehouses(),
        'total_orders': get_total_orders(),
        'total_earnings': get_total_earnings(),
        'total_employees': get_total_employees(),
        'low_stock_count': len(low_stock),
        'low_stock_products': low_stock[:5],
        'products_by_category': get_products_by_category(),
        'recent_orders': get_recent_orders(5),
        'best_sellers': get_best_sellers(10),
        'top_customers': get_top_customers(5),
        'orders_by_customer': get_orders_by_customer(),
        'highest_order': get_highest_order(),
        'orders_per_day': get_orders_per_day(30),
        'earnings_by_month': get_earnings_by_month(12)
    }
    return render_template("dashboards/employee.html", stats=stats)


# ---------- EMPLOYEE MANAGEMENT (ADMIN ONLY) ----------
@user_bp.route("/admin/employees")
@login_required
@admin_required
def admin_employees():
    """Employee management page for admin"""
    search = request.args.get("search", "").strip()

    employees = get_all_employees(search if search else None)
    total_employees = get_total_employees()

    return render_template(
        "admin/employees.html",
        employees=employees,
        total_employees=total_employees,
        search=search
    )


@user_bp.route("/admin/employees/add", methods=["GET", "POST"])
@login_required
@admin_required
def admin_add_employee():
    """Add a new employee"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        date_of_birth = request.form.get("date_of_birth") or None

        # Validate
        if not email or not password or not first_name or not last_name:
            flash("All fields are required.", "error")
            return redirect(url_for("user.admin_add_employee"))

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("user.admin_add_employee"))

        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message, "error")
            return redirect(url_for("user.admin_add_employee"))

        if get_user_by_email(email):
            flash("Email already exists.", "error")
            return redirect(url_for("user.admin_add_employee"))

        try:
            password_hash = generate_password_hash(password)
            create_employee(email, password_hash, first_name, last_name, date_of_birth)
            flash("Employee created successfully.", "success")
            return redirect(url_for("user.admin_employees"))
        except Exception as e:
            flash("Failed to create employee.", "error")
            return redirect(url_for("user.admin_add_employee"))

    return render_template("admin/add_employee.html")


@user_bp.route("/admin/employees/<int:employee_id>")
@login_required
@admin_required
def admin_employee_profile(employee_id):
    """View employee profile with warehouse activity statistics"""
    employee = get_employee_with_stats(employee_id)
    if not employee:
        flash("Employee not found.", "error")
        return redirect(url_for("user.admin_employees"))

    return render_template(
        "admin/employee_details.html",
        employee=employee,
        warehouse_transactions=[]
    )


@user_bp.route("/admin/employees/<int:employee_id>/deactivate", methods=["POST"])
@login_required
@admin_required
def admin_deactivate_employee(employee_id):
    """Deactivate an employee and generate report"""
    success = deactivate_employee(employee_id)
    if success:
        flash("Employee deactivated and report generated.", "success")
    else:
        flash("Failed to deactivate employee.", "error")

    return redirect(url_for("user.admin_employees"))


@user_bp.route("/admin/employees/<int:employee_id>/reactivate", methods=["POST"])
@login_required
@admin_required
def admin_reactivate_employee(employee_id):
    """Reactivate a deactivated employee"""
    success = reactivate_employee(employee_id)
    if success:
        flash("Employee reactivated.", "success")
    else:
        flash("Failed to reactivate employee.", "error")

    return redirect(url_for("user.admin_employees"))


# ---------- API (POSTMAN) ----------
@user_bp.route("/auth/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["user_password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Prevent inactive employees from logging in via API
    if user.get('user_type') == 'inactive_employee':
        return jsonify({"error": "Account is deactivated. Contact an administrator to reactivate."}), 403

    return jsonify({
        "user_id": user["user_id"],
        "user_type": user["user_type"]
    }), 200
