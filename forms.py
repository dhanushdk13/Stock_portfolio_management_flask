from datetime import datetime
from flask import flash, session
import pymysql

def buy_stocks(db, cursor, user_id, stock_symbol, quantity):
    # Fetch stock information to calculate total price
    cursor.execute("SELECT * FROM Stocks WHERE Symbol = %s", (stock_symbol,))
    stock_info = cursor.fetchone()
    if stock_info:
        close_price = stock_info[1]  # Assuming ClosePrice is in the 1st column

        # Calculate total price
        total_price = float(quantity) * float(close_price)

        # Update user balance
        cursor.execute("SELECT Balance FROM Users WHERE UserID = %s", (user_id,))
        user_balance = cursor.fetchone()[0]

        if user_balance >= total_price:
            new_balance = float(user_balance) - total_price

            # Update Transaction table
            cursor.execute("INSERT INTO Transactions (UserID, StockSymbol, TransactionType, Quantity, Price, TransactionDate) VALUES (%s, %s, %s, %s, %s, %s)",
                           (user_id, stock_symbol, 'Buy', quantity, total_price, datetime.now()))
            db.commit()

            # Check if the user has an existing stock profile
            cursor.execute("SELECT * FROM Profile WHERE UserID = %s AND StockSymbol = %s", (user_id, stock_symbol))
            existing_profile = cursor.fetchone()

            if existing_profile:
                # User has an existing profile for this stock, increase quantity
                existing_quantity = existing_profile[3]
                new_quantity = existing_quantity + int(quantity)
                cursor.execute("UPDATE Profile SET Quantity = %s WHERE UserID = %s AND StockSymbol = %s",
                               (new_quantity, user_id, stock_symbol))
            else:
                # User doesn't have a profile for this stock, insert a new entry
                cursor.execute("INSERT INTO Profile (UserID, StockSymbol, Quantity, PurchaseDate) VALUES (%s, %s, %s, %s)",
                               (user_id, stock_symbol, quantity, datetime.now()))
            
            cursor.execute("UPDATE Users SET Balance = %s WHERE UserID = %s", (new_balance, user_id))
            db.commit()

            # Update balance in session
            session['balance'] = str(new_balance)

            flash('Transaction completed successfully.', 'success')
        else:
            flash('Insufficient balance to make the purchase.', 'error')
    else:
        flash('Stock not found.', 'error')



def sell_stocks(db, cursor, user_id, stock_symbol, quantity):
    # Fetch stock information to calculate total price
    cursor.execute("SELECT * FROM Stocks WHERE Symbol = %s", (stock_symbol,))
    stock_info = cursor.fetchone()
    
    if stock_info:
        close_price = stock_info[1]  # Assuming ClosePrice is in the 1st column

        # Calculate total price
        total_price = float(quantity) * float(close_price)

        # Check if the user has sufficient quantity to sell
        cursor.execute("SELECT Quantity FROM Profile WHERE UserID = %s AND StockSymbol = %s", (user_id, stock_symbol))
        existing_quantity = cursor.fetchone()

        if existing_quantity:
            existing_quantity = existing_quantity[0]

            if existing_quantity >= int(quantity):
                # Update user balance
                cursor.execute("SELECT Balance FROM Users WHERE UserID = %s", (user_id,))
                user_balance = cursor.fetchone()[0]

                new_balance = float(user_balance) + total_price

                # Update Transaction table for sell
                cursor.execute("INSERT INTO Transactions (UserID, StockSymbol, TransactionType, Quantity, Price, TransactionDate) VALUES (%s, %s, %s, %s, %s, %s)",
                               (user_id, stock_symbol, 'Sell', quantity, total_price, datetime.now()))
                db.commit()

                # Update profile by decreasing quantity
                new_quantity = existing_quantity - int(quantity)
                cursor.execute("UPDATE Profile SET Quantity = %s WHERE UserID = %s AND StockSymbol = %s",
                               (new_quantity, user_id, stock_symbol))
                
                cursor.execute("UPDATE Users SET Balance = %s WHERE UserID = %s", (new_balance, user_id))
                db.commit()

                # Update balance in session
                session['balance'] = str(new_balance)

                flash('Transaction completed successfully.', 'success')
            else:
                flash('Insufficient quantity to make the sale.', 'error')
        else:
            flash('No matching stock found in your profile.', 'error')
    else:
        flash('Stock not found.', 'error')

