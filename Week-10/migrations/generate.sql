-- Used to fill tables

DELETE FROM recommendations;
DELETE FROM users;
DELETE FROM products;

INSERT INTO users (name, email)
SELECT 
    'User ' || gs,
    'user' || gs || '@example.com'
FROM generate_series(1,20000) AS gs;


INSERT INTO products (name, price)
SELECT 
    'Product ' || gs,
    round((random() * 100)::numeric, 2)
FROM generate_series(1,20000) AS gs;


INSERT INTO recommendations (user_id, product_id)
SELECT 
    u.id,
    floor(random() * 20000)::int + 1 AS product_id
FROM users u
CROSS JOIN generate_series(1, 100);
