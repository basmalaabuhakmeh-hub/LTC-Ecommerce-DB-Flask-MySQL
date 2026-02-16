# models/image_model.py
from database.db import get_db_connection


def get_images_by_product(product_id):
    """Get all images for a product ordered by display_order and primary status"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM Image
        WHERE product_id = %s
        ORDER BY is_primary DESC, display_order ASC, image_id ASC
    """, (int(product_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_primary_image(product_id):
    """Get the primary image for a product"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM Image
        WHERE product_id = %s
        ORDER BY is_primary DESC, display_order ASC, image_id ASC
        LIMIT 1
    """, (int(product_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def insert_image(product_id, image_url, is_primary=False, display_order=None):
    """Insert a new image for a product"""
    conn = get_db_connection()
    cur = conn.cursor()

    # If this is set as primary, unset other primary images
    if is_primary:
        cur.execute("""
            UPDATE Image SET is_primary = FALSE
            WHERE product_id = %s
        """, (int(product_id),))

    cur.execute("""
        INSERT INTO Image (product_id, image_url, is_primary, display_order)
        VALUES (%s, %s, %s, %s)
    """, (int(product_id), image_url, is_primary, display_order))
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return new_id


def set_primary_image(image_id, product_id):
    """Set an image as the primary image for a product"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Unset all other primary images for this product
    cur.execute("""
        UPDATE Image SET is_primary = FALSE
        WHERE product_id = %s
    """, (int(product_id),))

    # Set the specified image as primary
    cur.execute("""
        UPDATE Image SET is_primary = TRUE
        WHERE image_id = %s AND product_id = %s
    """, (int(image_id), int(product_id)))

    conn.commit()
    updated = cur.rowcount
    cur.close()
    conn.close()
    return updated


def delete_image(image_id):
    """Delete an image"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Image WHERE image_id = %s", (int(image_id),))
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()
    return deleted


def update_image_order(image_id, display_order):
    """Update the display order of an image"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Image SET display_order = %s
        WHERE image_id = %s
    """, (int(display_order), int(image_id)))
    conn.commit()
    updated = cur.rowcount
    cur.close()
    conn.close()
    return updated
