# coding=utf-8
from sys import exit

import pandas as pd

# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.constants import SymbolStatus


def from_contract_to_security(contract):
    ans = Security(secType=contract.secType, symbol=contract.symbol, currency=contract.currency)
    for para in ['secType', 'symbol', 'primaryExchange', 'exchange', 'currency', 'expiry', 'strike', 'right',
                 'multiplier', 'localSymbol']:
        tmp = getattr(contract, para)
        if tmp != '':
            setattr(ans, para, tmp)
    return ans


def from_security_to_contract(security):
    contract = IBCpp.Contract()
    contract.symbol = security.symbol
    contract.secType = security.secType
    contract.exchange = security.exchange
    contract.currency = security.currency
    contract.primaryExchange = security.primaryExchange
    contract.includeExpired = security.includeExpired
    contract.expiry = security.expiry
    contract.strike = float(security.strike)
    contract.right = security.right
    contract.multiplier = security.multiplier
    contract.localSymbol = security.localSymbol
    contract.conId = security.conId
    return contract


class OrderStyle(object):
    def __init__(self, orderType,
                 limit_price=None,  # default price is None to avoid any mis-formatted numbers
                 stop_price=None,
                 trailing_amount=None,
                 trailing_percent=None,
                 limit_offset=None,
                 tif='DAY'):
        self.orderType = orderType
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.trailing_amount = trailing_amount
        self.trailing_percent = trailing_percent
        self.limit_offset = limit_offset
        self.tif = tif

    def __str__(self):
        string_output = ''
        if self.orderType == 'MKT':
            string_output = 'MarketOrder,unknown exec price'
        elif self.orderType == 'STP':
            string_output = 'StopOrder, stop_price=' + str(self.stop_price)
        elif self.orderType == 'LMT':
            string_output = 'LimitOrder, limit_price=' + str(self.limit_price)
        elif self.orderType == 'STP LMT':
            string_output = 'StopLimitOrder, stop_price=%s limit_price=%s' % (self.stop_price, self.limit_price)
        elif self.orderType == 'TRAIL LIMIT':
            if self.trailing_amount is not None:
                string_output = 'TrailStopLimitOrder, stop_price=' + str(self.stop_price) \
                                + ' trailing_amount=' + str(self.trailing_amount) \
                                + ' limit_offset=' + str(self.limit_offset)
            if self.trailing_percent is not None:
                string_output = 'TrailStopLimitOrder, stop_price=' + str(self.stop_price) \
                                + ' trailing_percent=' + str(self.trailing_percent) \
                                + ' limit_offset=' + str(self.limit_offset)
        elif self.orderType == 'TRAIL':
            string_output = 'TrailStopLimitOrder:'
            if self.trailing_amount is not None:
                string_output += ' trailing_amount=%s' % (self.trailing_amount,)
            if self.trailing_percent is not None:
                string_output += ' trailing_percent=%s' % (self.trailing_percent,)
            if self.stop_price is not None:
                string_output += ' stop_price=%s' % (self.stop_price,)
        else:
            print(__name__ + '::OrderStyle:EXIT, cannot handle orderType=%s' % (self.orderType,))
            exit()
        return string_output


class MarketOrder(OrderStyle):
    def __init__(self, tif='DAY'):
        OrderStyle.__init__(self, orderType='MKT', tif=tif)


class StopOrder(OrderStyle):
    def __init__(self, stop_price, tif='DAY'):
        OrderStyle.__init__(self, orderType='STP', stop_price=stop_price, tif=tif)


class LimitOrder(OrderStyle):
    def __init__(self, limit_price, tif='DAY'):
        OrderStyle.__init__(self, orderType='LMT', limit_price=limit_price, tif=tif)


class StopLimitOrder(OrderStyle):
    def __init__(self, limit_price, stop_price, tif='DAY'):
        OrderStyle.__init__(self, orderType='STP LMT', limit_price=limit_price, stop_price=stop_price, tif=tif)


class TrailStopLimitOrder(OrderStyle):
    def __init__(self, stop_price, limit_offset, trailing_amount=None, trailing_percent=None, tif='DAY'):
        OrderStyle.__init__(self, orderType='TRAIL LIMIT',
                            stop_price=stop_price,
                            limit_offset=limit_offset,
                            # either limit_offset or limit_price, NOT BOTH, IBridgePy chooses to set limit_offset
                            trailing_amount=trailing_amount,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            trailing_percent=trailing_percent,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            tif=tif)


