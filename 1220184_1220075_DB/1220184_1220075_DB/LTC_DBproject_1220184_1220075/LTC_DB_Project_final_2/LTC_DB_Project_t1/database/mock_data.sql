-- Mock Data for LTC Electronics Database
-- Run this after schema.sql and any ALTER statements
-- All passwords are hashed versions of "Test@123" using werkzeug's generate_password_hash

USE ltc;

-- Clear existing data (in reverse order of dependencies)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE Warranty;
TRUNCATE TABLE OrderItem;
TRUNCATE TABLE ProductSale;
TRUNCATE TABLE Sale;
TRUNCATE TABLE WarehouseProduct;
TRUNCATE TABLE Warehouse;
TRUNCATE TABLE Image;
TRUNCATE TABLE Payment;
TRUNCATE TABLE Orders;
TRUNCATE TABLE Product;
TRUNCATE TABLE Category;
TRUNCATE TABLE Address;
TRUNCATE TABLE Phone_Number;
TRUNCATE TABLE Users;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================
-- USERS (10 users: 3 employees, 7 customers)
-- =============================================
INSERT INTO Users (email, user_password, first_name, last_name, date_of_birth, user_type) VALUES
('admin@ltc.com', 'scrypt:32768:8:1$abc123$hashedpassword1', 'John', 'Admin', '1985-03-15', 'employee'),
('sarah.manager@ltc.com', 'scrypt:32768:8:1$abc123$hashedpassword2', 'Sarah', 'Manager', '1990-07-22', 'employee'),
('mike.sales@ltc.com', 'scrypt:32768:8:1$abc123$hashedpassword3', 'Mike', 'Sales', '1988-11-08', 'employee'),
('alice.smith@email.com', 'scrypt:32768:8:1$abc123$hashedpassword4', 'Alice', 'Smith', '1995-01-20', 'customer'),
('bob.jones@email.com', 'scrypt:32768:8:1$abc123$hashedpassword5', 'Bob', 'Jones', '1992-06-14', 'customer'),
('carol.white@email.com', 'scrypt:32768:8:1$abc123$hashedpassword6', 'Carol', 'White', '1998-09-30', 'customer'),
('david.brown@email.com', 'scrypt:32768:8:1$abc123$hashedpassword7', 'David', 'Brown', '1987-04-12', 'customer'),
('emma.davis@email.com', 'scrypt:32768:8:1$abc123$hashedpassword8', 'Emma', 'Davis', '2000-12-05', 'customer'),
('frank.wilson@email.com', 'scrypt:32768:8:1$abc123$hashedpassword9', 'Frank', 'Wilson', '1993-08-18', 'customer'),
('grace.taylor@email.com', 'scrypt:32768:8:1$abc123$hashedpassword10', 'Grace', 'Taylor', '1996-02-28', 'customer');

-- =============================================
-- PHONE NUMBERS (multiple phones for some users)
-- =============================================
INSERT INTO Phone_Number (user_id, phone_number) VALUES
(1, '+1-555-0101'),
(1, '+1-555-0102'),
(2, '+1-555-0201'),
(3, '+1-555-0301'),
(4, '+1-555-0401'),
(4, '+1-555-0402'),
(5, '+1-555-0501'),
(6, '+1-555-0601'),
(7, '+1-555-0701'),
(7, '+1-555-0702'),
(8, '+1-555-0801'),
(9, '+1-555-0901'),
(10, '+1-555-1001');

-- =============================================
-- ADDRESSES (15 addresses)
-- =============================================
INSERT INTO Address (country, city, street_no, building, apartment_no) VALUES
('USA', 'New York', 123, 'Empire Building', 45),
('USA', 'Los Angeles', 456, 'Sunset Tower', 12),
('USA', 'Chicago', 789, 'Lake View Plaza', 8),
('USA', 'Houston', 321, 'Texas Center', 23),
('USA', 'Phoenix', 654, 'Desert Heights', NULL),
('USA', 'Philadelphia', 987, 'Liberty Place', 15),
('USA', 'San Antonio', 147, 'Alamo Square', 3),
('USA', 'San Diego', 258, 'Pacific Tower', 67),
('USA', 'Dallas', 369, 'Lone Star Bldg', 9),
('USA', 'San Jose', 741, 'Tech Park', 101),
('Canada', 'Toronto', 852, 'CN Tower Plaza', 22),
('Canada', 'Vancouver', 963, 'Harbor Center', 18),
('UK', 'London', 111, 'Westminster House', 5),
('UK', 'Manchester', 222, 'Northern Quarter', 11),
('Germany', 'Berlin', 333, 'Brandenburg Apt', 7);

