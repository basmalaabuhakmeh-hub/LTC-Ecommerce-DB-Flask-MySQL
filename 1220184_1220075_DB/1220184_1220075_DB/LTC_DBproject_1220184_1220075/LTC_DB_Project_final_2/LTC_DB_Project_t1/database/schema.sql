CREATE DATABASE ltc;
USE ltc;

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(32) NOT NULL UNIQUE,
    password VARCHAR(32) NOT NULL,
    first_name VARCHAR(32) NOT NULL,
    last_name VARCHAR(32) NOT NULL,
    date_of_birth DATE,
    user_type VARCHAR(16) NOT NULL
);

CREATE TABLE Phone_Number (
    number_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Address (
    address_id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(20) NOT NULL,
    city VARCHAR(20) NOT NULL,
    street_no INT NOT NULL,
    building VARCHAR(30),
    apartment_no INT
);

CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    address_id INT NOT NULL,
    order_date DATE NOT NULL,
    receive_date DATE,
    delivery_status VARCHAR(30),
    total_price DOUBLE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (address_id) REFERENCES Address(address_id)
);

CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    method VARCHAR(50) NOT NULL,
    payed_amount DOUBLE NOT NULL,
    payment_status VARCHAR(16) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE
);

CREATE TABLE Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(32) NOT NULL UNIQUE,
    category_description VARCHAR(255)
);

CREATE TABLE Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT,
    product_name VARCHAR(30) NOT NULL,
    product_description VARCHAR(50),
    price INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);

ALTER TABLE Product
MODIFY category_id INT;  # NOT NULL !!!!!!!!!!!!!!!!!!!

CREATE TABLE Image (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    display_order INT,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE
);

CREATE TABLE Warehouse (
    warehouse_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_quantity INT NOT NULL
);

CREATE TABLE WarehouseProduct (
    warehouse_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (warehouse_id, product_id),
    FOREIGN KEY (warehouse_id) REFERENCES Warehouse(warehouse_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE
);

CREATE TABLE Sale (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_amount INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

CREATE TABLE ProductSale (
    product_id INT NOT NULL,
    sale_id INT NOT NULL,
    PRIMARY KEY (product_id, sale_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (sale_id) REFERENCES Sale(sale_id) ON DELETE CASCADE
);

CREATE TABLE OrderItem (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_order DOUBLE NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE Warranty (
    warranty_id INT AUTO_INCREMENT PRIMARY KEY,
    order_item_id INT NOT NULL,
    FOREIGN KEY (order_item_id) REFERENCES OrderItem(order_item_id) ON DELETE CASCADE
);

CREATE TABLE CartItem (
    cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_product (user_id, product_id)
);

SHOW TABLES;
SELECT COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'ltc';

SELECT * FROM Product;
SELECT * FROM Users;

SELECT DATABASE();
SELECT COUNT(*) FROM Product;
SELECT * FROM Product;
ALTER TABLE Users MODIFY password VARCHAR(255) NOT NULL;

ALTER TABLE Orders
DROP COLUMN total_price;
SELECT * FROM Orders;

SELECT 
  o.order_id,
  SUM(oi.quantity * oi.price_at_order) AS total_price
FROM Orders o
JOIN OrderItem oi ON oi.order_id = o.order_id
GROUP BY o.order_id;

ALTER TABLE Warehouse
DROP COLUMN stock_quantity;




ALTER TABLE Product
MODIFY category_id INT NOT NULL;

ALTER TABLE OrderItem
ADD CONSTRAINT uq_order_product UNIQUE (order_id, product_id);

ALTER TABLE Product
MODIFY price DECIMAL(10,2) NOT NULL;

ALTER TABLE OrderItem
MODIFY price_at_order DECIMAL(10,2) NOT NULL;

ALTER TABLE Payment
MODIFY payed_amount DECIMAL(10,2) NOT NULL;

-- Add warranty information to products (displayed before purchase)
ALTER TABLE Product
ADD COLUMN warranty_months INT DEFAULT NULL,
ADD COLUMN warranty_provider VARCHAR(50) DEFAULT NULL;



