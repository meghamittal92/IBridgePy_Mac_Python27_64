from IBridgePy.constants import TimeGeneratorType, BrokerName, LogLevel, DataProviderName, \
    LiveBacktest, TraderRunMode
import pytz
import os

"""
XXXX_BASE in the names are required. Details see config_defs.py
"""
MARKET_MANAGER = {
    'baseFreqOfProcessMessage': 1,
    'marketName': None,
    'beforeTradeStartHour': None,
    'beforeTradeStartMinute': None
}

REPEATER = {
    'slowdownInSecond': 0.5
}

TIME_GENERATOR = {
    'timeGeneratorType': TimeGeneratorType.LIVE,  # Live, Auto, Custom
    'startingTime': None,
    'endingTime': None,
    'freq': None,
    'custom': []
}

PROJECT = {
    'accountCode': '',
    'fileName': '',
    'logLevel': LogLevel.INFO,
    'repBarFreq': None,
    'dataProviderName': DataProviderName.IB,
    'brokerName': BrokerName.IB,
    'sysTimeZone': pytz.timezone('US/Eastern'),
    'liveOrBacktest': LiveBacktest.LIVE,
    'rootFolderPath': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'histIngestionPlan': None,
    'runScheduledFunctionBeforeHandleData': False,  # As same as in Quantopian
    'showTimeZone': pytz.timezone('US/Eastern'),
}

TRADER = {
    'runMode': TraderRunMode.REGULAR  # run handle_data every second, not run_like_quantopian
}

BROKER_CLIENT = {
    'IB_CLIENT': {
        'host': '',  # config for IB client
        'port': 7496,  # config for IB client
        'clientId': 9,  # config for IB client
    },
    'TD_CLIENT': {
        'apiKey': '',
        'refreshToken': '',
        'refreshTokenCreatedOn': None  # the user input should be datetime.date()
    },
    'ROBINHOOD_CLIENT': {
        'username': '',
        'password': ''
    }
}

EMAIL_CLIENT = {
    'IBRIDGEPY_EMAIL_CLIENT': {
        'apiKey': ''
    }
}
