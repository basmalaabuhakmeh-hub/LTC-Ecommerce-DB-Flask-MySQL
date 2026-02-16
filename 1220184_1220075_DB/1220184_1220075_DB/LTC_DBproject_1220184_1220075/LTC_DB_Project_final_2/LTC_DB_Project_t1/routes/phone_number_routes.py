# routes/phone_number_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps

from models.phone_number_model import (
    get_phone_numbers_by_user_id,
    get_phone_number_by_id,
    insert_phone_number,
    update_phone_number,
    delete_phone_number,
    count_phone_numbers_by_user
)
from models.user_model import get_user_by_id

phone_number_bp = Blueprint("phone_number", __name__)


# ----------------------------
# AUTH DECORATORS
# ----------------------------
def login_required_api(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized (please login)"}), 401
        return view(*args, **kwargs)
    return wrapped


def login_required_ui(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("user.login"))
        return view(*args, **kwargs)
    return wrapped


def owner_or_employee_only(view):
    """Allow users to manage their own phone numbers, or employees to manage any"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized (please login)"}), 401
        
        user_id = kwargs.get('user_id') or request.args.get('user_id') or request.form.get('user_id')
        if user_id and int(user_id) != session.get("user_id") and session.get("user_type") != "employee":
            return jsonify({"error": "Forbidden - You can only manage your own phone numbers"}), 403
        return view(*args, **kwargs)
    return wrapped


# =========================================================
# API ROUTES (JSON)
# =========================================================

# GET /phone-numbers/user/<user_id>
@phone_number_bp.route("/phone-numbers/user/<int:user_id>", methods=["GET"])
@login_required_api
def get_user_phone_numbers_api(user_id):
    # Users can only view their own phone numbers unless they're employees
    if user_id != session.get("user_id") and session.get("user_type") != "employee":
        return jsonify({"error": "Forbidden"}), 403
    
    phone_numbers = get_phone_numbers_by_user_id(user_id)
    return jsonify({"total": len(phone_numbers), "results": phone_numbers}), 200


# GET /phone-numbers/<id>
@phone_number_bp.route("/phone-numbers/<int:number_id>", methods=["GET"])
@login_required_api
def get_phone_number_api(number_id):
    phone_number = get_phone_number_by_id(number_id)
    if not phone_number:
        return jsonify({"error": "Phone number not found"}), 404
    
    # Users can only view their own phone numbers unless they're employees
    if phone_number["user_id"] != session.get("user_id") and session.get("user_type") != "employee":
        return jsonify({"error": "Forbidden"}), 403
    
    return jsonify(phone_number), 200


# POST /phone-numbers
@phone_number_bp.route("/phone-numbers", methods=["POST"])
@login_required_api
def create_phone_number_api():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    phone_number = data.get("phone_number", "").strip()

    if not user_id or not phone_number:
        return jsonify({"error": "user_id and phone_number are required"}), 400

    # Users can only add phone numbers to their own account unless they're employees
    if int(user_id) != session.get("user_id") and session.get("user_type") != "employee":
        return jsonify({"error": "Forbidden"}), 403

    if not get_user_by_id(int(user_id)):
        return jsonify({"error": "User not found"}), 404

    try:
        new_id = insert_phone_number(int(user_id), phone_number)
        return jsonify({"message": "Created", "number_id": new_id}), 201
    except Exception as e:
        return jsonify({"error": "Failed to create phone number"}), 500


# PUT /phone-numbers/<id>
@phone_number_bp.route("/phone-numbers/<int:number_id>", methods=["PUT"])
@login_required_api
def update_phone_number_api(number_id):
    phone_number_record = get_phone_number_by_id(number_id)
    if not phone_number_record:
        return jsonify({"error": "Phone number not found"}), 404

    # Users can only update their own phone numbers unless they're employees
    if phone_number_record["user_id"] != session.get("user_id") and session.get("user_type") != "employee":
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    phone_number = data.get("phone_number", "").strip()

    if not phone_number:
        return jsonify({"error": "phone_number is required"}), 400

    updated = update_phone_number(number_id, phone_number)
    if not updated:
        return jsonify({"error": "Update failed"}), 500

    return jsonify({"message": "Updated"}), 200


# DELETE /phone-numbers/<id>
@phone_number_bp.route("/phone-numbers/<int:number_id>", methods=["DELETE"])
@login_required_api
def delete_phone_number_api(number_id):
    phone_number_record = get_phone_number_by_id(number_id)
    if not phone_number_record:
        return jsonify({"error": "Phone number not found"}), 404

    # Users can only delete their own phone numbers unless they're employees
    if phone_number_record["user_id"] != session.get("user_id") and session.get("user_type") != "employee":
        return jsonify({"error": "Forbidden"}), 403

    deleted = delete_phone_number(number_id)
    if not deleted:
        return jsonify({"error": "Delete failed"}), 500

    return jsonify({"message": "Deleted"}), 200


# =========================================================
# UI ROUTES (HTML pages)
# =========================================================

# GET /phone-numbers/ui
@phone_number_bp.route("/phone-numbers/ui", methods=["GET"])
@login_required_ui
def phone_numbers_ui():
    user_id = session.get("user_id")
    phone_numbers = get_phone_numbers_by_user_id(user_id)
    return render_template(
        "users/phone_numbers.html",
        phone_numbers=phone_numbers,
        total=len(phone_numbers),
        user_id=user_id
    )


# POST /phone-numbers/ui/add
@phone_number_bp.route("/phone-numbers/ui/add", methods=["POST"])
@login_required_ui
def phone_numbers_ui_add():
    user_id = session.get("user_id")
    phone_number = request.form.get("phone_number", "").strip()

    if not phone_number:
        flash("Phone number is required.", "error")
        return redirect(url_for("phone_number.phone_numbers_ui"))

    try:
        insert_phone_number(user_id, phone_number)
        flash("Phone number added successfully.", "success")
    except Exception:
        flash("Failed to add phone number.", "error")

    return redirect(url_for("phone_number.phone_numbers_ui"))


# POST /phone-numbers/ui/edit/<id>
@phone_number_bp.route("/phone-numbers/ui/edit/<int:number_id>", methods=["POST"])
@login_required_ui
def phone_numbers_ui_edit(number_id):
    phone_number_record = get_phone_number_by_id(number_id)
    if not phone_number_record:
        flash("Phone number not found.", "error")
        return redirect(url_for("phone_number.phone_numbers_ui"))

    # Users can only edit their own phone numbers
    if phone_number_record["user_id"] != session.get("user_id"):
        flash("You can only edit your own phone numbers.", "error")
        return redirect(url_for("phone_number.phone_numbers_ui"))

    phone_number = request.form.get("phone_number", "").strip()

    if not phone_number:
        flash("Phone number is required.", "error")
        return redirect(url_for("phone_number.phone_numbers_ui"))

    updated = update_phone_number(number_id, phone_number)
    flash("Phone number updated successfully." if updated else "Update failed.", 
          "success" if updated else "error")
    return redirect(url_for("phone_number.phone_numbers_ui"))


# POST /phone-numbers/ui/delete/<id>
@phone_number_bp.route("/phone-numbers/ui/delete/<int:number_id>", methods=["POST"])
@login_required_ui
def phone_numbers_ui_delete(number_id):
    phone_number_record = get_phone_number_by_id(number_id)
    if not phone_number_record:
        flash("Phone number not found.", "error")
        return redirect(url_for("phone_number.phone_numbers_ui"))

    # Users can only delete their own phone numbers
    if phone_number_record["user_id"] != session.get("user_id"):
        flash("You can only delete your own phone numbers.", "error")
        return redirect(url_for("phone_number.phone_numbers_ui"))

    deleted = delete_phone_number(number_id)
    flash("Phone number deleted." if deleted else "Delete failed.", 
          "success" if deleted else "error")
    return redirect(url_for("phone_number.phone_numbers_ui"))

