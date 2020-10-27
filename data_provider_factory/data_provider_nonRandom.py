# coding=utf-8
import bisect
import datetime as dt
import os
from sys import exit

import pandas as pd
import pytz

from BasicPyLib.BasicTools import dt_to_utc_in_seconds, utc_in_seconds_to_dt
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.IbridgepyTools import calculate_startTime, stripe_exchange_primaryExchange_from_security
from .data_provider import DataProvider


def _convert_strDatetime_to_epoch_int(aDatetime):
    # !!!!strptime silently discard tzinfo!!!
    aDatetime = dt.datetime.strptime(aDatetime, "%Y%m%d %H:%M:%S %Z")  # string -> dt.datetime
    aDatetime = pytz.timezone('UTC').localize(aDatetime)
    return int(dt_to_utc_in_seconds(aDatetime))


def _search_index_location_in_hist(hist, aDatetime):
    intDatetime = int(dt_to_utc_in_seconds(aDatetime))
    if intDatetime not in hist.index:
        indexPosition = bisect.bisect_left(hist.index, intDatetime)
        if indexPosition >= len(hist.index):
            indexPosition -= 1
        ans = indexPosition
        # print(__name__ + '::_search_index_location_in_hist: not in hist ans=%s' % (ans,))
        return ans
    else:
        ans = hist.index.get_loc(intDatetime)
        # print(__name__ + '::_search_index_location_in_hist: ans=%s' % (ans,))
        return ans


