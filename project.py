import sqlite3
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('amazon_products.db')
        print("Connection to SQLite DB successful")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite DB: {e}")
    return conn

def create_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS products
                          (asin TEXT PRIMARY KEY, name TEXT, cost TEXT, image_url TEXT, timestamp TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS price_history
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, asin TEXT, price TEXT, timestamp TEXT,
                          FOREIGN KEY (asin) REFERENCES products(asin))''')
        print("Tables created successfully")
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

def insert_product(conn, product):
    try:
        cursor = conn.cursor()
        # Check if the product with the same asin already exists
        cursor.execute("SELECT COUNT(*) FROM products WHERE asin = ?", (product['asin'],))
        existing_product_count = cursor.fetchone()[0]
        
        # If the product doesn't exist, insert it
        if existing_product_count == 0:
            cursor.execute('''INSERT INTO products (asin, name, cost, image_url, timestamp) VALUES (?, ?, ?, ?, ?)''',
                    (product['asin'], product['name'], int(product['cost']), product['image_url'], product['timestamp']))
        else:
            # Get the current price of the product
            cursor.execute("SELECT cost FROM products WHERE asin = ?", (product['asin'],))
            current_price = cursor.fetchone()[0]
            
            # Check if the price has changed
            if current_price != int(product['cost']):
                # Insert the price change into the price_history table
                cursor.execute('''INSERT INTO price_history (asin, price, timestamp) VALUES (?, ?, ?)''',
                        (product['asin'], int(product['cost']), product['timestamp']))
            
            # Update the product's information including the timestamp
            cursor.execute('''UPDATE products SET name = ?, cost = ?, image_url = ?, timestamp = ? WHERE asin = ?''',
                    (product['name'], int(product['cost']), product['image_url'], product['timestamp'], product['asin']))
        
        # Commit the changes
        conn.commit()
        print("Product inserted/updated successfully")
    except sqlite3.Error as e:
        print(f"Error inserting/updating product: {e}")



def search_amazon(product_name):
    url = f"https://www.amazon.in/s?k={product_name}"
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'
    }
    base_response = requests.get(url, headers=headers)
    cookies = base_response.cookies
    product_response = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(product_response.text, 'html.parser')
    links = soup.find_all(class_="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal")
    href_links = [link.get("href") for link in links]
    filtered_links = [link for link in href_links if "/sspa/click" not in link]
    asins = []
    image_urls = [] 
    for link in filtered_links:
        start_index = link.find("/dp/") + len("/dp/")
        end_index = link.find("/ref", start_index)
        asin = link[start_index:end_index]
        asins.append(asin)
        image_url = extract_image_url(asin)
        image_urls.append(image_url)

    base_url = 'https://www.amazon.in/dp/'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'
    }

    products = []
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    for i, prod in enumerate(asins):
        product_url = base_url + prod
        product_response = requests.get(product_url, headers=headers)
        soup = BeautifulSoup(product_response.text, 'html.parser')
        price_lines = soup.find_all(class_="a-price-whole")
        head_lines = soup.find_all(class_='a-size-large product-title-word-break')

        final_price = int(price_lines[0].text.strip().replace(',', '').replace('.', '')) if price_lines else -1
        final_head = str(head_lines[0].text.strip()) if head_lines else "Title not available"

        product_url = base_url + prod
        products.append({'asin': prod, 'name': final_head, 'cost': final_price, 'image_url': image_urls[i], 'timestamp': timestamp, 'product_url': product_url})
    return products

def extract_image_url(asin):
    url = f"https://www.amazon.in/dp/{asin}"
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    image_tag = soup.find('img', {'id': 'landingImage'})  
    if image_tag:
        return image_tag.get('src')
    return None
@app.route('/price_data/<asin>')
def price_data(asin):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price, timestamp FROM price_history WHERE asin = ? ORDER BY timestamp DESC", (asin,))
        price_history = cursor.fetchall()
        conn.close()
        return jsonify(price_history)
    return jsonify([])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_name = request.form.get('product')
        if product_name:
            products = search_amazon(product_name)
            conn = create_connection()
            if conn:
                create_tables(conn)
                for product in products:
                    insert_product(conn, product)
                conn.close()
                
            return render_template('results.html', products=products)
    return render_template('search.html')

@app.route('/history')
def history():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, cost, asin FROM products ORDER BY timestamp DESC")
        history = cursor.fetchall()
        conn.close()
        return render_template('history.html', history=history)
    return render_template('history.html', history=[])

@app.route('/price_history/<asin>')
def price_history(asin):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price, timestamp FROM price_history WHERE asin = ? ORDER BY timestamp DESC", (asin,))
        price_history = cursor.fetchall()
        conn.close()
        
        # Extracting data for plotting
        prices = [row[0] for row in price_history]
        timestamps = [row[1] for row in price_history]

        # Create the plot
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, prices, marker='o', linestyle='-')
        plt.title('Price History')
        plt.xlabel('Timestamp')
        plt.ylabel('Price')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot to a bytes object
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png')
        img_bytes.seek(0)
        
        # Encode the bytes object as base64
        img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        
        # Generate HTML with the image
        graph_html = f'<img src="data:image/png;base64,{img_base64}" alt="Price History Graph">'
        
        return render_template('price_history.html', asin=asin, price_history=price_history, graph_html=graph_html)
    return render_template('price_history.html', asin=asin, price_history=[], graph_html='')
if __name__ == '__main__':
    app.run(debug=True)
