import sqlite3

class Database:
    __DATABASE_FILE = "database.db"

    def __enter__(self):
        self.connection = sqlite3.connect(Database.__DATABASE_FILE)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def __exit__(self, *exc_info):
        self.connection.__exit__(*exc_info)
        self.connection.close()

