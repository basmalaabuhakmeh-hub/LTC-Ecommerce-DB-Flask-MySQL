# routes/warehouse_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps

from models.warehouse_model import (
    get_all_warehouses,
    get_warehouse_by_id,
    insert_warehouse,
    delete_warehouse,
    count_warehouses,
    get_warehouse_products,
    get_warehouse_product,
    add_product_to_warehouse,
    update_warehouse_product_quantity,
    remove_product_from_warehouse,
    get_all_products_for_warehouse,
)

from models.product_model import get_product_by_id

warehouse_bp = Blueprint("warehouse", __name__)


# ----------------------------
# AUTH DECORATORS
# ----------------------------
def employee_only_api(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized (please login)"}), 401
        if session.get("user_type") not in ["employee", "admin"]:
            return jsonify({"error": "Forbidden - Employees only"}), 403
        return view(*args, **kwargs)
    return wrapped


def employee_only_ui(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("user.login"))
        if session.get("user_type") not in ["employee", "admin"]:
            flash("Employees only.", "error")
            return redirect(url_for("user.customer_dashboard"))
        return view(*args, **kwargs)
    return wrapped


# =========================================================
# API ROUTES (JSON) - Postman
# =========================================================

# GET /warehouses
@warehouse_bp.route("/warehouses", methods=["GET"])
def warehouses_index():
    warehouses = get_all_warehouses()
    return jsonify({"total": count_warehouses(), "results": warehouses}), 200


# GET /warehouses/<id>
@warehouse_bp.route("/warehouses/<int:warehouse_id>", methods=["GET"])
def get_warehouse(warehouse_id):
    w = get_warehouse_by_id(warehouse_id)
    if not w:
        return jsonify({"error": "Warehouse not found"}), 404
    return jsonify(w), 200


# POST /warehouses -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses", methods=["POST"])
@employee_only_api
def create_warehouse():
    try:
        new_id = insert_warehouse()
        return jsonify({"message": "Created", "warehouse_id": new_id}), 201
    except Exception as e:
        return jsonify({"error": "Failed to create warehouse"}), 500


# DELETE /warehouses/<id> -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/<int:warehouse_id>", methods=["DELETE"])
@employee_only_api
def remove_warehouse(warehouse_id):
    deleted = delete_warehouse(warehouse_id)
    if not deleted:
        return jsonify({"error": "Warehouse not found"}), 404
    return jsonify({"message": "Deleted"}), 200


# GET /warehouses/<id>/products
@warehouse_bp.route("/warehouses/<int:warehouse_id>/products", methods=["GET"])
def get_warehouse_products_api(warehouse_id):
    if not get_warehouse_by_id(warehouse_id):
        return jsonify({"error": "Warehouse not found"}), 404
    products = get_warehouse_products(warehouse_id)
    return jsonify({"results": products}), 200


# POST /warehouses/<id>/products -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/<int:warehouse_id>/products", methods=["POST"])
@employee_only_api
def add_product_warehouse(warehouse_id):
    if not get_warehouse_by_id(warehouse_id):
        return jsonify({"error": "Warehouse not found"}), 404

    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    if not get_product_by_id(int(product_id)):
        return jsonify({"error": "Product not found"}), 404

    try:
        employee_id = session.get("user_id")
        add_product_to_warehouse(warehouse_id, int(product_id), int(quantity), employee_id)
        return jsonify({"message": "Product added to warehouse"}), 201
    except Exception:
        return jsonify({"error": "Failed to add product"}), 500


# PATCH /warehouses/<id>/products/<product_id> -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/<int:warehouse_id>/products/<int:product_id>", methods=["PATCH"])
@employee_only_api
def update_product_quantity(warehouse_id, product_id):
    data = request.get_json(silent=True) or {}
    quantity = data.get("quantity")

    if quantity is None:
        return jsonify({"error": "quantity is required"}), 400

    employee_id = session.get("user_id")
    updated = update_warehouse_product_quantity(warehouse_id, product_id, int(quantity), employee_id)
    if not updated:
        return jsonify({"error": "Warehouse product not found"}), 404

    return jsonify({"message": "Quantity updated"}), 200


# DELETE /warehouses/<id>/products/<product_id> -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/<int:warehouse_id>/products/<int:product_id>", methods=["DELETE"])
@employee_only_api
def remove_product_warehouse(warehouse_id, product_id):
    employee_id = session.get("user_id")
    deleted = remove_product_from_warehouse(warehouse_id, product_id, employee_id)
    if not deleted:
        return jsonify({"error": "Warehouse product not found"}), 404
    return jsonify({"message": "Product removed from warehouse"}), 200


# =========================================================
# UI ROUTES (HTML pages)
# =========================================================

# GET /warehouses/ui (list)
@warehouse_bp.route("/warehouses/ui", methods=["GET"])
@employee_only_ui
def warehouses_ui():
    warehouses = get_all_warehouses()
    return render_template(
        "warehouses/list.html",
        warehouses=warehouses,
        total=count_warehouses()
    )


# POST /warehouses/ui/create -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/ui/create", methods=["POST"])
@employee_only_ui
def warehouses_ui_create():
    try:
        insert_warehouse()
        flash("Warehouse created successfully.", "success")
    except Exception:
        flash("Failed to create warehouse.", "error")
    return redirect(url_for("warehouse.warehouses_ui"))


# POST /warehouses/ui/delete/<id> -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/ui/delete/<int:warehouse_id>", methods=["POST"])
@employee_only_ui
def warehouses_ui_delete(warehouse_id):
    deleted = delete_warehouse(warehouse_id)
    flash("Warehouse deleted." if deleted else "Warehouse not found.", "success" if deleted else "error")
    return redirect(url_for("warehouse.warehouses_ui"))


# GET /warehouses/ui/<id>/products (manage products in warehouse)
@warehouse_bp.route("/warehouses/ui/<int:warehouse_id>/products", methods=["GET"])
@employee_only_ui
def warehouse_products_ui(warehouse_id):
    warehouse = get_warehouse_by_id(warehouse_id)
    if not warehouse:
        flash("Warehouse not found.", "error")
        return redirect(url_for("warehouse.warehouses_ui"))
    
    products = get_warehouse_products(warehouse_id)
    all_products = get_all_products_for_warehouse()
    
    # Get product IDs already in warehouse
    existing_product_ids = {p['product_id'] for p in products}
    available_products = [p for p in all_products if p['product_id'] not in existing_product_ids]
    
    return render_template(
        "warehouses/products.html",
        warehouse=warehouse,
        products=products,
        available_products=available_products
    )


# POST /warehouses/ui/<id>/products/add -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/ui/<int:warehouse_id>/products/add", methods=["POST"])
@employee_only_ui
def warehouse_products_add(warehouse_id):
    product_id = request.form.get("product_id")
    quantity = request.form.get("quantity", "1")

    if not product_id:
        flash("Product is required.", "error")
        return redirect(url_for("warehouse.warehouse_products_ui", warehouse_id=warehouse_id))

    if not get_product_by_id(int(product_id)):
        flash("Product not found.", "error")
        return redirect(url_for("warehouse.warehouse_products_ui", warehouse_id=warehouse_id))

    try:
        employee_id = session.get("user_id")
        add_product_to_warehouse(warehouse_id, int(product_id), int(quantity), employee_id)
        flash("Product added to warehouse.", "success")
    except Exception:
        flash("Failed to add product.", "error")

    return redirect(url_for("warehouse.warehouse_products_ui", warehouse_id=warehouse_id))


# POST /warehouses/ui/<id>/products/<product_id>/update -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/ui/<int:warehouse_id>/products/<int:product_id>/update", methods=["POST"])
@employee_only_ui
def warehouse_products_update(warehouse_id, product_id):
    quantity = request.form.get("quantity")

    if not quantity:
        flash("Quantity is required.", "error")
        return redirect(url_for("warehouse.warehouse_products_ui", warehouse_id=warehouse_id))

    employee_id = session.get("user_id")
    updated = update_warehouse_product_quantity(warehouse_id, product_id, int(quantity), employee_id)
    flash("Quantity updated." if updated else "Product not found in warehouse.",
          "success" if updated else "error")
    return redirect(url_for("warehouse.warehouse_products_ui", warehouse_id=warehouse_id))


# POST /warehouses/ui/<id>/products/<product_id>/remove -- EMPLOYEE ONLY
@warehouse_bp.route("/warehouses/ui/<int:warehouse_id>/products/<int:product_id>/remove", methods=["POST"])
@employee_only_ui
def warehouse_products_remove(warehouse_id, product_id):
    employee_id = session.get("user_id")
    deleted = remove_product_from_warehouse(warehouse_id, product_id, employee_id)
    flash("Product removed from warehouse." if deleted else "Product not found.",
          "success" if deleted else "error")
    return redirect(url_for("warehouse.warehouse_products_ui", warehouse_id=warehouse_id))

