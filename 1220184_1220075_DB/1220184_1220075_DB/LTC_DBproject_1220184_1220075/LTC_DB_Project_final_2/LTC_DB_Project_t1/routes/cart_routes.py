# routes/cart_routes.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from functools import wraps
from models.cart_model import (
    get_cart_items,
    add_to_cart,
    remove_from_cart,
    update_cart_quantity,
    clear_cart,
    get_cart_count,
    get_cart_item_quantity
)
from models.product_model import get_product_by_id, get_product_total_stock

cart_bp = Blueprint("cart", __name__)


# Auth decorator for customers
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("user.login"))
        return view(*args, **kwargs)
    return wrapped


# GET /cart - View cart page
@cart_bp.route("/cart", methods=["GET"])
@login_required
def view_cart():
    # Only customers can access cart
    if session.get("user_type") in ["employee", "admin"]:
        flash("Cart is only available for customers.", "error")
        return redirect(url_for("user.customer_dashboard"))
    user_id = session.get('user_id')
    cart_data = get_cart_items(user_id)
    return render_template("cart/view.html", cart=cart_data)


# POST /cart/add - Add item to cart (API)
@cart_bp.route("/cart/add", methods=["POST"])
@login_required
def add_item():
    # Only customers can add to cart
    if session.get("user_type") in ["employee", "admin"]:
        return jsonify({"error": "Cart is only available for customers"}), 403
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    
    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400
    
    # Check if product exists
    product = get_product_by_id(int(product_id))
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # Check stock availability
    from models.cart_model import get_cart_item_quantity
    user_id = session.get('user_id')
    stock = get_product_total_stock(int(product_id))
    current_cart_qty = get_cart_item_quantity(user_id, int(product_id))
    requested_qty = int(quantity) + int(current_cart_qty)
    
    if stock < requested_qty:
        return jsonify({
            "error": f"Insufficient stock. Only {stock} available.",
            "available_stock": stock
        }), 400
    
    # Add to cart
    add_to_cart(user_id, product_id, quantity)
    cart_count = get_cart_count(user_id)
    
    return jsonify({
        "success": True,
        "message": "Item added to cart",
        "cart_count": cart_count
    }), 200


# POST /cart/remove - Remove item from cart
@cart_bp.route("/cart/remove", methods=["POST"])
@login_required
def remove_item():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    
    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400
    
    user_id = session.get('user_id')
    removed = remove_from_cart(user_id, product_id)
    if not removed:
        return jsonify({"error": "Item not found in cart"}), 404
    
    cart_count = get_cart_count(user_id)
    cart_data = get_cart_items(user_id)
    
    return jsonify({
        "success": True,
        "message": "Item removed from cart",
        "cart_count": cart_count,
        "cart_total": cart_data['total']
    }), 200


# POST /cart/update - Update item quantity
@cart_bp.route("/cart/update", methods=["POST"])
@login_required
def update_item():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    
    if not product_id or quantity is None:
        return jsonify({"error": "Product ID and quantity are required"}), 400
    
    quantity = int(quantity)
    
    # Check stock if increasing quantity
    if quantity > 0:
        stock = get_product_total_stock(int(product_id))
    if stock < quantity:
        return jsonify({
            "error": f"Insufficient stock. Only {stock} available.",
            "available_stock": stock
        }), 400
    
    user_id = session.get('user_id')
    updated = update_cart_quantity(user_id, product_id, quantity)
    if not updated:
        return jsonify({"error": "Item not found in cart"}), 404
    
    cart_count = get_cart_count(user_id)
    cart_data = get_cart_items(user_id)
    
    return jsonify({
        "success": True,
        "message": "Cart updated",
        "cart_count": cart_count,
        "cart_total": cart_data['total']
    }), 200


# GET /api/cart/count - Get cart count (for header badge)
@cart_bp.route("/api/cart/count", methods=["GET"])
def get_cart_count_api():
    if "user_id" not in session:
        return jsonify({"cart_count": 0}), 200
    
    user_id = session.get('user_id')
    count = get_cart_count(user_id)
    return jsonify({"cart_count": count}), 200


# GET /api/cart - Get cart data (for AJAX)
@cart_bp.route("/api/cart", methods=["GET"])
@login_required
def get_cart_api():
    user_id = session.get('user_id')
    cart_data = get_cart_items(user_id)
    return jsonify(cart_data), 200


# GET/POST /cart/checkout - Checkout page
@cart_bp.route("/cart/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    user_id = session.get('user_id')
    cart_data = get_cart_items(user_id)
    
    # If cart is empty, redirect to cart page
    if not cart_data['items']:
        flash("Your cart is empty. Add items before checkout.", "error")
        return redirect(url_for('cart.view_cart'))
    
    if request.method == "POST":
        # Get address information
        country = request.form.get("country", "").strip()
        city = request.form.get("city", "").strip()
        street_no = request.form.get("street_no", "").strip()
        building = request.form.get("building", "").strip() or None
        apartment_no = request.form.get("apartment_no", "").strip() or None
        
        # Get payment information
        payment_method = request.form.get("payment_method", "").strip()
        
        # Validation
        if not all([country, city, street_no]):
            flash("Country, city, and street number are required.", "error")
            return render_template("cart/checkout.html", cart=cart_data)
        
        if not payment_method:
            flash("Payment method is required.", "error")
            return render_template("cart/checkout.html", cart=cart_data)
        
        try:
            street_no = int(street_no)
            if apartment_no:
                apartment_no = int(apartment_no)
        except ValueError:
            flash("Street number and apartment number must be valid numbers.", "error")
            return render_template("cart/checkout.html", cart=cart_data)
        
        # Validate payment details for card payments
        if payment_method in ['Credit Card', 'Debit Card']:
            card_number = request.form.get("card_number", "").strip()
            card_expiry = request.form.get("card_expiry", "").strip()
            card_cvv = request.form.get("card_cvv", "").strip()
            cardholder_name = request.form.get("cardholder_name", "").strip()
            
            if not all([card_number, card_expiry, card_cvv, cardholder_name]):
                flash("Please fill in all card details.", "error")
                return render_template("cart/checkout.html", cart=cart_data)
        
        # Import order creation functions
        from models.order_model import insert_address, create_order, create_order_item, create_payment
        from models.product_model import get_product_by_id
        
        try:
            # Create address
            address_id = insert_address(country, city, street_no, building, apartment_no)
            
            # Create order with pending status
            order_id = create_order(user_id, address_id, delivery_status='Pending')
            
            # Create order items from cart
            for item in cart_data['items']:
                create_order_item(
                    order_id=order_id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price_at_order=item['price']
                )
            
            # Create payment record
            payment_status = 'Pending' if payment_method == 'Cash on Delivery' else 'Paid'
            create_payment(
                order_id=order_id,
                method=payment_method,
                payed_amount=cart_data['total'],
                payment_status=payment_status
            )
            
            # Clear cart from database after successful order
            clear_cart(user_id)
            
            flash(f"Order placed successfully! Order ID: #{order_id}", "success")
            return redirect(url_for('order.order_details', order_id=order_id))
            
        except Exception as e:
            flash(f"Failed to place order: {str(e)}", "error")
            return render_template("cart/checkout.html", cart=cart_data)
    
    # GET request - show checkout form
    return render_template("cart/checkout.html", cart=cart_data)

