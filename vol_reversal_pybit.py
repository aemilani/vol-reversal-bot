import time
import numpy as np
from datetime import datetime
from dotenv import dotenv_values
from pybit.unified_trading import HTTP


def open_long():
    # Get balance and price
    while True:
        try:
            balance = float(session.get_wallet_balance(
                accountType="UNIFIED")['result']['list'][0]['coin'][0]['walletBalance'])
            price = float(session.get_tickers(category="linear", symbol="BTCUSDT")['result']['list'][0]['lastPrice'])
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)
    # Calculate size
    size = pos_pct * balance / price * leverage
    size = "{:.3f}".format(size)
    # Place order
    while True:
        try:
            session.place_order(category="linear", symbol="BTCUSDT", side="Buy", orderType="Market", qty=size,
                                stopLoss="{:.2f}".format(((1 - sl / leverage) * price)))
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)


def open_short():
    # Get balance and price
    while True:
        try:
            balance = float(session.get_wallet_balance
                            (accountType="UNIFIED")['result']['list'][0]['coin'][0]['walletBalance'])
            price = float(session.get_tickers(category="linear", symbol="BTCUSDT")['result']['list'][0]['lastPrice'])
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)
    # Calculate size
    size = pos_pct * balance / price * leverage
    size = "{:.3f}".format(size)
    # Place order
    while True:
        try:
            session.place_order(category="linear", symbol="BTCUSDT", side="Sell", orderType="Market", qty=size,
                                stopLoss="{:.2f}".format(((1 + sl / leverage) * price)))
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)


def close_long():
    # Get size
    while True:
        try:
            size = float(session.get_positions(category="linear", symbol="BTCUSDT")['result']['list'][0]['size'])
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)
    size = "{:.3f}".format(size)
    # Close position
    while True:
        try:
            session.place_order(category="linear", symbol="BTCUSDT", side="Sell", orderType="Market", qty=str(size),
                                reduceOnly=True)
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)


def close_short():
    # Get size
    while True:
        try:
            size = float(session.get_positions(category="linear", symbol="BTCUSDT")['result']['list'][0]['size'])
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)
    size = "{:.3f}".format(size)
    # Close position
    while True:
        try:
            session.place_order(category="linear", symbol="BTCUSDT", side="Buy", orderType="Market", qty=str(size),
                                reduceOnly=True)
            break
        except Exception as ex:
            print(f'{datetime.now()}: {ex}. Trying again...')
            time.sleep(1)


config = dotenv_values('.env')
API_KEY = config.get('BYBIT_API_KEY')
API_SECRET = config.get('BYBIT_API_SECRET')

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

# Params

tf = 60
w = 14
std_multiple = 3

sl = 0.1
leverage = 10
pos_pct = 0.9

assert int(session.get_positions(category="linear", symbol="BTCUSDT")['result']['list'][0]['leverage']) == leverage


# Trading

print(f'{datetime.now()}: Trading started')

while True:
    try:
        candles = session.get_kline(category="linear", symbol="BTCUSDT", interval=tf, limit=w)['result']['list']
        break
    except Exception as e:
        print(f'{datetime.now()}: {e}. Trying again...')
        time.sleep(1)

curr_candle = candles[0]
curr_candle_size = float(curr_candle[2]) - float(curr_candle[3])

last_w_candles = candles
last_w_candle_sizes = [float(x[2]) - float(x[3]) for x in last_w_candles]
last_w_candle_sizes_mean = np.mean(last_w_candle_sizes)
last_w_candle_sizes_std = np.std(last_w_candle_sizes, ddof=1)
thr = last_w_candle_sizes_mean + std_multiple * last_w_candle_sizes_std

curr_ts = int(curr_candle[0])
next_ts = curr_ts + 3600000

if curr_candle_size >= thr:
    skip_candle = True
else:
    skip_candle = False

while True:
    # Get position size
    while True:
        try:
            pos_size = float(session.get_positions(category="linear", symbol="BTCUSDT")['result']['list'][0]['size'])
            break
        except Exception as e:
            print(f'{datetime.now()}: {e}. Trying again...')
            time.sleep(1)

    # Close the position
    if 1000 * time.time() >= next_ts:
        if pos_size > 0:
            print(f'{datetime.now()}: Closing position @ {curr_candle[4]}')
            while True:
                try:
                    side = session.get_positions(category="linear", symbol="BTCUSDT")['result']['list'][0]['side']
                    break
                except Exception as e:
                    print(f'{datetime.now()}: {e}. Trying again...')
                    time.sleep(1)
            if side == 'Buy':
                close_long()
            elif side == 'Sell':
                close_short()

        time.sleep(1)
        print(f'\n{datetime.fromtimestamp(next_ts / 1000)}: Next candle')
        skip_candle = False

    # Update candles
    while True:
        try:
            candles = session.get_kline(category="linear", symbol="BTCUSDT", interval=tf, limit=w)['result']['list']
            break
        except Exception as e:
            print(f'{datetime.now()}: {e}. Trying again...')
            time.sleep(1)

    curr_candle = candles[0]
    curr_candle_size = float(curr_candle[2]) - float(curr_candle[3])

    last_w_candles = candles
    last_w_candle_sizes = [float(x[2]) - float(x[3]) for x in last_w_candles]
    last_w_candle_sizes_mean = np.mean(last_w_candle_sizes)
    last_w_candle_sizes_std = np.std(last_w_candle_sizes, ddof=1)
    thr = last_w_candle_sizes_mean + std_multiple * last_w_candle_sizes_std

    curr_ts = int(curr_candle[0])
    next_ts = curr_ts + 3600000

    # Open position
    if not skip_candle and (pos_size == 0) and (curr_candle_size >= thr):
        print(f'Current candle size ({curr_candle_size}) > threshold ({thr})')
        if float(curr_candle[4]) > float(curr_candle[1]):  # if close > open
            print(f'{datetime.now()}: Opening short @ {curr_candle[4]}')
            open_short()
            skip_candle = True
        elif float(curr_candle[4]) < float(curr_candle[1]):  # if close < open
            print(f'{datetime.now()}: Opening long @ {curr_candle[4]}')
            open_long()
            skip_candle = True

    time.sleep(1)
