DROP TABLE IF EXISTS recommendations;

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY
    , user_id INT
    , product_id INT
    , created_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , updated_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , FOREIGN KEY (user_id) REFERENCES users(id)
    , FOREIGN KEY (product_id) REFERENCES products(id)
);