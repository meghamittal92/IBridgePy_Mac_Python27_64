import pytz
import datetime as dt

from IBridgePy.constants import TraderRunMode, MarketName

PROJECT = {
    'showTimeZone': pytz.timezone('US/Eastern'),
    'repBarFreq': 1,  # Positive integers only
    'logLevel': 'INFO',  # Possible values are ERROR, INFO, DEBUG, NOTSET, refer to http://www.ibridgepy.com/ibridgepy-documentation/#logLevel
}


MARKET_MANAGER = {  # these settings are applied ONLY when traderRunMode == RUN_LIKE_QUANTOPIAN
    'marketName': MarketName.NYSE,
    'beforeTradeStartHour': 9,
    'beforeTradeStartMinute': 25,
}

TRADER = {
    # Refer to http://www.ibridgepy.com/ibridgepy-documentation/#runMode
    'runMode': TraderRunMode.REGULAR  # run handle_data every second. Possible values are REGULAR, RUN_LIKE_QUANTOPIAN, SUDO_RUN_LIKE_QUANTOPIAN and HFT
}

BROKER_CLIENT = {
    'IB_CLIENT': {
        'clientId': 9,
        'port': 7496
    },
    'TD_CLIENT': {
        'apiKey': '',  # put your apiKey here. Refer to this tutorial https://www.youtube.com/watch?v=l3qBYMN4yMs
        'refreshToken': '',  # put your refresh token here. Refer to this tutorial https://youtu.be/Ql6VnR0GIYY
        'refreshTokenCreatedOn': dt.date(2020, 5, 7)  # put the date when the refresh token was created. IBridgePy will remind you when it is about to expire.
    },
    'ROBINHOOD_CLIENT': {
        'username': '',  # put your Robinhood username here. It is ok to leave it as-is. Then, you will be prompted to input it in command line later.
        'password': '',  # put your Robinhood password here. It is ok to leave it as-is. Then, you will be prompted to input it in command line later.
    }
}

EMAIL_CLIENT = {
    'IBRIDGEPY_EMAIL_CLIENT': {
        'apiKey': ''
    }
}

