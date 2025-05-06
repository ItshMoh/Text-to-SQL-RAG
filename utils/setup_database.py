import sqlite3
import os
from datetime import datetime, timedelta
import json

# Get database path from config (or define directly for setup script)
DATABASE_PATH = "../data/mydatabase.db"
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

def create_database():
    """Creates the SQLite database and tables."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Create customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL
            )
        ''')

        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        ''')
        conn.commit()
        print("Database and tables created successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def insert_dummy_data():
    """Inserts dummy data into the tables."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Insert customers
        customers_data = [
            (1, 'Alice Smith', 'CA'),
            (2, 'Bob Johnson', 'NY'),
            (3, 'Charlie Brown', 'TX'),
            (4, 'David Davis', 'CA'),
            (5, 'Eve Williams', 'NY')
        ]
        cursor.executemany('INSERT OR IGNORE INTO customers (customer_id, name, state) VALUES (?, ?, ?)', customers_data)

        # Insert orders (last 6 months)
        orders_data = []
        today = datetime.now()
        for i in range(20): # 20 dummy orders
            customer_id = (i % 5) + 1
            days_ago = i * 7 # spread orders over time
            order_date = today - timedelta(days=days_ago)
            amount = round(10.0 + i * 5.5 + customer_id * 2.0, 2) # Vary amount
            orders_data.append((customer_id, order_date.strftime('%Y-%m-%d'), amount))

        # Using INSERT OR IGNORE in case the script is run multiple times
        cursor.executemany('INSERT INTO orders (customer_id, order_date, amount) VALUES (?, ?, ?)', orders_data)

        conn.commit()
        print("Dummy data inserted successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
    insert_dummy_data()