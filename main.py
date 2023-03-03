import requests
import pprint
import csv
import smtplib
import os
from datetime import datetime, timedelta
from tkinter import *
from twilio.rest import Client
from requests.auth import HTTPBasicAuth
from tkinter import messagebox

MY_EMAIL = "durubum@yahoo.com"
PASSWORD = os.getenv("PASSWORD")
VIRTUAL_TWILIO_NUMBER = ""
VERIFIED_NUMBER = ""
PASS = os.getenv("PASS")
BASIC = HTTPBasicAuth('golddust588', PASS)

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
COIN_ENDPOINT = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
SHEETY_ENDPOINT = os.getenv("SHEETY_ENDPOINT")

ALPHA_VANTAGE_API = os.getenv("ALPHA_VANTAGE_API")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWILIO_SID = ""
TWILIO_AUTH_TOKEN = ""

# ---------------------------- STOCKS TO BE IN UI ------------------------------------------------------------------ #
# From https://www.nasdaq.com/market-activity/stocks/screener downloaded csv of Mega ($200>B) market cap stock
# information at February 2023.

with open("top_stocks.csv") as file:
    data = csv.reader(file)
    stock_symbols = []
    for row in data:
        if row[0] != "Symbol":
            stock_symbols.append(row[0])
    # print(stock_symbols)

with open("top_stocks.csv") as file:
    data = csv.reader(file)
    full_stock_names = []
    for row in data:
        if row[1] != "Name":
            full_stock_names.append(row[1])
    # print(full_stock_names)

# ---------------------------- COINS TO BE IN UI ------------------------------------------------------------------- #

# Get top crypto by market cap information
parameters = {
    "start": "1",
    "limit": "15",
    "convert": "USD",
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
}

response = requests.get(url=COIN_ENDPOINT, params=parameters, headers=headers)
response.raise_for_status()

coin_data = response.json()
# pprint.pprint(coin_data)

# Received coin_data is not sorted by the name of the Coin, but by the current market cap, so I decided to
# make it myself.

# This filters top 15 coin names from www.Coinbase.com based on Market Cap.
coin_symbols = []
for n in range(15):
    coin_symbols.append(coin_data["data"][n]["name"])

# ---------------------------- UI SETUP -------------------------------------------------------------------------- #

window = Tk()
window.title("Stock-Coin market news alert app")
window.config(padx=10, pady=10)

canvas = Canvas(width=600, height=304, highlightthickness=0)
lock_img = PhotoImage(file="logo.png")
canvas.create_image(300, 152, image=lock_img)
first_text = canvas.create_text(400, 20, text="1. Choose a stock or a crypto you are interested in",
                                fill="green", font=("Arial", 11))
second_text = canvas.create_text(400, 60, text="2. Select the percentage of daily price\n change to be alerted",
                                 fill="green", font=("Arial", 11))
third_text = canvas.create_text(150, 260, text="3. Enter your email to subscribe!",
                                fill="green", font=("Arial", 11))
canvas.grid(column=0, row=0, columnspan=3)

# Labels:

stock_label = Label(text="Choose a stock:")
stock_label.grid(column=0, row=1)

crypto_label = Label(text="Choose a crypto:")
crypto_label.grid(column=0, row=2)

percentage_label = Label(text="What percentage of price jump/drop you are interested in?:")
percentage_label.grid(column=0, row=3)

email_label = Label(text="Your email:")
email_label.grid(column=0, row=4)

subscribe_label = Label(text="You can subscribe to one stock/crypto\n price volatility alert at a time",
                        font=("Arial", 10, "bold"))
subscribe_label.grid(column=0, row=5)


# Spinbox

def spinbox_used():
    # gets the current value in spinbox.
    return spinbox.get()


spinbox = Spinbox(from_=0, to=15, width=7, command=spinbox_used)
spinbox.grid(column=1, row=3)

# Entries:

email_entry = Entry(width=42)
email_entry.grid(column=1, row=4, columnspan=2)


def get_email():
    return email_entry.get()


# Listbox with a scrollbar

selected_stock = None  # global variable
selected_crypto = None  # global variable


def on_stock_listbox_click(event):
    # Gets current selection from stock listbox
    global selected_stock
    global selected_crypto
    selected_stock = event.widget.get(event.widget.curselection())
    selected_crypto = None
    print(f"Selected item: {selected_stock}")


stock_scrollbar = Scrollbar()
stock_listbox = Listbox(height=6, yscrollcommand=stock_scrollbar.set)
stock_listbox.grid(column=1, row=1)
for item in stock_symbols:
    stock_listbox.insert(stock_symbols.index(item), item)
