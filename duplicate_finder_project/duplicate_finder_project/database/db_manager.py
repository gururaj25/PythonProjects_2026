import sqlite3

DB_NAME = "duplicate_finder.db"

class DatabaseManager:

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            file_hash TEXT,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        )

        self.conn.commit()

    def insert_scan(self, file_path, file_hash):
        cursor = self.conn.cursor()

        cursor.execute(
        '''
        INSERT INTO scans(file_path, file_hash)
        VALUES(?, ?)
        ''',
        (file_path, file_hash)
        )

        self.conn.commit()