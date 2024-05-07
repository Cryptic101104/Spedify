import sqlite3

# Create a connection to the SQLite database
conn = sqlite3.connect('amazon_products.db')
c = conn.cursor()

# Create the 'products' table
c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                asin TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                UNIQUE(asin)
            )''')

# Create the 'price_history' table
c.execute('''CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )''')

# Commit changes and close the connection
conn.commit()
conn.close()

