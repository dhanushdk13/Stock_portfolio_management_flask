from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql
import secrets
from datetime import datetime
from forms import buy_stocks,sell_stocks


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configure MySQL connection
db = pymysql.connect(host="localhost", user="root", password="1234", database="Stock_Management")
cursor = db.cursor()

# Home page - Login
@app.route('/')
def login():
    return render_template('login.html')

# Login route
@app.route('/login', methods=['POST'])
def login_user():
    username = request.form['username']
    password = request.form['password']
    
    # Check if the user exists in the user table
    cursor.execute("SELECT * FROM Users WHERE Username = %s AND Password = %s", (username, password))
    user = cursor.fetchone()
    
    if user:
        user_type = user[4]  # Assuming UserType is in the 4th column
        session['logged_in'] = True
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['usertype'] = user[4]
        session['balance'] = str(user[5])

        if user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        flash('Invalid username or password. Please try again.', 'error')
        return redirect(url_for('login'))


# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    return render_template('admin_dashboard.html', users=users)
# User dashboard
# ... (Your existing code)

@app.route('/user', methods=['GET', 'POST'])
def user_dashboard():
    #if not session.get('logged_in'):
    #   return redirect(url_for('login'))
    
    cursor.execute("SELECT * FROM Stocks")
    stocks = cursor.fetchall()
    
    buy_requests={}
    sell_requests={}

    if request.method == 'POST':
        for stock in stocks:
            stock_symbol = stock[0]
            try:
                transaction_type = request.form.get(f"transaction[{stock_symbol}]")
                quantity = request.form.get(f"quantities[{stock_symbol}]")
            except KeyError:
                    continue
            if quantity==0:
                continue
            if transaction_type == f"buy:{stock_symbol}":
                buy_requests[stock_symbol]=quantity
                
            elif transaction_type == f"sell:{stock_symbol}":
                sell_requests[stock_symbol]=quantity
        
        # Process buy and sell requests
        for symbol, quantity in buy_requests.items():
            buy_stocks(db, cursor, session['user_id'], symbol, quantity)
        for symbol, quantity in sell_requests.items():
            sell_stocks(db, cursor, session['user_id'], symbol, quantity)

    return render_template('user_dashboard.html', stocks=stocks)

# Registration page
@app.route('/register')
def register():
    return render_template('register.html')

# Registration route
@app.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    user_type = 'normal'

    # Insert user details into the "Users" table with the specified user type
    try:
        cursor.execute("INSERT INTO Users (Username, Password, Email, UserType) VALUES (%s, %s, %s, %s)", (username, password, email, user_type))
        db.commit()
        return redirect(url_for('login'))
    except:
        db.rollback()
        return "Registration failed. Please try again."

if __name__ == '__main__':
    app.run()
