import psycopg2
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# PostgreSQL connection details
DB_NAME = "Expense-Tracker"
DB_USER = "postgres"
DB_PASSWORD = "pakshal1234"
DB_HOST = "localhost"  # Change if using a remote server
DB_PORT = "5432"

def get_db_connection():
    """Returns a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
def setup_database():
    """Creates the expenses table if it does not exist in PostgreSQL."""
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

setup_database()  # Initialize the database

def add_expense():
    """Adds an expense to the PostgreSQL database."""
    category = category_entry.get()
    amount = amount_entry.get()
    
    if not category or not amount:
        messagebox.showerror("Error", "Please enter category and amount!")
        return
    
    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number!")
        return

    date = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (date, category, amount) VALUES (%s, %s, %s)", (date, category, amount))
    conn.commit()
    cursor.close()
    conn.close()

    category_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)

    messagebox.showinfo("Success", "Expense added!")
    show_expenses()

def show_expenses():
    """Displays all expenses in the GUI table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, category, amount FROM expenses ORDER BY date DESC")
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in tree.get_children():
        tree.delete(row)

    for expense in expenses:
        tree.insert("", tk.END, values=expense)

def generate_report():
    """Displays a monthly spending report."""
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM expenses", conn)
    conn.close()

    if df.empty:
        messagebox.showinfo("Report", "No expenses recorded yet!")
        return

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    current_month = datetime.now().strftime("%Y-%m")
    monthly_data = df[df["month"].astype(str) == current_month].groupby("category")["amount"].sum()

    if monthly_data.empty:
        messagebox.showinfo("Report", "No expenses recorded for this month!")
        return

    report_text = "\n".join([f"{cat}: ₹{amt:.2f}" for cat, amt in monthly_data.items()])
    messagebox.showinfo("Monthly Report", report_text)

def visualize_expenses():
    """Creates a pie chart of expenses by category."""
    conn = get_db_connection()
    df = pd.read_sql("SELECT category, amount FROM expenses", conn)
    conn.close()

    if df.empty:
        messagebox.showinfo("Chart", "No expenses recorded yet!")
        return

    summary = df.groupby("category")["amount"].sum()

    plt.figure(figsize=(7, 7))
    plt.pie(summary, labels=summary.index, autopct="%1.1f%%", startangle=140)
    plt.title("Expense Distribution")
    plt.show()

# GUI Setup
root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("500x600")

# Input Fields
tk.Label(root, text="Category:").pack()
category_entry = tk.Entry(root)
category_entry.pack()

tk.Label(root, text="Amount:").pack()
amount_entry = tk.Entry(root)
amount_entry.pack()

tk.Button(root, text="Add Expense", command=add_expense).pack(pady=5)
tk.Button(root, text="Show Expenses", command=show_expenses).pack()
tk.Button(root, text="Generate Monthly Report", command=generate_report).pack()
tk.Button(root, text="Visualize Expenses", command=visualize_expenses).pack()

# Expense Table
columns = ("Date", "Category", "Amount")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=100)
tree.pack(pady=10)

show_expenses()

root.mainloop()
