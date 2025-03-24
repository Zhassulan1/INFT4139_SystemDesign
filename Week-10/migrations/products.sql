DROP TABLE IF EXISTS products;

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY
    , name VARCHAR(255)
    , price NUMERIC
    , created_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , updated_at TIMESTAMP(0) NOT NULL DEFAULT now()
);