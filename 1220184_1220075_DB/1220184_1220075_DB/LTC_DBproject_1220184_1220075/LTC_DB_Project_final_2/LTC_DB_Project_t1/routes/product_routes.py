# routes/product_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps

from models.product_model import (
    get_all_products,
    get_product_by_id,
    insert_product,
    update_product_full,
    update_product_partial,
    delete_product,
    count_products,
    search_products_by_name,
    filter_products_by_price,
    get_filtered_products,
    get_filtered_products_with_stock,
    get_similar_products,
    get_price_range,
    get_product_with_stock,
    get_product_total_stock
)

from models.category_model import get_all_categories, get_category_by_id
from models.warehouse_model import get_all_warehouses, add_product_to_warehouse
from models.image_model import get_images_by_product, insert_image, get_primary_image, set_primary_image, delete_image
import os
from werkzeug.utils import secure_filename


product_bp = Blueprint("product", __name__)


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

# GET /products (optional ?q=... or ?min_price=...&max_price=...)
@product_bp.route("/products", methods=["GET"])
def products_index():
    q = request.args.get("q", "").strip()
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")

    if q:
        products = search_products_by_name(q)
    elif min_price is not None and max_price is not None:
        products = filter_products_by_price(min_price, max_price)
    else:
        products = get_all_products()

    return jsonify({"total": count_products(), "results": products}), 200

# GET /products/<id>
@product_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    p = get_product_by_id(product_id)
    if not p:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(p), 200

# POST /products -- EMPLOYEE ONLY (category_id REQUIRED)
@product_bp.route("/products", methods=["POST"])
@employee_only_api
def create_product():
    data = request.get_json(silent=True) or {}

    category_id = data.get("category_id")
    product_name = (data.get("product_name") or "").strip()
    product_description = data.get("product_description")
    price = data.get("price")

    if category_id in (None, "") or not product_name or price in (None, ""):
        return jsonify({"error": "category_id, product_name and price are required"}), 400

    if not get_category_by_id(int(category_id)):
        return jsonify({"error": "Invalid category_id (category not found)"}), 400

    try:
        new_id = insert_product(int(category_id), product_name, product_description, price)
        
        # Handle warranty separately in Warranty table
        warranty_months = data.get("warranty_months")
        warranty_provider = data.get("warranty_provider")
        if warranty_months or warranty_provider:
            from models.warranty_model import create_warranty
            # Normalize warranty_months
            if warranty_months in (None, ""):
                warranty_months = None
            else:
                warranty_months = int(warranty_months)
            create_warranty(new_id, warranty_months=warranty_months, warranty_provider=warranty_provider)
    except Exception as e:
        return jsonify({"error": f"Failed to create product: {str(e)}"}), 500

    return jsonify({"message": "Created", "product_id": new_id}), 201


# PUT /products/<id> -- EMPLOYEE ONLY (full update, category_id REQUIRED)
@product_bp.route("/products/<int:product_id>", methods=["PUT"])
@employee_only_api
def put_product(product_id):
    data = request.get_json(silent=True) or {}

    category_id = data.get("category_id")
    product_name = (data.get("product_name") or "").strip()
    product_description = data.get("product_description")
    price = data.get("price")

    if category_id in (None, "") or not product_name or price in (None, ""):
        return jsonify({"error": "category_id, product_name and price are required"}), 400

    if not get_category_by_id(int(category_id)):
        return jsonify({"error": "Invalid category_id (category not found)"}), 400

    updated = update_product_full(product_id, int(category_id), product_name, product_description, price)
    if not updated:
        return jsonify({"error": "Product not found"}), 404
    
    # Handle warranty separately in Warranty table
    warranty_months = data.get("warranty_months")
    warranty_provider = data.get("warranty_provider")
    if warranty_months is not None or warranty_provider is not None:
        from models.warranty_model import update_warranty
        if warranty_months in (None, ""):
            warranty_months = None
        else:
            warranty_months = int(warranty_months)
        update_warranty(product_id, warranty_months=warranty_months, warranty_provider=warranty_provider)

    return jsonify({"message": "Updated (full)"}), 200


