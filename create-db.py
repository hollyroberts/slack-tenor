import os
import sqlite3

if os.path.exists("database.db"):
    os.remove("database.db")
    print("Destroyed previous DB")
db = sqlite3.connect("database.db")

# Create tables
db.execute("""
CREATE TABLE scraped_at (
    id              INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT        NOT NULL,
    user_id         TEXT        NOT NULL,
    conversation_id TEXT        NOT NULL,
    search_string   TEXT        NOT NULL,
    ephemeral_msg   TEXT        NOT NULL
)
""")

db.commit()
db.close()

print("Database created")
