# -*- coding: utf-8 -*-
"""
@author: IBridgePy@gmail.com
"""
from BasicPyLib.BasicTools import CONSTANTS

"""
This module defines the constants used by IB.
For other brokers, checkout broker_client_factory::TdAmeritrade::BrokerClient_TdAmeritrade.py. There are a few converters
"""


class SecType(CONSTANTS):
    CASH = 'CASH'
    STK = 'STK'
    FUT = 'FUT'
    OPT = 'OPT'
    IND = 'IND'
    CFD = 'CFD'
    BOND = 'BOND'


class LiveBacktest(CONSTANTS):
    LIVE = 1
    BACKTEST = 2


class BrokerName(CONSTANTS):
    LOCAL_BROKER = 'LOCAL_BROKER'
    IB = 'IB'
    ROBINHOOD = 'ROBINHOOD'
    TDAMERITRADE = 'TDAMERITRADE'


class DataProviderName(CONSTANTS):
    LOCAL_FILE = 'LOCAL_FILE'
    RANDOM = 'RANDOM'
    IB = 'IB'


class DataSourceName(CONSTANTS):
    IB = 'IB'
    YAHOO = 'YAHOO'
    GOOGLE = 'GOOGLE'
    LOCAL_FILE = 'LOCAL_FILE'


class SymbolStatus(CONSTANTS):
    DEFAULT = 0
    SUPER_SYMBOL = 1
    ADJUSTED = 2
    STRING_CONVERTED = 3


class TraderRunMode(CONSTANTS):
    REGULAR = 'REGULAR'
    RUN_LIKE_QUANTOPIAN = 'RUN_LIKE_QUANTOPIAN'
    SUDO_RUN_LIKE_QUANTOPIAN = 'SUDO_RUN_LIKE_QUANTOPIAN'
    HFT = 'HFT'


class OrderStatus(CONSTANTS):
    """
    The values should match IB's order status value in string
    """
    PRESUBMITTED = 'PreSubmitted'
    SUBMITTED = 'Submitted'
    CANCELLED = 'Cancelled'
    APIPENDING = 'ApiPending'
    PENDINGSUBMIT = 'PendingSubmit'
    PENDINGCANCEL = 'PendingCancel'
    FILLED = 'Filled'
    INACTIVE = 'Inactive'


class OrderAction(CONSTANTS):
    BUY = 'BUY'
    SELL = 'SELL'


class OrderTif(CONSTANTS):
    DAY = 'DAY'  # good for today
    GTC = 'GTC'  # good to cancel


class OrderType(CONSTANTS):
    MKT = 'MKT'
    LMT = 'LMT'
    STP = 'STP'
    TRAIL_LIMIT = 'TRAIL LIMIT'
    TRAIL = 'TRAIL'
    STP_LMT = 'STP LMT'


class ExchangeName(CONSTANTS):
    ISLAND = 'ISLAND'


class MarketName(CONSTANTS):
    NYSE = 'NYSE'
    NONSTOP = 'NONSTOP'


class Default(CONSTANTS):
    DEFAULT = 'default'


class FollowUpRequest(CONSTANTS):
    DO_NOT_FOLLOW_UP = False
    FOLLOW_UP = True


class RequestDataParam(CONSTANTS):
    WAIT_30_SECONDS = 30
    WAIT_1_SECOND = 1
    DO_NOT_REPEAT = 0


class LogLevel(CONSTANTS):
    ERROR = 'ERROR'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    NOTSET = 'NOTSET'


class TimeGeneratorType(CONSTANTS):
    LIVE = 'LIVE'
    AUTO = 'AUTO'
    CUSTOM = 'CUSTOM'


class TimeConcept(CONSTANTS):
    NEW_DAY = 'new_day'
    NEW_HOUR = 'new_hour'


if __name__ == '__main__':
    pass
