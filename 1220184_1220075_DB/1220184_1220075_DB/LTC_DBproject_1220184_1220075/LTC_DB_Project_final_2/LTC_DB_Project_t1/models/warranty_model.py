# models/warranty_model.py
from database.db import get_db_connection


def get_warranty_by_product_id(product_id):
    """Get warranty information for a specific product"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT warranty_id, product_id, warranty_months, warranty_provider
        FROM Warranty
        WHERE product_id = %s
        ORDER BY warranty_id DESC
        LIMIT 1
    """, (int(product_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_warranty_for_product(product_id):
    """Get active warranty information for display (returns warranty_months and warranty_provider)"""
    warranty = get_warranty_by_product_id(product_id)
    if warranty:
        return {
            'warranty_months': warranty.get('warranty_months'),
            'warranty_provider': warranty.get('warranty_provider')
        }
    return None


def create_warranty(product_id, warranty_months=None, warranty_provider=None):
    """Create or update warranty for a product"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if warranty already exists for this product
    existing = get_warranty_by_product_id(product_id)
    
    try:
        if existing:
            # Update existing warranty
            updates = []
            params = []
            
            if warranty_months is not None:
                updates.append("warranty_months = %s")
                params.append(int(warranty_months) if warranty_months else None)
            
            if warranty_provider is not None:
                updates.append("warranty_provider = %s")
                params.append(warranty_provider if warranty_provider else None)
            
            if updates:
                params.append(existing['warranty_id'])
                query = f"UPDATE Warranty SET {', '.join(updates)} WHERE warranty_id = %s"
                cur.execute(query, tuple(params))
                warranty_id = existing['warranty_id']
            else:
                warranty_id = existing['warranty_id']
        else:
            # Create new warranty
            cur.execute("""
                INSERT INTO Warranty (product_id, warranty_months, warranty_provider)
                VALUES (%s, %s, %s)
            """, (
                int(product_id),
                int(warranty_months) if warranty_months else None,
                warranty_provider
            ))
            warranty_id = cur.lastrowid
        
        conn.commit()
        cur.close()
        conn.close()
        return warranty_id
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise e


def update_warranty(product_id, warranty_months=None, warranty_provider=None):
    """Update warranty for a product (simplified version for product forms)"""
    return create_warranty(product_id, warranty_months=warranty_months, warranty_provider=warranty_provider)


def delete_warranty(product_id):
    """Delete warranty for a product"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Warranty WHERE product_id = %s", (int(product_id),))
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return affected > 0

