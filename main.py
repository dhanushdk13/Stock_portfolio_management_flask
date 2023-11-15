from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql
import secrets
from datetime import datetime,timedelta
import yfinance as yf

from forms import buy_stocks,sell_stocks,get_transaction_history,get_profile_data,update_stock_price,update_quantity_proc,remove_user


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
        user_type = user[4] 
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
@app.route('/admin',methods=['GET', 'POST'])
def admin_dashboard():
    #if not session.get('logged_in') or session.get('usertype') != 'admin':
    #    return redirect(url_for('login'))

    # Assuming you have a function to get all stocks from the database
    cursor.execute("SELECT * FROM Stocks")
    stocks = cursor.fetchall()

    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Users WHERE PremiumStatus = 'Requested'")
    premium_requests = cursor.fetchall()
    
    if request.method == 'POST':
        stock_symbol = request.form.get('stock_symbol')
        new_price = request.form.get('new_price')

        if stock_symbol and new_price:
            # Call the function to update the stock price
            update_stock_price(db, cursor, stock_symbol, new_price)

    return render_template('admin_dashboard.html', users=users, stocks=stocks, premium_requests=premium_requests)


@app.route('/admin/remove_users', methods=['POST'])
def remove_users():
    if request.method == 'POST':
        user_ids_to_remove = request.form.getlist('remove_user[]')
        
        # Remove selected users
        for user_id in user_ids_to_remove:
            remove_user(db, cursor, user_id)  # Implement the function to remove user in forms.py
        
        # Redirect back to the admin dashboard after user removal
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/update_quantity', methods=['POST'])
def update_quantity():
    if request.method == 'POST':
        quantity_multiplier = request.form.get('quantity_multiplier')

        if quantity_multiplier:
            # Call the function to update quantity using stored procedure
            update_quantity_proc(db, cursor, quantity_multiplier)
            return jsonify({'message': 'Quantity updated successfully.'})
        else:
            return jsonify({'error': 'Invalid request parameters.'})
    else:
        return jsonify({'error': 'Invalid request method.'})
    

@app.route('/request_premium', methods=['POST'])
def request_premium():
    if request.method == 'POST':
        user_id = session.get('user_id')  # Get user ID from the session
        try:
            cursor.execute("UPDATE Users SET PremiumStatus = 'Requested' WHERE UserID = %s", (user_id,))
            db.commit()
            flash('Premium subscription request sent.', 'success')
        except Exception as e:
            db.rollback()
            flash(f"Failed to send premium request. Error: {str(e)}", 'error')
        return redirect(url_for('user_dashboard'))
    
@app.route('/process_premium_request/<int:user_id>', methods=['POST'])
def process_premium_request(user_id):
    if request.method == 'POST':
        action = request.form.get('action')
        if action in ('approve', 'reject'):
            try:
                if action == 'approve':
                    cursor.execute("UPDATE Users SET PremiumStatus = 'Approved' WHERE UserID = %s", (user_id,))
                    cursor.execute("UPDATE Users SET PremiumStatus = 'Approved', UserType = 'premium' WHERE UserID = %s", (user_id,))
                else:
                    cursor.execute("UPDATE Users SET PremiumStatus = 'None' WHERE UserID = %s", (user_id,))
                db.commit()
                flash('Premium request processed successfully.', 'success')
            except Exception as e:
                db.rollback()
                flash(f"Failed to process premium request. Error: {str(e)}", 'error')
        else:
            flash('Invalid action.', 'error')
        return redirect(url_for('admin_dashboard'))
    




# User dashboard
@app.route('/user', methods=['GET', 'POST'])
def user_dashboard():
    #if not session.get('logged_in'):
    #   return redirect(url_for('login'))
    
    cursor.execute("SELECT * FROM Stocks")
    stocks = cursor.fetchall()
    
    buy_requests={}
    sell_requests={}
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cursor.execute("SELECT * FROM Stocks")
        stocks = cursor.fetchall()
        
        stock_data = []
        for stock in stocks:
            symbol = stock[0]
            close_price = float(stock[1])
            daily_change = float(stock[2])
            daily_change_percent = float(stock[3])
            high_price = float(stock[4])
            low_price = float(stock[5])
            open_price = float(stock[6])
            previous_close = float(stock[7])

            stock_dict = {
                "Symbol": symbol,
                "ClosePrice": close_price,
                "DailyChange": daily_change,
                "DailyChangePercent": daily_change_percent,
                "HighPrice": high_price,
                "LowPrice": low_price,
                "OpenPrice": open_price,
                "PreviousClose": previous_close
            }
            stock_data.append(stock_dict)
        return jsonify(stocks=stock_data)  
    

    if request.method == 'POST':
        for stock in stocks:
            stock_symbol = stock[0]
            try:
                transaction_type = request.form.get(f"transaction[{stock_symbol}]")
                quantity = request.form.get(f"quantities[{stock_symbol}]")
            except KeyError:
                    continue
            if transaction_type == f"buy:{stock_symbol}":
                if quantity != "0":
                    buy_requests[stock_symbol]=quantity
                
            elif transaction_type == f"sell:{stock_symbol}":
                if quantity != "0":
                    sell_requests[stock_symbol]=quantity
        
        # Process buy and sell requests
        for symbol, quantity in buy_requests.items():
            buy_stocks(db, cursor, session['user_id'], symbol, quantity)
        for symbol, quantity in sell_requests.items():
            sell_stocks(db, cursor, session['user_id'], symbol, quantity)
    
    return render_template('user_dashboard.html', stocks=stocks)


