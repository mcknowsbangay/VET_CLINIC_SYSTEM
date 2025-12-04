import os
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

from PIL import Image, ImageTk
import webbrowser
import json
import csv
from datetime import datetime, timedelta

# ==================== COLOR THEME ==================== 
COLORS = {
    "primary": "#2E86AB",      # Vibrant blue
    "secondary": "#A23B72",    # Purple
    "accent": "#F18F01",       # Orange
    "success": "#4CAF50",      # Green
    "warning": "#FF9800",      # Amber
    "danger": "#F44336",       # Red
    "dark": "#2C3E50",         # Dark blue-gray
    "light": "#ECF0F1",        # Light gray
    "background": "#34495E",   # Dark background
    "card": "#2C3E50",         # Card background
    "text_light": "#FFFFFF",   # White text
    "text_dark": "#2C3E50"     # Dark text
}

class Medicine:
    """Represents a medicine or supply in the inventory"""

    def __init__(self, id=None, name="", price=0.0, stock=0, category="", brand="",
                 animal_type="", dosage="", expiration_date=""):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category
        self.brand = brand
        self.animal_type = animal_type
        self.dosage = dosage
        self.expiration_date = expiration_date

    def to_dict(self):
        """Convert medicine to dictionary for database operations"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'brand': self.brand,
            'animal_type': self.animal_type,
            'dosage': self.dosage,
            'expiration_date': self.expiration_date
        }

    @classmethod
    def from_dict(cls, data):
        """Create Medicine instance from dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            price=data.get('price', 0.0),
            stock=data.get('stock', 0),
            category=data.get('category', ''),
            brand=data.get('brand', ''),
            animal_type=data.get('animal_type', ''),
            dosage=data.get('dosage', ''),
            expiration_date=data.get('expiration_date', '')
        )


class CartItem:
    """Represents an item in the shopping cart (for medicines/supplies/foods)"""

    def __init__(self, item_id, name, price, quantity=1, category=""):
        self.item_id = item_id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.category = category

    @property
    def subtotal(self):
        return self.price * self.quantity

    def to_dict(self):
        return {
            'id': self.item_id,
            'name': self.name,
            'price': self.price,
            'qty': self.quantity,
            'subtotal': self.subtotal,
            'category': self.category
        }


class Appointment:
    """Represents a veterinary appointment"""

    def __init__(self, appointment_id="", patient_name="", owner_name="", animal_type="", 
                 service="", notes="", status="SCHEDULED"):
        self.appointment_id = appointment_id
        self.patient_name = patient_name
        self.owner_name = owner_name
        self.animal_type = animal_type
        self.service = service
        self.notes = notes
        self.status = status
        self.date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.services = []
        self.total_amount = 0.0

    def add_service(self, service_name, quantity, price, subtotal):
        """Add service to appointment with proper pricing"""
        self.services.append({
            'service': service_name,
            'qty': quantity,
            'price': price,
            'subtotal': subtotal
        })
        self.total_amount += subtotal

    def to_dict(self):
        """Convert appointment to dictionary for database operations"""
        return {
            'appointment_id': self.appointment_id,
            'patient_name': self.patient_name,
            'owner_name': self.owner_name,
            'animal_type': self.animal_type,
            'service': self.service,
            'notes': self.notes,
            'status': self.status,
            'date': self.date,
            'total_amount': self.total_amount,
            'services': self.services
        }


class User:
    """Represents a system user (vet or staff)"""

    def __init__(self, id=None, username="", password="", role="staff"):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

    def authenticate(self, input_username, input_password):
        """Authenticate user credentials"""
        return self.username == input_username and self.password == input_password