class TrailStopOrder(OrderStyle):
    def __init__(self, stop_price=None, trailing_amount=None, trailing_percent=None, tif='DAY'):
        OrderStyle.__init__(self, orderType='TRAIL',
                            stop_price=stop_price,
                            trailing_amount=trailing_amount,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            trailing_percent=trailing_percent,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            tif=tif)


class LimitOnCloseOrder(OrderStyle):
    def __init__(self, limit_price):
        OrderStyle.__init__(self, orderType='LOC', limit_price=limit_price)


class LimitOnOpenOrder(OrderStyle):
    def __init__(self, limit_price):
        OrderStyle.__init__(self, orderType='LOO', limit_price=limit_price)


# Quantopian compatible data structures
class Security(object):
    def __init__(self,
                 secType=None,
                 symbol=None,
                 currency='USD',
                 exchange='',  # default value, when IB returns contract
                 primaryExchange='',  # default value, when IB returns contract
                 expiry='',
                 strike=0.0,  # default value=0.0, when IB returns contract
                 right='',
                 multiplier='',  # default value, when IB returns contract
                 includeExpired=False,
                 sid=-1,
                 conId=0,  # for special secType, conId must be used.
                 localSymbol='',
                 security_name=None,
                 security_start_date=None,
                 security_end_date=None,
                 symbolStatus=SymbolStatus.DEFAULT):
        self.secType = secType
        self.symbol = symbol
        self.currency = currency
        self.exchange = exchange
        self.primaryExchange = primaryExchange
        self.expiry = expiry
        self.strike = strike
        self.right = right
        self.multiplier = multiplier
        self.includeExpired = includeExpired
        self.sid = sid
        self.conId = conId
        self.localSymbol = localSymbol
        self.security_name = security_name
        self.security_start_date = security_start_date
        self.security_end_date = security_end_date
        self.symbolStatus = symbolStatus

    def __str__(self):
        if self.secType in ['FUT', 'BOND']:
            return '%s,%s,%s,%s' % (self.secType, self.symbol, self.currency, self.expiry)
        elif self.secType == 'CASH':
            return 'CASH,%s,%s' % (self.symbol, self.currency)
        elif self.secType == 'OPT':
            return 'OPT,%s,%s,%s,%s,%s,%s' % (self.symbol, self.currency, self.expiry, self.strike, self.right, self.multiplier)
        else:
            return '%s,%s,%s' % (self.secType, self.symbol, self.currency)

    def __eq__(self, security):
        return self.full_print() == security.full_print()

    def __hash__(self):
        return id(self)

    def full_print(self):  # VERY IMPORTANT because context.portfolio.positions using security.full_print as the key.
        if self.secType in ['FUT', 'BOND']:
            return '%s,%s,%s,%s,%s,%s' % (self.secType, self.primaryExchange, self.exchange, self.symbol, self.currency, self.expiry)
        elif self.secType in ['CASH', 'STK', 'CMDTY', 'IND', 'CFD']:
            return '%s,%s,%s,%s,%s' % (self.secType, self.primaryExchange, self.exchange, self.symbol, self.currency)
        # strike needs to be formatted in same way. Otherwise, context.portfolio.positions[superSymbol[xxx]) will show 0
        # because strike is not the same.
        else:
            return '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (self.secType, self.primaryExchange, self.exchange, self.symbol, self.currency,
                                                      self.expiry, "{:10.2f}".format(self.strike), self.right, self.multiplier, self.localSymbol)