# Transaction History route
@app.route('/transaction-history')
def transaction_history():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    transaction_history_data = get_transaction_history(db,cursor,user_id)
    return render_template('transaction_history.html', transaction_history_data=transaction_history_data)

@app.route('/User-transactions', methods=['GET'])
def user_transactions():
    # Fetch aggregate query results
    cursor.execute("SELECT userid, COUNT(*) AS transaction_count FROM Transactions GROUP BY userid;")
    user_transaction_counts = cursor.fetchall()

    return render_template('user_transactions.html', user_transaction_counts=user_transaction_counts)

@app.route('/user_transaction_history', methods=['GET', 'POST'])
def user_transaction_history():
    if request.method == 'GET':
        # Fetch all users for the dropdown
        cursor.execute("SELECT UserID, Username FROM Users")
        users = cursor.fetchall()
        return render_template('user_transaction_history.html', users=users)

    elif request.method == 'POST':
        # Get the selected username from the form
        selected_username = request.form.get('username')

        # Fetch transaction history for the selected user
        cursor.execute("SELECT Transactions.StockSymbol, Transactions.TransactionType, Transactions.Quantity, Transactions.Price, Transactions.TransactionDate,(SELECT username FROM Users WHERE Users.userid = Transactions.userid) AS username FROM Transactions WHERE Transactions.userid IN (SELECT userid FROM Users WHERE Users.username = %s);", (selected_username,))
        user_transaction_history = cursor.fetchall()

        return render_template('user_transaction_history.html', user_transaction_history=user_transaction_history, selected_username=selected_username)


# Profile route
@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    profile_data = get_profile_data(db,cursor,user_id)
    return render_template('profile.html', profile_data=profile_data)

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
    user_type = request.form['usertype']

    # Insert user details into the "Users" table with the specified user type
    try:
        cursor.execute("INSERT INTO Users (Username, Password, Email, UserType) VALUES (%s, %s, %s, %s)", (username, password, email, user_type))
        db.commit()
        return redirect(url_for('login'))
    except:
        db.rollback()
        return "Registration failed. Please try again."
    
# Route for showing the historical chart
@app.route('/historical_chart', methods=['GET'])
def historical_chart():
    # Fetch the list of stocks from the database
    cursor.execute("SELECT symbol FROM Stocks")
    stocks = cursor.fetchall()

    return render_template('historical_chart.html', stocks=stocks)

@app.route('/fetch_historical_data', methods=['POST'])
def fetch_historical_data():
    selected_stock = request.form.get('selected_stock')
    selected_time_period = request.form.get('selected_time_period')

    try:
        # Define the time period based on user selection
        if selected_time_period == '1day':
            # Fetch intraday data for the last trading day
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            stock_data = yf.download(selected_stock, start=start_date, end=end_date, interval='1h')
        elif selected_time_period == '1month':
            stock_data = yf.download(selected_stock, period='1mo')
        elif selected_time_period == '1year':
            stock_data = yf.download(selected_stock, period='1y')
        else:
            return jsonify({"error": "Invalid time period."})

        # Extract relevant data for plotting
        historical_data = {
            date.strftime('%Y-%m-%d %H:%M:%S'): {'Close': close_price}
            for date, close_price in zip(stock_data.index, stock_data['Close'])
        }

        return jsonify(historical_data)
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return jsonify({"error": "Failed to fetch historical data."})

# Add a new route for the trackers page
@app.route('/trackers', methods=['GET', 'POST'])
def trackers():
    if request.method == 'POST':
        selected_symbol = request.form.get('selected_symbol')
        selected_tracker = request.form.get('selected_tracker')

        # Fetch the tracker value based on the selected symbol and tracker type
        cursor.execute("SELECT TrackerValue FROM trackers WHERE Symbol = %s AND TrackerName = %s",
                       (selected_symbol, selected_tracker))
        tracker_value = cursor.fetchone()

        if tracker_value:
            return render_template('tracker_result.html', symbol=selected_symbol, tracker=selected_tracker, value=tracker_value[0])
        else:
            return render_template('tracker_result.html', error="Tracker value not found.")

    # Fetch symbols from the stocks table for dropdown
    cursor.execute("SELECT Symbol FROM Stocks")
    symbols = cursor.fetchall()

    return render_template('trackers.html', symbols=symbols)

# Delete Stocks route
@app.route('/delete_stocks', methods=['GET', 'POST'])
def delete_stocks():
    if request.method == 'POST':
        selected_stocks = request.form.getlist('delete_stock[]')

        # Validate if any stock is selected
        if not selected_stocks:
            flash('Please select at least one stock to delete.', 'error')
        else:
            # Delete selected stocks from the Stocks table
            for stock_symbol in selected_stocks:
                cursor.execute("DELETE FROM Stocks WHERE Symbol = %s", (stock_symbol,))
                db.commit()

            flash('Selected stocks deleted successfully.', 'success')

    # Fetch all stocks for display
    cursor.execute("SELECT * FROM Stocks")
    stocks = cursor.fetchall()

    return render_template('delete_stocks.html', stocks=stocks)

if __name__ == '__main__':
    app.run()