class InventoryManager:
    """Manages inventory operations for medicines and foods"""

    def __init__(self, db_connection):
        self.db = db_connection

    def get_all_items(self):
        """Get all items from inventory (medicines and foods)"""
        try:
            cur = self.db.cursor()
            cur.execute("SELECT * FROM inventory ORDER BY category, name")
            rows = cur.fetchall()
            items = []
            for row in rows:
                item = Medicine(
                    id=row[0],
                    name=row[1],
                    price=row[2],
                    stock=row[3],
                    category=row[4],
                    brand=row[6] if len(row) > 6 else "",
                    animal_type=row[7] if len(row) > 7 else "",
                    dosage=row[8] if len(row) > 8 else "",
                    expiration_date=row[9] if len(row) > 9 else ""
                )
                items.append(item)
            return items
        except sqlite3.Error as e:
            print(f"Error getting items: {e}")
            return []

    def search_items(self, search_term):
        """Search items by name"""
        try:
            cur = self.db.cursor()
            cur.execute("SELECT * FROM inventory WHERE name LIKE ? OR category LIKE ? ORDER BY category, name",
                        (f"%{search_term}%", f"%{search_term}%"))
            rows = cur.fetchall()
            items = []
            for row in rows:
                item = Medicine(
                    id=row[0],
                    name=row[1],
                    price=row[2],
                    stock=row[3],
                    category=row[4],
                    brand=row[6] if len(row) > 6 else "",
                    animal_type=row[7] if len(row) > 7 else "",
                    dosage=row[8] if len(row) > 8 else "",
                    expiration_date=row[9] if len(row) > 9 else ""
                )
                items.append(item)
            return items
        except sqlite3.Error as e:
            print(f"Error searching items: {e}")
            return []

    def update_item_stock(self, item_id, quantity_used):
        """Update item stock after use"""
        try:
            cur = self.db.cursor()
            cur.execute("UPDATE inventory SET stock = stock - ? WHERE id = ?",
                        (quantity_used, item_id))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating stock: {e}")
            return False

    def add_item(self, medicine):
        """Add new item to inventory"""
        try:
            cur = self.db.cursor()
            cur.execute("""INSERT INTO inventory 
                        (name, price, stock, category, brand, animal_type, dosage, expiration_date) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (medicine.name, medicine.price, medicine.stock, medicine.category,
                         medicine.brand, medicine.animal_type, medicine.dosage, medicine.expiration_date))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding item: {e}")
            return False

    def update_item(self, medicine):
        """Update existing item in inventory"""
        try:
            cur = self.db.cursor()
            cur.execute("""UPDATE inventory SET 
                        name=?, price=?, stock=?, category=?, brand=?, animal_type=?, dosage=?, expiration_date=?
                        WHERE id=?""",
                        (medicine.name, medicine.price, medicine.stock, medicine.category,
                         medicine.brand, medicine.animal_type, medicine.dosage, medicine.expiration_date, medicine.id))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating item: {e}")
            return False

    def delete_item(self, item_id):
        """Delete item from inventory"""
        try:
            cur = self.db.cursor()
            cur.execute("DELETE FROM inventory WHERE id=?", (item_id,))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting item: {e}")
            return False


class AppointmentManager:
    """Manages appointment operations"""

    def __init__(self, db_connection):
        self.db = db_connection

    def record_appointment(self, appointment):
        """Record an appointment in the database - FIXED VERSION"""
        try:
            cur = self.db.cursor()
            
            # Check if appointments table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
            table_exists = cur.fetchone()
            
            if not table_exists:
                # Create the appointments table with correct structure
                cur.execute("""
                    CREATE TABLE appointments(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        appointment_id TEXT,
                        patient_name TEXT,
                        owner_name TEXT,
                        animal_type TEXT,
                        service TEXT,
                        qty INTEGER,
                        price REAL,
                        subtotal REAL,
                        date TEXT,
                        notes TEXT,
                        status TEXT,
                        total_amount REAL
                    )
                """)
                print("Created appointments table")
            
            # Record the appointment with services
            for service in appointment.services:
                cur.execute("""INSERT INTO appointments 
                            (appointment_id, patient_name, owner_name, animal_type, service, 
                             qty, price, subtotal, date, notes, status, total_amount) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (appointment.appointment_id, appointment.patient_name, appointment.owner_name,
                             appointment.animal_type, service['service'], service['qty'], service['price'],
                             service['subtotal'], appointment.date, appointment.notes, 
                             appointment.status, appointment.total_amount))
            
            self.db.commit()
            print(f"Appointment {appointment.appointment_id} recorded successfully!")
            print(f"Total amount: {appointment.total_amount}")
            return True
        except sqlite3.Error as e:
            print(f"Error recording appointment: {e}")
            self.db.rollback()
            return False

    def get_appointments_history(self, date_filter="", appointment_filter=""):
        """Get appointments history with optional filters"""
        try:
            cur = self.db.cursor()
            query = "SELECT * FROM appointments WHERE 1=1"
            params = []

            if date_filter:
                query += " AND date LIKE ?"
                params.append(f"{date_filter}%")

            if appointment_filter:
                query += " AND appointment_id LIKE ?"
                params.append(f"%{appointment_filter}%")

            query += " ORDER BY date DESC"
            cur.execute(query, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting appointments history: {e}")
            return []

    def get_all_appointments(self):
        """Get all unique appointments - FIXED VERSION"""
        try:
            cur = self.db.cursor()
            cur.execute("""
                SELECT DISTINCT appointment_id, patient_name, owner_name, animal_type, 
                       date, notes, status, total_amount
                FROM appointments 
                GROUP BY appointment_id 
                ORDER BY date DESC
            """)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting appointments: {e}")
            return []

    def update_appointment_status(self, appointment_id, new_status):
        """Update appointment status"""
        try:
            cur = self.db.cursor()
            cur.execute("UPDATE appointments SET status = ? WHERE appointment_id = ?", 
                       (new_status, appointment_id))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating appointment status: {e}")
            return False

    def delete_appointment(self, appointment_id):
        """Delete an appointment"""
        try:
            cur = self.db.cursor()
            cur.execute("DELETE FROM appointments WHERE appointment_id = ?", (appointment_id,))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting appointment: {e}")
            return False


class ShoppingCart:
    """Manages shopping cart operations for items"""

    def __init__(self):
        self.items = []

    def add_item(self, item_id, item_name, price, quantity=1, category=""):
        """Add item to cart"""
        for item in self.items:
            if item.item_id == item_id:
                item.quantity += quantity
                return

        new_item = CartItem(item_id, item_name, price, quantity, category)
        self.items.append(new_item)

    def remove_item(self, item_id):
        """Remove item from cart"""
        self.items = [
            item for item in self.items if item.item_id != item_id]

    def update_quantity(self, item_id, quantity):
        """Update item quantity in cart"""
        for item in self.items:
            if item.item_id == item_id:
                if quantity <= 0:
                    self.remove_item(item_id)
                else:
                    item.quantity = quantity
                return

    def clear(self):
        """Clear all items from cart"""
        self.items = []

    @property
    def total(self):
        """Calculate total cart value"""
        return sum(item.subtotal for item in self.items)

    @property
    def item_count(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items)

    def to_legacy_format(self):
        """Convert to legacy format for existing code"""
        return [item.to_dict() for item in self.items]


class ReceiptManager:
    """Manages receipt generation and printing"""
    @staticmethod
    def generate_receipt_text(appointment_id, patient_name, owner_name, animal_type, notes, date, total_amount, cart_items):
        """Generate receipt as text string"""
        receipt = "=" * 50 + "\n"
        receipt += "         VETERINARY CLINIC\n"
        receipt += "       Official Service Receipt\n"
        receipt += "   123 Main Street, City, Philippines\n"
        receipt += "          Tel: (02) 1234-5678\n"
        receipt += "=" * 50 + "\n\n"

        receipt += f"Appointment: {appointment_id}\n"
        receipt += f"Date: {date}\n"
        receipt += f"Patient: {patient_name}\n"
        receipt += f"Owner: {owner_name}\n"
        receipt += f"Animal Type: {animal_type}\n"
        if notes:
            receipt += f"Notes: {notes}\n"
        receipt += "\n" + "-" * 50 + "\n"
        receipt += "SERVICE/ITEM                       QTY   PRICE   SUBTOTAL\n"
        receipt += "-" * 50 + "\n"

        for item in cart_items:
            item_name = item['name']
            if len(item_name) > 30:
                item_name = item_name[:27] + "..."

            receipt += f"{item_name:<30} {item['qty']:>3}  ₱{item['price']:>6.2f}  ₱{item['subtotal']:>7.2f}\n"

        receipt += "-" * 50 + "\n"
        receipt += f"TOTAL: ₱{total_amount:>38.2f}\n"
        receipt += "=" * 50 + "\n\n"

        receipt += "POLICY:\n"
        receipt += "• Follow-up appointments as advised\n"
        receipt += "• Keep this receipt for records\n"
        receipt += "• Contact us for any concerns\n\n"

        receipt += "Thank you for choosing our clinic!\n"
        receipt += "We care for your pets\n"
        receipt += "=" * 50 + "\n"

        return receipt

    @staticmethod
    def save_receipt_to_file(receipt_text, filename=None):
        """Save receipt to text file"""
        if filename is None:
            filename = f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(receipt_text)
            return filename
        except Exception as e:
            print(f"Error saving receipt: {e}")
            return None

class SalesManager:
    """Manages sales and transactions"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def record_sale(self, transaction_id, items, total_amount, payment_method, customer_name=""):
        """Record a sale transaction"""
        try:
            cur = self.db.cursor()
            for item in items:
                cur.execute("""INSERT INTO sales 
                            (transaction_id, item_id, item_name, quantity, price, subtotal, 
                             total_amount, payment_method, customer_name, sale_date) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (transaction_id, item['id'], item['name'], item['qty'], 
                             item['price'], item['subtotal'], total_amount, payment_method,
                             customer_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            # Update inventory stock
            for item in items:
                cur.execute("UPDATE inventory SET stock = stock - ? WHERE id = ?",
                           (item['qty'], item['id']))
            
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error recording sale: {e}")
            return False
    
    def get_sales_report(self, start_date=None, end_date=None):
        """Get sales report for a date range"""
        try:
            cur = self.db.cursor()
            query = "SELECT * FROM sales WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND sale_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND sale_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY sale_date DESC"
            cur.execute(query, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting sales report: {e}")
            return []

# ==================== MAIN APPLICATION ====================

APP_TITLE = "Veterinary Clinic Management System"
DB_FILE = "vetclinic.db"
THEME_MODE = "dark"

# Service prices for appointments - EXPANDED AND FIXED
SERVICE_PRICES = {
    "Consultation": 500.00,
    "Vaccination": 800.00,
    "Surgery": 2500.00,
    "Grooming": 600.00,
    "Checkup": 400.00,
    "Dental Cleaning": 1200.00,
    "X-Ray": 1500.00,
    "Blood Test": 800.00,
    "Emergency Care": 2000.00,
    "Vaccine Booster": 600.00,
    "Spay/Neuter": 3000.00,
    "Microchipping": 800.00
}

def get_db():
    return sqlite3.connect(DB_FILE)

def apply_theme(window=None):
    ctk.set_appearance_mode(THEME_MODE)
    ctk.set_default_color_theme("blue")
    if window is not None:
        try:
            window.update()
        except tk.TclError:
            pass

def generate_appointment_id():
    return f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}"

def generate_transaction_id():
    return f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"

def validate_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False

def clear_test_data():
    """Clear any test appointment data that might exist"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check if there are any appointments and delete them
        cur.execute("SELECT COUNT(*) FROM appointments")
        count = cur.fetchone()[0]
        
        if count > 0:
            cur.execute("DELETE FROM appointments")
            conn.commit()
            print(f"Cleared {count} test appointments from database")
        
        conn.close()
    except sqlite3.Error as e:
        print(f"Error clearing test data: {e}")

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()

        # Users table - FIXED: Ensure role column exists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'staff'
            )
            """
        )

        # Check if role column exists, if not add it
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]
        if 'role' not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'staff'")

        # Inventory table
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'"
        )
        inv_exists = cur.fetchone()

        if not inv_exists:
            cur.execute(
                """
                CREATE TABLE inventory(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price REAL,
                    stock INTEGER,
                    category TEXT,
                    image TEXT,
                    brand TEXT,
                    animal_type TEXT,
                    dosage TEXT,
                    expiration_date TEXT
                )
                """
            )
        else:
            cur.execute("PRAGMA table_info(inventory)")
            cols = {row[1] for row in cur.fetchall()}
            extra_cols = {
                "brand": "ALTER TABLE inventory ADD COLUMN brand TEXT",
                "animal_type": "ALTER TABLE inventory ADD COLUMN animal_type TEXT",
                "dosage": "ALTER TABLE inventory ADD COLUMN dosage TEXT",
                "expiration_date": "ALTER TABLE inventory ADD COLUMN expiration_date TEXT",
            }
            for col, sql in extra_cols.items():
                if col not in cols:
                    try:
                        cur.execute(sql)
                    except sqlite3.Error:
                        pass  # Column might already exist

        # Appointments table - FIXED: Added total_amount column
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'"
        )
        apt_exists = cur.fetchone()

        if not apt_exists:
            cur.execute(
                """
                CREATE TABLE appointments(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id TEXT,
                    patient_name TEXT,
                    owner_name TEXT,
                    animal_type TEXT,
                    service TEXT,
                    qty INTEGER,
                    price REAL,
                    subtotal REAL,
                    date TEXT,
                    notes TEXT,
                    status TEXT,
                    total_amount REAL
                )
                """
            )
        else:
            # Check if total_amount column exists, if not add it
            cur.execute("PRAGMA table_info(appointments)")
            apt_columns = [column[1] for column in cur.fetchall()]
            if 'total_amount' not in apt_columns:
                cur.execute("ALTER TABLE appointments ADD COLUMN total_amount REAL")

        # Sales table
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sales'"
        )
        sales_exists = cur.fetchone()

        if not sales_exists:
            cur.execute(
                """
                CREATE TABLE sales(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    item_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER,
                    price REAL,
                    subtotal REAL,
                    total_amount REAL,
                    payment_method TEXT,
                    customer_name TEXT,
                    sale_date TEXT
                )
                """
            )

        # Insert default admin user - FIXED: Ensure proper user creation
        default_username = "admin"
        default_password = "admin123"
        
        # Check if admin user exists
        cur.execute("SELECT * FROM users WHERE username = ?", (default_username,))
        admin_exists = cur.fetchone()
        
        if not admin_exists:
            cur.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
                """,
                (default_username, default_password, "admin"),
            )

        # Insert default staff user
        staff_username = "staff"
        staff_password = "staff123"
        
        cur.execute("SELECT * FROM users WHERE username = ?", (staff_username,))
        staff_exists = cur.fetchone()
        
        if not staff_exists:
            cur.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
                """,
                (staff_username, staff_password, "staff"),
            )

        conn.commit()
        conn.close()
        
        # Clear any existing test data
        clear_test_data()
        
        print("Database initialized successfully!")

    except sqlite3.Error as e:
        print(f"Database initialization error: {str(e)}")
        messagebox.showerror(
            "Database Error", f"Database initialization failed: {str(e)}")

# ==================== COMPLETE CATALOGS ====================

DOG_MEDICINES = {
    "vaccines": {
        "rabies_vaccine": {
            "Rabies Vaccine (1 dose)": {"price": 350.00, "animal_type": "Dog", "dosage": "1ml", "expiration": "2 years"},
        },
        "dhpp_vaccine": {
            "DHPP Vaccine (1 dose)": {"price": 450.00, "animal_type": "Dog", "dosage": "1ml", "expiration": "1 year"},
        }
    },
    "medications": {
        "antibiotics": {
            "Amoxicillin 500mg (tablet)": {"price": 25.00, "animal_type": "Dog", "dosage": "1 tablet", "expiration": "2 years"},
        },
        "anti_inflammatories": {
            "Carprofen 100mg (tablet)": {"price": 35.00, "animal_type": "Dog", "dosage": "1 tablet", "expiration": "2 years"},
        }
    },
    "supplies": {
        "bandages": {
            "Sterile Bandage 5cm x 5m": {"price": 150.00, "animal_type": "All", "dosage": "N/A", "expiration": "5 years"},
        }
    }
}

CAT_MEDICINES = {
    "vaccines": {
        "fvr_vaccine": {
            "FVR Vaccine (1 dose)": {"price": 400.00, "animal_type": "Cat", "dosage": "1ml", "expiration": "1 year"},
        }
    },
    "medications": {
        "antibiotics": {
            "Clindamycin 75mg (capsule)": {"price": 30.00, "animal_type": "Cat", "dosage": "1 capsule", "expiration": "2 years"},
        }
    }
}

PET_FOODS = {
    "dog_food": {
        "dry_food": {
            "Premium Dog Dry Food 5kg": {"price": 850.00, "animal_type": "Dog", "dosage": "N/A", "expiration": "2 years"},
            "Puppy Dry Food 3kg": {"price": 650.00, "animal_type": "Dog", "dosage": "N/A", "expiration": "2 years"},
        },
        "wet_food": {
            "Dog Wet Food Cans (12 pack)": {"price": 480.00, "animal_type": "Dog", "dosage": "N/A", "expiration": "1 year"},
        }
    },
    "cat_food": {
        "dry_food": {
            "Adult Cat Dry Food 2kg": {"price": 550.00, "animal_type": "Cat", "dosage": "N/A", "expiration": "2 years"},
        },
        "wet_food": {
            "Cat Wet Food Pouches (12 pack)": {"price": 420.00, "animal_type": "Cat", "dosage": "N/A", "expiration": "1 year"},
        }
    }
}

