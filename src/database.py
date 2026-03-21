"""
Database module for CloudMart product catalog.

THIS FILE IS FULLY IMPLEMENTED. DO NOT MODIFY.

Provides a SQLite backed product database with simulated network latency
to demonstrate the benefits of caching. In a real cloud deployment,
database queries travel over a network and take tens of milliseconds.
The simulated delay here makes caching improvements clearly visible.
"""

import sqlite3
import time
import threading
from typing import List, Optional, Dict, Any

DB_LATENCY_MS = 50


class Database:
    """SQLite backed product database with simulated network latency."""

    def __init__(self, db_path: str = "cloudmart.db", latency_ms: int = DB_LATENCY_MS):
        self.db_path = db_path
        self.latency_ms = latency_ms
        self._local = threading.local()
        self._init_db()

    def _get_connection(self):
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _simulate_latency(self):
        """Simulate network latency to a remote database server."""
        time.sleep(self.latency_ms / 1000.0)

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                stock INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]

        if count == 0:
            self._seed_data(cursor)

        conn.commit()
        conn.close()

    def _seed_data(self, cursor):
        """Populate database with sample CloudMart products."""
        products = [
            ("Laptop Pro 15", "Electronics", 1299.99,
             "High performance laptop with 16GB RAM and 512GB SSD", 45, 4.5),
            ("Wireless Mouse", "Electronics", 29.99,
             "Ergonomic wireless mouse with USB receiver", 200, 4.2),
            ("USB C Hub", "Electronics", 49.99,
             "7 in 1 USB C adapter with HDMI and ethernet", 150, 4.0),
            ("Mechanical Keyboard", "Electronics", 89.99,
             "RGB mechanical keyboard with Cherry MX switches", 80, 4.7),
            ("Monitor 27 inch", "Electronics", 399.99,
             "4K IPS display with adjustable stand", 30, 4.6),
            ("Webcam HD", "Electronics", 69.99,
             "1080p webcam with built in microphone", 100, 3.9),
            ("Headphones Pro", "Electronics", 199.99,
             "Active noise cancelling over ear headphones", 65, 4.7),
            ("Tablet 10 inch", "Electronics", 329.99,
             "10 inch tablet with stylus support", 50, 4.3),
            ("Smart Watch", "Electronics", 249.99,
             "Fitness tracking smartwatch with GPS", 75, 4.4),
            ("External SSD 1TB", "Electronics", 109.99,
             "Portable solid state drive USB 3.2", 110, 4.5),
            ("Python Programming", "Books", 45.99,
             "Complete guide to Python programming", 500, 4.8),
            ("Cloud Computing", "Books", 59.99,
             "Cloud architecture patterns and best practices", 300, 4.5),
            ("Data Structures", "Books", 39.99,
             "Algorithms and data structures in depth", 400, 4.3),
            ("Machine Learning Basics", "Books", 54.99,
             "Introduction to ML with Python examples", 250, 4.6),
            ("Networking Fundamentals", "Books", 49.99,
             "Computer networking from the ground up", 200, 4.2),
            ("Design Patterns", "Books", 44.99,
             "Software design patterns explained clearly", 350, 4.7),
            ("Operating Systems", "Books", 55.99,
             "OS concepts and principles textbook", 180, 4.1),
            ("Database Systems", "Books", 62.99,
             "Relational database design and SQL", 160, 4.4),
            ("Office Chair Ergo", "Furniture", 249.99,
             "Ergonomic office chair with lumbar support", 60, 4.1),
            ("Standing Desk", "Furniture", 499.99,
             "Electric height adjustable standing desk", 25, 4.4),
            ("Desk Lamp LED", "Furniture", 34.99,
             "LED desk lamp with brightness dimmer", 180, 4.0),
            ("Bookshelf 5 Tier", "Furniture", 129.99,
             "5 tier wooden bookshelf oak finish", 40, 3.8),
            ("Filing Cabinet", "Furniture", 89.99,
             "3 drawer metal filing cabinet", 55, 3.7),
            ("Coffee Maker", "Kitchen", 79.99,
             "Programmable 12 cup drip coffee maker", 90, 4.2),
            ("Blender Pro", "Kitchen", 59.99,
             "High speed blender with 6 blades", 70, 4.0),
            ("Toaster Oven", "Kitchen", 89.99,
             "Convection toaster oven 6 slice capacity", 55, 4.3),
            ("Water Bottle Insulated", "Kitchen", 24.99,
             "Insulated stainless steel water bottle 32oz", 300, 4.5),
            ("Running Shoes", "Sports", 119.99,
             "Lightweight breathable running shoes", 120, 4.4),
            ("Yoga Mat", "Sports", 29.99,
             "Non slip exercise yoga mat 6mm thick", 200, 4.1),
            ("Resistance Bands Set", "Sports", 19.99,
             "Set of 5 resistance bands with handles", 250, 4.2),
        ]

        cursor.executemany(
            "INSERT INTO products (name, category, price, description, stock, rating) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )

    # ---- Product Queries ----

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Return all products sorted by id."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Return a single product by id, or None if not found."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search products by name or description, ordered by rating."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE name LIKE ? OR description LIKE ? "
            "ORDER BY rating DESC",
            (f"%{query}%", f"%{query}%"),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Return all products in a given category, ordered by rating."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY rating DESC",
            (category,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_products_by_price_range(
        self, min_price: float, max_price: float
    ) -> List[Dict[str, Any]]:
        """Return products within a price range, ordered by price."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE price BETWEEN ? AND ? ORDER BY price ASC",
            (min_price, max_price),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_top_rated(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the top rated products."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products ORDER BY rating DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_categories(self) -> List[str]:
        """Return a sorted list of distinct product categories."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        return [row[0] for row in cursor.fetchall()]

    def get_product_count(self) -> int:
        """Return the total number of products."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        return cursor.fetchone()[0]

    # ---- Order Operations ----

    def create_order(
        self, product_id: int, quantity: int, customer_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create an order if the product exists and has sufficient stock.
        Returns the order dict on success, or None on failure.
        """
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            return None
        if dict(product)["stock"] < quantity:
            return None

        cursor.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (quantity, product_id),
        )
        cursor.execute(
            "INSERT INTO orders (product_id, quantity, customer_name) VALUES (?, ?, ?)",
            (product_id, quantity, customer_name),
        )
        conn.commit()

        order_id = cursor.lastrowid
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Return an order by id, or None if not found."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_order_status(
        self, order_id: int, status: str
    ) -> Optional[Dict[str, Any]]:
        """Update the status of an order. Returns the updated order or None."""
        self._simulate_latency()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
