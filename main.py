# IMPORTING LIBRARIES
import requests
import datetime as dt
import os
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient

# CONSTANTS

# STOCK
COMPANY_STOCK = "TSLA"
COMPANY_NAME = "Tesla"
STOCK_API_KEY = os.environ.get("STOCK_API_KEY")
STOCK_API_ENDPOINT = os.environ.get("STOCK_API_ENDPOINT")
STOCK_CHANGE_PERCENT = 5

# DAYS
MONDAY = 0
TUESDAY = 1
SUNDAY = 6

# NEWS
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
NEWS_API_ENDPOINT = os.environ.get("NEWS_API_ENDPOINT")
NUM_ARTICLES = 3

# TWILIO
ACCOUNT_SID = os.environ.get("ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
FROM_MOBILE_NUMBER = os.environ.get("FROM_NUMBER")
TO_MOBILE_NUMBER = os.environ.get("TO_NUMBER")


def get_trading_date():
    today_date = dt.date.today()
    today_day = today_date.weekday()

    if today_day == MONDAY:
        yesterday_date = str(today_date - dt.timedelta(days=3))
        day_before_yesterday_date = str(today_date - dt.timedelta(days=4))
    elif today_day == SUNDAY:
        yesterday_date = str(today_date - dt.timedelta(days=2))
        day_before_yesterday_date = str(today_date - dt.timedelta(days=3))
    elif today_day == TUESDAY:
        yesterday_date = str(today_date - dt.timedelta(days=1))
        day_before_yesterday_date = str(today_date - dt.timedelta(days=4))
    else:
        yesterday_date = str(today_date - dt.timedelta(days=1))
        day_before_yesterday_date = str(today_date - dt.timedelta(days=2))
    return (yesterday_date, day_before_yesterday_date)


def get_stock_json(stock_parameters):
    stock_response = requests.get(url=STOCK_API_ENDPOINT, params=stock_parameters)
    stock_response.raise_for_status()
    stock_data = stock_response.json()
    return stock_data


def get_news(news_parameters):
    news_response = requests.get(url=NEWS_API_ENDPOINT, params=news_parameters)
    news_response.raise_for_status()
    news_data = news_response.json()["articles"]
    return news_data


def get_articles(articles, is_higher, change_percent):
    messages = []
    change_symbol = "🔺" if is_higher else "🔻"
    for article in articles:
        message = f"{COMPANY_STOCK}: {change_symbol}{change_percent}%\nHeadline: {article['title']}\nBrief: {article['description']}"
        messages.append(message)
    return messages


def send_message(messages):
    proxy_client = TwilioHttpClient(
        proxy={"http": os.environ["http_proxy"], "https": os.environ["https_proxy"]}
    )
    client = Client(ACCOUNT_SID, AUTH_TOKEN)  # , http_client=proxy_client)
    for i in messages:
        message = client.messages.create(
            body=i,
            from_=FROM_MOBILE_NUMBER,
            to=TO_MOBILE_NUMBER,
        )
        print(message.status)
    return


stock_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": COMPANY_STOCK,
    "apikey": STOCK_API_KEY,
}


stock_data = get_stock_json(stock_parameters)
yesterday, day_before_yesterday = get_trading_date()
yesterday_price = float(stock_data["Time Series (Daily)"][yesterday]["4. close"])
day_before_yesterday_price = float(
    stock_data["Time Series (Daily)"][day_before_yesterday]["4. close"]
)


news_parameters = {
    "apiKey": NEWS_API_KEY,
    "q": COMPANY_NAME,
    "pageSize": NUM_ARTICLES,
    "page": 1,
    "sortBy": "relevancy",
    "language": "en",
    "from": day_before_yesterday,
}


price_difference_percent = (
    (yesterday_price - day_before_yesterday_price) * 100 / yesterday_price
)
is_higher = True if (price_difference_percent > 0) else False
price_difference_percent = round(abs(price_difference_percent), 2)


if price_difference_percent >= STOCK_CHANGE_PERCENT:
    news_articles = get_news(news_parameters)
    news_messages = get_articles(news_articles, is_higher, price_difference_percent)
    send_message(news_messages)
