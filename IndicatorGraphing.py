import yfinance as yf
import pandas as pd
from technicalIndicators import ADXIndicator
from technicalIndicators import *
import talib as ta
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
import matplotlib.ticker as ticker
import matplotlib
import stockstats
import tulipy
import numpy as np

matplotlib.rcParams['timezone'] = 'US/Eastern'
DI_TIME_PERIOD = 21
ADX_TIME_PERIOD = 9


# aapl = yf.download('AAPL', '2017-1-1','2019-12-18')

# aapl['Adj Open'] = aapl.Open * aapl['Adj Close']/aapl['Close']
# aapl['Adj High'] = aapl.High * aapl['Adj Close']/aapl['Close']
# aapl['Adj Low'] = aapl.Low * aapl['Adj Close']/aapl['Close']
# aapl.dropna(inplace=True)

# print(aapl)

df = pd.read_csv('AAPL15mins.csv')
print(df)

# adxI = ADXIndicator(df['high'],df['low'],df['close'],21,False)
# df['posDI1'] = adxI.adx_pos()
# df['negDI1'] = adxI.adx_neg()
# df['adx1'] = adxI.adx()

# df['negDI2'] = ta.MINUS_DI(df.high, df.low, df.close, timeperiod=21)
# df['posDI2'] = ta.PLUS_DI(df.high, df.low, df.close, timeperiod=21)
# df['adx2'] = ta.ADX(df.high, df.low, df.close, timeperiod=21)


stockstats.StockDataFrame.PDI_SMMA = 21
stockstats.StockDataFrame.MDI_SMMA = 21

stock = stockstats.StockDataFrame.retype(df)

df['adx3'] = stock['dx_' + str(ADX_TIME_PERIOD) + '_ema']
#df.drop(columns=['pdm_' + str(ADX_TIME_PERIOD) ,'close_-1_s','tr','tr_' + str(ADX_TIME_PERIOD) + '_smma','low_delta','dm','pdm','pdm_'+ str(ADX_TIME_PERIOD) + '_ema','atr_' + str(ADX_TIME_PERIOD)], inplace=True, axis=1)
df['posDI3'] = stock['pdi']
#df['adx5'] = stock['adx']
df['negDI3'] = stock['mdi']



posDI, negDI = tulipy.di( high=df.high.values, low=df.low.values, close=df.close.values, period=DI_TIME_PERIOD)
# print(posDI)
# print(negDI)
df['posDI4'] = np.NAN
df['posDI4'][DI_TIME_PERIOD - 1:] = posDI
df['negDI4'] = np.NAN
df['negDI4'][DI_TIME_PERIOD - 1:] = negDI
# df['ADX4'] = np.NAN
# df['ADX4'][DI_TIME_PERIOD - 1:] = tulipy.adx(df.high.values, df.low.values, df.close.values, period=DI_TIME_PERIOD)

dfextra = ADX(df, 21, 21)
df['posDI5'] = dfextra['posDI5']
print(df)

df2 = df[df['unnamed: 0'] >= 1603188000]

df3 = df2[df2['unnamed: 0'] <= 1603200000]
print(df3)

def plot_graph(data, columnName1, columnName2, columnName3):
    
    secs = mdate.epoch2num(data['unnamed: 0'])
    fig, ax = plt.subplots()
    # Plot the date using plot_date rather than plot
    ax.plot_date(secs, data[columnName1],linestyle='solid', marker='None', color='green')
    if(columnName2 != ''):
        ax.plot_date(secs, data[columnName2],linestyle='solid', marker='None', color='red')
    if(columnName3 != ''):
        ax.plot_date(secs, data[columnName3],linestyle='solid', marker='None', color='black')
    #locator = mdate.AutoDateLocator(minticks=90, maxticks=90)
    locator = mdate.MinuteLocator(interval=15)
    ax.xaxis.set_major_locator(locator)


    #ax2 = ax.twinx()
    #ax2.plot_date(secs, data['negDI'])
    # Choose your xtick format string
    date_fmt = '%d-%m-%y %H:%M:%S'

    # Use a DateFormatter to set the data to the correct format.
    date_formatter = mdate.DateFormatter(date_fmt)
    ax.xaxis.set_major_formatter(date_formatter)

    # Sets the tick labels diagonal so they fit easier.
    fig.autofmt_xdate()
    ####
    # plot1 = plt.figure(figsize=(10,7))
    # plt.grid()
    # plt.plot(data['Unnamed: 0'], data[columnName])
    # plt.ylabel(ylabel)
    # plt.xlabel(xlabel)
def plot_graph2(data, columnName, ylabel,xlabel):
    secs = mdate.epoch2num(data['Unnamed: 0'])
    plot1 = plt.figure(figsize=(10,7))
    plt.grid()
    plt.plot(secs, data[columnName])
    date_fmt = '%d-%m-%y %H:%M:%S'

    # Use a DateFormatter to set the data to the correct format.
    date_formatter = mdate.DateFormatter(date_fmt)
    
    plt.xaxis.set_major_formatter(date_formatter)
   
#plot_graph(aapl, 'Adj Close', 'Close Price', 'Date')
#plot_graph(df2, 'posdi1', 'negdi1')
#plot_graph(df2, 'posdi2', 'negdi2')
#plot_graph(df3, 'posDI3', 'negDI3')
#plot_graph(df2, 'adx3', 'adx5')
plot_graph(df3, 'posDI3', 'negDI3','adx3')
#plot_graph(df2, 'posDI4', 'negDI4')
plt.show()