GROOM_SERVICES = {
    "dog_grooming": {
        "basic_groom": {
            "Basic Dog Grooming": {"price": 500.00, "animal_type": "Dog", "description": "Bath, brush, nail trim"},
        },
        "full_groom": {
            "Full Dog Grooming": {"price": 1200.00, "animal_type": "Dog", "description": "Bath, brush, nail trim, haircut"},
        }
    },
    "cat_grooming": {
        "basic_groom": {
            "Basic Cat Grooming": {"price": 400.00, "animal_type": "Cat", "description": "Bath, brush, nail trim"},
        }
    }
}

# ==================== CATALOG POPULATION FUNCTIONS ====================

def populate_initial_inventory():
    """Populate the database with initial inventory items"""
    try:
        conn = get_db()
        inventory_manager = InventoryManager(conn)
        
        # Clear existing inventory
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory")
        
        # Add dog medicines
        for category, subcategories in DOG_MEDICINES.items():
            for subcategory, medicines in subcategories.items():
                for med_name, med_info in medicines.items():
                    medicine = Medicine(
                        name=med_name,
                        price=med_info['price'],
                        stock=50,
                        category="Dog Medicines",
                        brand="Generic",
                        animal_type=med_info['animal_type'],
                        dosage=med_info['dosage'],
                        expiration_date=med_info['expiration']
                    )
                    inventory_manager.add_item(medicine)
        
        # Add cat medicines
        for category, subcategories in CAT_MEDICINES.items():
            for subcategory, medicines in subcategories.items():
                for med_name, med_info in medicines.items():
                    medicine = Medicine(
                        name=med_name,
                        price=med_info['price'],
                        stock=50,
                        category="Cat Medicines",
                        brand="Generic",
                        animal_type=med_info['animal_type'],
                        dosage=med_info['dosage'],
                        expiration_date=med_info['expiration']
                    )
                    inventory_manager.add_item(medicine)
        
        # Add pet foods
        for category, subcategories in PET_FOODS.items():
            for subcategory, foods in subcategories.items():
                for food_name, food_info in foods.items():
                    medicine = Medicine(
                        name=food_name,
                        price=food_info['price'],
                        stock=30,
                        category="Pet Food",
                        brand="Premium",
                        animal_type=food_info['animal_type'],
                        dosage=food_info['dosage'],
                        expiration_date=food_info['expiration']
                    )
                    inventory_manager.add_item(medicine)
        
        conn.commit()
        conn.close()
        print("Initial inventory populated successfully!")
        return True
    except Exception as e:
        print(f"Error populating inventory: {e}")
        return False

# ==================== MODERN UI COMPONENTS ====================

class ModernButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        # Set default colors if not provided
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = COLORS["primary"]
        if 'hover_color' not in kwargs:
            kwargs['hover_color'] = COLORS["secondary"]
        if 'text_color' not in kwargs:
            kwargs['text_color'] = COLORS["text_light"]
            
        super().__init__(master, **kwargs)
        self.configure(
            font=("Arial", 12, "bold"),
            border_width=2,
            corner_radius=8
        )

class ModernEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            font=("Arial", 12),
            border_width=2,
            corner_radius=6,
            fg_color=COLORS["card"],
            text_color=COLORS["text_light"],
            border_color=COLORS["primary"]
        )

class ModernLabel(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        if 'text_color' not in kwargs:
            kwargs['text_color'] = COLORS["text_light"]
        super().__init__(master, **kwargs)
        self.configure(font=("Arial", 12))

class ModernFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = COLORS["card"]
        if 'border_color' not in kwargs:
            kwargs['border_color'] = COLORS["primary"]
        super().__init__(master, **kwargs)
        self.configure(corner_radius=10, border_width=1)

class ColorfulCard(ctk.CTkFrame):
    def __init__(self, master, title, value, color):
        super().__init__(master)
        self.configure(
            fg_color=color,
            corner_radius=15,
            border_width=2,
            border_color=COLORS["primary"]
        )
        
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self, 
            text=title,
            font=("Arial", 14, "bold"),
            text_color=COLORS["text_light"]
        )
        title_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        # Value
        value_label = ctk.CTkLabel(
            self,
            text=value,
            font=("Arial", 24, "bold"),
            text_color=COLORS["text_light"]
        )
        value_label.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="w")

# ==================== MAIN APPLICATION WINDOW ====================

class VeterinaryClinicApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        # Set background color
        self.root.configure(fg_color=COLORS["background"])
        
        # Initialize database FIRST
        print("Initializing database...")
        init_db()
        print("Populating initial inventory...")
        populate_initial_inventory()
        
        # Initialize managers
        self.db = get_db()
        self.inventory_manager = InventoryManager(self.db)
        self.appointment_manager = AppointmentManager(self.db)
        self.sales_manager = SalesManager(self.db)
        self.cart = ShoppingCart()
        self.current_user = None
        
        # Apply theme
        apply_theme(self.root)
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.main_content = ModernFrame(self.root)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # Show login screen initially
        self.show_login_screen()
        
    def create_sidebar(self):
        """Create the sidebar navigation"""
        self.sidebar = ModernFrame(self.root, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.sidebar.grid_rowconfigure(7, weight=1)
        
        # Title with color
        title_label = ModernLabel(self.sidebar, text="🐾 Vet Clinic", 
                                 font=("Arial", 20, "bold"),
                                 text_color=COLORS["accent"])
        title_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Navigation buttons (will be populated after login)
        self.nav_buttons = {}
        
    def setup_navigation(self):
        """Setup navigation buttons after login"""
        # Clear existing buttons
        for btn in self.nav_buttons.values():
            btn.destroy()
        self.nav_buttons.clear()
        
        nav_items = [
            ("🏠 Dashboard", self.show_dashboard),
            ("📅 Appointments", self.show_appointments),
            ("📦 Inventory", self.show_inventory),
            ("💰 Point of Sale", self.show_pos),
            ("📊 Reports", self.show_reports),
            ("⚙️ Settings", self.show_settings)
        ]
        
        for i, (text, command) in enumerate(nav_items, 1):
            btn = ModernButton(self.sidebar, text=text, command=command,
                              fg_color="transparent", 
                              border_color=COLORS["primary"],
                              hover_color=COLORS["secondary"],
                              text_color=COLORS["text_light"])
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons[text] = btn
        
        # Logout button
        logout_btn = ModernButton(self.sidebar, text="🚪 Logout", command=self.logout,
                                 fg_color=COLORS["danger"], 
                                 hover_color="#c9302c")
        logout_btn.grid(row=8, column=0, padx=10, pady=20, sticky="ew")
    
    def clear_main_content(self):
        """Clear the main content area"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Show the login screen"""
        self.clear_main_content()
        
        login_frame = ModernFrame(self.main_content)
        login_frame.grid(row=0, column=0, sticky="nsew", padx=100, pady=100)
        login_frame.grid_rowconfigure(4, weight=1)
        login_frame.grid_columnconfigure(0, weight=1)
        
        # Title with color
        title_label = ModernLabel(login_frame, text="Veterinary Clinic Login", 
                                 font=("Arial", 24, "bold"),
                                 text_color=COLORS["accent"])
        title_label.grid(row=0, column=0, pady=40)
        
        # Username
        ModernLabel(login_frame, text="Username:").grid(row=1, column=0, sticky="w", pady=5)
        username_entry = ModernEntry(login_frame, placeholder_text="Enter username")
        username_entry.grid(row=1, column=0, pady=5, sticky="ew")
        
        # Password
        ModernLabel(login_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        password_entry = ModernEntry(login_frame, placeholder_text="Enter password", show="•")
        password_entry.grid(row=2, column=0, pady=5, sticky="ew")
        
        # Login button
        login_btn = ModernButton(login_frame, text="Login", 
                                command=lambda: self.login(username_entry.get(), password_entry.get()),
                                fg_color=COLORS["success"])
        login_btn.grid(row=3, column=0, pady=20, sticky="ew")
        
        # Default credentials hint
        hint_label = ModernLabel(login_frame, 
                                text="Default: admin/admin123 or staff/staff123",
                                text_color=COLORS["accent"],
                                font=("Arial", 10))
        hint_label.grid(row=4, column=0, pady=10)
        
        # Bind Enter key to login
        username_entry.bind("<Return>", lambda e: self.login(username_entry.get(), password_entry.get()))
        password_entry.bind("<Return>", lambda e: self.login(username_entry.get(), password_entry.get()))
        
        # Set focus to username field
        username_entry.focus()
    
    def login(self, username, password):
        """Handle user login - FIXED VERSION"""
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                       (username, password))
            user_data = cur.fetchone()
            conn.close()
            
            if user_data:
                # FIXED: Safe user data access
                if len(user_data) >= 4:
                    user_id, username, password, role = user_data[0], user_data[1], user_data[2], user_data[3]
                    self.current_user = User(user_id, username, password, role)
                    self.setup_navigation()
                    self.show_dashboard()
                    messagebox.showinfo("Success", f"Welcome, {username}!")
                else:
                    # Handle case where role column might be missing
                    user_id, username, password = user_data[0], user_data[1], user_data[2]
                    role = "staff"  # Default role
                    self.current_user = User(user_id, username, password, role)
                    self.setup_navigation()
                    self.show_dashboard()
                    messagebox.showinfo("Success", f"Welcome, {username}!")
            else:
                messagebox.showerror("Error", "Invalid username or password")
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Login failed: {str(e)}")
    
    def logout(self):
        """Handle user logout"""
        self.current_user = None
        # Clear navigation buttons
        for btn in self.nav_buttons.values():
            btn.destroy()
        self.nav_buttons.clear()
        self.show_login_screen()
    
    def show_dashboard(self):
        """Show the dashboard screen with colorful design"""
        self.clear_main_content()
        
        # Main dashboard frame
        dashboard_frame = ModernFrame(self.main_content)
        dashboard_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        dashboard_frame.grid_rowconfigure(2, weight=1)
        dashboard_frame.grid_columnconfigure(0, weight=1)
        
        # Welcome header
        header_frame = ModernFrame(dashboard_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        
        welcome_label = ModernLabel(header_frame, 
                                   text=f"🐕 Welcome to Veterinary Clinic Management System 🐈",
                                   font=("Arial", 20, "bold"),
                                   text_color=COLORS["accent"])
        welcome_label.grid(row=0, column=0, pady=10)
        
        user_label = ModernLabel(header_frame, 
                                text=f"Logged in as: {self.current_user.username} ({self.current_user.role})",
                                font=("Arial", 14),
                                text_color=COLORS["text_light"])
        user_label.grid(row=1, column=0, pady=5)
        
        # Statistics cards - FIXED: Count unique appointments
        stats_frame = ModernFrame(dashboard_frame)
        stats_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Get actual statistics - FIXED: Count unique appointments
        total_items = len(self.inventory_manager.get_all_items())
        
        # Get unique appointment counts
        appointments = self.appointment_manager.get_all_appointments()
        
        # Count unique appointments by appointment_id
        unique_appointments = set()
        today_unique_appointments = set()
        
        for apt in appointments:
            if len(apt) > 0 and apt[0]:  # appointment_id
                unique_appointments.add(apt[0])
                
                # Check if it's today's appointment
                if len(apt) > 4 and apt[4] and apt[4].startswith(datetime.now().strftime('%Y-%m-%d')):
                    today_unique_appointments.add(apt[0])
        
        total_appointments_count = len(unique_appointments)
        today_appointments_count = len(today_unique_appointments)
        
        low_stock = len([item for item in self.inventory_manager.get_all_items() if item.stock < 10])
        
        stats_data = [
            ("Total Inventory", f"{total_items} items", COLORS["primary"]),
            ("Today's Appointments", f"{today_appointments_count}", COLORS["success"]),
            ("All Appointments", f"{total_appointments_count}", COLORS["secondary"]),
            ("Low Stock Items", f"{low_stock}", COLORS["warning"])
        ]
        
        for i, (title, value, color) in enumerate(stats_data):
            card = ColorfulCard(stats_frame, title, value, color)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
        
        # Quick actions
        actions_frame = ModernFrame(dashboard_frame)
        actions_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        actions_frame.grid_columnconfigure((0, 1), weight=1)
        actions_frame.grid_rowconfigure(1, weight=1)
        
        ModernLabel(actions_frame, text="Quick Actions", 
                   font=("Arial", 18, "bold"),
                   text_color=COLORS["accent"]).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Quick action buttons
        quick_actions = [
            ("➕ New Appointment", self.create_new_appointment, COLORS["success"]),
            ("📦 Manage Inventory", self.show_inventory, COLORS["primary"]),
            ("💰 POS Sale", self.show_pos, COLORS["secondary"]),
            ("📊 View Reports", self.show_reports, COLORS["warning"])
        ]
        
        for i, (text, command, color) in enumerate(quick_actions):
            btn = ModernButton(actions_frame, text=text, command=command,
                             fg_color=color, hover_color=COLORS["dark"])
            btn.grid(row=1, column=i, padx=10, pady=10, sticky="nsew")
    
    def show_appointments(self):
        """Show appointments management screen with functional buttons"""
        self.clear_main_content()
        
        # Main appointments frame
        appointments_frame = ModernFrame(self.main_content)
        appointments_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        appointments_frame.grid_rowconfigure(1, weight=1)
        appointments_frame.grid_columnconfigure(0, weight=1)
        
        # Title with icon
        title_label = ModernLabel(appointments_frame, text="📅 Appointment Management", 
                                 font=("Arial", 24, "bold"),
                                 text_color=COLORS["accent"])
        title_label.grid(row=0, column=0, sticky="w", pady=20)
        
        # Create appointment management interface
        self.create_appointments_interface(appointments_frame)
    
    def create_appointments_interface(self, parent):
        """Create appointments management interface with functional buttons"""
        # Button frame
        button_frame = ModernFrame(parent)
        button_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        button_frame.grid_rowconfigure(1, weight=1)
        
        # Action buttons with colors
        new_appt_btn = ModernButton(button_frame, text="➕ New Appointment", 
                                   command=self.create_new_appointment,
                                   fg_color=COLORS["success"], 
                                   hover_color="#218838")
        new_appt_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        view_appt_btn = ModernButton(button_frame, text="👁️ View Details", 
                                    command=self.view_appointments,
                                    fg_color=COLORS["primary"])
        view_appt_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        update_appt_btn = ModernButton(button_frame, text="✏️ Update Status", 
                                      command=self.update_appointment_status,
                                      fg_color=COLORS["warning"])
        update_appt_btn.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        
        delete_appt_btn = ModernButton(button_frame, text="🗑️ Delete", 
                                      command=self.delete_appointment,
                                      fg_color=COLORS["danger"], 
                                      hover_color="#c82333")
        delete_appt_btn.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        
        # Appointments list frame
        list_frame = ModernFrame(parent)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for appointments
        columns = ("ID", "Patient", "Owner", "Animal", "Date", "Status", "Amount")
        self.appointments_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background=COLORS["card"],
                       foreground=COLORS["text_light"],
                       fieldbackground=COLORS["card"],
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background=COLORS["primary"],
                       foreground=COLORS["text_light"],
                       borderwidth=0)
        style.map("Treeview", background=[('selected', COLORS["secondary"])])
        
        # Configure columns
        column_widths = {
            "ID": 120, "Patient": 120, "Owner": 120, "Animal": 100,
            "Date": 150, "Status": 100, "Amount": 100
        }
        
        for col in columns:
            self.appointments_tree.heading(col, text=col)
            self.appointments_tree.column(col, width=column_widths.get(col, 100))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.appointments_tree.yview)
        self.appointments_tree.configure(yscrollcommand=scrollbar.set)
        
        self.appointments_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Load appointments data
        self.load_appointments_data()
    
    def load_appointments_data(self):
        """Load appointments data into the treeview"""
        # Clear existing data
        for item in self.appointments_tree.get_children():
            self.appointments_tree.delete(item)
        
        # Get appointments
        appointments = self.appointment_manager.get_all_appointments()
        
        # Populate treeview
        for apt in appointments:
            self.appointments_tree.insert("", "end", values=(
                apt[0] if len(apt) > 0 else "",  # appointment_id
                apt[1] if len(apt) > 1 else "",  # patient_name
                apt[2] if len(apt) > 2 else "",  # owner_name
                apt[3] if len(apt) > 3 else "",  # animal_type
                apt[4] if len(apt) > 4 else "",  # date
                apt[6] if len(apt) > 6 else "", # status
                f"₱{apt[7]:.2f}" if len(apt) > 7 and apt[7] else "₱0.00"  # total_amount
            ))
    
    def create_new_appointment(self):
        """Create a new appointment dialog with proper pricing - FIXED VERSION"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("New Appointment")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        
        ModernLabel(dialog, text="Create New Appointment", 
                   font=("Arial", 20, "bold"),
                   text_color=COLORS["accent"]).pack(pady=20)
        
        # Form frame
        form_frame = ModernFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Form fields
        fields = [
            ("Patient Name:", "entry"),
            ("Owner Name:", "entry"),
            ("Animal Type:", "combo", ["Dog", "Cat", "Bird", "Other"]),
            ("Service Type:", "combo", list(SERVICE_PRICES.keys())),
            ("Notes:", "text"),
            ("Status:", "combo", ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
        ]
        
        entries = {}
        row = 0
        
        for field in fields:
            ModernLabel(form_frame, text=field[0]).grid(row=row, column=0, sticky="w", padx=10, pady=5)
            
            if field[1] == "entry":
                entry = ModernEntry(form_frame, width=300)
                entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                entries[field[0]] = entry
            elif field[1] == "combo":
                combo = ctk.CTkComboBox(form_frame, values=field[2], width=300)
                combo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                entries[field[0]] = combo
                
                # Add price display for service type
                if field[0] == "Service Type:":
                    price_label = ModernLabel(form_frame, text="Price: ₱0.00", 
                                            text_color=COLORS["accent"])
                    price_label.grid(row=row, column=2, padx=10, pady=5)
                    
                    def update_price(event=None):
                        service = combo.get()
                        price = SERVICE_PRICES.get(service, 0.0)
                        price_label.configure(text=f"Price: ₱{price:.2f}")
                    
                    combo.configure(command=lambda e: update_price())
                    # Set initial price
                    update_price()
                    
            elif field[1] == "text":
                text_widget = ctk.CTkTextbox(form_frame, width=300, height=80)
                text_widget.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                entries[field[0]] = text_widget
            
            row += 1
        
        # Submit button
        def submit_appointment():
            try:
                # Get form values
                patient_name = entries["Patient Name:"].get().strip()
                owner_name = entries["Owner Name:"].get().strip()
                animal_type = entries["Animal Type:"].get()
                service_type = entries["Service Type:"].get()
                notes = entries["Notes:"].get("1.0", "end-1c").strip() if hasattr(entries["Notes:"], 'get') else entries["Notes:"].get()
                status = entries["Status:"].get()
                
                # Validate required fields
                if not patient_name:
                    messagebox.showerror("Error", "Patient name is required")
                    return
                if not owner_name:
                    messagebox.showerror("Error", "Owner name is required")
                    return
                if not service_type:
                    messagebox.showerror("Error", "Service type is required")
                    return
                
                # Get service price
                price = SERVICE_PRICES.get(service_type, 0.0)
                
                # Create appointment object
                appointment = Appointment(
                    appointment_id=generate_appointment_id(),
                    patient_name=patient_name,
                    owner_name=owner_name,
                    animal_type=animal_type,
                    service=service_type,
                    notes=notes,
                    status=status
                )
                
                # Add service with proper pricing
                appointment.add_service(service_type, 1, price, price)
                
                print(f"Creating appointment: {appointment.appointment_id}")
                print(f"Service: {service_type}, Price: {price}")
                print(f"Total amount: {appointment.total_amount}")
                
                # Save to database
                if self.appointment_manager.record_appointment(appointment):
                    messagebox.showinfo("Success", "Appointment created successfully!")
                    self.load_appointments_data()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to create appointment")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create appointment: {str(e)}")
                print(f"Appointment creation error: {e}")
        
        submit_btn = ModernButton(dialog, text="Create Appointment", 
                                 command=submit_appointment,
                                 fg_color=COLORS["success"], 
                                 hover_color="#218838")
        submit_btn.pack(pady=20)
    
    def view_appointments(self):
        """View selected appointment details"""
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an appointment to view")
            return
        
        item = self.appointments_tree.item(selection[0])
        values = item['values']
        
        # Show appointment details in a colorful dialog
        details_window = ctk.CTkToplevel(self.root)
        details_window.title("Appointment Details")
        details_window.geometry("400x300")
        details_window.configure(fg_color=COLORS["background"])
        
        ModernLabel(details_window, text="📋 Appointment Details", 
                   font=("Arial", 18, "bold"),
                   text_color=COLORS["accent"]).pack(pady=20)
        
        details_frame = ModernFrame(details_window)
        details_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        details_text = f"Appointment ID: {values[0]}\n"
        details_text += f"Patient: {values[1]}\n"
        details_text += f"Owner: {values[2]}\n"
        details_text += f"Animal Type: {values[3]}\n"
        details_text += f"Date: {values[4]}\n"
        details_text += f"Status: {values[5]}\n"
        details_text += f"Amount: {values[6]}"
        
        details_label = ModernLabel(details_frame, text=details_text,
                                   font=("Arial", 12),
                                   justify="left")
        details_label.pack(padx=20, pady=20)
    
    def update_appointment_status(self):
        """Update appointment status"""
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an appointment to update")
            return
        
        item = self.appointments_tree.item(selection[0])
        values = item['values']
        appointment_id = values[0]
        
        # Status selection dialog
        status_dialog = ctk.CTkToplevel(self.root)
        status_dialog.title("Update Status")
        status_dialog.geometry("300x200")
        status_dialog.transient(self.root)
        status_dialog.grab_set()
        status_dialog.configure(fg_color=COLORS["background"])
        
        ModernLabel(status_dialog, text="Select New Status", 
                   font=("Arial", 16, "bold"),
                   text_color=COLORS["accent"]).pack(pady=20)
        
        status_var = ctk.StringVar(value=values[5])
        status_combo = ctk.CTkComboBox(status_dialog, 
                                      values=["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
                                      variable=status_var)
        status_combo.pack(pady=10)
        
        def update_status():
            new_status = status_var.get()
            if self.appointment_manager.update_appointment_status(appointment_id, new_status):
                messagebox.showinfo("Success", "Status updated successfully!")
                self.load_appointments_data()
                status_dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to update status")
        
        update_btn = ModernButton(status_dialog, text="Update Status", 
                                command=update_status,
                                fg_color=COLORS["success"])
        update_btn.pack(pady=20)
    
    def delete_appointment(self):
        """Delete selected appointment"""
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an appointment to delete")
            return
        
        item = self.appointments_tree.item(selection[0])
        values = item['values']
        appointment_id = values[0]
        
        # Confirmation dialog
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete appointment {appointment_id}?")
        
        if result:
            if self.appointment_manager.delete_appointment(appointment_id):
                messagebox.showinfo("Success", "Appointment deleted successfully!")
                self.load_appointments_data()
            else:
                messagebox.showerror("Error", "Failed to delete appointment")

    def show_inventory(self):
        """Show inventory management screen"""
        self.clear_main_content()
        
        # Main inventory frame
        inventory_frame = ModernFrame(self.main_content)
        inventory_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        inventory_frame.grid_rowconfigure(1, weight=1)
        inventory_frame.grid_columnconfigure(0, weight=1)
        
        # Title with icon
        title_label = ModernLabel(inventory_frame, text="📦 Inventory Management", 
                                 font=("Arial", 24, "bold"),
                                 text_color=COLORS["accent"])
        title_label.grid(row=0, column=0, sticky="w", pady=20)
        
        # Create inventory management interface
        self.create_inventory_interface(inventory_frame)

    def create_inventory_interface(self, parent):
        """Create inventory management interface"""
        # Search and controls frame
        controls_frame = ModernFrame(parent)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Search entry
        ModernLabel(controls_frame, text="Search:").grid(row=0, column=0, padx=10, pady=10)
        self.search_entry = ModernEntry(controls_frame, placeholder_text="Search items...")
        self.search_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Search button
        search_btn = ModernButton(controls_frame, text="🔍 Search", 
                                 command=self.search_inventory)
        search_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Action buttons frame
        action_frame = ModernFrame(parent)
        action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        action_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Action buttons
        add_btn = ModernButton(action_frame, text="➕ Add Item", 
                              command=self.add_inventory_item,
                              fg_color=COLORS["success"])
        add_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        edit_btn = ModernButton(action_frame, text="✏️ Edit Item", 
                               command=self.edit_inventory_item,
                               fg_color=COLORS["primary"])
        edit_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        delete_btn = ModernButton(action_frame, text="🗑️ Delete Item", 
                                 command=self.delete_inventory_item,
                                 fg_color=COLORS["danger"])
        delete_btn.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        
        refresh_btn = ModernButton(action_frame, text="🔄 Refresh", 
                                  command=self.load_inventory_data)
        refresh_btn.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        
        # Inventory list frame
        list_frame = ModernFrame(parent)
        list_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for inventory
        columns = ("ID", "Name", "Price", "Stock", "Category", "Brand", "Animal Type", "Expiration")
        self.inventory_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background=COLORS["card"],
                       foreground=COLORS["text_light"],
                       fieldbackground=COLORS["card"],
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background=COLORS["primary"],
                       foreground=COLORS["text_light"],
                       borderwidth=0)
        style.map("Treeview", background=[('selected', COLORS["secondary"])])
        
        # Configure columns
        column_widths = {
            "ID": 60, "Name": 150, "Price": 80, "Stock": 60, 
            "Category": 100, "Brand": 100, "Animal Type": 100, "Expiration": 100
        }
        
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=column_widths.get(col, 100))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inventory_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Load inventory data
        self.load_inventory_data()

    def load_inventory_data(self):
        """Load inventory data into the treeview"""
        # Clear existing data
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Get inventory items
        items = self.inventory_manager.get_all_items()
        
        # Populate treeview
        for item in items:
            self.inventory_tree.insert("", "end", values=(
                item.id,
                item.name,
                f"₱{item.price:.2f}",
                item.stock,
                item.category,
                item.brand,
                item.animal_type,
                item.expiration_date
            ))

    def search_inventory(self):
        """Search inventory items"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.load_inventory_data()
            return
        
        # Clear existing data
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Search items
        items = self.inventory_manager.search_items(search_term)
        
        # Populate treeview with search results
        for item in items:
            self.inventory_tree.insert("", "end", values=(
                item.id,
                item.name,
                f"₱{item.price:.2f}",
                item.stock,
                item.category,
                item.brand,
                item.animal_type,
                item.expiration_date
            ))

    def add_inventory_item(self):
        """Add new inventory item"""
        self.show_inventory_item_dialog()

    def edit_inventory_item(self):
        """Edit selected inventory item"""
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to edit")
            return
        
        item = self.inventory_tree.item(selection[0])
        values = item['values']
        item_id = values[0]
        
        # Get the full item details
        items = self.inventory_manager.get_all_items()
        selected_item = None
        for item_obj in items:
            if item_obj.id == item_id:
                selected_item = item_obj
                break
        
        if selected_item:
            self.show_inventory_item_dialog(selected_item)

    def delete_inventory_item(self):
        """Delete selected inventory item"""
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
        
        item = self.inventory_tree.item(selection[0])
        values = item['values']
        item_id = values[0]
        item_name = values[1]
        
        # Confirmation dialog
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete '{item_name}'?")
        
        if result:
            if self.inventory_manager.delete_item(item_id):
                messagebox.showinfo("Success", "Item deleted successfully!")
                self.load_inventory_data()
            else:
                messagebox.showerror("Error", "Failed to delete item")

    def show_inventory_item_dialog(self, item=None):
        """Show dialog for adding/editing inventory items"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Item" if item is None else "Edit Item")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        
        title = "Add New Item" if item is None else f"Edit Item: {item.name}"
        ModernLabel(dialog, text=title, 
                   font=("Arial", 20, "bold"),
                   text_color=COLORS["accent"]).pack(pady=20)
        
        # Form frame
        form_frame = ModernFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Form fields
        fields = [
            ("Name:", "entry"),
            ("Price:", "entry"),
            ("Stock:", "entry"),
            ("Category:", "combo", ["Dog Medicines", "Cat Medicines", "Pet Food", "Supplies"]),
            ("Brand:", "entry"),
            ("Animal Type:", "combo", ["Dog", "Cat", "All", "Other"]),
            ("Dosage:", "entry"),
            ("Expiration Date:", "entry")
        ]
        
        entries = {}
        row = 0
        
        for field in fields:
            ModernLabel(form_frame, text=field[0]).grid(row=row, column=0, sticky="w", padx=10, pady=5)
            
            if field[1] == "entry":
                entry = ModernEntry(form_frame, width=300)
                if item is not None:
                    if field[0] == "Name:":
                        entry.insert(0, item.name)
                    elif field[0] == "Price:":
                        entry.insert(0, str(item.price))
                    elif field[0] == "Stock:":
                        entry.insert(0, str(item.stock))
                    elif field[0] == "Brand:":
                        entry.insert(0, item.brand)
                    elif field[0] == "Dosage:":
                        entry.insert(0, item.dosage)
                    elif field[0] == "Expiration Date:":
                        entry.insert(0, item.expiration_date)
                entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                entries[field[0]] = entry
            elif field[1] == "combo":
                combo = ctk.CTkComboBox(form_frame, values=field[2], width=300)
                if item is not None:
                    if field[0] == "Category:":
                        combo.set(item.category)
                    elif field[0] == "Animal Type:":
                        combo.set(item.animal_type)
                combo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                entries[field[0]] = combo
            
            row += 1
        
        # Submit button
        def submit_item():
            try:
                # Validate required fields
                if not entries["Name:"].get().strip():
                    messagebox.showerror("Error", "Name is required")
                    return
                
                # Create medicine object
                medicine = Medicine(
                    id=item.id if item else None,
                    name=entries["Name:"].get().strip(),
                    price=float(entries["Price:"].get() or 0),
                    stock=int(entries["Stock:"].get() or 0),
                    category=entries["Category:"].get(),
                    brand=entries["Brand:"].get().strip(),
                    animal_type=entries["Animal Type:"].get(),
                    dosage=entries["Dosage:"].get().strip(),
                    expiration_date=entries["Expiration Date:"].get().strip()
                )
                
                # Save to database
                if item is None:
                    success = self.inventory_manager.add_item(medicine)
                else:
                    success = self.inventory_manager.update_item(medicine)
                
                if success:
                    messagebox.showinfo("Success", 
                                      "Item added successfully!" if item is None else "Item updated successfully!")
                    self.load_inventory_data()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to save item")
                    
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid numbers for price and stock")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save item: {str(e)}")
        
        submit_btn = ModernButton(dialog, text="Save Item", 
                                 command=submit_item,
                                 fg_color=COLORS["success"])
        submit_btn.pack(pady=20)

    def show_pos(self):
        """Show point of sale screen"""
        self.clear_main_content()
        
        # Main POS frame
        pos_frame = ModernFrame(self.main_content)
        pos_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        pos_frame.grid_rowconfigure(1, weight=1)
        pos_frame.grid_columnconfigure(0, weight=1)
        pos_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ModernLabel(pos_frame, text="💰 Point of Sale", 
                                 font=("Arial", 24, "bold"),
                                 text_color=COLORS["accent"])
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=20)
        
        # Create POS interface
        self.create_pos_interface(pos_frame)
    
    def create_pos_interface(self, parent):
        """Create complete point of sale interface"""
        # Left side - Products
        products_frame = ModernFrame(parent)
        products_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        products_frame.grid_rowconfigure(1, weight=1)
        products_frame.grid_columnconfigure(0, weight=1)
        
        ModernLabel(products_frame, text="🛍️ Available Products", 
                   font=("Arial", 16, "bold"),
                   text_color=COLORS["accent"]).grid(row=0, column=0, sticky="w", pady=10)
        
        # Products treeview
        products_columns = ("ID", "Name", "Price", "Stock", "Category")
        self.products_tree = ttk.Treeview(products_frame, columns=products_columns, show="headings", height=15)
        
        for col in products_columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=100)
        
        # Style products treeview
        style = ttk.Style()
        style.configure("Products.Treeview", 
                       background=COLORS["card"],
                       foreground=COLORS["text_light"],
                       fieldbackground=COLORS["card"])
        
        products_scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        self.products_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        products_scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Add to cart button
        add_to_cart_btn = ModernButton(products_frame, text="➕ Add to Cart", 
                                      command=self.add_to_cart,
                                      fg_color=COLORS["success"])
        add_to_cart_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # Right side - Cart and checkout
        cart_frame = ModernFrame(parent)
        cart_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        cart_frame.grid_rowconfigure(1, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)
        
        ModernLabel(cart_frame, text="🛒 Shopping Cart", 
                   font=("Arial", 16, "bold"),
                   text_color=COLORS["accent"]).grid(row=0, column=0, sticky="w", pady=10)
        
        # Cart treeview
        cart_columns = ("Name", "Price", "Qty", "Subtotal")
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=10)
        
        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=100)
        
        cart_scrollbar = ttk.Scrollbar(cart_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        self.cart_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        cart_scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Cart controls
        cart_controls_frame = ModernFrame(cart_frame)
        cart_controls_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        cart_controls_frame.grid_columnconfigure((0, 1), weight=1)
        
        remove_item_btn = ModernButton(cart_controls_frame, text="➖ Remove Item", 
                                      command=self.remove_from_cart,
                                      fg_color=COLORS["warning"])
        remove_item_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        clear_cart_btn = ModernButton(cart_controls_frame, text="🗑️ Clear Cart", 
                                     command=self.clear_cart,
                                     fg_color=COLORS["danger"])
        clear_cart_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Customer info and totals
        info_frame = ModernFrame(cart_frame)
        info_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        info_frame.grid_columnconfigure(1, weight=1)
        
        ModernLabel(info_frame, text="Customer Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.customer_name_entry = ModernEntry(info_frame)
        self.customer_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ModernLabel(info_frame, text="Payment Method:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.payment_method_combo = ctk.CTkComboBox(info_frame, values=["Cash", "Credit Card", "GCash", "Bank Transfer"])
        self.payment_method_combo.set("Cash")
        self.payment_method_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Totals display
        totals_frame = ModernFrame(cart_frame)
        totals_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        totals_frame.grid_columnconfigure(1, weight=1)
        
        self.total_label = ModernLabel(totals_frame, text="Total: ₱0.00", 
                                      font=("Arial", 16, "bold"),
                                      text_color=COLORS["accent"])
        self.total_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Checkout button
        checkout_btn = ModernButton(cart_frame, text="💳 Checkout", 
                                   command=self.process_checkout,
                                   fg_color=COLORS["success"],
                                   font=("Arial", 14, "bold"))
        checkout_btn.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        
        # Load products
        self.load_products_for_pos()
        self.update_cart_display()
    
    def load_products_for_pos(self):
        """Load products for POS interface"""
        # Clear existing data
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Get inventory items
        items = self.inventory_manager.get_all_items()
        
        # Populate products treeview
        for item in items:
            if item.stock > 0:  # Only show items with stock
                self.products_tree.insert("", "end", values=(
                    item.id,
                    item.name,
                    f"₱{item.price:.2f}",
                    item.stock,
                    item.category
                ))
    
    def add_to_cart(self):
        """Add selected product to cart"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product to add to cart")
            return
        
        item = self.products_tree.item(selection[0])
        values = item['values']
        
        item_id = values[0]
        item_name = values[1]
        item_price = float(values[2].replace('₱', ''))
        item_stock = values[3]
        
        # Check stock
        if item_stock <= 0:
            messagebox.showwarning("Warning", "This item is out of stock")
            return
        
        # Add to cart
        self.cart.add_item(item_id, item_name, item_price, 1, values[4])
        self.update_cart_display()
    
    def remove_from_cart(self):
        """Remove selected item from cart"""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to remove from cart")
            return
        
        item = self.cart_tree.item(selection[0])
        values = item['values']
        
        # Find item ID by name (this is a simplification)
        for cart_item in self.cart.items:
            if cart_item.name == values[0]:
                self.cart.remove_item(cart_item.item_id)
                break
        
        self.update_cart_display()
    
    def clear_cart(self):
        """Clear all items from cart"""
        self.cart.clear()
        self.update_cart_display()
    
    def update_cart_display(self):
        """Update cart display with current items and total"""
        # Clear cart display
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Add cart items
        for item in self.cart.items:
            self.cart_tree.insert("", "end", values=(
                item.name,
                f"₱{item.price:.2f}",
                item.quantity,
                f"₱{item.subtotal:.2f}"
            ))
        
        # Update total
        self.total_label.configure(text=f"Total: ₱{self.cart.total:.2f}")
    
    def process_checkout(self):
        """Process the checkout and record sale"""
        if not self.cart.items:
            messagebox.showwarning("Warning", "Cart is empty")
            return
        
        # Validate customer name
        customer_name = self.customer_name_entry.get().strip()
        if not customer_name:
            customer_name = "Walk-in Customer"
        
        payment_method = self.payment_method_combo.get()
        
        # Check stock availability
        for cart_item in self.cart.items:
            # Get current stock from database
            items = self.inventory_manager.get_all_items()
            for item in items:
                if item.id == cart_item.item_id:
                    if item.stock < cart_item.quantity:
                        messagebox.showerror("Error", 
                                           f"Not enough stock for {item.name}. Available: {item.stock}")
                        return
                    break
        
        # Process sale
        transaction_id = generate_transaction_id()
        cart_items_dict = self.cart.to_legacy_format()
        
        if self.sales_manager.record_sale(transaction_id, cart_items_dict, 
                                        self.cart.total, payment_method, customer_name):
            # Generate receipt
            receipt_text = ReceiptManager.generate_receipt_text(
                transaction_id, 
                customer_name, 
                customer_name, 
                "Various", 
                "POS Sale", 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                self.cart.total, 
                cart_items_dict
            )
            
            # Show success message with receipt
            receipt_window = ctk.CTkToplevel(self.root)
            receipt_window.title("Sale Completed - Receipt")
            receipt_window.geometry("500x600")
            receipt_window.configure(fg_color=COLORS["background"])
            
            ModernLabel(receipt_window, text="✅ Sale Completed!", 
                       font=("Arial", 20, "bold"),
                       text_color=COLORS["success"]).pack(pady=20)
            
            receipt_frame = ModernFrame(receipt_window)
            receipt_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            receipt_text_widget = ctk.CTkTextbox(receipt_frame, font=("Courier", 12))
            receipt_text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            receipt_text_widget.insert("1.0", receipt_text)
            receipt_text_widget.configure(state="disabled")
            
            # Save receipt button
            def save_receipt():
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                    initialfile=f"receipt_{transaction_id}.txt"
                )
                if filename:
                    ReceiptManager.save_receipt_to_file(receipt_text, filename)
                    messagebox.showinfo("Success", f"Receipt saved as {filename}")
            
            save_btn = ModernButton(receipt_window, text="💾 Save Receipt", 
                                   command=save_receipt)
            save_btn.pack(pady=10)
            
            # Clear cart and refresh products
            self.cart.clear()
            self.update_cart_display()
            self.load_products_for_pos()
            self.customer_name_entry.delete(0, 'end')
            
            messagebox.showinfo("Success", f"Sale completed! Transaction ID: {transaction_id}")
        else:
            messagebox.showerror("Error", "Failed to process sale")

    def show_reports(self):
        """Show reports and analytics screen"""
        self.clear_main_content()
        
        # Main reports frame
        reports_frame = ModernFrame(self.main_content)
        reports_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        reports_frame.grid_rowconfigure(1, weight=1)
        reports_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ModernLabel(reports_frame, text="📊 Reports & Analytics", 
                                 font=("Arial", 24, "bold"),
                                 text_color=COLORS["accent"])
        title_label.grid(row=0, column=0, sticky="w", pady=20)
        
        # Create reports interface
        self.create_reports_interface(reports_frame)
    
    def create_reports_interface(self, parent):
        """Create reports and analytics interface"""
        # Date selection frame
        date_frame = ModernFrame(parent)
        date_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        date_frame.grid_columnconfigure((1, 3), weight=1)
        
        ModernLabel(date_frame, text="From:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = ModernEntry(date_frame, placeholder_text="YYYY-MM-DD")
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ModernLabel(date_frame, text="To:").grid(row=0, column=2, padx=5, pady=5)
        self.end_date_entry = ModernEntry(date_frame, placeholder_text="YYYY-MM-DD")
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Set default dates (last 30 days)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.start_date_entry.insert(0, start_date)
        self.end_date_entry.insert(0, end_date)
        
        # Report buttons
        report_buttons_frame = ModernFrame(parent)
        report_buttons_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        report_buttons_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        sales_report_btn = ModernButton(report_buttons_frame, text="💰 Sales Report", 
                                       command=self.generate_sales_report,
                                       fg_color=COLORS["success"])
        sales_report_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        inventory_report_btn = ModernButton(report_buttons_frame, text="📦 Inventory Report", 
                                           command=self.generate_inventory_report,
                                           fg_color=COLORS["primary"])
        inventory_report_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        appointments_report_btn = ModernButton(report_buttons_frame, text="📅 Appointments Report", 
                                              command=self.generate_appointments_report,
                                              fg_color=COLORS["secondary"])
        appointments_report_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        export_btn = ModernButton(report_buttons_frame, text="📤 Export Data", 
                                 command=self.export_data,
                                 fg_color=COLORS["warning"])
        export_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Report display frame
        self.report_display_frame = ModernFrame(parent)
        self.report_display_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.report_display_frame.grid_rowconfigure(0, weight=1)
        self.report_display_frame.grid_columnconfigure(0, weight=1)
        
        # Initial report cards
        self.show_report_cards()
    
    def show_report_cards(self):
        """Show summary report cards"""
        # Clear display
        for widget in self.report_display_frame.winfo_children():
            widget.destroy()
        
        # Get report data
        total_sales = self.calculate_total_sales()
        total_appointments = len(self.appointment_manager.get_all_appointments())
        low_stock_items = len([item for item in self.inventory_manager.get_all_items() if item.stock < 10])
        total_inventory_value = sum(item.price * item.stock for item in self.inventory_manager.get_all_items())
        
        report_cards = [
            ("💰 Total Sales", f"₱{total_sales:,.2f}", COLORS["success"]),
            ("📅 Total Appointments", f"{total_appointments}", COLORS["primary"]),
            ("⚠️ Low Stock Items", f"{low_stock_items}", COLORS["warning"]),
            ("📦 Inventory Value", f"₱{total_inventory_value:,.2f}", COLORS["secondary"])
        ]
        
        for i, (title, value, color) in enumerate(report_cards):
            card = ColorfulCard(self.report_display_frame, title, value, color)
            card.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
    
    def calculate_total_sales(self):
        """Calculate total sales amount"""
        try:
            cur = self.db.cursor()
            cur.execute("SELECT SUM(total_amount) FROM sales")
            result = cur.fetchone()
            return result[0] or 0.0
        except sqlite3.Error:
            return 0.0
    
    def generate_sales_report(self):
        """Generate and display sales report"""
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        
        sales = self.sales_manager.get_sales_report(start_date, end_date)
        
        # Clear display
        for widget in self.report_display_frame.winfo_children():
            widget.destroy()
        
        # Create sales report treeview
        columns = ("Transaction ID", "Item", "Qty", "Price", "Subtotal", "Date", "Payment Method")
        sales_tree = ttk.Treeview(self.report_display_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            sales_tree.heading(col, text=col)
            sales_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.report_display_frame, orient="vertical", command=sales_tree.yview)
        sales_tree.configure(yscrollcommand=scrollbar.set)
        
        sales_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Populate sales data
        total_sales = 0
        for sale in sales:
            sales_tree.insert("", "end", values=(
                sale[1] if len(sale) > 1 else "",  # transaction_id
                sale[3] if len(sale) > 3 else "",  # item_name
                sale[4] if len(sale) > 4 else "",  # quantity
                f"₱{sale[5]:.2f}" if len(sale) > 5 and sale[5] else "₱0.00",  # price
                f"₱{sale[6]:.2f}" if len(sale) > 6 and sale[6] else "₱0.00",  # subtotal
                sale[9] if len(sale) > 9 else "",  # sale_date
                sale[7] if len(sale) > 7 else ""   # payment_method
            ))
            total_sales += sale[6] if len(sale) > 6 and sale[6] else 0  # subtotal
        
        # Add total row
        sales_tree.insert("", "end", values=("TOTAL", "", "", "", f"₱{total_sales:.2f}", "", ""))
    
    def generate_inventory_report(self):
        """Generate and display inventory report"""
        items = self.inventory_manager.get_all_items()
        
        # Clear display
        for widget in self.report_display_frame.winfo_children():
            widget.destroy()
        
        # Create inventory report treeview
        columns = ("ID", "Name", "Category", "Price", "Stock", "Value", "Status")
        inventory_tree = ttk.Treeview(self.report_display_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            inventory_tree.heading(col, text=col)
            inventory_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(self.report_display_frame, orient="vertical", command=inventory_tree.yview)
        inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        inventory_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Populate inventory data
        for item in items:
            status = "✅ OK" if item.stock >= 10 else "⚠️ Low" if item.stock > 0 else "❌ Out"
            inventory_tree.insert("", "end", values=(
                item.id,
                item.name,
                item.category,
                f"₱{item.price:.2f}",
                item.stock,
                f"₱{item.price * item.stock:.2f}",
                status
            ))
    
    def generate_appointments_report(self):
        """Generate and display appointments report"""
        appointments = self.appointment_manager.get_all_appointments()
        
        # Clear display
        for widget in self.report_display_frame.winfo_children():
            widget.destroy()
        
        # Create appointments report treeview
        columns = ("Appointment ID", "Patient", "Owner", "Animal", "Date", "Status", "Amount")
        appointments_tree = ttk.Treeview(self.report_display_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            appointments_tree.heading(col, text=col)
            appointments_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.report_display_frame, orient="vertical", command=appointments_tree.yview)
        appointments_tree.configure(yscrollcommand=scrollbar.set)
        
        appointments_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Populate appointments data
        total_amount = 0
        for apt in appointments:
            appointments_tree.insert("", "end", values=(
                apt[0] if len(apt) > 0 else "",  # appointment_id
                apt[1] if len(apt) > 1 else "",  # patient_name
                apt[2] if len(apt) > 2 else "",  # owner_name
                apt[3] if len(apt) > 3 else "",  # animal_type
                apt[4] if len(apt) > 4 else "",  # date
                apt[6] if len(apt) > 6 else "", # status
                f"₱{apt[7]:.2f}" if len(apt) > 7 and apt[7] else "₱0.00"
            ))
            total_amount += apt[7] if len(apt) > 7 and apt[7] else 0
        
        # Add total row
        appointments_tree.insert("", "end", values=("TOTAL", "", "", "", "", "", f"₱{total_amount:.2f}"))
    
    def export_data(self):
        """Export data to CSV"""
        file_types = [
            ("Sales Data", "sales"),
            ("Inventory Data", "inventory"),
            ("Appointments Data", "appointments")
        ]
        
        # Create dialog for export type selection
        export_dialog = ctk.CTkToplevel(self.root)
        export_dialog.title("Export Data")
        export_dialog.geometry("300x200")
        export_dialog.transient(self.root)
        export_dialog.grab_set()
        export_dialog.configure(fg_color=COLORS["background"])
        
        ModernLabel(export_dialog, text="Select Data to Export", 
                   font=("Arial", 16, "bold"),
                   text_color=COLORS["accent"]).pack(pady=20)
        
        export_var = ctk.StringVar(value="sales")
        
        for text, value in file_types:
            radio = ctk.CTkRadioButton(export_dialog, text=text, variable=export_var, value=value)
            radio.pack(pady=5)
        
        def perform_export():
            export_type = export_var.get()
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"vetclinic_{export_type}_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                if self.export_to_csv(export_type, filename):
                    messagebox.showinfo("Success", f"Data exported to {filename}")
                    export_dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to export data")
        
        export_btn = ModernButton(export_dialog, text="Export", command=perform_export)
        export_btn.pack(pady=20)
    
    def export_to_csv(self, data_type, filename):
        """Export data to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                if data_type == "sales":
                    # Export sales data
                    sales = self.sales_manager.get_sales_report()
                    writer.writerow(["Transaction ID", "Item Name", "Quantity", "Price", "Subtotal", "Total Amount", "Payment Method", "Customer Name", "Sale Date"])
                    for sale in sales:
                        writer.writerow(sale[1:10])  # Skip ID column
                
                elif data_type == "inventory":
                    # Export inventory data
                    items = self.inventory_manager.get_all_items()
                    writer.writerow(["ID", "Name", "Price", "Stock", "Category", "Brand", "Animal Type", "Dosage", "Expiration Date"])
                    for item in items:
                        writer.writerow([
                            item.id, item.name, item.price, item.stock, item.category,
                            item.brand, item.animal_type, item.dosage, item.expiration_date
                        ])
                
                elif data_type == "appointments":
                    # Export appointments data
                    appointments = self.appointment_manager.get_all_appointments()
                    writer.writerow(["Appointment ID", "Patient Name", "Owner Name", "Animal Type", "Date", "Notes", "Status", "Total Amount"])
                    for apt in appointments:
                        writer.writerow(apt[:8])  # Use first 8 columns
        
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False

    def show_settings(self):
        """Show settings screen with complete functionality"""
        self.clear_main_content()
        
        # Main settings frame
        settings_frame = ModernFrame(self.main_content)
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        settings_frame.grid_rowconfigure(1, weight=1)
        settings_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ModernLabel(settings_frame, text="⚙️ System Settings", 
                                 font=("Arial", 24, "bold"),
                                 text_color=COLORS["accent"])
        title_label.grid(row=0, column=0, sticky="w", pady=20)
        
        # Create settings interface
        self.create_settings_interface(settings_frame)
    
    def create_settings_interface(self, parent):
        """Create complete settings interface"""
        # Notebook for settings categories
        settings_notebook = ttk.Notebook(parent)
        settings_notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # User Management Tab
        user_frame = ModernFrame(settings_notebook)
        settings_notebook.add(user_frame, text="👤 User Management")
        self.create_user_management_tab(user_frame)
        
        # Theme Settings Tab
        theme_frame = ModernFrame(settings_notebook)
        settings_notebook.add(theme_frame, text="🎨 Theme Settings")
        self.create_theme_settings_tab(theme_frame)
        
        # Database Tab
        db_frame = ModernFrame(settings_notebook)
        settings_notebook.add(db_frame, text="💾 Database")
        self.create_database_tab(db_frame)
        
        # Security Tab
        security_frame = ModernFrame(settings_notebook)
        settings_notebook.add(security_frame, text="🔒 Security")
        self.create_security_tab(security_frame)
    
    def create_user_management_tab(self, parent):
        """Create user management settings"""
        parent.grid_columnconfigure(0, weight=1)
        
        # Current user info
        current_user_frame = ModernFrame(parent)
        current_user_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        current_user_frame.grid_columnconfigure(1, weight=1)
        
        ModernLabel(current_user_frame, text="Current User:", 
                   font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ModernLabel(current_user_frame, text=f"{self.current_user.username} ({self.current_user.role})",
                   font=("Arial", 14)).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # User list (admin only)
        if self.current_user.role == "admin":
            ModernLabel(parent, text="User Accounts:", 
                       font=("Arial", 16, "bold"),
                       text_color=COLORS["accent"]).grid(row=1, column=0, sticky="w", padx=10, pady=10)
            
            # Users treeview
            users_columns = ("ID", "Username", "Role")
            self.users_tree = ttk.Treeview(parent, columns=users_columns, show="headings", height=8)
            
            for col in users_columns:
                self.users_tree.heading(col, text=col)
                self.users_tree.column(col, width=100)
            
            users_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.users_tree.yview)
            self.users_tree.configure(yscrollcommand=users_scrollbar.set)
            
            self.users_tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
            users_scrollbar.grid(row=2, column=1, sticky="ns")
            
            # User management buttons
            user_buttons_frame = ModernFrame(parent)
            user_buttons_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
            user_buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
            
            add_user_btn = ModernButton(user_buttons_frame, text="➕ Add User", 
                                       command=self.add_user)
            add_user_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            change_password_btn = ModernButton(user_buttons_frame, text="🔑 Change Password", 
                                             command=self.change_password)
            change_password_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            delete_user_btn = ModernButton(user_buttons_frame, text="🗑️ Delete User", 
                                         command=self.delete_user,
                                         fg_color=COLORS["danger"])
            delete_user_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
            
            # Load users
            self.load_users()
        else:
            # For non-admin users, show limited options
            limited_frame = ModernFrame(parent)
            limited_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
            
            ModernLabel(limited_frame, text="User management features are available for administrators only.",
                       font=("Arial", 12)).pack(expand=True)
    
    def load_users(self):
        """Load users into the treeview"""
        if self.current_user.role != "admin":
            return
        
        # Clear existing data
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        try:
            cur = self.db.cursor()
            cur.execute("SELECT id, username, role FROM users ORDER BY id")
            users = cur.fetchall()
            
            for user in users:
                self.users_tree.insert("", "end", values=user)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load users: {str(e)}")
    
    def add_user(self):
        """Add new user dialog"""
        if self.current_user.role != "admin":
            messagebox.showwarning("Permission Denied", "Only administrators can add users")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New User")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        
        ModernLabel(dialog, text="Add New User", 
                   font=("Arial", 20, "bold"),
                   text_color=COLORS["accent"]).pack(pady=20)
        
        form_frame = ModernFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Form fields
        fields = [
            ("Username:", "entry"),
            ("Password:", "entry"),
            ("Role:", "combo", ["admin", "staff"])
        ]
        
        entries = {}
        row = 0
        
        for field in fields:
            ModernLabel(form_frame, text=field[0]).grid(row=row, column=0, sticky="w", padx=10, pady=10)
            
            if field[1] == "entry":
                entry = ModernEntry(form_frame, width=200, show="•" if field[0] == "Password:" else "")
                entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
                entries[field[0]] = entry
            elif field[1] == "combo":
                combo = ctk.CTkComboBox(form_frame, values=field[2], width=200)
                combo.set("staff")
                combo.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
                entries[field[0]] = combo
            
            row += 1
        
        def submit_user():
            username = entries["Username:"].get().strip()
            password = entries["Password:"].get()
            role = entries["Role:"].get()
            
            if not username or not password:
                messagebox.showerror("Error", "Username and password are required")
                return
            
            try:
                cur = self.db.cursor()
                cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           (username, password, role))
                self.db.commit()
                
                messagebox.showinfo("Success", "User added successfully!")
                self.load_users()
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to add user: {str(e)}")
        
        submit_btn = ModernButton(dialog, text="Add User", command=submit_user)
        submit_btn.pack(pady=20)
    
    def change_password(self):
        """Change password dialog"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        item = self.users_tree.item(selection[0])
        values = item['values']
        user_id = values[0]
        username = values[1]
        
        # Users can only change their own password unless they're admin
        if self.current_user.role != "admin" and user_id != self.current_user.id:
            messagebox.showwarning("Permission Denied", "You can only change your own password")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Change Password")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        
        ModernLabel(dialog, text=f"Change Password for {username}", 
                   font=("Arial", 18, "bold"),
                   text_color=COLORS["accent"]).pack(pady=20)
        
        form_frame = ModernFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ModernLabel(form_frame, text="New Password:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        password_entry = ModernEntry(form_frame, show="•", width=200)
        password_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ModernLabel(form_frame, text="Confirm Password:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        confirm_entry = ModernEntry(form_frame, show="•", width=200)
        confirm_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        def submit_password():
            new_password = password_entry.get()
            confirm_password = confirm_entry.get()
            
            if not new_password:
                messagebox.showerror("Error", "Password cannot be empty")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            try:
                cur = self.db.cursor()
                cur.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
                self.db.commit()
                
                messagebox.showinfo("Success", "Password changed successfully!")
                dialog.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to change password: {str(e)}")
        
        submit_btn = ModernButton(dialog, text="Change Password", command=submit_password)
        submit_btn.pack(pady=20)
    
    def delete_user(self):
        """Delete selected user"""
        if self.current_user.role != "admin":
            messagebox.showwarning("Permission Denied", "Only administrators can delete users")
            return
        
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        item = self.users_tree.item(selection[0])
        values = item['values']
        user_id = values[0]
        username = values[1]
        
        # Prevent deleting own account
        if user_id == self.current_user.id:
            messagebox.showwarning("Warning", "You cannot delete your own account")
            return
        
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete user '{username}'?")
        
        if result:
            try:
                cur = self.db.cursor()
                cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
                self.db.commit()
                
                messagebox.showinfo("Success", "User deleted successfully!")
                self.load_users()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
    
    def create_theme_settings_tab(self, parent):
        """Create theme settings tab"""
        parent.grid_columnconfigure(0, weight=1)
        
        ModernLabel(parent, text="Appearance Settings", 
                   font=("Arial", 16, "bold"),
                   text_color=COLORS["accent"]).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Theme selection
        theme_frame = ModernFrame(parent)
        theme_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        theme_frame.grid_columnconfigure(1, weight=1)
        
        ModernLabel(theme_frame, text="Theme Mode:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        theme_var = ctk.StringVar(value=THEME_MODE)
        theme_combo = ctk.CTkComboBox(theme_frame, 
                                     values=["dark", "light", "system"],
                                     variable=theme_var)
        theme_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Color scheme selection
        ModernLabel(theme_frame, text="Color Scheme:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        
        color_var = ctk.StringVar(value="blue")
        color_combo = ctk.CTkComboBox(theme_frame, 
                                     values=["blue", "green", "dark-blue"],
                                     variable=color_var)
        color_combo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        def apply_theme_settings():
            global THEME_MODE
            THEME_MODE = theme_var.get()
            ctk.set_appearance_mode(THEME_MODE)
            ctk.set_default_color_theme(color_var.get())
            apply_theme(self.root)
            messagebox.showinfo("Success", "Theme settings applied!")
        
        apply_btn = ModernButton(parent, text="Apply Theme Settings", 
                                command=apply_theme_settings)
        apply_btn.grid(row=2, column=0, padx=10, pady=20, sticky="ew")
    
    def create_database_tab(self, parent):
        """Create database management tab"""
        parent.grid_columnconfigure(0, weight=1)
        
        ModernLabel(parent, text="Database Management", 
                   font=("Arial", 16, "bold"),
                   text_color=COLORS["accent"]).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Database actions frame
        db_actions_frame = ModernFrame(parent)
        db_actions_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        db_actions_frame.grid_columnconfigure((0, 1), weight=1)
        
        backup_btn = ModernButton(db_actions_frame, text="💾 Backup Database", 
                                 command=self.backup_database,
                                 fg_color=COLORS["success"])
        backup_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        restore_btn = ModernButton(db_actions_frame, text="🔄 Restore Database", 
                                  command=self.restore_database,
                                  fg_color=COLORS["warning"])
        restore_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Database info
        info_frame = ModernFrame(parent)
        info_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Get database info
        try:
            cur = self.db.cursor()
            
            # Table counts
            tables = ["users", "inventory", "appointments", "sales"]
            table_counts = {}
            
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                table_counts[table] = cur.fetchone()[0]
            
            ModernLabel(info_frame, text="Database File:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            ModernLabel(info_frame, text=DB_FILE).grid(row=0, column=1, sticky="w", padx=10, pady=5)
            
            ModernLabel(info_frame, text="Users:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
            ModernLabel(info_frame, text=str(table_counts["users"])).grid(row=1, column=1, sticky="w", padx=10, pady=5)
            
            ModernLabel(info_frame, text="Inventory Items:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
            ModernLabel(info_frame, text=str(table_counts["inventory"])).grid(row=2, column=1, sticky="w", padx=10, pady=5)
            
            ModernLabel(info_frame, text="Appointments:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
            ModernLabel(info_frame, text=str(table_counts["appointments"])).grid(row=3, column=1, sticky="w", padx=10, pady=5)
            
            ModernLabel(info_frame, text="Sales:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
            ModernLabel(info_frame, text=str(table_counts["sales"])).grid(row=4, column=1, sticky="w", padx=10, pady=5)
            
        except sqlite3.Error as e:
            ModernLabel(info_frame, text=f"Error loading database info: {str(e)}").grid(row=0, column=0, columnspan=2, padx=10, pady=5)
    
    def backup_database(self):
        """Backup database to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            initialfile=f"vetclinic_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        if filename:
            try:
                # Close current connection
                self.db.close()
                
                # Copy database file
                import shutil
                shutil.copy2(DB_FILE, filename)
                
                # Reopen connection
                self.db = get_db()
                
                messagebox.showinfo("Success", f"Database backed up to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed: {str(e)}")
                # Reopen connection on error
                self.db = get_db()
    
    def restore_database(self):
        """Restore database from backup"""
        filename = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if filename:
            result = messagebox.askyesno("Confirm Restore", 
                                       "This will replace the current database. Continue?")
            
            if result:
                try:
                    # Close current connection
                    self.db.close()
                    
                    # Replace database file
                    import shutil
                    shutil.copy2(filename, DB_FILE)
                    
                    # Reopen connection
                    self.db = get_db()
                    self.inventory_manager = InventoryManager(self.db)
                    self.appointment_manager = AppointmentManager(self.db)
                    self.sales_manager = SalesManager(self.db)
                    
                    messagebox.showinfo("Success", "Database restored successfully!")
                    messagebox.showinfo("Info", "Please restart the application for changes to take effect.")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Restore failed: {str(e)}")
                    # Reopen connection on error
                    self.db = get_db()
    
    def create_security_tab(self, parent):
        """Create security settings tab"""
        parent.grid_columnconfigure(0, weight=1)
        
        ModernLabel(parent, text="Security Settings", 
                   font=("Arial", 16, "bold"),
                   text_color=COLORS["accent"]).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Security options frame
        security_frame = ModernFrame(parent)
        security_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        security_frame.grid_columnconfigure(1, weight=1)
        
        # Auto-logout setting
        ModernLabel(security_frame, text="Auto-logout (minutes):").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        logout_var = ctk.StringVar(value="30")
        logout_combo = ctk.CTkComboBox(security_frame, 
                                      values=["15", "30", "60", "120", "Never"],
                                      variable=logout_var)
        logout_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Password policy
        ModernLabel(security_frame, text="Password Policy:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        
        policy_var = ctk.StringVar(value="Medium")
        policy_combo = ctk.CTkComboBox(security_frame, 
                                      values=["Low", "Medium", "High"],
                                      variable=policy_var)
        policy_combo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        def save_security_settings():
            # In a real application, you would save these to a config file or database
            messagebox.showinfo("Success", "Security settings saved!")
        
        save_btn = ModernButton(parent, text="Save Security Settings", 
                               command=save_security_settings)
        save_btn.grid(row=2, column=0, padx=10, pady=20, sticky="ew")
        
        # Session info
        session_frame = ModernFrame(parent)
        session_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        ModernLabel(session_frame, text="Current Session", 
                   font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        ModernLabel(session_frame, text=f"User: {self.current_user.username}").grid(row=1, column=0, sticky="w", padx=10, pady=2)
        ModernLabel(session_frame, text=f"Role: {self.current_user.role}").grid(row=2, column=0, sticky="w", padx=10, pady=2)
        ModernLabel(session_frame, text=f"Login Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").grid(row=3, column=0, sticky="w", padx=10, pady=2)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()
    
    def __del__(self):
        """Cleanup when application is closed"""
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except:
                pass

# ==================== APPLICATION START ====================

if __name__ == "__main__":
    try:
        print("Starting Veterinary Clinic Management System...")
        app = VeterinaryClinicApp()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Application Error", f"The application encountered an error: {str(e)}")    