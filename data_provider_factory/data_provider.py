# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""


# !!! Everything will only be used for backtester.!!!
class DataProvider(object):
    def __init__(self, log, dataProviderClient):
        # these are needed to construct an instance
        self.log = log
        self.dataProviderClient = dataProviderClient

        # The format of self.hist should be self.hist[str_security][barSize] = pandas.df
        # str_security should not have exchange and primaryExchange so that local brokerService does not need to
        # get exchange and primaryExchange
        # self.hist should be loaded by self.dataProvider.get_historical_data()
        self.hist = {}

    @property
    def name(self):
        """
        Name of the data provider

        :return: string name
        """
        raise NotImplementedError()

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        raise NotImplementedError

    # !!! the returned price will only be used for backtester.!!!
    def get_real_time_price(self, security, timeNow, tickType):
        self.log.notset(__name__ + '::get_real_time_price: security=%s timeNow=%s tickType=%s' % (security.full_print(), timeNow, tickType))
        if isinstance(tickType, list):
            ans = []
            for ct in tickType:
                ans.append(self.get_one_real_time_price(security, timeNow, ct))
            return ans
        else:
            return self.get_one_real_time_price(security, timeNow, tickType)

    def get_one_real_time_price(self, security, timeNow, tickType, freq='1 min'):
        """

        :param freq:
        :param security:
        :param timeNow:
        :param tickType: string ONLY
        :return:
        """
        raise NotImplementedError

    # !!! the returned hist will only be used for backtester.!!!
    def provide_historical_data(self, security, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        """

        :param security: IBridgePy::quantopian::Security
        :param endTime: request's ending time with format yyyyMMdd HH:mm:ss {TMZ} ---from IB api doc
        :param goBack:
        :param barSize: string 1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins,
                                30 mins, 1 hour, 1 day
        :param whatToShow:
        :param useRTH:
        :param formatDate:
        :return:
        """
        raise NotImplementedError
