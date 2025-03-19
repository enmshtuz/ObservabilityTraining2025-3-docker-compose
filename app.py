import os
import time
import json
import signal
import psycopg2
from http.server import BaseHTTPRequestHandler, HTTPServer

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB", "testdb")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

def is_ready():
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return True
    except Exception:
        return False

def connect_db():
    global conn
    while True:
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            if is_ready():
                print("Database connection established")
                return conn
            else:
                print("Database connection established but not ready")
        except Exception as e:
            print(f"Waiting for DB connection: {e}")
            time.sleep(2)

conn = connect_db()
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL
    );
""")
conn.commit()

class CRUDHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        # Liveness probe
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Healthy")
            return

        # Readiness probe
        if self.path == "/ready":
            if is_ready():
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Ready")
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"Not Ready")
            return

        # Get all items
        if self.path == "/get-all":
            cursor.execute("SELECT * FROM items;")
            rows = cursor.fetchall()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(rows).encode())
            return

        # Get a specific item by ID
        if self.path.startswith("/get/"):
            try:
                item_id = int(self.path.split("/")[-1])
                cursor.execute("SELECT * FROM items WHERE id = %s;", (item_id,))
                row = cursor.fetchone()
                if row:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(row).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Item not found")
            except ValueError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid ID")
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        # Create a new item
        if self.path.startswith("/add/"):
            name = self.path.split("/")[-1]
            cursor.execute("INSERT INTO items (name) VALUES (%s) RETURNING id;", (name,))
            new_id = cursor.fetchone()[0]
            conn.commit()
            self.send_response(201)
            self.end_headers()
            self.wfile.write(f"Added: {name} with ID {new_id}".encode())
            return

        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        # Update an item by ID
        if self.path.startswith("/update/"):
            try:
                item_id = int(self.path.split("/")[-1])
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                new_name = post_data.decode()

                cursor.execute("UPDATE items SET name = %s WHERE id = %s;", (new_name, item_id))
                if cursor.rowcount == 0:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Item not found")
                else:
                    conn.commit()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(f"Updated ID {item_id} to {new_name}".encode())
            except ValueError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid ID")
            return

        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        # Delete an item by ID
        if self.path.startswith("/delete/"):
            try:
                item_id = int(self.path.split("/")[-1])
                cursor.execute("DELETE FROM items WHERE id = %s;", (item_id,))
                if cursor.rowcount == 0:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Item not found")
                else:
                    conn.commit()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(f"Deleted ID {item_id}".encode())
            except ValueError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid ID")
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, CRUDHandler)
    print("Starting server on port 8080...")

    # Graceful shutdown handling
    def shutdown_server(signum, frame):
        print("\nReceived shutdown signal, stopping server...")
        httpd.shutdown()
        print("Server stopped gracefully")

    # Register signals for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)

    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