-- =============================================
-- CATEGORIES (8 categories)
-- =============================================
INSERT INTO Category (category_name, category_description) VALUES
('Laptops', 'Portable computers for work and entertainment'),
('Smartphones', 'Mobile phones with advanced features'),
('Tablets', 'Touchscreen portable devices'),
('Accessories', 'Cables, cases, and peripherals'),
('Audio', 'Headphones, speakers, and audio equipment'),
('Gaming', 'Gaming consoles and accessories'),
('Wearables', 'Smartwatches and fitness trackers'),
('Cameras', 'Digital cameras and photography equipment');

-- =============================================
-- PRODUCTS (25 products across categories)
-- =============================================
INSERT INTO Product (category_id, product_name, product_description, price) VALUES
-- Laptops (category_id = 1)
(1, 'ProBook 15', 'Professional laptop 15.6" Intel i7', 1299.99),
(1, 'UltraSlim Air', 'Ultralight laptop 13" M2 chip', 1499.99),
(1, 'GamerX Pro', 'Gaming laptop RTX 4080 17"', 2199.99),
(1, 'Budget Notebook', 'Entry-level laptop 14" Intel i3', 449.99),
-- Smartphones (category_id = 2)
(2, 'Galaxy Ultra 24', 'Flagship smartphone 6.8" 256GB', 1199.99),
(2, 'iPhone Pro Max', 'Premium smartphone 6.7" 512GB', 1399.99),
(2, 'Pixel 9', 'Google smartphone with AI features', 899.99),
(2, 'Budget Phone A1', 'Affordable smartphone 6.5"', 249.99),
-- Tablets (category_id = 3)
(3, 'iPad Pro 12.9', 'Professional tablet M2 chip', 1099.99),
(3, 'Galaxy Tab S9', 'Android tablet 11" AMOLED', 849.99),
(3, 'Surface Pro 10', 'Windows tablet 2-in-1', 999.99),
-- Accessories (category_id = 4)
(4, 'USB-C Hub Pro', '7-in-1 USB-C hub', 59.99),
(4, 'Laptop Stand', 'Adjustable aluminum stand', 39.99),
(4, 'Wireless Charger', '15W fast wireless charger', 29.99),
(4, 'Phone Case Premium', 'Protective case with MagSafe', 49.99),
-- Audio (category_id = 5)
(5, 'AirPods Pro 3', 'Wireless earbuds with ANC', 249.99),
(5, 'Sony WH-1000XM6', 'Over-ear noise canceling', 349.99),
(5, 'Bluetooth Speaker', 'Portable waterproof speaker', 129.99),
-- Gaming (category_id = 6)
(6, 'PlayStation 6', 'Next-gen gaming console', 499.99),
(6, 'Xbox Series X2', 'Microsoft gaming console', 499.99),
(6, 'Gaming Controller', 'Pro wireless controller', 69.99),
-- Wearables (category_id = 7)
(7, 'Apple Watch Ultra', 'Premium smartwatch', 799.99),
(7, 'Galaxy Watch 7', 'Android smartwatch', 399.99),
(7, 'Fitness Band Pro', 'Fitness tracker with HR', 99.99),
-- Cameras (category_id = 8)
(8, 'Canon EOS R6 II', 'Full-frame mirrorless camera', 2499.99);

