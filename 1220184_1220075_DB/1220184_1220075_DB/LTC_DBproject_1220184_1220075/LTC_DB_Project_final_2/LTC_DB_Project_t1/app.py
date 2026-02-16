from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from routes.user_routes import user_bp
from routes.product_routes import product_bp
from routes.category_routes import category_bp
from routes.warehouse_routes import warehouse_bp
from routes.phone_number_routes import phone_number_bp
from routes.order_routes import order_bp
from routes.admin_routes import admin_bp
from routes.cart_routes import cart_bp
from routes.sale_routes import sale_bp
from models.dashboard_model import get_best_sellers
from models.category_model import get_all_categories
from models.image_model import get_primary_image

app = Flask(__name__)
app.config.from_object("config.Config")
app.secret_key = app.config.get("SECRET_KEY", "dev-secret")

# Session configuration: permanent sessions last 30 days (only when "Remember Me" is checked)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# HOME PAGE ROUTE
@app.route("/")
def index():
    # Get best sellers from database (top 3)
    best_sellers = get_best_sellers(3)

    # Get primary image for each best seller
    for product in best_sellers:
        img = get_primary_image(product['product_id'])
        product['primary_image'] = img['image_url'] if img else None

    # Get categories for shop by category section
    categories = get_all_categories()[:3]  # Limit to 3 categories

    return render_template("index.html", best_sellers=best_sellers, categories=categories)

# blueprints
app.register_blueprint(category_bp)
app.register_blueprint(user_bp)
app.register_blueprint(product_bp)
app.register_blueprint(warehouse_bp)
app.register_blueprint(phone_number_bp)
app.register_blueprint(order_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(sale_bp)


@app.before_request
def before_request_checks():
    """Run checks before every request"""
    # Automatically deactivate expired sales on every request
    from models.sale_model import check_and_deactivate_expired_sales
    check_and_deactivate_expired_sales()
    
    # Check login requirement for write methods
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # always allow static assets
        if request.endpoint == 'static':
            return

        # allow authentication endpoints (login/signup/choose)
        allowed = {'user.login', 'user.signup', 'user.auth_choice', 'user.logout', 'user.login'}
        if request.endpoint in allowed:
            return

        # if user is logged in, allow
        if session.get('user_id'):
            return

        # otherwise block: return JSON 401 for API requests, redirect to login for UI
        if request.headers.get('Accept', '').lower().startswith('application/json') or request.is_json:
            return jsonify({"error": "Unauthorized - please login"}), 401
        return redirect(url_for('user.login'))

if __name__ == "__main__":
    app.run(debug=True)

