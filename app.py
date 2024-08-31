import os
import uuid
import pandas as pd
import time
import threading
from flask import Flask, request, jsonify
from PIL import Image
import requests
from io import BytesIO
import sqlite3
import csv

app = Flask(__name__)

# SQLite database setup
DATABASE = 'image_processing.db'
conn = sqlite3.connect(DATABASE, check_same_thread=False)  # Only use this in the main thread
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        serial_number VARCHAR(255) UNIQUE,
                        product_name VARCHAR(255),
                        input_image_urls TEXT,
                        output_image_urls TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id VARCHAR(36) UNIQUE,
                        status VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        product_id INTEGER,
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )''')
    conn.commit()

init_db()

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

IMAGE_FOLDER = 'images'
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

OUTPUT_FOLDER = 'output'
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Shared list to accumulate all processed results
processed_results = []

def compress_image(input_url, output_path, quality=50):
    response = requests.get(input_url)
    img = Image.open(BytesIO(response.content))

    if img.mode != 'RGB':
        img = img.convert('RGB')

    img.save(output_path, "JPEG", quality=quality)

def process_images(request_id, serial_number, product_name, input_image_urls):
    global processed_results  # Reference the shared list

    # Create a new connection and cursor for this thread
    local_conn = sqlite3.connect(DATABASE)
    local_cursor = local_conn.cursor()

    image_urls = input_image_urls.split(',')
    processed_images = []

    for url in image_urls:
        output_image_path = os.path.join(IMAGE_FOLDER, f"{uuid.uuid4()}.jpg")
        compress_image(url, output_image_path)
        time.sleep(1)  # Simulate processing time
        processed_images.append(output_image_path)

    output_image_urls = ','.join(processed_images)

    # Update the products table with the output image URLs
    local_cursor.execute('UPDATE products SET output_image_urls=? WHERE serial_number=?', (output_image_urls, serial_number))
    local_cursor.execute('UPDATE requests SET status="completed", updated_at=CURRENT_TIMESTAMP WHERE request_id=?', (request_id,))
    local_conn.commit()

    # Append the processed data to the shared list
    processed_results.append({
        'Serial Number': serial_number,
        'Product Name': product_name,
        'Input Image Urls': input_image_urls,
        'Output Image Urls': output_image_urls
    })

    # Close the local connection
    local_conn.close()

    # If all threads are done, save the output CSV
    if len(processed_results) == total_records:
        output_csv_path = os.path.join(OUTPUT_FOLDER, f'{request_id}_output.csv')
        with open(output_csv_path, 'w', newline='') as csvfile:
            fieldnames = ['Serial Number', 'Product Name', 'Input Image Urls', 'Output Image Urls']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(processed_results)  # Write all rows at once

        print(f"Output CSV saved at {output_csv_path}")


@app.route('/upload', methods=['POST'])
def upload_csv():
    global total_records  # Reference the total record count

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        df = pd.read_csv(file_path)
        if 'Serial Number' not in df.columns or 'Product Name' not in df.columns or 'Input Image Urls' not in df.columns:
            return jsonify({"error": "Invalid CSV format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    total_records = len(df)  # Track the number of records

    for _, row in df.iterrows():
        try:
            # Generate a unique request_id for each product
            request_id = str(uuid.uuid4())

            cursor.execute('INSERT INTO products (serial_number, product_name, input_image_urls) VALUES (?, ?, ?)',
                        (row['Serial Number'], row['Product Name'], row['Input Image Urls']))
            product_id = cursor.lastrowid

            cursor.execute('INSERT INTO requests (request_id, status, product_id) VALUES (?, "processing", ?)', 
                        (request_id, product_id))
            conn.commit()

            # Start a new thread for each request_id to process images in the background
            thread = threading.Thread(target=process_images, args=(request_id, row['Serial Number'], row['Product Name'], row['Input Image Urls']))
            thread.start()

        except sqlite3.IntegrityError as e:
            return jsonify({"error": f"Integrity error: {e}"}), 400

        
    return jsonify({"request id": (request_id)}), 200

@app.route('/status/<request_id>', methods=['GET'])
def check_status(request_id):
    cursor.execute('SELECT status FROM requests WHERE request_id=?', (request_id,))
    status = cursor.fetchone()

    if status:
        if status[0] == "completed":
            return jsonify({"status": "completed"}), 200
        else:
            return jsonify({"status": "processing"}), 200
    else:
        return jsonify({"error": "Request ID not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