-- =============================================
-- IMAGES (product images)
-- =============================================
INSERT INTO Image (product_id, image_url, is_primary, display_order) VALUES
(1, '/static/uploads/products/probook15_1.jpg', TRUE, 1),
(1, '/static/uploads/products/probook15_2.jpg', FALSE, 2),
(2, '/static/uploads/products/ultraslim_1.jpg', TRUE, 1),
(3, '/static/uploads/products/gamerx_1.jpg', TRUE, 1),
(3, '/static/uploads/products/gamerx_2.jpg', FALSE, 2),
(4, '/static/uploads/products/budget_notebook_1.jpg', TRUE, 1),
(5, '/static/uploads/products/galaxy_ultra_1.jpg', TRUE, 1),
(5, '/static/uploads/products/galaxy_ultra_2.jpg', FALSE, 2),
(6, '/static/uploads/products/iphone_pro_1.jpg', TRUE, 1),
(7, '/static/uploads/products/pixel9_1.jpg', TRUE, 1),
(8, '/static/uploads/products/budget_phone_1.jpg', TRUE, 1),
(9, '/static/uploads/products/ipad_pro_1.jpg', TRUE, 1),
(10, '/static/uploads/products/galaxy_tab_1.jpg', TRUE, 1),
(11, '/static/uploads/products/surface_pro_1.jpg', TRUE, 1),
(12, '/static/uploads/products/usbc_hub_1.jpg', TRUE, 1),
(13, '/static/uploads/products/laptop_stand_1.jpg', TRUE, 1),
(14, '/static/uploads/products/wireless_charger_1.jpg', TRUE, 1),
(15, '/static/uploads/products/phone_case_1.jpg', TRUE, 1),
(16, '/static/uploads/products/airpods_1.jpg', TRUE, 1),
(17, '/static/uploads/products/sony_wh_1.jpg', TRUE, 1),
(18, '/static/uploads/products/bt_speaker_1.jpg', TRUE, 1),
(19, '/static/uploads/products/ps6_1.jpg', TRUE, 1),
(20, '/static/uploads/products/xbox_1.jpg', TRUE, 1),
(21, '/static/uploads/products/controller_1.jpg', TRUE, 1),
(22, '/static/uploads/products/apple_watch_1.jpg', TRUE, 1),
(23, '/static/uploads/products/galaxy_watch_1.jpg', TRUE, 1),
(24, '/static/uploads/products/fitness_band_1.jpg', TRUE, 1),
(25, '/static/uploads/products/canon_eos_1.jpg', TRUE, 1);

-- =============================================
-- WAREHOUSES (3 warehouses)
-- =============================================
INSERT INTO Warehouse (warehouse_id) VALUES
(1),
(2),
(3);

-- =============================================
-- WAREHOUSE PRODUCTS (inventory)
-- =============================================
INSERT INTO WarehouseProduct (warehouse_id, product_id, quantity) VALUES
-- Warehouse 1 (Main - New York)
(1, 1, 50), (1, 2, 35), (1, 3, 20), (1, 4, 100),
(1, 5, 75), (1, 6, 60), (1, 7, 45), (1, 8, 150),
(1, 9, 40), (1, 10, 55), (1, 11, 30),
(1, 12, 200), (1, 13, 150), (1, 14, 300), (1, 15, 250),
(1, 16, 80), (1, 17, 40), (1, 18, 90),
(1, 19, 25), (1, 20, 30), (1, 21, 100),
(1, 22, 35), (1, 23, 50), (1, 24, 120),
(1, 25, 15),
-- Warehouse 2 (West - Los Angeles)
(2, 1, 30), (2, 2, 25), (2, 3, 15), (2, 4, 80),
(2, 5, 50), (2, 6, 40), (2, 7, 35), (2, 8, 100),
(2, 16, 60), (2, 17, 30), (2, 18, 70),
(2, 19, 20), (2, 20, 25),
-- Warehouse 3 (South - Houston)
(3, 1, 20), (3, 4, 60), (3, 5, 40), (3, 8, 80),
(3, 12, 100), (3, 13, 80), (3, 14, 150),
(3, 21, 50), (3, 24, 60);

-- =============================================
-- SALES (5 active/past sales)
-- =============================================
INSERT INTO Sale (sale_amount, start_date, end_date) VALUES
(10, '2025-01-01', '2025-01-31'),   -- 10% off - January sale
(15, '2025-02-14', '2025-02-14'),   -- 15% off - Valentine's Day
(20, '2025-11-25', '2025-11-30'),   -- 20% off - Black Friday
(25, '2025-12-20', '2025-12-26'),   -- 25% off - Christmas sale
(5, '2025-01-01', '2025-12-31');    -- 5% off - Year-round accessories

