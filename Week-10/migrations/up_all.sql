CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY
    , name VARCHAR(255)
    , price NUMERIC
    , created_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , updated_at TIMESTAMP(0) NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY
    , name VARCHAR(255)
    , email VARCHAR(255)
    , created_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , updated_at TIMESTAMP(0) NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY
    , user_id INT
    , product_id INT
    , created_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , updated_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , FOREIGN KEY (user_id) REFERENCES users(id)
    , FOREIGN KEY (product_id) REFERENCES products(id)
);


-- generate data
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
