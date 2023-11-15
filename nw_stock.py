import finnhub
import pymysql
from datetime import datetime
import time

# Initialize the Finnhub client
finnhub_client = finnhub.Client(api_key="cl4ssi9r01qrlanq468gcl4ssi9r01qrlanq4690")

# List of stock symbols
stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA']

# Establish a connection to the MySQL database
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="1234",
    database="Stock_Management"
)
cursor = conn.cursor()

# Specify the update interval in seconds (e.g., update every 5 minutes)
update_interval = 30  # 5 minutes

while True:
    for symbol in stocks:
        quote_data = finnhub_client.quote(symbol)
        if "t" in quote_data:
            timestamp = datetime.utcfromtimestamp(quote_data["t"]).strftime("%Y-%m-%d %H:%M:%S")

            update_query = """
            UPDATE Stocks 
            SET ClosePrice = %s, DailyChange = %s, DailyChangePercent = %s,
                HighPrice = %s, LowPrice = %s, OpenPrice = %s, PreviousClose = %s, Timestamp = %s
            WHERE Symbol = %s
            """
            cursor.execute(update_query, (
                quote_data["c"],
                quote_data["d"],
                quote_data["dp"],
                quote_data["h"],
                quote_data["l"],
                quote_data["o"],
                quote_data["pc"],
                timestamp,
                symbol
            ))
            conn.commit()
    
    print("Table updated.")

    # Wait for the specified update interval before the next update
    time.sleep(update_interval)

# Close the cursor and database connection (this code will not reach this point in the loop)
cursor.close()
conn.close()
