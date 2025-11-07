# FILE: src/server.py

import sqlite3
import os
from flask import Flask, jsonify, request
import threading

# --- Configuration ---
# NOTE: BASE_DIR is now the 'src' folder. We need to go UP one level to find 'data'.
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Go up one level (from 'src') then into 'data/db'
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "db") 
DB_FILE = os.path.join(DATA_DIR, "inspection_data.db")
print("DB_FILE:", DB_FILE) 
# ... (rest of configuration, VALID_TABLES, app initialization)

app = Flask(__name__)

# Define valid tables... (KEEP VALID_TABLES DICTIONARY HERE)
VALID_TABLES = {
    'CHIPINSPECTION': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'PASS_FAIL'],
    'INLINEINSPECTIONBOTTOM': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'Antenna', 'Capacitor', 'Speaker', 'Result', 'ManualAntenna', 'ManualCapacitor', 'ManualSpeaker', 'ManualResult'],
    'INLINEINSPECTIONTOP': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'Screw', 'Plate', 'Result', 'ManualScrew', 'ManualPlate', 'ManualResult'],
    'EOLTINSPECTION': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'Upper', 'Lower', 'Left', 'Right', 'Result', 'Printtext', 'Barcodetext', 'ManualUpper', 'ManualLower', 'ManualLeft', 'ManualRight', 'ManualResult'],
}

# --- Database Helper Functions (Keep these the same) ---
# ... (get_db_connection and execute_db_command functions remain the same)
# ... (dynamic_handler, dynamic_get, dynamic_post, dynamic_put, dynamic_delete functions remain the same)

def get_db_connection():
    """Connects to the SQLite database."""
    # ... (function body remains the same)
    if not os.path.exists(DB_FILE):
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        return None

def execute_db_command(query, params=()):
    # ... (function body remains the same)
    conn = get_db_connection()
    if conn is None:
        return 0, "Database connection failed."
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected, "Success"
    except sqlite3.Error as e:
        conn.close()
        return 0, str(e)


@app.route('/api/<string:table_name>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def dynamic_handler(table_name):
    # ... (function body remains the same)
    # 1. Validate Table Name
    table = table_name.upper()
    if table not in VALID_TABLES:
        return jsonify({"error": f"Invalid table name: {table_name}. Valid tables are: {', '.join(VALID_TABLES.keys())}"}), 400

    # 2. Handle HTTP Methods
    if not os.path.exists(DB_FILE):
        # print(DB_FILE) # Remove this print in production
        return jsonify({"error": "Database file not found. Run automation script first."}), 500

    if request.method == 'GET':
        return dynamic_get(table)
    elif request.method == 'POST':
        return dynamic_post(table)
    elif request.method == 'PUT':
        return dynamic_put(table)
    elif request.method == 'DELETE':
        return dynamic_delete(table)
    
    return jsonify({"error": "Method not allowed."}), 405

# ... (dynamic_get, dynamic_post, dynamic_put, dynamic_delete functions remain the same)

# --- New Function for Threading ---

def start_server():
    """Function to run the Flask app."""
    # Ensure the DB data directory exists before running
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print(f"\n🚀 Starting Flask server on http://127.0.0.1:5000")
    print(f"   Database expected at: {DB_FILE}\n")
    # Set use_reloader=False to prevent issues with threading
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=5000)

if __name__ == '__main__':
    # Running server.py directly is still supported
    if not os.path.exists(DB_FILE):
        print(DB_FILE)
        exit("Database file not found. Point DB file to data/db/inspection_data.db and run automation script first")
    start_server()