# PATCH /products/<id> -- EMPLOYEE ONLY (partial update, category_id allowed)
@product_bp.route("/products/<int:product_id>", methods=["PATCH"])
@employee_only_api
def patch_product(product_id):
    data = request.get_json(silent=True) or {}

    category_id = data.get("category_id", None)
    product_name = data.get("product_name", None)
    product_description = data.get("product_description", None)
    price = data.get("price", None)

    if category_id is not None and not get_category_by_id(int(category_id)):
        return jsonify({"error": "Invalid category_id (category not found)"}), 400

    updated = update_product_partial(product_id, category_id, product_name, product_description, price)

    if updated == 0:
        if not get_product_by_id(product_id):
            return jsonify({"error": "Product not found"}), 404
        # Check if only warranty fields were provided
        warranty_months = data.get("warranty_months", None)
        warranty_provider = data.get("warranty_provider", None)
        if warranty_months is not None or warranty_provider is not None:
            # Update warranty even if no product fields changed
            from models.warranty_model import update_warranty
            if warranty_months in (None, ""):
                warranty_months = None
            else:
                warranty_months = int(warranty_months)
            update_warranty(product_id, warranty_months=warranty_months, warranty_provider=warranty_provider)
            return jsonify({"message": "Updated (partial - warranty)"}), 200
        return jsonify({"error": "No fields provided to update"}), 400
    
    # Handle warranty separately in Warranty table if provided
    warranty_months = data.get("warranty_months", None)
    warranty_provider = data.get("warranty_provider", None)
    if warranty_months is not None or warranty_provider is not None:
        from models.warranty_model import update_warranty
        if warranty_months in (None, ""):
            warranty_months = None
        else:
            warranty_months = int(warranty_months)
        update_warranty(product_id, warranty_months=warranty_months, warranty_provider=warranty_provider)

    return jsonify({"message": "Updated (partial)"}), 200


# DELETE /products/<id> -- EMPLOYEE ONLY
@product_bp.route("/products/<int:product_id>", methods=["DELETE"])
@employee_only_api
def remove_product(product_id):
    deleted = delete_product(product_id)
    if not deleted:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Deleted"}), 200


# =========================================================
# UI ROUTES (HTML pages)
# =========================================================

# GET /products/ui - UNIFIED PRODUCTS PAGE (different views for employees and customers)
@product_bp.route("/products/ui", methods=["GET"])
def products_ui():
    # Get filter parameters
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    sort_by = request.args.get("sort", "newest").strip()

    # Convert empty strings to None
    category_id = int(category_id) if category_id else None
    min_price = float(min_price) if min_price else None
    max_price = float(max_price) if max_price else None

    # Get filtered products WITH stock information
    products = get_filtered_products_with_stock(
        q=q if q else None,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by
    )

    # Get primary image for each product
    for p in products:
        img = get_primary_image(p['product_id'])
        p['primary_image'] = img['image_url'] if img else None

    # Get all categories for filter dropdown
    categories = get_all_categories()

    # Get price range for slider
    price_range = get_price_range()

    template_data = {
        'products': products,
        'categories': categories,
        'price_range': price_range,
        'total': count_products(),
        'q': q,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by
    }

    # Check if user is employee or admin to show management template
    if session.get('user_type') in ['employee', 'admin']:
        return render_template("products/manage.html", **template_data)

    return render_template("products/browse.html", **template_data)


# GET /products/shop - Redirect to unified page
@product_bp.route("/products/shop", methods=["GET"])
def products_shop():
    return redirect(url_for("product.products_ui"))