stock_listbox.selection_clear(0, END)
stock_listbox.bind("<<ListboxSelect>>", on_stock_listbox_click)
stock_scrollbar.config(command=stock_listbox.yview)
stock_scrollbar.grid(column=2, row=1)


def on_crypto_listbox_click(event):
    # Gets current selection from crypto listbox
    global selected_crypto
    global selected_stock
    selected_crypto = event.widget.get(event.widget.curselection())
    selected_stock = None
    print(f"Selected item: {selected_crypto}")


crypto_scrollbar = Scrollbar()
crypto_listbox = Listbox(height=6, yscrollcommand=crypto_scrollbar.set)
crypto_listbox.grid(column=1, row=2)
for item in coin_symbols:
    crypto_listbox.insert(coin_symbols.index(item), item)
crypto_listbox.selection_clear(0, END)
crypto_listbox.bind("<<ListboxSelect>>", on_crypto_listbox_click)
crypto_scrollbar.config(command=crypto_listbox.yview)
crypto_scrollbar.grid(column=2, row=2)


# ---------------------------- SHEETY DATABASE UPLOAD SUBSCRIPTIONS FROM UI ----------------------------------------- #

def subscribe():
    global BASIC
    if len(get_email()) == 0:
        messagebox.showinfo(title="Error", message="Please enter your email.")
    elif float(spinbox_used()) == 0.00:
        messagebox.showinfo(title="Error", message="Please choose price volatility you want to follow.")
    elif float(spinbox_used()) < 0:
        messagebox.showinfo(title="Error", message="Can not be negative volatility.")
    elif selected_stock is None and selected_crypto is None:
        messagebox.showinfo(title="Error", message="Please choose one stock or crypto currency to follow.")
    elif selected_crypto is None:
        is_ok_stock = messagebox.askokcancel(title="Subscription", message=f"These are the details entered: \nChosen"
                                                                           f" stock: {selected_stock}\n"
                                                                           f"Volatility to be alerted: {spinbox_used()}\n"
                                                                           f"Your email: {get_email()}\n"
                                                                           f"Pres OK to subscribe!")

        if is_ok_stock:
            sheety_post_body = {
                "lapas1": {
                    "stocks": selected_stock,
                    "cryptocurrencies": selected_crypto,
                    "volatility": spinbox_used(),
                    "email": get_email()
                }
            }
            requests.post(SHEETY_ENDPOINT, json=sheety_post_body, auth=BASIC)
    else:
        is_ok_crypto = messagebox.askokcancel(title="Subscription", message=f"These are the details entered: \nChosen"
                                                                            f" crypto currency: {selected_crypto}\n"
                                                                            f"Volatility to be alerted: {spinbox_used()}\n"
                                                                            f"Your email: {get_email()}\n"
                                                                            f"Pres OK to subscribe!")

        if is_ok_crypto:
            sheety_post_body = {
                "lapas1": {
                    "stocks": selected_stock,
                    "cryptocurrencies": selected_crypto,
                    "volatility": spinbox_used(),
                    "email": get_email()
                }
            }
            requests.post(SHEETY_ENDPOINT, json=sheety_post_body, auth=BASIC)


# Buttons:

subscribe_button = Button(text="Subscribe to get latest news!", width=36, activebackground="green", command=subscribe)
subscribe_button.grid(column=1, row=5, columnspan=2)

window.mainloop()


# ---------------------------- TAKING DATA FROM SHEETY DATABASE TO SEND NEWS----------------------------------------- #


