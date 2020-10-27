# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""
from IBridgePy.constants import DataProviderName
from data_provider_factory.data_provider import DataProvider
from BasicPyLib.BasicTools import roundToMinTick, create_random_hist
from IBridgePy.IbridgepyTools import calculate_startTime, stripe_exchange_primaryExchange_from_security
import random
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from sys import exit


def barSizeTransformer(barSize):
    transfer = {'1 second': '1S',
                '1 minute': '1T',
                '1 min': '1T',
                '1 hour': '1H',
                '4 hours': '4H',
                '1 day': '1D'}
    return transfer.get(barSize)


class RandomDataProvider(DataProvider):
    # Used as a cache to speed up
    _lastRealTimePrice = {}

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        pass

    @property
    def name(self):
        return DataProviderName.RANDOM

    def get_one_real_time_price(self, security, timeNow, tickType, freq='dummy'):
        # Store the last value, be prepared that this function is fired twice at one timeNow
        security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(security)
        str_security = security_no_exchange_primaryExchange.full_print()
        if (str_security, timeNow, tickType) in self._lastRealTimePrice:
            self.log.notset(__name__ + '::get_one_real_time_price: str_security=%s timeNow=%s tickType=%s returnedValue=SavedValue'
                            % (str_security, timeNow, tickType))
            return self._lastRealTimePrice[(str_security, timeNow, tickType)]

        ans = -1
        if tickType in [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.LAST, IBCpp.TickType.OPEN,
                        IBCpp.TickType.HIGH, IBCpp.TickType.LOW, IBCpp.TickType.CLOSE]:
            ans = roundToMinTick(random.uniform(50, 100))
        elif tickType in [IBCpp.TickType.VOLUME, IBCpp.TickType.BID_SIZE, IBCpp.TickType.ASK_SIZE]:
            ans = roundToMinTick(random.uniform(10000, 50000), 1)
        else:
            self.log.error(__name__ + '::get_one_real_time_price: EXIT, do not support tickType=%s' % (str(tickType),))
            exit()
        self._lastRealTimePrice[(str_security, timeNow, tickType)] = ans
        if tickType == IBCpp.TickType.CLOSE:
            self._lastRealTimePrice[(str_security, timeNow, IBCpp.TickType.ASK)] = ans
            self._lastRealTimePrice[(str_security, timeNow, IBCpp.TickType.BID)] = ans
        self.log.notset(__name__ + '::get_one_real_time_price: str_security=%s timeNow=%s tickType=%s returnedValue=%s'
                        % (str_security, timeNow, tickType, ans))
        return ans

    def provide_historical_data(self, security, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        """
        endTime: string with timezone of UTC !!!
        :return: pd.DataFrame('open', 'high', 'low', 'close', 'volume'), index = datetime
        """
        self.log.debug(__name__ + '::get_historical_data: security=%s endTime=%s goBack=%s barSze=%s whatToShow=%s useRTH=%s formatDate=%s' % (security.full_print(), endTime, goBack, barSize, whatToShow, useRTH, formatDate))
        startTime, endTime = calculate_startTime(endTime, goBack, barSize)
        self.log.debug(__name__ + '::get_historical_data: startTime=%s endTime=%s' % (startTime, endTime))
        return create_random_hist(startTime, endTime, barSizeTransformer(barSize), miniTick=0.01)