# GET /products/<id>/similar - Get similar products (AJAX endpoint)
@product_bp.route("/products/<int:product_id>/similar", methods=["GET"])
def get_product_similar(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    similar = get_similar_products(product_id, product["category_id"], limit=4)
    # Enrich similar products with primary image and stock info for the client
    enriched = []
    from models.image_model import get_primary_image
    from models.product_model import get_product_total_stock
    for p in similar:
        img = get_primary_image(p['product_id'])
        p['primary_image'] = img['image_url'] if img else None
        try:
            p['total_stock'] = get_product_total_stock(p['product_id'])
        except Exception:
            p['total_stock'] = None
        enriched.append(p)

    return jsonify(enriched), 200


# Helper for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# GET/POST /products/ui/create -- EMPLOYEE ONLY (category required)
@product_bp.route("/products/ui/create", methods=["GET", "POST"])
@employee_only_ui
def products_ui_create():
    categories = get_all_categories()
    warehouses = get_all_warehouses()

    if request.method == "POST":
        category_id = request.form.get("category_id")
        name = (request.form.get("product_name") or "").strip()
        desc = request.form.get("product_description")
        price = request.form.get("price")
        warranty_provider = request.form.get("warranty_provider")
        warranty_months = request.form.get("warranty_months")
        if warranty_months in (None, ""):
            warranty_months = None
        else:
            try:
                warranty_months = int(warranty_months)
            except ValueError:
                warranty_months = None

        if not category_id or not name or not price:
            flash("Category, product name and price are required.", "error")
            return redirect(url_for("product.products_ui_create"))

        if not get_category_by_id(int(category_id)):
            flash("Invalid category selected.", "error")
            return redirect(url_for("product.products_ui_create"))

        # Create the product first
        new_product_id = insert_product(int(category_id), name, desc, price)
        
        # Handle warranty separately in Warranty table
        if warranty_months or warranty_provider:
            from models.warranty_model import create_warranty
            create_warranty(new_product_id, warranty_months=warranty_months, warranty_provider=warranty_provider)

        # Handle warehouse quantities
        for wh in warehouses:
            qty_field = f"warehouse_{wh['warehouse_id']}"
            qty = request.form.get(qty_field, "").strip()
            if qty and int(qty) > 0:
                add_product_to_warehouse(wh['warehouse_id'], new_product_id, int(qty))

        # Handle image uploads
        files = request.files.getlist('product_images')
        primary_image_index = request.form.get('primary_image', '0')

        try:
            primary_image_index = int(primary_image_index)
        except ValueError:
            primary_image_index = 0

        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'products')
        os.makedirs(upload_folder, exist_ok=True)

        for idx, file in enumerate(files):
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add product_id and timestamp to make filename unique
                import time
                unique_filename = f"{new_product_id}_{int(time.time())}_{idx}_{filename}"
                filepath = os.path.join(upload_folder, unique_filename)
                file.save(filepath)

                # Store relative URL
                image_url = f"/static/uploads/products/{unique_filename}"
                is_primary = (idx == primary_image_index)
                insert_image(new_product_id, image_url, is_primary=is_primary, display_order=idx)

        flash("Product created successfully.", "success")
        return redirect(url_for("product.products_ui"))

    return render_template("products/create.html", categories=categories, warehouses=warehouses)


# GET/POST /products/ui/edit/<id> -- EMPLOYEE ONLY
@product_bp.route("/products/ui/edit/<int:product_id>", methods=["GET", "POST"])
@employee_only_ui
def products_ui_edit(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("product.products_ui"))

    categories = get_all_categories()
    images = get_images_by_product(product_id)

    if request.method == "POST":
        category_id = request.form.get("category_id")
        name = (request.form.get("product_name") or "").strip()
        desc = request.form.get("product_description")
        price = request.form.get("price")
        warranty_provider = request.form.get("warranty_provider")
        warranty_months = request.form.get("warranty_months")
        if warranty_months in (None, ""):
            warranty_months = None
        else:
            try:
                warranty_months = int(warranty_months)
            except ValueError:
                warranty_months = None

        if not category_id or not name or not price:
            flash("Category, product name and price are required.", "error")
            return redirect(url_for("product.products_ui_edit", product_id=product_id))

        if not get_category_by_id(int(category_id)):
            flash("Invalid category selected.", "error")
            return redirect(url_for("product.products_ui_edit", product_id=product_id))

        updated = update_product_full(product_id, int(category_id), name, desc, price)
        
        # Handle warranty separately in Warranty table
        from models.warranty_model import update_warranty
        update_warranty(product_id, warranty_months=warranty_months, warranty_provider=warranty_provider)
        
        flash("Product updated successfully." if updated else "Update failed.", "success" if updated else "error")
        return redirect(url_for("product.products_ui"))

    return render_template("products/edit.html", product=product, categories=categories, images=images)


