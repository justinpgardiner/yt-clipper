import sqlite3

class SQLiteQueue:
    def __init__(self, db_name='queue.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def enqueue(self, item):
        self.cursor.execute('INSERT INTO queue (data) VALUES (?)', (item,))
        self.conn.commit()

    def dequeue(self):
        self.cursor.execute('SELECT id, data FROM queue ORDER BY id LIMIT 1')
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute('DELETE FROM queue WHERE id = ?', (row[0],))
            self.conn.commit()
            return row[1]
        return None  # Queue is empty

    def peek(self):
        self.cursor.execute('SELECT data FROM queue ORDER BY id LIMIT 1')
        row = self.cursor.fetchone()
        return row[0] if row else None

    def size(self):
        self.cursor.execute('SELECT COUNT(*) FROM queue')
        return self.cursor.fetchone()[0]

    def close(self):
        self.conn.close()