# !!! Everything will ONLY be used for backtester.!!!
class NonRandom(DataProvider):
    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        raise NotImplementedError

    def _ingest_hists(self, histIngestionPlan, funcToFetchHist):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        self.log.debug(__name__ + '::ingest_hists: loadingPlan=%s client=%s' % (histIngestionPlan, self.dataProviderClient))
        for plan in histIngestionPlan.finalPlan:
            security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(plan.security)
            str_security_no_exchange_primaryExchange = security_no_exchange_primaryExchange.full_print()
            barSize = plan.barSize.lower()
            if str_security_no_exchange_primaryExchange not in self.hist:
                self.hist[str_security_no_exchange_primaryExchange] = {}
            if barSize not in self.hist[str_security_no_exchange_primaryExchange]:
                self.hist[str_security_no_exchange_primaryExchange][barSize] = {}
            df_hist = funcToFetchHist(plan)
            self.hist[str_security_no_exchange_primaryExchange][barSize] = df_hist
            if histIngestionPlan.saveToFile:
                PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                targetDir = os.path.join(PROJECT_ROOT_DIR, 'Input')
                if not os.path.exists(targetDir):
                    os.mkdir(targetDir)
                targetFileFullName = os.path.join(targetDir, '%s_%s_%s.csv' % (plan.security, plan.barSize, plan.goBack))
                if os.path.exists(targetFileFullName):
                    print(__name__ + '::_ingest_hists: %s exists !!! Please delete it or rename it and try backtest again!' % (targetFileFullName,))
                    exit()
                df_hist.to_csv(targetFileFullName)
                self.log.info('Saved hist to %s' % (targetFileFullName,))
            print('ingested hist of security=%s barSize=%s' % (str_security_no_exchange_primaryExchange, barSize))
            try:
                print('1st line=%s' % (utc_in_seconds_to_dt(self.hist[str_security_no_exchange_primaryExchange][barSize].index[0], str_timezone='US/Eastern')))
                print('last line=%s' % (utc_in_seconds_to_dt(self.hist[str_security_no_exchange_primaryExchange][barSize].index[-1], str_timezone='US/Eastern')))
            except ValueError:
                self.log.error('security=%s barSize=%s index=%s is not valid. The format of index should be epoch time. Refer to https://www.epochconverter.com/' % (str_security_no_exchange_primaryExchange, barSize, self.hist[str_security_no_exchange_primaryExchange][barSize].index[0]))
                self.log.error('If you need help on coding, please refer to the well known Rent-a-Coder service https://ibridgepy.com/rent-a-coder/')
                exit()
        if len(self.hist) == 0:
            self.log.debug(__name__ + '::ingest_hists: EXIT, loading errors')
            exit()

    @property
    def name(self):
        return 'NonRandom'

    def get_one_real_time_price(self, security, timeNow, tickType, freq='1 min'):
        """
        Both of prices and volume will be provided.
        :param freq:
        :param security:
        :param timeNow:
        :param tickType: string ONLY
        :return:
        """
        security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(security)
        str_security = security_no_exchange_primaryExchange.full_print()
        if str_security not in self.hist:
            self.log.error(__name__ + '::get_one_real_time_prices: EXIT, Do not have hist for str_security=%s '
                                      'dataProvider=%s' % (str_security, self))
            print('keys in hist are:')
            for ct in self.hist:
                print(ct)
            exit()
        if freq not in self.hist[str_security]:
            self.log.error(__name__ + '::get_one_real_time_price: EXIT, hist of %s does not have freq=%s'
                           % (str_security, freq))
            exit()

        fieldName = None
        if tickType in [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.LAST, IBCpp.TickType.OPEN]:
            fieldName = 'open'
        elif tickType == IBCpp.TickType.HIGH:
            fieldName = 'high'
        elif tickType == IBCpp.TickType.LOW:
            fieldName = 'low'
        elif tickType == IBCpp.TickType.CLOSE:
            fieldName = 'close'
        elif tickType == IBCpp.TickType.VOLUME:
            fieldName = 'volume'
        else:
            self.log.error(__name__ + '::get_one_real_time_price: EXIT, cannot handle tickType=%s' % (tickType,))
            exit()

        timeNow = int(dt_to_utc_in_seconds(timeNow))
        hist = self.hist[str_security][freq]
        if timeNow in hist.index:
            ans = hist.loc[timeNow, fieldName]
            self.log.debug(
                __name__ + '::get_one_real_time_price: str_security=%s timeNow=%s tickType=%s returnedValue=%s'
                % (str_security, timeNow, tickType, ans))
            return ans
        else:
            # Solution: if timeNow is not in hist, then raise Exception. Maybe it is not a good idea
            # timeNow = utc_in_seconds_to_dt(timeNow).astimezone(self.showTimeZone)  # default is UTC
            # time1st = utc_in_seconds_to_dt(self.hist[str_security][freq].index[0]).astimezone(self.showTimeZone)
            # timeLast = utc_in_seconds_to_dt(self.hist[str_security][freq].index[-1]).astimezone(self.showTimeZone)
            # self.log.error(__name__ + '::get_one_real_time_prices: loaded hist does not have timeNow=%s' % (str(timeNow),))
            # self.log.error(__name__ + '::get_one_real_time_prices: loaded hist of security=%s from %s to %s'
            #                % (str_security,  time1st, timeLast))
            # raise AssertionError  # AssertionError will be caught by broker_client_factory::BrokerClient_Local.py::processMessagesWrapper

            # Solution 2: look for the timeBar immediately before timeNow, and use its value.
            timeNowPosition = bisect.bisect_left(hist.index, timeNow)
            if timeNowPosition >= len(hist.index):
                timeNowPosition -= 1
            ans = hist.iloc[timeNowPosition][fieldName]
            self.log.debug(
                __name__ + '::get_one_real_time_price: str_security=%s timeNow=%s tickType=%s returnedValue=%s'
                % (str_security, timeNow, tickType, ans))
            return ans

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
        self.log.debug(__name__ + '::provide_historical_data: endTime=%s goBack=%s barSize=%s' % (endTime, goBack, barSize))

        # Read in self.hist to provide data and check errors
        security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(security)
        securityFullPrint = security_no_exchange_primaryExchange.full_print()
        barSize = barSize.lower()
        if securityFullPrint not in self.hist:
            self.log.error(__name__ + '::provide_historical_data: EXIT, hist of %s is not ingested.' % (securityFullPrint,))
            exit()
        if barSize not in self.hist[securityFullPrint]:
            self.log.error(__name__ + '::provide_historical_data: EXIT, hist of %s exists but barSize=%s is not ingested.' % (securityFullPrint, barSize))
            print(self.hist[securityFullPrint].keys())
            exit()
        hist = self.hist[securityFullPrint][barSize]
        if not isinstance(hist, pd.DataFrame):
            self.log.error(__name__ + '::provide_historical_data: EXIT, hist is empty')
            exit()

        startTime, endTime = calculate_startTime(endTime, goBack, barSize)
        # There are some bugs here because of weekend issue: Monday go back 2 days will be Saturday and Saturday does not have data.

        # look for the location of endTime in hist.index
        endTimePosition = _search_index_location_in_hist(hist, endTime)
        startTimePosition = _search_index_location_in_hist(hist, startTime)
        # print('startTime', startTime, startTimePosition, dt_to_utc_in_seconds(startTime))
        # print('startTime', endTime, endTimePosition, dt_to_utc_in_seconds(endTime))
        # print(hist.tail(15))
        if startTimePosition >= len(hist) - 2:
            self.log.error(__name__ + '::provide_historical_data: EXIT, Not enough hist security=%s barSize=%s is provided to backtest.' % (securityFullPrint, barSize))
            self.log.error(__name__ + '::provide_historical_data: first line in hist=%s' % (utc_in_seconds_to_dt(hist.index[0])))
            self.log.error(__name__ + '::provide_historical_data: last line in hist=%s' % (utc_in_seconds_to_dt(hist.index[-1])))
            self.log.error(__name__ + '::provide_historical_data: backtest at this spot time=%s' % (startTime,))
            exit()

        if startTimePosition < endTimePosition:
            return hist.iloc[startTimePosition:endTimePosition + 1]
        else:
            self.log.error(__name__ + '::provide_historical_data: Incorrect endTime=%s or goBack=%s when barSize=%s' % (endTime, goBack, barSize))
            self.log.error(__name__ + '::provide_historical_data: Hint: startTime=%s endTime=%s Are they too close to each other?' % (startTime, endTime))
            self.log.error(__name__ + '::provide_historical_data: first line in hist=%s' % (utc_in_seconds_to_dt(hist.index[0])))
            self.log.error(__name__ + '::provide_historical_data: last line in hist=%s' % (utc_in_seconds_to_dt(hist.index[-1])))
            self.log.error(__name__ + '::provide_historical_data: Hint: Based on the 1st line and last line of the hist, Are hist data too short?')
            exit()