class QDataClass(object):
    """
    This is a wrapper to match quantopian's dataFromServer class
    """

    def __init__(self, parentTrader):
        self.data = {}
        self.dataHash = {}
        self.parentTrader = parentTrader

    def current(self, security, field):
        if type(security) == list and type(field) != list:
            ans = {}
            for ct in security:
                ans[ct] = self.current_one(ct, field)
            return pd.Series(ans)
        elif type(security) == list and type(field) == list:
            ans = {}
            for ct1 in field:
                ans[ct1] = {}
                for ct2 in security:
                    ans[ct1][ct2] = self.current_one(ct2, ct1)
            return pd.DataFrame(ans)
        elif type(security) != list and type(field) == list:
            ans = {}
            for ct in field:
                ans[ct] = self.current_one(security, ct)
            return pd.Series(ans)
        else:
            return self.current_one(security, field)

    def current_one(self, security, version):
        self.parentTrader.log.notset(__name__ + '::current_one')
        return self.parentTrader.show_real_time_price(security, version)

    def history(self, security, fields, bar_count, frequency):
        goBack = None
        if frequency == '1d':
            frequency = '1 day'
            if bar_count > 365:
                goBack = str(int(bar_count / 365.0) + 1) + ' Y'
            else:
                goBack = str(bar_count) + ' D'
        elif frequency == '1m':
            frequency = '1 min'
            goBack = str(bar_count * 60) + ' S'
        elif frequency == '30m':
            frequency = '30 mins'
            goBack = str(int(bar_count / 13.0) + 2) + ' D'
        elif frequency == '1 hour' or frequency == '1h':
            goBack = str(int(bar_count / 6.5) + 2) + ' D'
        else:
            print (__name__ + '::history: EXIT, cannot handle frequency=%s' % (str(frequency, )))
            exit()
        if type(security) != list:
            return self.history_one(security, fields, goBack, frequency).tail(bar_count)
        else:
            if type(fields) == str:
                ans = {}
                for sec in security:
                    ans[sec] = self.history_one(sec, fields, goBack, frequency).tail(bar_count)
                return pd.DataFrame(ans)
            else:
                tmp = {}
                for sec in security:
                    tmp[sec] = self.history_one(sec, fields, goBack, frequency).tail(bar_count)
                ans = {}
                for fld in fields:
                    ans[fld] = {}
                    for sec in security:
                        ans[fld][sec] = tmp[sec][fld]
                return pd.DataFrame(ans,
                                    columns=ans.keys())

    def history_one(self, security, fields, goBack, frequency):
        tmp = self.parentTrader.request_historical_data(security, frequency, goBack)
        tmp = tmp.assign(price=tmp.close)
        tmp['price'].fillna(method='pad')
        return tmp[fields]

    @staticmethod
    def can_trade(security):
        """
        This function is provided by Quantopian.
        IBridgePy supports the same function.
        However, as of 20180128, IBridgePy will not check if the str_security is
        tradeable.
        In the future, IBridgePy will check it.
        Input: Security
        Output: Bool
        """
        if security:  # Remove pep8 warning
            return True
        return True


class TimeBasedRules(object):
    def __init__(self, onNthMonthDay='any',
                 onNthWeekDay='any',
                 onHour='any',
                 onMinute='any',
                 onSecond='any',
                 func=None):
        self.onNthMonthDay = onNthMonthDay
        self.onNthWeekDay = onNthWeekDay  # Monday=0, Friday=4
        self.onHour = onHour
        self.onMinute = onMinute
        self.onSecond = onSecond
        self.func = func

    def __str__(self):
        return str(self.onNthMonthDay) + ' ' + str(self.onNthWeekDay) \
               + ' ' + str(self.onHour) + ' ' + str(self.onMinute) + ' ' + str(self.func)


# noinspection PyPep8Naming
class calendars(object):
    US_EQUITIES = (9, 30, 16, 0)
    US_FUTURES = (6, 30, 17, 0)


# noinspection PyPep8Naming
class time_rules(object):
    # noinspection PyPep8Naming
    class market_open(object):
        def __init__(self, hours=0, minutes=1):
            self.hour = hours
            self.minute = minutes
            self.second = 0
            self.version = 'market_open'

    # noinspection PyPep8Naming
    class market_close(object):
        def __init__(self, hours=0, minutes=1):
            self.hour = hours
            self.minute = minutes
            self.second = 0
            self.version = 'market_close'

    # noinspection PyPep8Naming
    class spot_time(object):
        def __init__(self, hour=0, minute=0, second=0):
            self.hour = hour
            self.minute = minute
            self.second = second
            self.version = 'spot_time'


# noinspection PyPep8Naming
class date_rules(object):
    # noinspection PyPep8Naming
    class every_day(object):
        def __init__(self):
            self.version = 'every_day'

    # noinspection PyPep8Naming
    class week_start(object):
        def __init__(self, days_offset=0):
            self.weekDay = days_offset
            self.version = 'week_start'

    # noinspection PyPep8Naming
    class week_end(object):
        def __init__(self, days_offset=0):
            self.weekDay = days_offset
            self.version = 'week_end'

    # noinspection PyPep8Naming
    class month_start(object):
        def __init__(self, days_offset=0):
            self.monthDay = days_offset
            self.version = 'month_start'

    # noinspection PyPep8Naming
    class month_end(object):
        def __init__(self, days_offset=0):
            self.monthDay = days_offset
            self.version = 'month_end'
