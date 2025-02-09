-- DROP TABLE IF EXISTS tokens;

-- CREATE TABLE IF NOT EXISTS tokens
-- (
--     user_id     BIGINT                      NOT NULL PRIMARY KEY
--     ,token      TEXT                        NOT NULL
--     ,expiry     TIMESTAMP WITH TIME ZONE    NOT NULL
-- );

-- CREATE INDEX token_hash ON tokens USING HASH (user_id); 

-- INSERT INTO tokens (token, user_id, expiry) VALUES ('12kjsfhk3456789SD,GFHJKBXVJH0', 1234567890, 1234567890);


DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY
    ,name TEXT
    ,password TEXT
    ,scopes TEXT
    ,created_at TIMESTAMP DEFAULT NOW()
);