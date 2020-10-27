# coding=utf-8
import random
from sys import exit
import pandas as pd
import pytz
import datetime as dt


class CONSTANTS(object):
    def __init__(self):
        pass

    def get(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            print(__name__, '::CONSTANTS: key=%s does not exist from %s' % (key, self))
            exit()


class Timer(object):
    def __init__(self):
        self.startTime = dt.datetime.now()

    def elapsedInSecond(self):
        return (dt.datetime.now() - self.startTime).total_seconds()


def roundToMinTick(price, minTick=0.01):
    """
    for US interactive Brokers, the minimum price change in US stocks is
    $0.01. So if the singleTrader made calculations on any price, the calculated
    price must be round using this function to the minTick, e.g., $0.01
    """
    if price < 0.0:
        print(__name__ + '::roundToMinTick: EXIT, negative price =' + str(price))
        exit()
    return int(price / minTick) * minTick


def dt_to_utc_in_seconds(a_dt, showTimeZone=None):
    """
    dt.datetime.fromtimestamp
    the return value depends on local machine timezone!!!!
    So, dt.datetime.fromtimestamp(0) will create different time at different machine
    So, this implementation does not use dt.datetime.fromtimestamp
    """
    # print (__name__+'::dt_to_utc_in_seconds: EXIT, read function comments')
    # exit()
    if a_dt.tzinfo is None:
        if showTimeZone:
            a_dt = showTimeZone.localize(a_dt)
        else:
            a_dt = pytz.utc.localize(a_dt)
            # print(__name__+'::dt_to_utc_in_seconds:EXIT, a_dt is native time, showTimeZone must be not None')
            # exit()
    return (a_dt.astimezone(pytz.utc) - pytz.utc.localize(dt.datetime(1970, 1, 1, 0, 0))).total_seconds()


def utc_in_seconds_to_dt(utcInSeconds, str_timezone='UTC'):
    return pytz.timezone(str_timezone).localize(dt.datetime.utcfromtimestamp(int(utcInSeconds)))
    # Another implementation
    # return dt.datetime.utcfromtimestamp(epoch, tz=pytz.utc)


def isAllLettersCapital(word):
    for letter in word:
        if letter.isalpha():
            if not letter.isupper():
                return False
    return True


def create_random_hist(startTime, endTime, barSize, miniTick):
    """

    :param startTime: dt.datetime
    :param endTime: dt.datetime
    :param barSize: 1S = 1 second; 1T = 1 minute; 1H = 1 hour
    :param miniTick: float, 0.01, 0.05, 0.1, etc.
    :return: pd.DataFrame('open', 'high', 'low', 'close', 'volume'), index = datetime
    """
    ans = pd.DataFrame()

    # !!!!!!!
    # pd.data_range is a badly designed function because it cannot recognize timezone
    # It always returns time range in local machine timezone
    # !!!!!!!
    index = pd.date_range(startTime, endTime, freq=barSize, tz=pytz.timezone('UTC'))
    for dateTime in index:
        openPrice = random.uniform(50, 100)
        closePrice = openPrice * random.uniform(0.95, 1.05)
        highPrice = max(openPrice, closePrice) * random.uniform(1, 1.05)
        lowPrice = max(openPrice, closePrice) * random.uniform(0.95, 1)

        newRow = pd.DataFrame({'open': roundToMinTick(openPrice, miniTick),
                               'high': roundToMinTick(highPrice, miniTick),
                               'low': roundToMinTick(lowPrice, miniTick),
                               'close': roundToMinTick(closePrice, miniTick),
                               'volume': random.randint(10000, 50000)},
                              index=[int(dt_to_utc_in_seconds(dateTime))])
        ans = ans.append(newRow)
    # print(utc_in_seconds_to_dt(ans.index[0]))
    # print(utc_in_seconds_to_dt(ans.index[-1]))
    return ans