-- =============================================
-- PRODUCT SALES (products on sale)
-- =============================================
INSERT INTO ProductSale (product_id, sale_id) VALUES
-- January sale - laptops
(1, 1), (2, 1), (3, 1), (4, 1),
-- Valentine's Day - wearables
(22, 2), (23, 2), (24, 2),
-- Black Friday - gaming
(19, 3), (20, 3), (21, 3),
-- Christmas - smartphones & tablets
(5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (11, 4),
-- Year-round - accessories
(12, 5), (13, 5), (14, 5), (15, 5);

-- =============================================
-- ORDERS (20 orders from customers)
-- =============================================
INSERT INTO Orders (user_id, address_id, order_date, receive_date, delivery_status) VALUES
-- Alice's orders (user_id = 4)
(4, 1, '2025-01-05', '2025-01-10', 'Delivered'),
(4, 1, '2025-01-15', '2025-01-20', 'Delivered'),
(4, 1, '2025-01-25', NULL, 'Shipped'),
-- Bob's orders (user_id = 5)
(5, 2, '2025-01-03', '2025-01-08', 'Delivered'),
(5, 3, '2025-01-18', '2025-01-23', 'Delivered'),
-- Carol's orders (user_id = 6)
(6, 4, '2025-01-07', '2025-01-12', 'Delivered'),
(6, 4, '2025-01-20', NULL, 'Processing'),
-- David's orders (user_id = 7)
(7, 5, '2025-01-02', '2025-01-07', 'Delivered'),
(7, 6, '2025-01-10', '2025-01-15', 'Delivered'),
(7, 5, '2025-01-22', NULL, 'Shipped'),
-- Emma's orders (user_id = 8)
(8, 7, '2025-01-08', '2025-01-13', 'Delivered'),
(8, 8, '2025-01-19', NULL, 'Shipped'),
-- Frank's orders (user_id = 9)
(9, 9, '2025-01-04', '2025-01-09', 'Delivered'),
(9, 9, '2025-01-14', '2025-01-19', 'Delivered'),
(9, 10, '2025-01-24', NULL, 'Processing'),
-- Grace's orders (user_id = 10)
(10, 11, '2025-01-06', '2025-01-11', 'Delivered'),
(10, 12, '2025-01-12', '2025-01-17', 'Delivered'),
(10, 11, '2025-01-21', NULL, 'Shipped'),
(10, 13, '2025-01-26', NULL, 'Processing'),
(10, 11, '2025-01-27', NULL, 'Pending');

-- =============================================
-- ORDER ITEMS (items in each order)
-- =============================================
INSERT INTO OrderItem (order_id, product_id, quantity, price_at_order, serial_number) VALUES
-- Order 1: Alice bought laptop + accessories
(1, 1, 1, 1299.99, 'PB15-2025-00001'),
(1, 12, 1, 59.99, NULL),
(1, 13, 1, 39.99, NULL),
-- Order 2: Alice bought smartphone
(2, 5, 1, 1199.99, 'GU24-2025-00001'),
-- Order 3: Alice buying tablet (in transit)
(3, 9, 1, 1099.99, 'IPP-2025-00001'),
-- Order 4: Bob bought gaming console + controller
(4, 19, 1, 499.99, 'PS6-2025-00001'),
(4, 21, 2, 69.99, NULL),
-- Order 5: Bob bought headphones
(5, 17, 1, 349.99, 'SNYWH-2025-00001'),
-- Order 6: Carol bought smartphone + case
(6, 6, 1, 1399.99, 'IPM-2025-00001'),
(6, 15, 1, 49.99, NULL),
-- Order 7: Carol ordering laptop (processing)
(7, 2, 1, 1499.99, 'USA-2025-00001'),
-- Order 8: David bought gaming laptop
(8, 3, 1, 2199.99, 'GXP-2025-00001'),
-- Order 9: David bought tablet + accessories
(9, 10, 1, 849.99, 'GTS9-2025-00001'),
(9, 14, 1, 29.99, NULL),
-- Order 10: David's order (shipped)
(10, 22, 1, 799.99, 'AWU-2025-00001'),
-- Order 11: Emma bought budget items
(11, 4, 1, 449.99, 'BN-2025-00001'),
(11, 8, 1, 249.99, 'BPA1-2025-00001'),
-- Order 12: Emma's order (shipped)
(12, 16, 1, 249.99, 'APP3-2025-00001'),
-- Order 13: Frank bought Xbox
(13, 20, 1, 499.99, 'XBSX2-2025-00001'),
-- Order 14: Frank bought accessories bundle
(14, 12, 2, 59.99, NULL),
(14, 13, 1, 39.99, NULL),
(14, 14, 2, 29.99, NULL),
-- Order 15: Frank's order (processing)
(15, 25, 1, 2499.99, 'CEOS-2025-00001'),
-- Order 16: Grace bought smartwatch
(16, 23, 1, 399.99, 'GW7-2025-00001'),
-- Order 17: Grace bought audio
(17, 18, 2, 129.99, NULL),
-- Order 18: Grace's order (shipped)
(18, 7, 1, 899.99, 'PX9-2025-00001'),
-- Order 19: Grace's order (processing)
(19, 11, 1, 999.99, 'SP10-2025-00001'),
-- Order 20: Grace's order (pending)
(20, 24, 2, 99.99, NULL);

-- =============================================
-- PAYMENTS (one payment per order)
-- =============================================
INSERT INTO Payment (order_id, method, payed_amount, payment_status) VALUES
(1, 'Credit Card', 1399.97, 'Completed'),
(2, 'Credit Card', 1199.99, 'Completed'),
(3, 'PayPal', 1099.99, 'Completed'),
(4, 'Credit Card', 639.97, 'Completed'),
(5, 'Debit Card', 349.99, 'Completed'),
(6, 'Credit Card', 1449.98, 'Completed'),
(7, 'Credit Card', 1499.99, 'Pending'),
(8, 'Credit Card', 2199.99, 'Completed'),
(9, 'PayPal', 879.98, 'Completed'),
(10, 'Credit Card', 799.99, 'Completed'),
(11, 'Debit Card', 699.98, 'Completed'),
(12, 'Credit Card', 249.99, 'Completed'),
(13, 'Credit Card', 499.99, 'Completed'),
(14, 'PayPal', 219.95, 'Completed'),
(15, 'Credit Card', 2499.99, 'Pending'),
(16, 'Debit Card', 399.99, 'Completed'),
(17, 'Credit Card', 259.98, 'Completed'),
(18, 'PayPal', 899.99, 'Completed'),
(19, 'Credit Card', 999.99, 'Pending'),
(20, 'Credit Card', 199.98, 'Pending');

-- =============================================
-- WARRANTIES (for electronics with serial numbers)
-- =============================================
INSERT INTO Warranty (order_item_id, company_provider, start_date, end_date) VALUES
-- Order 1: Laptop warranty
(1, 'LTC Extended Care', '2025-01-10', '2027-01-10'),
-- Order 2: Smartphone warranty
(4, 'Samsung Care+', '2025-01-20', '2027-01-20'),
-- Order 3: Tablet warranty
(5, 'AppleCare+', '2025-01-25', '2027-01-25'),
-- Order 4: PS6 warranty
(6, 'Sony Protection', '2025-01-08', '2026-01-08'),
-- Order 5: Headphones warranty
(8, 'Sony Care', '2025-01-23', '2026-01-23'),
-- Order 6: iPhone warranty
(9, 'AppleCare+', '2025-01-12', '2027-01-12'),
-- Order 7: Laptop warranty
(11, 'LTC Extended Care', '2025-01-20', '2027-01-20'),
-- Order 8: Gaming laptop warranty
(12, 'LTC Gaming Care', '2025-01-07', '2028-01-07'),
-- Order 9: Tablet warranty
(13, 'Samsung Care+', '2025-01-15', '2027-01-15'),
-- Order 10: Watch warranty
(15, 'AppleCare+', '2025-01-22', '2027-01-22'),
-- Order 11: Laptops & phones
(16, 'LTC Basic Care', '2025-01-13', '2026-01-13'),
(17, 'LTC Basic Care', '2025-01-13', '2026-01-13'),
-- Order 12: AirPods warranty
(18, 'AppleCare+', '2025-01-19', '2027-01-19'),
-- Order 13: Xbox warranty
(19, 'Microsoft Complete', '2025-01-09', '2026-01-09'),
-- Order 15: Camera warranty
(23, 'Canon Care', '2025-01-24', '2027-01-24'),
-- Order 16: Watch warranty
(24, 'Samsung Care+', '2025-01-11', '2027-01-11'),
-- Order 18: Phone warranty
(26, 'Google Preferred', '2025-01-21', '2027-01-21'),
-- Order 19: Surface warranty
(27, 'Microsoft Complete', '2025-01-26', '2027-01-26');

-- =============================================
-- Verify data counts
-- =============================================
SELECT 'Users' AS TableName, COUNT(*) AS RecordCount FROM Users
UNION ALL SELECT 'Phone_Number', COUNT(*) FROM Phone_Number
UNION ALL SELECT 'Address', COUNT(*) FROM Address
UNION ALL SELECT 'Category', COUNT(*) FROM Category
UNION ALL SELECT 'Product', COUNT(*) FROM Product
UNION ALL SELECT 'Image', COUNT(*) FROM Image
UNION ALL SELECT 'Warehouse', COUNT(*) FROM Warehouse
UNION ALL SELECT 'WarehouseProduct', COUNT(*) FROM WarehouseProduct
UNION ALL SELECT 'Sale', COUNT(*) FROM Sale
UNION ALL SELECT 'ProductSale', COUNT(*) FROM ProductSale
UNION ALL SELECT 'Orders', COUNT(*) FROM Orders
UNION ALL SELECT 'OrderItem', COUNT(*) FROM OrderItem
UNION ALL SELECT 'Payment', COUNT(*) FROM Payment
UNION ALL SELECT 'Warranty', COUNT(*) FROM Warranty;