def send_news(coin_symbols, coin_data, stock_symbols, full_stock_names):
    global SHEETY_ENDPOINT
    global BASIC
    global ALPHA_VANTAGE_API
    global NEWS_API_KEY
    global MY_EMAIL
    global PASSWORD
    global VIRTUAL_TWILIO_NUMBER
    global VERIFIED_NUMBER

    response = requests.get(SHEETY_ENDPOINT, auth=BASIC)
    sheety_data = response.json()
    pprint.pprint(sheety_data)

    for subscription in sheety_data["lapas1"]:
        volatility = subscription["volatility"]
        email = subscription["email"]

        # ---------------------------- STOCK SECTION ------------------------------------------------------------ #
        if subscription["cryptocurrencies"] == "":
            subscribed_stock = subscription["stocks"]

            # Get yesterday's closing stock price. API offers only hourly (not daily) time series for free,
            # so I use that.
            parameters = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": subscribed_stock,
                "interval": "60min",
                "outputsize": "compact",
                "apikey": ALPHA_VANTAGE_API,
            }

            response = requests.get(url="https://www.alphavantage.co/query", params=parameters)
            response.raise_for_status()

            stock_data = response.json()
            # pprint.pprint(stock_data)

            # Because Stock Exchange probably is not at the same time zone as customer's, a bug in code forms.
            # The code does not perform if customer's time is already past midnight, but Stock Exchange is still in
            # yesterday's time zone.
            # Also, need to keep in mind that prises are based on US exchange market witch closes on friday 20:00 pm and
            # opens on monday morning.

            yesterday_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

            last_open_market_date = stock_data["Meta Data"]["3. Last Refreshed"][:10]
            last_market_date_object = datetime.strptime(last_open_market_date, '%Y-%m-%d')
            day_before_last_market_date = (last_market_date_object - timedelta(1)).strftime('%Y-%m-%d')
            two_days_before_last_market_day = (last_market_date_object - timedelta(2)).strftime('%Y-%m-%d')
            try:
                yesterday_closing_price = stock_data["Time Series (60min)"][f"{last_open_market_date} 20:00:00"][
                    "4. close"]
                day_before_closing_price = stock_data["Time Series (60min)"][f"{day_before_last_market_date} "
                                                                             f"20:00:00"]["4. close"]
                difference = abs(float(yesterday_closing_price) - float(day_before_closing_price))
                stock_percentage_diff = round(difference * 100 / float(day_before_closing_price), 3)

                # print(difference)
                print(stock_percentage_diff)

            except KeyError:
                yesterday_closing_price = stock_data["Time Series (60min)"][f"{day_before_last_market_date} 20:00:00"][
                    "4. close"]
                day_before_closing_price = stock_data["Time Series (60min)"][f"{two_days_before_last_market_day}"
                                                                             f" 20:00:00"]["4. close"]
                difference = abs(float(yesterday_closing_price) - float(day_before_closing_price))
                stock_percentage_diff = round(difference * 100 / float(day_before_closing_price), 3)
                # print(difference)
                print(stock_percentage_diff)

            if stock_percentage_diff > float(volatility):

                # ---------------------------- NEWS ARTICLES API SETUP + SEND EMAIL OR SMS -------------------------- #

                # Filtering company name of the stock symbol. From full stock name we need only first two words:
                i = stock_symbols.index(subscribed_stock)
                selected_stock_full_name = full_stock_names[i]
                first_two_words = " ".join(selected_stock_full_name.split()[:2])

                # Getting recent news

                parameters = {
                    "q": first_two_words,
                    "from": yesterday_date,
                    "sortBy": "populiarity",
                    "apikey": NEWS_API_KEY,
                    "language": 'en'
                }

                response = requests.get(url="https://newsapi.org/v2/everything", params=parameters)
                response.raise_for_status()

                news_data = response.json()
                three_articles = news_data["articles"][0:3]

                first_title = (three_articles[0]["title"]).replace('’', "'").replace("—", "-").replace("…", "...")\
                    .replace("‘", "'").replace("“", "'").replace("”", "'")
                first_description = (three_articles[0]["description"]).replace('’', "'").replace("—", "-")\
                    .replace("…", "...").replace("‘", "'").replace("“", "'").replace("”", "'")
                first_url = (three_articles[0]["url"])
                second_title = (three_articles[1]["title"]).replace('’', "'").replace("—", "-").replace("…", "...")\
                    .replace("‘", "'").replace("“", "'").replace("”", "'")
                second_description = (three_articles[1]["description"]).replace('’', "'").replace("—", "-")\
                    .replace("…", "...").replace("‘", "'").replace("“", "'").replace("”", "'")
                second_url = (three_articles[1]["url"])

                # News subject attribute:

                def stock_up_down():
                    if float(yesterday_closing_price) > float(day_before_closing_price):
                        return "Up"
                    else:
                        return "Down"

                stock_subject = f"{subscribed_stock} is {stock_up_down()} by {stock_percentage_diff}%"
                stock_subject.replace('’', "'")

                # Sending two most popular news stories of the day associated with particular stock/crypto

                email_text = f"On the last stock market closure {stock_subject}, comparing from the day before.\n" \
                             f"Here are some news on {subscribed_stock}:\n" \
                             f"Headline: {first_title}\n" \
                             f"Brief: {first_description}\n" \
                             f"Read more: {first_url}\n" \
                             f"Second Headline: {second_title}\n" \
                             f"Second Brief: {second_description}\n" \
                             f"Read more: {second_url}\n"

                # Setting up email sending

                with smtplib.SMTP("smtp.mail.yahoo.com", port=587) as connection:
                    connection.starttls()
                    connection.login(user=MY_EMAIL, password=PASSWORD)
                    connection.sendmail(
                        from_addr=MY_EMAIL,
                        to_addrs=email,
                        msg=f"Subject:{stock_subject}\n\n{email_text}"
                    )

                # This function instead of email, sends SMS, which I prefer and use. For the sake of simplicity,
                # in the UI there is only email option.

                # client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
                # message = client.messages.create(
                #     body=f"{subscribed_stock}: {stock_up_down}{stock_percentage_diff}%\n"
                #          f"Headline: {first_title}\n"
                #          f"Brief: {first_description}",
                #     from_=VIRTUAL_TWILIO_NUMBER,
                #     to=VERIFIED_NUMBER
                # )
                # print(message.sid)

            # ---------------------------- COIN PRICE VOLATILITY ---------------------------------------- #
        else:
            subscribed_crypto = subscription["cryptocurrencies"]
            i = coin_symbols.index(subscribed_crypto)
            coin_percentage_diff = coin_data["data"][i]["quote"]["USD"]["percent_change_24h"]
            print(coin_percentage_diff)

            if abs(float(coin_percentage_diff)) > float(volatility):
                yesterday_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

                # Getting recent news if needed

                parameters = {
                    "q": subscribed_crypto,
                    "from": yesterday_date,
                    "sortBy": "populiarity",
                    "apikey": NEWS_API_KEY,
                    "language": 'en'
                }

                response = requests.get(url="https://newsapi.org/v2/everything", params=parameters)
                response.raise_for_status()

                news_data = response.json()
                three_articles = news_data["articles"][0:3]

                first_title = (three_articles[0]["title"]).replace('’', "'").replace("—", "-").replace("…", "...")\
                    .replace("‘", "'").replace("“", "'").replace("”", "'")
                first_description = (three_articles[0]["description"]).replace('’', "'").replace("—", "-")\
                    .replace("…", "...").replace("‘", "'").replace("“", "'").replace("”", "'")
                first_url = (three_articles[0]["url"])
                second_title = (three_articles[1]["title"]).replace('’', "'").replace("—", "-").replace("…", "...")\
                    .replace("‘", "'").replace("“", "'").replace("”", "'")
                second_description = (three_articles[1]["description"]).replace('’', "'").replace("—", "-")\
                    .replace("…", "...").replace("‘", "'").replace("“", "'").replace("”", "'")
                second_url = (three_articles[1]["url"])

                # News subject attribute:

                def coin_up_down():
                    if float(coin_percentage_diff) > 0:
                        return "Up"
                    else:
                        return "Down"

                coin_subject = f"{subscribed_crypto} is {coin_up_down()} by {coin_percentage_diff}%"
                coin_subject.replace('’', "'")

                email_text = f"In the last 24h {coin_subject}.\n" \
                             f"Here are some news on {subscribed_crypto}:\n" \
                             f"Headline: {first_title}\n" \
                             f"Brief: {first_description}\n" \
                             f"Read more: {first_url}\n" \
                             f"Second Headline: {second_title}\n" \
                             f"Second Brief: {second_description}\n" \
                             f"Read more: {second_url}\n"

                # Setting up email sending

                with smtplib.SMTP("smtp.mail.yahoo.com", port=587) as connection:
                    connection.starttls()
                    connection.login(user=MY_EMAIL, password=PASSWORD)
                    connection.sendmail(
                        from_addr=MY_EMAIL,
                        to_addrs=email,
                        msg=f"Subject:{coin_subject}\n\n{email_text}"
                    )

                # This function instead of email, sends SMS, which I prefer and use. For the sake of simplicity,
                # in the UI there is only email option.

                # client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
                # message = client.messages.create(
                #     body=f"{subscribed_crypto}: {coin_up_down}{coin_percentage_diff}%\n"
                #          f"Headline: {first_title}\n"
                #          f"Brief: {first_description}",
                #     from_=VIRTUAL_TWILIO_NUMBER,
                #     to=VERIFIED_NUMBER
                # )
                # print(message.sid)


send_news(coin_symbols=coin_symbols, coin_data=coin_data, stock_symbols=stock_symbols,
          full_stock_names=full_stock_names)
