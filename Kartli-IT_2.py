from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import time
import MetaTrader5 as mt5

if not mt5.initialize():
    print("initialize() failed")
    quit()

symbol_1 = 'EURUSD'
symbol_2 = 'GBPUSD'

symbol_1_info = mt5.symbol_info(symbol_1)
symbol_2_info = mt5.symbol_info(symbol_2)
if symbol_1_info and symbol_2_info is None:
    print(symbol_1, 'and', symbol_2, "not found, can not call order_check()")
    mt5.shutdown()
    quit()

if not symbol_1_info.visible and symbol_2_info.visible:
    print(symbol_1, 'and', symbol_2, "is not visible, trying to switch on")
    if not mt5.symbol_select(symbol_1,True) and mt5.symbol_select(symbol_2,True):
        print("symbol_select({}}) failed, exit",symbol_1)
        print("symbol_select({}}) failed, exit",symbol_2)
        mt5.shutdown()
        quit()

timezone = pytz.timezone("Etc/UTC")
utc_from = datetime(2017, 7, 25, tzinfo=timezone)
utc_to = datetime(2018, 7, 25, tzinfo=timezone)

rates_eur = mt5.copy_rates_range(symbol_1, mt5.TIMEFRAME_D1, utc_from, utc_to)
rates_gbp = mt5.copy_rates_range(symbol_2, mt5.TIMEFRAME_D1, utc_from, utc_to)

rates_eur_frame = pd.DataFrame(rates_eur)
rates_eur_frame['time'] = pd.to_datetime(rates_eur_frame['time'], unit='s')
rates_gbp_frame = pd.DataFrame(rates_gbp)
rates_gbp_frame['time'] = pd.to_datetime(rates_gbp_frame['time'], unit='s')

eur_sum = sum(rates_eur_frame['close'])
gbp_sum = sum(rates_gbp_frame['close'])

eur_pr = rates_eur_frame['close']
gbp_pr = rates_gbp_frame['close']

gbp_pr[len(gbp_pr)] = 1.31980

if eur_sum > gbp_sum:
    spread = eur_pr - gbp_pr
else:
    spread = gbp_pr - eur_pr
median = spread.mean()

lot = 1
rol = spread.rolling(25).mean()
point_1 = mt5.symbol_info(symbol_1).point
point_2 = mt5.symbol_info(symbol_2).point
deviation = 2

spread = spread.fillna(spread[1])
rol = rol.fillna(spread)

for i in range(len(spread)):
    if spread[i] > rol[i]:
        request_buy = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol_1,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": eur_pr[i],
            "sl": eur_pr[i] - 100 * point_1,
            "tp": eur_pr[i] + 100 * point_1,
            "deviation": deviation,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        request_sell = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol_2,
            "volume": lot,
            "type": mt5.ORDER_TYPE_SELL,
            "price": gbp_pr[i],
            "sl": gbp_pr[i] - 100 * point_2,
            "tp": gbp_pr[i] + 100 * point_2,
            "deviation": deviation,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        result_buy = mt5.order_send(request_buy)
        result_sell = mt5.order_send(request_sell)
    if spread[i] <= rol[i]:
        request_buy = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol_2,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": gbp_pr[i],
            "sl": gbp_pr[i] - 100 * point_2,
            "tp": gbp_pr[i] + 100 * point_2,
            "deviation": deviation,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        request_sell = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol_1,
            "volume": lot,
            "type": mt5.ORDER_TYPE_SELL,
            "price": eur_pr[i],
            "sl": eur_pr[i] - 100 * point_1,
            "tp": eur_pr[i] + 100 * point_1,
            "deviation": deviation,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        result_buy = mt5.order_send(request_buy)
        result_sell = mt5.order_send(request_sell)

plt.subplot(1, 2, 1)
plt.plot(eur_pr, label='EUR')
plt.plot(gbp_pr, label='GBP')
plt.title('График EUDUSD и GBPUSD')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(spread)
plt.plot(rol, color='red')
plt.axhline(median, color='violet', linestyle='--')
plt.title('График спреда')

plt.show()

mt5.shutdown()
