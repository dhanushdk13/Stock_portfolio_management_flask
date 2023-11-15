import yfinance as yf
import ta
import mysql.connector
import schedule
import time
import pandas as pd

def fetch_yahoo_finance_indicators(symbol, start_date, end_date, interval='1d', rsi_time_period=14, macd_fast=12, macd_slow=26, macd_signal=9, adx_time_period=14):
    # Fetch historical stock data from Yahoo Finance
    data = yf.download(symbol, start=start_date, end=end_date, interval=interval)

    # Calculate RSI using ta library
    data['rsi'] = ta.momentum.RSIIndicator(close=data['Close'], window=rsi_time_period, fillna=True).rsi()

    # Calculate MACD using ta library
    data['macd'] = ta.trend.MACD(close=data['Close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal).macd()

    # Calculate ADX using ta library
    data['adx'] = ta.trend.ADXIndicator(high=data['High'], low=data['Low'], close=data['Close'], window=adx_time_period, fillna=True).adx()

    return data

def insert_into_trackers(connection, symbol, tracker_name, tracker_value):
    # Insert data into the trackers table
    query = f"INSERT INTO trackers (Symbol, TrackerName, TrackerValue) VALUES ('{symbol}', '{tracker_name}', {tracker_value})"
    with connection.cursor() as cursor:
        cursor.execute(query)
    connection.commit()

def process_symbol(symbol, start_date, end_date, connection):
    # Get the latest RSI, MACD, and ADX values for a symbol
    data = fetch_yahoo_finance_indicators(symbol, start_date, end_date)
    
    if not data.empty:
        latest_rsi = data['rsi'].iloc[-1]
        latest_macd = data['macd'].iloc[-1]
        latest_adx = data['adx'].iloc[-1]

        # Insert the latest values into the trackers table
        insert_into_trackers(connection, symbol, 'RSI', latest_rsi)
        insert_into_trackers(connection, symbol, 'MACD', latest_macd)
        insert_into_trackers(connection, symbol, 'ADX', latest_adx)

        print(f"Updated trackers table with live values for {symbol}")
    else:
        print(f"No data available for {symbol}")

def fetch_and_insert_data(connection, start_date, end_date):
    # Truncate the trackers table before inserting new data
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE trackers")
        connection.commit()

    # Fetch all symbols from the stocks table
    query_symbols = "SELECT DISTINCT Symbol FROM stocks"
    symbols_df = pd.read_sql_query(query_symbols, connection)

    if not symbols_df.empty:
        # Process each symbol and insert into trackers table
        for _, symbol_row in symbols_df.iterrows():
            symbol = symbol_row['Symbol']
            process_symbol(symbol, start_date, end_date, connection)
    else:
        print("No symbols found in the stocks table.")

def job():
    # Your existing database connection details here...
    db_config = {
        'user': 'root',
        'password': '1234',
        'host': 'localhost',
        'database': 'Stock_Management',
    }

    # Create a MySQL connection
    connection = mysql.connector.connect(
        user=db_config['user'],
        password=db_config['password'],
        host=db_config['host'],
        database=db_config['database']
    )

    # Fetch and insert data into the trackers table
    fetch_and_insert_data(connection, '2023-01-01', '2023-12-31')

    # Close the MySQL connection
    connection.close()

# Schedule the job to run every 30 seconds
schedule.every(30).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

# import yfinance as yf
# import pandas as pd
# import ta
# import mysql.connector





# # tracking.py

# import mysql.connector

# def get_stock_symbols():
#     # Your database connection details
#     db_config = {
#         'user': 'root',
#         'password': 'sql123',
#         'host': 'localhost',
#         'database': 'stock_management_system',
#     }

#     # Initialize an empty list to store stock symbols
#     stock_symbols = []

#     # Connect to the database
#     with mysql.connector.connect(**db_config) as connection:
#         # Create a cursor
#         with connection.cursor() as cursor:
#             # Fetch all stock symbols from the stocks table
#             cursor.execute("SELECT DISTINCT Symbol FROM stocks")
#             result = cursor.fetchall()

#             # Extract stock symbols from the result and add them to the list
#             stock_symbols = [row[0] for row in result]

#     return stock_symbols





# def fetch_yahoo_finance_indicators(symbol, start_date, end_date, interval='1d', rsi_time_period=14, macd_fast=12, macd_slow=26, macd_signal=9, adx_time_period=14):
#     # Fetch historical stock data from Yahoo Finance
#     data = yf.download(symbol, start=start_date, end=end_date, interval=interval)

#     # Calculate RSI using ta library
#     data['rsi'] = ta.momentum.RSIIndicator(close=data['Close'], window=rsi_time_period, fillna=True).rsi()

#     # Calculate MACD using ta library
#     data['macd'] = ta.trend.MACD(close=data['Close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal).macd()

#     # Calculate ADX using ta library
#     data['adx'] = ta.trend.ADXIndicator(high=data['High'], low=data['Low'], close=data['Close'], window=adx_time_period, fillna=True).adx()

#     return data

# def get_latest_indicators_for_symbols(symbols, start_date, end_date):
#     indicators_data = []

#     for symbol in symbols:
#         data = fetch_yahoo_finance_indicators(symbol, start_date, end_date)
#         if not data.empty:
#             latest_rsi = data['rsi'].iloc[-1]
#             latest_macd = data['macd'].iloc[-1]
#             latest_adx = data['adx'].iloc[-1]

#             indicators_data.append({
#                 'symbol': symbol,
#                 'rsi': latest_rsi,
#                 'macd': latest_macd,
#                 'adx': latest_adx
#             })

#     return indicators_data

# # Your database connection details
# db_config = {
#     'user': 'root',
#     'password': 'sql123',
#     'host': 'localhost',
#     'database': 'stock_management_system',
# }

# # Fetch stock symbols from the stocks table
# stock_symbols = get_stock_symbols()

# # Get the latest RSI, MACD, and ADX values for each stock
# indicators_data = get_latest_indicators_for_symbols(stock_symbols, '2023-01-01', '2023-12-31')

# # Connect to the database
# with mysql.connector.connect(**db_config) as connection:
#     # Insert the latest values into the trackers table
#     for data in indicators_data:
#         symbol = data['symbol']
#         rsi_value = data['rsi']
#         macd_value = data['macd']
#         adx_value = data['adx']

#         # Insert data into the trackers table
#         query = f"INSERT INTO trackers (Symbol, TrackerName, TrackerValue) VALUES ('{symbol}', 'RSI', {rsi_value})"
#         with connection.cursor() as cursor:
#             cursor.execute(query)

#         query = f"INSERT INTO trackers (Symbol, TrackerName, TrackerValue) VALUES ('{symbol}', 'MACD', {macd_value})"
#         with connection.cursor() as cursor:
#             cursor.execute(query)

#         query = f"INSERT INTO trackers (Symbol, TrackerName, TrackerValue) VALUES ('{symbol}', 'ADX', {adx_value})"
#         with connection.cursor() as cursor:
#             cursor.execute(query)

#     # Commit the transactions
#     connection.commit()
