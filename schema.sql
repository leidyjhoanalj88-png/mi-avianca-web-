CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    telegram_username VARCHAR(255),
    date_registered DATETIME
);

CREATE TABLE IF NOT EXISTS admins (
    user_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS user_keys (
    key_id INT AUTO_INCREMENT PRIMARY KEY,
    key_value VARCHAR(255) UNIQUE NOT NULL,
    user_id BIGINT,
    expiration_date DATETIME,
    redeemed BOOLEAN DEFAULT FALSE
);

INSERT IGNORE INTO admins (user_id) VALUES (8575033873);
INSERT IGNORE INTO admins (user_id) VALUES (8114050673);