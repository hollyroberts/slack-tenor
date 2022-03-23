import os
import sqlite3

if os.path.exists("database.db"):
    os.remove("database.db")
    print("Destroyed previous DB")
db = sqlite3.connect("database.db")

# Create tables
# language=SQL
db.execute("""
CREATE TABLE slack_request (
    id              INTEGER     NOT NULL CONSTRAINT pk_slack_request PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT        NOT NULL,
    user_id         TEXT        NOT NULL,
    conversation_id TEXT        NOT NULL,
    block_uid       TEXT        NOT NULL,
    search_string   TEXT        NOT NULL,
    status          TEXT        NOT NULL,
    
    CONSTRAINT uk_slack_request_block_uid UNIQUE (block_uid),
    CONSTRAINT ck_slack_request_status CHECK (status IN ('SELECTING', 'CANCELLED', 'POSTED'))
)
""")

# language=SQL
db.execute("""
CREATE TABLE tenor_result (
    id                  INTEGER     NOT NULL CONSTRAINT pk_tenor_result PRIMARY KEY AUTOINCREMENT,
    slack_request_id    INTEGER     NOT NULL,
    position            INTEGER     NOT NULL,
    gif_object          TEXT        NOT NULL,
    status              TEXT        NOT NULL,
    next_pos            TEXT        NULL,
    
    CONSTRAINT uk_tenor_result_slack_request_order UNIQUE (slack_request_id, position),      
    CONSTRAINT fk_tenor_result_slack_request FOREIGN KEY (slack_request_id) REFERENCES slack_request (id),
    CONSTRAINT ck_tenor_result_status CHECK (status IN ('FETCHED', 'SELECTING', 'USED'))
)
""")

db.commit()
db.close()

print("Database created")
