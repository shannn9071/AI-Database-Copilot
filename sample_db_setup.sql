-- ============================================================
-- sample_db_setup.sql
-- Sample business database for AI Database Copilot demos.
-- Run this after creating the database, e.g.:
--   createdb ai_copilot_db
--   psql -d ai_copilot_db -f sample_db_setup.sql
-- ============================================================

-- Clean slate (safe to re-run during development)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- ---------- Tables ----------

CREATE TABLE customers (
    customer_id   SERIAL PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(120) UNIQUE NOT NULL,
    city          VARCHAR(60),
    signup_date   DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE products (
    product_id    SERIAL PRIMARY KEY,
    product_name  VARCHAR(120) NOT NULL,
    category      VARCHAR(60),
    price         NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    stock_qty     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE orders (
    order_id      SERIAL PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    status        VARCHAR(20) NOT NULL DEFAULT 'completed'
                  CHECK (status IN ('completed', 'pending', 'cancelled'))
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id),
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

-- ---------- Sample data ----------

INSERT INTO customers (full_name, email, city, signup_date) VALUES
('Ananya Rao',        'ananya.rao@example.com',    'Bengaluru', '2023-01-15'),
('Rahul Mehta',        'rahul.mehta@example.com',   'Mumbai',    '2023-03-22'),
('Priya Nair',         'priya.nair@example.com',    'Kochi',     '2023-05-10'),
('Karan Singh',        'karan.singh@example.com',   'Delhi',     '2023-07-01'),
('Sneha Iyer',         'sneha.iyer@example.com',    'Chennai',   '2023-08-19'),
('Vikram Patel',       'vikram.patel@example.com',  'Ahmedabad', '2023-11-02'),
('Divya Menon',        'divya.menon@example.com',   'Bengaluru', '2024-01-27'),
('Arjun Kumar',        'arjun.kumar@example.com',   'Hyderabad', '2024-02-14'),
('Meera Joshi',        'meera.joshi@example.com',   'Pune',      '2024-04-30'),
('Rohan Das',          'rohan.das@example.com',     'Kolkata',   '2024-06-05');

INSERT INTO products (product_name, category, price, stock_qty) VALUES
('Wireless Mouse',        'Electronics', 799.00,  120),
('Mechanical Keyboard',   'Electronics', 3499.00, 60),
('USB-C Hub',             'Electronics', 1599.00, 80),
('Office Chair',          'Furniture',   8999.00, 15),
('Standing Desk',         'Furniture',   14999.00, 10),
('Notebook Set',          'Stationery',  249.00,  300),
('Fountain Pen',          'Stationery',  599.00,  90),
('Desk Lamp',             'Furniture',   1299.00, 45),
('Bluetooth Speaker',     'Electronics', 2199.00, 55),
('Water Bottle',          'Lifestyle',   399.00,  200),
('Backpack',              'Lifestyle',   1899.00, 70),
('Monitor Stand',         'Furniture',   1199.00, 0);

INSERT INTO orders (customer_id, order_date, status) VALUES
(1, '2024-11-02', 'completed'),
(2, '2024-11-05', 'completed'),
(1, '2024-11-20', 'completed'),
(3, '2024-12-01', 'completed'),
(4, '2024-12-03', 'cancelled'),
(5, '2024-12-10', 'completed'),
(6, '2025-01-05', 'completed'),
(7, '2025-01-15', 'completed'),
(2, '2025-01-18', 'pending'),
(8, '2025-02-02', 'completed'),
(9, '2025-02-11', 'completed'),
(1, '2025-02-20', 'completed'),
(10, '2025-03-01', 'completed'),
(3, '2025-03-10', 'completed'),
(6, '2025-03-15', 'completed');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 799.00),
(1, 3, 1, 1599.00),
(2, 2, 1, 3499.00),
(3, 6, 5, 249.00),
(3, 7, 2, 599.00),
(4, 4, 1, 8999.00),
(5, 9, 1, 2199.00),
(6, 10, 3, 399.00),
(7, 5, 1, 14999.00),
(8, 1, 1, 799.00),
(8, 11, 1, 1899.00),
(9, 3, 2, 1599.00),
(10, 8, 1, 1299.00),
(11, 6, 10, 249.00),
(12, 2, 1, 3499.00),
(12, 9, 1, 2199.00),
(13, 7, 3, 599.00),
(14, 1, 4, 799.00),
(15, 4, 1, 8999.00),
(15, 5, 1, 14999.00);

-- ---------- Quick sanity checks ----------
-- SELECT * FROM customers;
-- SELECT * FROM products;
-- SELECT * FROM orders;
-- SELECT * FROM order_items;
