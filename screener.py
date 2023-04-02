import time
from binance.client import Client
from binance.enums import KLINE_INTERVAL_1MINUTE
import numpy as np
import logging
import os

# Ключи API Binance
api_key = os.getenv("API KEY BINANCE")
api_secret = os.getenv("API SECRET BINANCE")

logging.basicConfig(level=logging.INFO)
# Создаем клиент Binance API
client = Client(api_key, api_secret)


# Достаем цену в реальном времени
def get_current_price(symbol):
    ticker = client.futures_symbol_ticker(symbol=symbol)
    return float(ticker['price'])


# Функция для показа цены тикера "symbol" за интервал "interval"
def get_historical_klines(symbol: str, interval, time_period: str):
    klines = client.get_historical_klines(symbol, interval, time_period)
    return [float(kline[4]) for kline in klines]


def calculate_corr_coef(price_list_1, price_list_2):
    return np.corrcoef([price_list_1, price_list_2])[0, 1]


def calculate_adj_price(price_1, price_2, corr_coef):
    return price_2 - price_1 * corr_coef


def log_price_change(symbol, percentage_change):
    if abs(percentage_change) >= 1:
        if percentage_change > 0:
            logging.warning(
                f"Цена {symbol} повысилась на "
                "{percentage_change}% за последний час"
                )
        else:
            logging.warning(
                f"Цена {symbol} снизилась "
                "{percentage_change}% за последний час"
                )


# Получаем первоначальные цены BTCUSDT и ETHUSDT
btc_price = get_current_price("BTCUSDT")
eth_price = get_current_price("ETHUSDT")

# Получаем исторические данные цены BTCUSDT и ETHUSDT за последние 24 часа
btc_price_list = get_historical_klines(
    "BTCUSDT", KLINE_INTERVAL_1MINUTE, "24 hour ago UTC")
eth_price_list = get_historical_klines(
    "ETHUSDT", KLINE_INTERVAL_1MINUTE, "24 hour ago UTC")

# Считаем кореляционный коэфициент за 24 часа и приспосабливаем его к ETHUSDT
corr_coef = calculate_corr_coef(btc_price_list, eth_price_list)
adj_eth_price = calculate_adj_price(btc_price, eth_price, corr_coef)

# Создайте список для хранения цен ETH за последний час
prices_last_hour = []

# Создаем переменную для хранения процентного изменения цены ETH за
# последний час
percentage_change = 0.0

# Запускаем бесконечный цикл для отслеживания цены в реальном времени
while True:
    try:
        # Добавляем текущую цену ETH в список
        prices_last_hour.append(adj_eth_price)
        # Если в списке цен больше 60, удаляем самую старую
        if len(prices_last_hour) > 60:
            prices_last_hour.pop(0)

            # Вычесляем процент изменений цены за последний час
            percentage_change = (
                adj_eth_price
                - prices_last_hour[0]) / prices_last_hour[0] * 100

            current_price = get_current_price("ETHUSDT")
            if current_price:
                logging.info(f'Текущая цена: {current_price}')
            time.sleep(10)
            # Функция запущена в бесконечном цикле, если цена измениться больше
            # чем на 1%, выведется сообщение в терминал
            log_price_change("ETHUSDT", percentage_change)
            time.sleep(10)
    except Exception as e:
        logging.error(
            f'Ошибка определения цены, перезагрузка, подожди 60 секунд {e}')
        time.sleep(60)
