# routes/order_routes.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from functools import wraps
from models.order_model import (
    get_customer_orders,
    get_order_items,
    get_order_by_id,
    get_customer_order_stats,
    get_spending_by_category,
    get_customer_orders_summary,
    get_order_statuses
)
from models.image_model import get_primary_image

order_bp = Blueprint("order", __name__)


# Auth decorator for customers
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("user.login"))
        return view(*args, **kwargs)
    return wrapped


# GET /orders/my - My Orders page
@order_bp.route("/orders/my", methods=["GET"])
@login_required
def my_orders():
    user_id = session.get("user_id")

    # Get filter parameters
    period = request.args.get("period", "").strip()  # weekly, monthly, yearly
    status = request.args.get("status", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Convert empty strings to None
    period = period if period else None
    status = status if status else None
    start_date = start_date if start_date else None
    end_date = end_date if end_date else None

    # Get orders with filters
    orders = get_customer_orders(
        user_id,
        period=period,
        status=status,
        start_date=start_date,
        end_date=end_date
    )

    # Get order stats
    stats = get_customer_order_stats(
        user_id,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Get spending by category
    spending_by_category = get_spending_by_category(
        user_id,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Get all available statuses for filter dropdown
    all_statuses = get_order_statuses()

    return render_template(
        "orders/my_orders.html",
        orders=orders,
        stats=stats,
        spending_by_category=spending_by_category,
        all_statuses=all_statuses,
        selected_period=period,
        selected_status=status,
        start_date=start_date,
        end_date=end_date
    )


# GET /orders/<id> - Order details
@order_bp.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def order_details(order_id):
    user_id = session.get("user_id")

    # Get order (verify ownership for customers)
    order = get_order_by_id(order_id, user_id if session.get("user_type") == "customer" else None)

    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("order.my_orders"))

    # Get order items with product images
    items = get_order_items(order_id)
    for item in items:
        img = get_primary_image(item['product_id'])
        item['primary_image'] = img['image_url'] if img else None

    return render_template(
        "orders/order_details.html",
        order=order,
        items=items
    )


# API endpoint for dashboard summary
@order_bp.route("/api/orders/summary", methods=["GET"])
@login_required
def orders_summary_api():
    user_id = session.get("user_id")
    summary = get_customer_orders_summary(user_id)
    return jsonify(summary), 200
