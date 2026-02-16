# routes/category_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps

from models.category_model import (
    get_all_categories,
    get_category_by_id,
    insert_category,
    update_category_full,
    update_category_partial,
    delete_category,
    count_categories,
    search_categories_by_name,
    get_categories_with_product_count,
    get_top_products_by_category,
)
from models.image_model import get_primary_image

category_bp = Blueprint("category", __name__)


# ----------------------------
# AUTH DECORATORS (same idea as product_routes.py)
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

# GET /categories  (optional: ?q=...)
@category_bp.route("/categories", methods=["GET"])
def categories_index():
    q = request.args.get("q", "").strip()
    if q:
        categories = search_categories_by_name(q)
    else:
        categories = get_all_categories()

    return jsonify({"total": count_categories(), "results": categories}), 200


# GET /categories/<id>
@category_bp.route("/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):
    c = get_category_by_id(category_id)
    if not c:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(c), 200


# POST /categories  -- EMPLOYEE ONLY
@category_bp.route("/categories", methods=["POST"])
#@employee_only_api
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("category_name") or "").strip()
    desc = data.get("category_description")

    if not name:
        return jsonify({"error": "category_name is required"}), 400

    try:
        new_id = insert_category(name, desc)
    except Exception:
        return jsonify({"error": "Failed to create category (maybe name already exists)"}), 500

    return jsonify({"message": "Created", "category_id": new_id}), 201


# PUT /categories/<id> (full replace) -- EMPLOYEE ONLY
@category_bp.route("/categories/<int:category_id>", methods=["PUT"])
@employee_only_api
def put_category(category_id):
    data = request.get_json(silent=True) or {}
    name = (data.get("category_name") or "").strip()
    desc = data.get("category_description")

    if not name:
        return jsonify({"error": "category_name is required"}), 400

    updated = update_category_full(category_id, name, desc)
    if not updated:
        return jsonify({"error": "Category not found"}), 404

    return jsonify({"message": "Updated (full)"}), 200


# PATCH /categories/<id> (partial update) -- EMPLOYEE ONLY
@category_bp.route("/categories/<int:category_id>", methods=["PATCH"])
@employee_only_api
def patch_category(category_id):
    data = request.get_json(silent=True) or {}
    name = data.get("category_name", None)
    desc = data.get("category_description", None)

    updated = update_category_partial(category_id, name, desc)

    if updated == 0:
        if not get_category_by_id(category_id):
            return jsonify({"error": "Category not found"}), 404
        return jsonify({"error": "No fields provided to update"}), 400

    return jsonify({"message": "Updated (partial)"}), 200


# DELETE /categories/<id> -- EMPLOYEE ONLY
@category_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@employee_only_api
def remove_category(category_id):
    deleted = delete_category(category_id)
    if not deleted:
        return jsonify({"error": "Category not found"}), 404
    return jsonify({"message": "Deleted"}), 200


# =========================================================
# UI ROUTES (HTML pages)
# =========================================================

# GET /categories/ui - UNIFIED CATEGORIES PAGE (for customers)
@category_bp.route("/categories/ui", methods=["GET"])
def categories_ui():
    q = request.args.get("q", "").strip()

    # Get categories with product counts
    categories = get_categories_with_product_count()

    # Filter by search if provided
    if q:
        categories = [c for c in categories if q.lower() in c['category_name'].lower()]

    # Get top 3 products for each category and attach primary images
    for cat in categories:
        cat['top_products'] = get_top_products_by_category(cat['category_id'], limit=3)
        for p in cat['top_products']:
            img = get_primary_image(p['product_id'])
            p['primary_image'] = img['image_url'] if img else None

    # Check if user is employee or admin to show different template
    if session.get('user_type') in ['employee', 'admin']:
        return render_template(
            "categories/manage.html",
            categories=categories,
            total=count_categories(),
            q=q
        )

    return render_template(
        "categories/browse.html",
        categories=categories,
        total=count_categories(),
        q=q
    )


# GET/POST /categories/ui/create -- EMPLOYEE ONLY
@category_bp.route("/categories/ui/create", methods=["GET", "POST"])
@employee_only_ui
def categories_ui_create():
    if request.method == "POST":
        name = (request.form.get("category_name") or "").strip()
        desc = request.form.get("category_description")

        if not name:
            flash("Category name is required.", "error")
            return redirect(url_for("category.categories_ui_create"))

        insert_category(name, desc)
        flash("Category created successfully.", "success")
        return redirect(url_for("category.categories_ui"))

    return render_template("categories/create.html")


# GET/POST /categories/ui/edit/<id> -- EMPLOYEE ONLY
@category_bp.route("/categories/ui/edit/<int:category_id>", methods=["GET", "POST"])
@employee_only_ui
def categories_ui_edit(category_id):
    category = get_category_by_id(category_id)
    if not category:
        flash("Category not found.", "error")
        return redirect(url_for("category.categories_ui"))

    if request.method == "POST":
        name = (request.form.get("category_name") or "").strip()
        desc = request.form.get("category_description")

        if not name:
            flash("Category name is required.", "error")
            return redirect(url_for("category.categories_ui_edit", category_id=category_id))

        updated = update_category_full(category_id, name, desc)
        flash("Category updated successfully." if updated else "Update failed.", "success" if updated else "error")
        return redirect(url_for("category.categories_ui"))

    return render_template("categories/edit.html", category=category)


# POST /categories/ui/delete/<id> -- EMPLOYEE ONLY
@category_bp.route("/categories/ui/delete/<int:category_id>", methods=["POST"])
@employee_only_ui
def categories_ui_delete(category_id):
    deleted = delete_category(category_id)
    flash("Category deleted." if deleted else "Category not found.", "success" if deleted else "error")
    return redirect(url_for("category.categories_ui"))