# POST /products/ui/<id>/images -- Add images to product (EMPLOYEE ONLY)
@product_bp.route("/products/ui/<int:product_id>/images", methods=["POST"])
@employee_only_ui
def add_images(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("product.products_ui"))

    files = request.files.getlist('new_images')
    set_as_primary = request.form.get('set_as_primary') == '1'

    if not files or all(f.filename == '' for f in files):
        flash("No images selected.", "error")
        return redirect(url_for("product.products_ui_edit", product_id=product_id))

    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'products')
    os.makedirs(upload_folder, exist_ok=True)

    uploaded_count = 0
    for idx, file in enumerate(files):
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            unique_filename = f"{product_id}_{int(time.time())}_{idx}_{filename}"
            filepath = os.path.join(upload_folder, unique_filename)
            file.save(filepath)

            image_url = f"/static/uploads/products/{unique_filename}"
            is_primary = set_as_primary and idx == 0
            insert_image(product_id, image_url, is_primary=is_primary, display_order=idx)
            uploaded_count += 1

    if uploaded_count > 0:
        flash(f"{uploaded_count} image(s) uploaded successfully.", "success")
    else:
        flash("No valid images were uploaded.", "error")

    return redirect(url_for("product.products_ui_edit", product_id=product_id))


# POST /products/ui/<id>/images/<image_id>/primary -- Set image as primary (EMPLOYEE ONLY)
@product_bp.route("/products/ui/<int:product_id>/images/<int:image_id>/primary", methods=["POST"])
@employee_only_ui
def set_primary_image_route(product_id, image_id):
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("product.products_ui"))

    updated = set_primary_image(image_id, product_id)
    if updated:
        flash("Primary image updated.", "success")
    else:
        flash("Failed to update primary image.", "error")

    return redirect(url_for("product.products_ui_edit", product_id=product_id))


# POST /products/ui/<id>/images/<image_id>/delete -- Delete an image (EMPLOYEE ONLY)
@product_bp.route("/products/ui/<int:product_id>/images/<int:image_id>/delete", methods=["POST"])
@employee_only_ui
def delete_image_route(product_id, image_id):
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("product.products_ui"))

    # Get image info before deleting to remove the file
    images = get_images_by_product(product_id)
    image_to_delete = next((img for img in images if img['image_id'] == image_id), None)

    if image_to_delete:
        # Try to delete the physical file
        if image_to_delete['image_url'].startswith('/static/uploads/'):
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), image_to_delete['image_url'].lstrip('/'))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # File deletion failed, but continue with DB deletion

        deleted = delete_image(image_id)
        if deleted:
            flash("Image deleted.", "success")
        else:
            flash("Failed to delete image.", "error")
    else:
        flash("Image not found.", "error")

    return redirect(url_for("product.products_ui_edit", product_id=product_id))


# POST /products/ui/delete/<id> -- EMPLOYEE ONLY
@product_bp.route("/products/ui/delete/<int:product_id>", methods=["POST"])
@employee_only_ui
def products_ui_delete(product_id):
    deleted = delete_product(product_id)
    flash("Product deleted." if deleted else "Product not found.", "success" if deleted else "error")
    return redirect(url_for("product.products_ui"))
