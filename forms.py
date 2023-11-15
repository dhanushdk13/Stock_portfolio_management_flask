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

            '''if existing_profile:
                # User has an existing profile for this stock, increase quantity
                existing_quantity = existing_profile[3]
                new_quantity = existing_quantity + int(quantity)
                cursor.execute("UPDATE Profile SET Quantity = %s WHERE UserID = %s AND StockSymbol = %s",
                               (new_quantity, user_id, stock_symbol))
            else:
                # User doesn't have a profile for this stock, insert a new entry
                cursor.execute("INSERT INTO Profile (UserID, StockSymbol, Quantity, PurchaseDate) VALUES (%s, %s, %s, %s)",
                               (user_id, stock_symbol, quantity, datetime.now()))'''
            
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
                #cursor.execute("UPDATE Profile SET Quantity = %s WHERE UserID = %s AND StockSymbol = %s",
                 #              (new_quantity, user_id, stock_symbol))
                
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
    

def update_stock_price(db, cursor, stock_symbol, new_price):
    try:
        # Update the stock price in the Stocks table
        cursor.execute("UPDATE Stocks SET ClosePrice = %s WHERE Symbol = %s", (new_price, stock_symbol))
        db.commit()
        flash(f'Stock price for {stock_symbol} updated successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error updating stock price for {stock_symbol}: {str(e)}', 'error')
    
        
def get_transaction_history(db,cursor,user_id):
    cursor.execute("SELECT * FROM Transactions WHERE UserID = %s", (user_id,))
    transaction_history_data = cursor.fetchall()
    return transaction_history_data

def get_profile_data(db,cursor,user_id):
    cursor.execute("SELECT StockSymbol, Quantity, PurchaseDate FROM Profile WHERE UserID = %s", (user_id,))
    profile_data = cursor.fetchall()
    return profile_data


def update_quantity_proc(db, cursor, multiplier):
    try:
        # Execute the stored procedure
        cursor.callproc('update_quantity_proc', [multiplier])
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error updating quantity: {str(e)}")

def remove_user(db, cursor, user_id):
    try:
        # Perform the deletion
        cursor.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
        db.commit()
    except Exception as e:
        # Handle any errors, for example, log the error
        print(f"Error removing user: {e}")
        db.rollback()
