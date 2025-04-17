import sqlite3
import requests
import tkinter as tk
from PIL import Image, ImageTk  # For handling jpg and resizing
from tkinter import ttk, messagebox, Menu, PhotoImage
import hashlib
import re
import os

current_user = None  # To maintain session

# Database Setup
def setup_database():
    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            balance REAL DEFAULT 1000
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rates (
            currency TEXT PRIMARY KEY,
            rate REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_balances (
            username TEXT,
            currency TEXT,
            amount REAL DEFAULT 0,
            PRIMARY KEY (username, currency)
        )
    ''')

    conn.commit()
    conn.close()

setup_database()

# Fetch & Update Exchange Rates
def fetch_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['rates']
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch exchange rates: {e}")
        return {}

def update_exchange_rates():
    rates = fetch_exchange_rates()
    if not rates:
        return

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    for code, rate in rates.items():
        cursor.execute('REPLACE INTO exchange_rates (currency, rate) VALUES (?, ?)', (code, rate))
    conn.commit()
    conn.close()


# Password Hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Password Validation
def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


# Save Session
def save_session(username):
    with open('session.txt', 'w') as f:
        f.write(username)

# Logout Function
def logout_user(trading_window):
    global current_user
    current_user = None
    clear_session()
    trading_window.destroy()
    root.deiconify()  # Show login again

# Load Session
def load_session():
    global current_user
    if os.path.exists('session.txt'):
        with open('session.txt', 'r') as f:
            username = f.read().strip()
            if username:
                current_user = username
                return True
    return False


# Clear Session
def clear_session():
    if os.path.exists('session.txt'):
        os.remove('session.txt')


# Register User
def register_user():
    username = entry_username.get()
    password = entry_password.get()
    if not username or not password:
        messagebox.showerror("Error", "All fields are required")
        return

    if not is_valid_password(password):
        messagebox.showerror("Error",
                             "Password must be at least 8 characters long,\ncontain uppercase, lowercase, number, and special character.")
        return

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        messagebox.showinfo("Success", "Registration Successful!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists")
    finally:
        conn.close()


# Login User
def login_user():
    global current_user
    username = entry_username.get()
    password = entry_password.get()
    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    hashed_password = hash_password(password)

    if user and user[0] == hashed_password:
        current_user = username
        save_session(username)
        messagebox.showinfo("Success", "Login Successful!")
        root.withdraw()  # Hide login
        open_trading_screen()
    else:
        messagebox.showerror("Error", "Invalid credentials")
    conn.close()


# Update Balance Label
def update_balance_label():
    global current_user
    if not current_user:
        return

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE username = ?', (current_user,))
    balance = cursor.fetchone()

    if balance:
        balance_label.config(text=f"Balance: {balance[0]:.2f} USD")
    
    conn.close()

# Register User
'''def register_user():
    username = entry_username.get()
    password = entry_password.get()
    if not username or not password:
        messagebox.showerror("Error", "All fields are required")
        return

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        messagebox.showinfo("Success", "Registration Successful!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists")
    finally:
        conn.close()

# Login User
def login_user():
    global current_user
    username = entry_username.get()
    password = entry_password.get()
    
    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if user and check_password_hash(user[0], password):
        current_user = username  
        messagebox.showinfo("Success", "Login Successful!")

        entry_username.config(state='disabled')
        entry_password.config(state='disabled')
        root.withdraw()

        open_trading_screen()  
    else:
        messagebox.showerror("Error", "Invalid credentials")
'''
# Buy Currency
def buy_currency():
    global current_user
    if not current_user:
        messagebox.showerror("Error", "You must be logged in to trade.")
        return

    currency = currency_combobox.get()
    amount=entry_amount.get()
    try:
        amount = float(entry_amount.get())
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Enter a valid positive number")
        return

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()

    cursor.execute('SELECT rate FROM exchange_rates WHERE currency = ?', (currency,))
    rate = cursor.fetchone()

    if not rate:
        messagebox.showerror("Error", "Invalid currency selected")
        conn.close()
        return

    rate = rate[0]
    cost = amount / rate

    cursor.execute('SELECT balance FROM users WHERE username = ?', (current_user,))
    balance = cursor.fetchone()[0]

    if not balance or balance < cost:
        messagebox.showerror("Error", "Insufficient balance")
        conn.close()
        return

    new_balance = balance - cost

    cursor.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, current_user))

    cursor.execute('''
        INSERT INTO user_balances (username, currency, amount)
        VALUES (?, ?, ?)
        ON CONFLICT(username, currency) DO UPDATE SET amount = amount + excluded.amount
    ''', (current_user, currency, amount))

    conn.commit()
    conn.close()

    messagebox.showinfo("Success", f"Bought {amount} {currency} for {cost:.2f} USD")
    update_balance_label()


# Sell Currency
def sell_currency():
    currency = currency_combobox.get()
    amount = entry_amount.get()

    if not amount.isdigit():
        messagebox.showerror("Error", "Enter a valid amount")
        return

    amount = float(amount)

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()

    cursor.execute('SELECT rate FROM exchange_rates WHERE currency = ?', (currency,))
    rate = cursor.fetchone()[0]

    earnings = amount / rate  # Convert currency to USD

    cursor.execute('SELECT amount FROM user_balances WHERE username = ? AND currency = ?', (current_user, currency))
    currency_balance = cursor.fetchone()

    if not currency_balance or currency_balance[0] < amount:
        messagebox.showerror("Error", "Insufficient currency balance")
        return

    cursor.execute('UPDATE user_balances SET amount = amount - ? WHERE username = ? AND currency = ?',
                   (amount, current_user, currency))

    cursor.execute('SELECT balance FROM users WHERE username = ?', (current_user,))
    usd_balance = cursor.fetchone()[0]
    new_usd_balance = usd_balance + earnings
    cursor.execute('UPDATE users SET balance = ? WHERE username = ?', (new_usd_balance, current_user))

    conn.commit()
    conn.close()

    messagebox.showinfo("Success", f"Sold {amount} {currency} for {earnings:.2f} USD")
    update_balance_label()


def currency_balance():

    currency_window = tk.Toplevel(root)
    currency_window.title("Currency Balance")
    currency_window.state("zoomed")

    container = tk.Frame(currency_window)
    canvas = tk.Canvas(container, height=500)  # Set height for scrolling
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()

    cursor.execute('SELECT currency,amount FROM user_balances WHERE username = ?', (current_user,))
    result = cursor.fetchall()

    conn.close()

    for currency, amount in result:
        tk.Label(scrollable_frame, text=f"{currency}: {amount:.2f}", font=("Arial", 12)).pack(pady=2)

    def _on_touch_scroll(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    currency_window.bind("<B1-Motion>", _on_touch_scroll)



''' if result:
        currency_balances = result[0]
    else:
        currency_balances = 0.0  # Default to 0 if no balance is found

    # Create and update label properly
    currency_balance_label = tk.Label(currency_window, text=f"Currency Balance: {currency_balances:.2f} {currency}",
                                      font=("Arial", 14), fg="green")
    currency_balance_label.pack(pady=10)
'''
def show_exchange_rates():
    update_exchange_rates()

    rates_window = tk.Toplevel(root)
    rates_window.title("Exchange Rates")
    rates_window.geometry("900x2500")  # Adjust size for mobile view
    rates_window.configure(bg='#000000')

    # Scrollable Frame Setup
    container = tk.Frame(rates_window)
    canvas = tk.Canvas(container, height=500)  # Set height for scrolling
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Fetch and Display Exchange Rates
    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM exchange_rates')
    rates = cursor.fetchall()
    conn.close()

    for currency, rate in rates:
        tk.Label(scrollable_frame, text=f"{currency}: {rate:.2f}", font=("Arial", 12)).pack(pady=2)

    # Enable touch scrolling
    def _on_touch_scroll(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    rates_window.bind("<B1-Motion>", _on_touch_scroll)  # Scroll using touch gestures


# Open Trading Window
def open_trading_screen():
    global balance_label, currency_combobox, entry_amount

    trading_window = tk.Toplevel(root)
    trading_window.title("Forex Trading")
    trading_window.state("zoomed")
    trading_window.configure(bg='#000000')

    #update_exchange_rates()

    balance_label = tk.Label(trading_window, text="Balance: 1000 USD", font=("Arial", 14), fg="#ffffff",bg="#000000")
    balance_label.pack(pady=10)

    tk.Label(trading_window, text="Select Currency:", font=("Arial", 12),fg="#ffffff",bg="#000000").pack()
    currency_combobox = ttk.Combobox(trading_window)
    currency_combobox.pack()

    conn = sqlite3.connect('forex_trading.db')
    cursor = conn.cursor()
    cursor.execute("SELECT currency FROM exchange_rates")
    currencies = [row[0] for row in cursor.fetchall()]
    conn.close()
    currency_combobox['values'] = currencies

    tk.Label(trading_window, text="Enter Amount:", font=("Arial", 12),fg="#ffffff",bg="#000000").pack()
    entry_amount = tk.Entry(trading_window)
    entry_amount.pack(pady=5)

    tk.Button(trading_window, text="Buy", bg="green", fg="white", font=("Arial", 12), command=buy_currency).pack(pady=5)
    tk.Button(trading_window, text="Sell", bg="red", fg="white", font=("Arial", 12), command=sell_currency).pack(pady=5)
    #tk.Button(trading_window, text="exchange rates", bg="red", fg="white", font=("Arial", 12), command=show_exchange_rates).pack(pady=5)
    logout_btn=tk.Button(trading_window, text='Logout', bg='orange', fg='white',command=lambda: logout_user(trading_window))
    logout_btn.place(relx=0.97, rely=0.02, anchor="ne")
    #tk.Button(trading_window, text="currency balance", bg="blue", fg="white", font=("Arial", 12),command=currency_balance).pack(pady=5)

    update_balance_label()

    menu_bar = Menu(root)

    # File Menu
    file_menu = Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="New")
    file_menu.add_command(label="Open")
    file_menu.add_command(label="Save")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)

    # Trade Menu
    trade_menu = Menu(menu_bar, tearoff=0)
    trade_menu.add_command(label="Refresh Trading Screen", command=open_trading_screen)
    trade_menu.add_command(label="Order History")

    # Market Menu
    market_menu = Menu(menu_bar, tearoff=0)
    market_menu.add_command(label="Currency Balance", command=currency_balance)
    market_menu.add_command(label="Exchange Rates", command=show_exchange_rates)

    # Help Menu
    help_menu = Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="User Guide")
    help_menu.add_command(label="About")

    # Adding menus to the menu bar
    menu_bar.add_cascade(label="File", menu=file_menu)
    menu_bar.add_cascade(label="Trade", menu=trade_menu)
    menu_bar.add_cascade(label="Market", menu=market_menu)
    menu_bar.add_cascade(label="Help", menu=help_menu)

    # Attach the menu bar to the root window
    trading_window.config(menu=menu_bar)


# Function to update the background image on resize
def resize_bg(event):
    global bg_photo
    new_width = root.winfo_width()
    new_height = root.winfo_height()
    resized_image = bg_image.resize((new_width, new_height))
    bg_photo = ImageTk.PhotoImage(resized_image)
    canvas.itemconfig(bg_image_id, image=bg_photo)

# Create the main window
root = tk.Tk()
root.title("Forex Trading System")
root.state('zoomed') # Open in fullscreen mode

# Load the background image
bg_image = Image.open("background4.png")  # Replace with your image file
bg_photo = ImageTk.PhotoImage(bg_image)

# Create a canvas to hold the background
canvas = tk.Canvas(root)
canvas.pack(fill="both", expand=True)

# Set the background image
bg_image_id = canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# Bind the resize event to update the background
root.bind("<Configure>", resize_bg)

# Function to place widgets proportionally
def place_widget(widget, relx, rely):
    widget.place(relx=relx, rely=rely, anchor="center")

def add_placeholder(entry, text):
    entry.insert(0, text)
    entry.config(fg="gray")

    def on_focus_in(event):
        if entry.get() == text:
            entry.delete(0, "end")
            entry.config(fg="black")

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, text)
            entry.config(fg="gray")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


# Add labels and input fields
label_title = tk.Label(root, text="Z Trade", font=('arial', 34, 'bold'), bg='#000D2F', fg='#ffffff')
place_widget(label_title, 0.5, 0.23)  # Centered horizontally

#label_user = tk.Label(root, text="Username:", font=('arial', 12, 'bold'), bg='#000000', fg='#ffffff')
#place_widget(label_user, 0.4, 0.38)
entry_username = tk.Entry(root, width=15,font=("Arial", 14))
place_widget(entry_username, 0.5, 0.35)
add_placeholder(entry_username,"username")

#label_pass = tk.Label(root, text="Password:", font=('arial', 12, 'bold'), bg='#000000', fg='#ffffff')
#place_widget(label_pass, 0.4, 0.44)
entry_password = tk.Entry(root,show="*", width=15,font=("Arial", 14))
place_widget(entry_password, 0.5, 0.42)
add_placeholder(entry_password,"password")

# Password visibility toggle
def toggle_password():
    if entry_password.cget('show') == '*':
        entry_password.config(show='')
        toggle_btn.config(text="Hide")
    else:
        entry_password.config(show='*')
        toggle_btn.config(text="Show")

toggle_btn = tk.Button(root, text="Show", command=toggle_password, width=10)
place_widget(toggle_btn, 0.6, 0.42)

# Auto-login if session exists
if load_session():
    root.withdraw()
    open_trading_screen()

# Login & Register buttons
btn_register = tk.Button(root, text="Register", width=15, command=register_user,fg="#000000",bg="#FCDBC9")
place_widget(btn_register, 0.50, 0.55)

btn_login = tk.Button(root, text="Login", width=15, command=login_user,fg="#000000",bg="#FCDBC9")
place_widget(btn_login, 0.5, 0.50)

root.mainloop()
