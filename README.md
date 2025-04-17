
# Foreign Trading System

A user-friendly desktop application for simulating foreign currency trading, built with **Python**, **CustomTkinter**, and **SQLite**. This project allows users to register, log in securely, view real-time exchange rates, and perform currency buy/sell transactions.

---

## Features

- **User Authentication**
  - Secure registration and login system
  - Password hashing using **PBKDF2 HMAC SHA-256** with random salt
  - Strong password validation (min 8 characters, uppercase, lowercase, number, special character)

- **Trading Dashboard**
  - View live exchange rates in a scrollable interface
  - Buy and sell foreign currencies
  - Auto-update of balances after transactions

- **Database Integration**
  - SQLite backend with tables: `Users`, `ExchangeRates`, `Currencies`, `Transactions`, and `UserBalances`
  - Session file for persistent login without re-login

- **User Interface**
  - Built with **CustomTkinter** for a modern look
  - Rounded entry boxes and password visibility toggle
  - Full-screen trading window (optimized for PC)

---

## Screenshot

![Trading Dashboard](screenshots/dashboard.png)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/foreign-trading-system.git
   cd foreign-trading-system

2. ***Install dependencies***
   ```bash
   pip install customtkinter


3. ***Run the application***
   ```bash
   python main.py

---
## License

This project is licensed under the MIT License.


---

## Author

Ajith - GitHub

---


