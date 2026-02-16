# routes/sale_routes.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from functools import wraps
from models.sale_model import (
    get_all_sales,
    get_sale_by_id,
    create_sale,
    update_sale,
    delete_sale,
    assign_products_to_sale,
    get_products_in_sale,
    get_sales_statistics,
    check_and_deactivate_expired_sales
)
from models.product_model import get_all_products
from datetime import datetime

sale_bp = Blueprint("sale", __name__)


# Auth decorators
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("user.login"))
        return view(*args, **kwargs)
    return wrapped


def employee_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_type") not in ["employee", "admin"]:
            flash("Employees and admins only.", "error")
            return redirect(url_for("user.customer_dashboard"))
        return view(*args, **kwargs)
    return wrapped


# GET /sales - List all sales
@sale_bp.route("/sales", methods=["GET"])
@login_required
@employee_required
def list_sales():
    """List all sales for management"""
    # Check and deactivate expired sales
    check_and_deactivate_expired_sales()
    
    # Show all sales (both active and inactive) in management view
    include_inactive = request.args.get("include_inactive", "true").lower() == "true"
    sales = get_all_sales(include_inactive=include_inactive)
    stats = get_sales_statistics()
    
    return render_template(
        "sales/list.html",
        sales=sales,
        stats=stats,
        include_inactive=include_inactive
    )


# GET/POST /sales/create - Create new sale
@sale_bp.route("/sales/create", methods=["GET", "POST"])
@login_required
@employee_required
def create_sale_route():
    """Create a new sale"""
    if request.method == "POST":
        sale_name = request.form.get("sale_name", "").strip()
        sale_type = request.form.get("sale_type", "percentage").strip()
        discount_value = request.form.get("discount_value", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        product_ids = request.form.getlist("product_ids")
        
        # Validation
        if not all([sale_name, discount_value, start_date, end_date]):
            flash("All fields are required.", "error")
            return redirect(url_for("sale.create_sale_route"))
        
        try:
            discount_value = float(discount_value)
            if sale_type == "percentage" and (discount_value < 0 or discount_value > 100):
                flash("Percentage discount must be between 0 and 100.", "error")
                return redirect(url_for("sale.create_sale_route"))
            if sale_type == "fixed" and discount_value < 0:
                flash("Fixed discount must be positive.", "error")
                return redirect(url_for("sale.create_sale_route"))
            
            # Validate dates
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            if end < start:
                flash("End date must be after start date.", "error")
                return redirect(url_for("sale.create_sale_route"))
            
            # Convert product_ids to integers
            product_ids = [int(pid) for pid in product_ids if pid]
            
            sale_id = create_sale(
                sale_name=sale_name,
                sale_type=sale_type,
                discount_value=discount_value,
                start_date=start_date,
                end_date=end_date,
                product_ids=product_ids if product_ids else None
            )
            
            flash(f"Sale '{sale_name}' created successfully!", "success")
            return redirect(url_for("sale.view_sale", sale_id=sale_id))
            
        except ValueError as e:
            flash(f"Invalid input: {str(e)}", "error")
            return redirect(url_for("sale.create_sale_route"))
        except Exception as e:
            flash(f"Failed to create sale: {str(e)}", "error")
            return redirect(url_for("sale.create_sale_route"))
    
    # GET request - show form
    products = get_all_products()
    return render_template("sales/create.html", products=products)


# GET /sales/<id> - View sale details
@sale_bp.route("/sales/<int:sale_id>", methods=["GET"])
@login_required
@employee_required
def view_sale(sale_id):
    """View sale details"""
    sale = get_sale_by_id(sale_id)
    if not sale:
        flash("Sale not found.", "error")
        return redirect(url_for("sale.list_sales"))
    
    products = get_products_in_sale(sale_id)
    all_products = get_all_products()
    
    return render_template(
        "sales/view.html",
        sale=sale,
        products=products,
        all_products=all_products
    )


# GET/POST /sales/<id>/edit - Edit sale
@sale_bp.route("/sales/<int:sale_id>/edit", methods=["GET", "POST"])
@login_required
@employee_required
def edit_sale(sale_id):
    """Edit a sale"""
    sale = get_sale_by_id(sale_id)
    if not sale:
        flash("Sale not found.", "error")
        return redirect(url_for("sale.list_sales"))
    
    if request.method == "POST":
        sale_name = request.form.get("sale_name", "").strip()
        sale_type = request.form.get("sale_type", "percentage").strip()
        discount_value = request.form.get("discount_value", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        is_active = request.form.get("is_active") == "on"
        product_ids = request.form.getlist("product_ids")
        
        try:
            discount_value = float(discount_value) if discount_value else None
            
            updated = update_sale(
                sale_id=sale_id,
                sale_name=sale_name if sale_name else None,
                sale_type=sale_type if sale_type else None,
                discount_value=discount_value,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                is_active=is_active
            )
            
            # Update product assignments
            if product_ids:
                product_ids = [int(pid) for pid in product_ids if pid]
                assign_products_to_sale(sale_id, product_ids)
            
            if updated:
                flash("Sale updated successfully!", "success")
            else:
                flash("No changes made.", "info")
            
            return redirect(url_for("sale.view_sale", sale_id=sale_id))
            
        except Exception as e:
            flash(f"Failed to update sale: {str(e)}", "error")
            return redirect(url_for("sale.edit_sale", sale_id=sale_id))
    
    # GET request - show edit form
    products = get_products_in_sale(sale_id)
    all_products = get_all_products()
    selected_product_ids = [p['product_id'] for p in products]
    
    return render_template(
        "sales/edit.html",
        sale=sale,
        products=products,
        all_products=all_products,
        selected_product_ids=selected_product_ids
    )


# POST /sales/<id>/delete - Delete sale
@sale_bp.route("/sales/<int:sale_id>/delete", methods=["POST"])
@login_required
@employee_required
def delete_sale_route(sale_id):
    """Delete a sale"""
    deleted = delete_sale(sale_id)
    if deleted:
        flash("Sale deleted successfully.", "success")
    else:
        flash("Sale not found.", "error")
    return redirect(url_for("sale.list_sales"))


# POST /sales/<id>/products - Update product assignments
@sale_bp.route("/sales/<int:sale_id>/products", methods=["POST"])
@login_required
@employee_required
def update_sale_products(sale_id):
    """Update which products are in a sale"""
    product_ids = request.form.getlist("product_ids")
    product_ids = [int(pid) for pid in product_ids if pid]
    
    try:
        assign_products_to_sale(sale_id, product_ids)
        flash("Products updated successfully!", "success")
    except Exception as e:
        flash(f"Failed to update products: {str(e)}", "error")
    
    return redirect(url_for("sale.view_sale", sale_id=sale_id))

