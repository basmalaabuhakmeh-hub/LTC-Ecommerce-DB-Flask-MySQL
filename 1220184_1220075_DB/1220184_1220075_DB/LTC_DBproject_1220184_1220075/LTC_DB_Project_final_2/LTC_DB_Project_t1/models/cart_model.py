# models/cart_model.py
from database.db import get_db_connection
from models.product_model import get_product_by_id
from models.image_model import get_primary_image


def get_cart_items(user_id):
    """Get all items in the cart from database, with sale prices"""
    from models.sale_model import get_product_with_sale_price
    
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("""
        SELECT ci.cart_item_id, ci.product_id, ci.quantity
        FROM CartItem ci
        WHERE ci.user_id = %s
        ORDER BY ci.added_at DESC
    """, (int(user_id),))
    
    cart_rows = cur.fetchall()
    cur.close()
    conn.close()
    
    items = []
    total = 0.0
    
    for row in cart_rows:
        try:
            product_id = int(row['product_id'])
            # Get product with sale price
            product = get_product_with_sale_price(product_id)
            if product:
                img = get_primary_image(product_id)
                # Use sale price if available, otherwise regular price
                price = float(product.get('sale_price', product.get('price', 0)))
                quantity = int(row['quantity'])
                item = {
                    'cart_item_id': row['cart_item_id'],
                    'product_id': product_id,
                    'product_name': product['product_name'],
                    'product_description': product.get('product_description', ''),
                    'price': price,
                    'original_price': float(product.get('original_price', product.get('price', 0))),
                    'quantity': quantity,
                    'subtotal': price * quantity,
                    'is_on_sale': product.get('is_on_sale', False),
                    'discount_percentage': product.get('discount_percentage', 0),
                    'primary_image': img['image_url'] if img else None,
                    'category_name': product.get('category_name', '')
                }
                items.append(item)
                total += item['subtotal']
        except (ValueError, TypeError):
            continue
    
    return {
        'items': items,
        'total': total,
        'item_count': sum(item['quantity'] for item in items)
    }


def add_to_cart(user_id, product_id, quantity=1):
    """Add a product to cart or update quantity if already exists"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if item already exists in cart
        cur.execute("""
            SELECT cart_item_id, quantity
            FROM CartItem
            WHERE user_id = %s AND product_id = %s
        """, (int(user_id), int(product_id)))
        
        existing = cur.fetchone()
        
        if existing:
            # Update quantity
            new_quantity = existing[1] + int(quantity)
            cur.execute("""
                UPDATE CartItem
                SET quantity = %s
                WHERE cart_item_id = %s
            """, (new_quantity, existing[0]))
        else:
            # Insert new cart item
            cur.execute("""
                INSERT INTO CartItem (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (int(user_id), int(product_id), int(quantity)))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def remove_from_cart(user_id, product_id):
    """Remove a product from cart"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            DELETE FROM CartItem
            WHERE user_id = %s AND product_id = %s
        """, (int(user_id), int(product_id)))
        
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def update_cart_quantity(user_id, product_id, quantity):
    """Update quantity of a product in cart"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        qty = int(quantity)
        if qty <= 0:
            # Remove item if quantity is 0 or less
            return remove_from_cart(user_id, product_id)
        
        cur.execute("""
            UPDATE CartItem
            SET quantity = %s
            WHERE user_id = %s AND product_id = %s
        """, (qty, int(user_id), int(product_id)))
        
        updated = cur.rowcount > 0
        conn.commit()
        return updated
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def clear_cart(user_id):
    """Clear all items from cart"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            DELETE FROM CartItem
            WHERE user_id = %s
        """, (int(user_id),))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def get_cart_count(user_id):
    """Get total number of items in cart"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COALESCE(SUM(quantity), 0) as total
            FROM CartItem
            WHERE user_id = %s
        """, (int(user_id),))
        
        result = cur.fetchone()
        return int(result[0]) if result else 0
    except Exception:
        return 0
    finally:
        cur.close()
        conn.close()


def get_cart_item_quantity(user_id, product_id):
    """Get current quantity of a product in user's cart"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT quantity
            FROM CartItem
            WHERE user_id = %s AND product_id = %s
        """, (int(user_id), int(product_id)))
        
        row = cur.fetchone()
        return int(row['quantity']) if row else 0
    except Exception:
        return 0
    finally:
        cur.close()
        conn.close()
