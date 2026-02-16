# LTC E-Commerce Website — Database Project (COMP333)

E-commerce web application for **Light for Technology & Computer (LTC)**, a computer and networking store in Ramallah. Customers can browse products, use a shopping cart, and place orders; admins and employees manage products, inventory, orders, and users. Backend: **Flask (Python)**; database: **MySQL**. Phase 1 and Phase 2 reports describe scope, entities, relations, and queries (CREATE/READ/UPDATE/DELETE).


## Overview

- **Scope:** Customer registration and login, product browsing and search, categories and filtering, shopping cart and checkout, order and delivery tracking, admin panel for products and orders. Database stores customers, products, orders, branches, employees, warehouses, sales, payments, users.
- **Phase 1:** Project description, client info, technology stack (Windows, HTML/CSS, Flask, MySQL), expected entities and relations, and a list of queries (add product/customer/order/supplier/stock; read branches, managers, employees, products, orders, revenue, best sellers, out-of-stock, users; update price/stock/customer/order status; delete product/order/customer).
- **Phase 2:** Refined entities and relations (branches, employees, managers, warehouses, products, orders, sales, payments, users), same query set, and ER diagram.
- **Implementation:** Flask app in **1220184_1220075_DB** (nested path: `.../LTC_DB_Project_t1/`). Includes `app.py`, `config.py`, models (user, product, category, warehouse, order, cart, sale, admin, dashboard, etc.), routes (user, product, category, warehouse, order, admin, cart, sale, phone_number), templates (HTML), and database scripts (`schema.sql`, `mock_data.sql`). MySQL database name: **ltc**.

---

## Project structure

```
.
├── README.md
├── 1220184_1220075_phase1_Database.pdf   # Phase 1 report (scope, entities, queries)
├── 1220184_1220075_phase1_Database.docx
├── 1220184_1220075_phase2_Database.pdf   # Phase 2 report (refined design, ER diagram)
├── 1220184_1220075_phase2_Database.docx
├── Demo.txt
├── 1220184_1220075_DB.zip                # Optional: archive of the code folder
└── 1220184_1220075_DB/                    # Code folder
    └── 1220184_1220075_DB/
        └── LTC_DBproject_1220184_1220075/
            └── LTC_DB_Project_final_2/
                └── LTC_DB_Project_t1/     # Flask app root
                    ├── app.py
                    ├── config.py
                    ├── models/
                    ├── routes/
                    ├── templates/
                    └── database/
                        ├── schema.sql
                        └── mock_data.sql
```

---

## Requirements

- **Python 3.x** with **Flask** and **MySQL** connector (e.g. `flask`, `mysql-connector-python` or `PyMySQL`).
- **MySQL** server. Create a database named **ltc** (or change `MYSQL_DB` in `config.py`).
- **config.py** (in `LTC_DB_Project_t1`) sets `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`; adjust for your environment.

---

## Usage

1. **MySQL:** Create database and load schema and data:
   ```bash
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS ltc;"
   mysql -u root -p ltc < "1220184_1220075_DB/1220184_1220075_DB/LTC_DBproject_1220184_1220075/LTC_DB_Project_final_2/LTC_DB_Project_t1/database/schema.sql"
   mysql -u root -p ltc < "1220184_1220075_DB/.../LTC_DB_Project_t1/database/mock_data.sql"
   ```
   (Use the actual path to `schema.sql` and `mock_data.sql` on your machine.)

2. **Config:** Edit `LTC_DB_Project_t1/config.py` if needed (host, user, password, db name).

3. **Python:** From `LTC_DB_Project_t1`:
   ```bash
   pip install flask mysql-connector-python
   python app.py
   ```
   The app runs with `debug=True` (default Flask port 5000). Open the site in a browser for customer and admin flows.

---

## Reports

- **Phase 1:** Scope, client, tech stack, entities/relations, full query list — **1220184_1220075_phase1_Database.pdf** 
- **Phase 2:** Refined design, relations, ER diagram — **1220184_1220075_phase2_Database.pdf**

