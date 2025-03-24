DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY
    , name VARCHAR(255)
    , email VARCHAR(255)
    , created_at TIMESTAMP(0) NOT NULL DEFAULT now()
    , updated_at TIMESTAMP(0) NOT NULL DEFAULT now()
);