# FILE: src/server.py

import sqlite3
import os
from flask import Flask, jsonify, request
import threading

# --- Global Configuration (will be set by main.py) ---
DB_FILE = None
DATA_DIR = None

app = Flask(__name__)

# Define valid tables... (KEEP VALID_TABLES DICTIONARY HERE)
VALID_TABLES = {
    'CHIPINSPECTION': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'PASS_FAIL'],
    'INLINEINSPECTIONBOTTOM': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'Antenna', 'Capacitor', 'Speaker', 'Result', 'ManualAntenna', 'ManualCapacitor', 'ManualSpeaker', 'ManualResult'],
    'INLINEINSPECTIONTOP': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'Screw', 'Plate', 'Result', 'ManualScrew', 'ManualPlate', 'ManualResult'],
    'EOLTINSPECTION': ['Barcode', 'DT', 'Process_id', 'Station_ID', 'Upper', 'Lower', 'Left', 'Right', 'Result', 'Printtext', 'Barcodetext', 'ManualUpper', 'ManualLower', 'ManualLeft', 'ManualRight', 'ManualResult'],
}

def configure_database(db_path):
    """Configure the database path. Must be called before starting the server."""
    global DB_FILE, DATA_DIR
    DB_FILE = db_path
    DATA_DIR = os.path.dirname(db_path)
    print(f"DB_FILE configured: {DB_FILE}")

# --- Database Helper Functions (Keep these the same) ---

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


# --- Dynamic CRUD Handlers ---

def dynamic_get(table_name):
    """
    GET: Retrieve the latest record(s) by DT.
    If 'barcode' is provided, return ONLY the latest record for that barcode.
    If 'all_latest' parameter is provided, return the latest record for each unique barcode.
    Otherwise, return the single latest record from the entire table.
    """
    barcode = request.args.get('barcode')
    all_latest = request.args.get('all_latest', 'false').lower() == 'true'
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed."}), 500

    cursor = conn.cursor()
    
    if barcode:
        # Latest record for specific barcode
        query = f"SELECT * FROM {table_name} WHERE Barcode = ? ORDER BY DT DESC LIMIT 1"
        cursor.execute(query, (barcode,))
    elif all_latest:
        # Latest record for each unique barcode (using window function)
        query = f"""
        SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY Barcode ORDER BY DT DESC) as rn
            FROM {table_name}
        ) WHERE rn = 1 ORDER BY DT DESC
        """
        cursor.execute(query)
    else:
        # Single latest record from entire table
        query = f"SELECT * FROM {table_name} ORDER BY DT DESC LIMIT 1" 
        cursor.execute(query)
    
    rows = cursor.fetchall()
    conn.close()
    
    data = [dict(row) for row in rows]
    
    if barcode and not data:
         return jsonify({"message": f"No record found in {table_name} for Barcode: {barcode}"}), 404
         
    return jsonify({"table": table_name, "count": len(data), "data": data, "latest_only": True})

def dynamic_post(table_name):
    """POST: Create/Insert a new record."""
    data = request.get_json()
    if not data or 'Barcode' not in data or 'DT' not in data:
        return jsonify({"error": "Missing required fields ('Barcode' or 'DT') in request body."}), 400

    all_columns = VALID_TABLES[table_name]
    
    # Prepare placeholders and values based on the table's schema
    placeholders = ', '.join(['?'] * len(all_columns))
    column_names = ', '.join(all_columns)
    
    # Map data to columns, defaulting missing values to None (for TEXT/DATETIME) or 0 (for INTEGER/BOOLEAN)
    values = []
    for col in all_columns:
        # Simple heuristic for defaulting: 0 for typically integer fields, None for others
        default_val = 0 if 'ID' in col or 'PASS' in col or 'FAIL' in col or 'RESULT' in col or 'MANUAL' in col or col in ['Upper', 'Lower', 'Left', 'Right', 'Screw', 'Plate', 'Antenna', 'Capacitor', 'Speaker'] else None
        
        # Use provided value or default value
        values.append(data.get(col, default_val))

    query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
    
    rows_affected, status = execute_db_command(query, values)
    
    if rows_affected > 0:
        return jsonify({"message": f"Record created successfully in {table_name}.", "barcode": data['Barcode']}), 201
    else:
        return jsonify({"error": f"Failed to insert record: {status}"}), 500

def dynamic_put(table_name):
    """PUT: Update an existing record, requires Barcode in payload."""
    data = request.get_json()
    barcode = data.get('Barcode')
    
    if not barcode:
        return jsonify({"error": "Missing 'Barcode' for update operation."}), 400
        
    set_clauses = []
    update_values = []
    
    # Use the table's columns, excluding Barcode
    update_fields = [c for c in VALID_TABLES[table_name] if c != 'Barcode']
    
    for field in update_fields:
        if field in data:
            set_clauses.append(f"{field} = ?")
            update_values.append(data[field])

    if not set_clauses:
        return jsonify({"message": "No fields provided for update."}), 200

    # Note: This updates ALL records with that barcode.
    query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE Barcode = ?"
    update_values.append(barcode)
    
    rows_affected, status = execute_db_command(query, update_values)
    
    if rows_affected > 0:
        return jsonify({"message": f"Record(s) updated successfully in {table_name}.", "barcode": barcode}), 200
    elif "no such table" in status:
        return jsonify({"error": status}), 500
    else:
        return jsonify({"message": f"No record found or updated for Barcode: {barcode} in {table_name}"}), 404

def dynamic_delete(table_name):
    """DELETE: Delete a record, requires Barcode in query parameter."""
    barcode = request.args.get('barcode')
    
    if not barcode:
        return jsonify({"error": "Missing 'barcode' query parameter for delete operation."}), 400

    query = f"DELETE FROM {table_name} WHERE Barcode = ?"
    rows_affected, status = execute_db_command(query, (barcode,))
    
    if rows_affected > 0:
        return jsonify({"message": f"Record(s) deleted successfully from {table_name}.", "barcode": barcode}), 200
    elif "no such table" in status:
        return jsonify({"error": status}), 500
    else:
        return jsonify({"message": f"No record found to delete for Barcode: {barcode} in {table_name}"}), 404


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


# --- New Function for Threading ---

def start_server(host='127.0.0.1', port=5001, debug=False, threaded=True):
    """Function to run the Flask app with configurable parameters."""
    if DB_FILE is None:
        raise ValueError("Database not configured. Call configure_database() first.")
    
    # Ensure the DB data directory exists before running
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print(f"\n🚀 Starting Flask server on http://{host}:{port}")
    print(f"   Database expected at: {DB_FILE}\n")
    
    # Set use_reloader=False to prevent issues with threading
    app.run(debug=debug, use_reloader=False, host=host, port=port, threaded=threaded)

if __name__ == '__main__':
    # Running server.py directly is still supported
    # But we need to configure the database path first
    import os.path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    db_path = os.path.join(project_root, "data", "db", "inspection_data.db")
    configure_database(db_path)
    
    if not os.path.exists(DB_FILE):
        print(DB_FILE)
        exit("Database file not found. Point DB file to data/db/inspection_data.db and run automation script first")
    start_server()
    start_server()