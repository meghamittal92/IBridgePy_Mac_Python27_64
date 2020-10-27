# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""
import datetime as dt

import pytz

from IBridgePy.IbridgepyTools import choose_whatToShow
from IBridgePy.constants import BrokerName
from broker_client_factory.BrokerClientDefs import ReqHistoricalData
from .data_provider_nonRandom import NonRandom


# !!! Everything will ONLY be used for backtester.!!!
class IB(NonRandom):
    @property
    def name(self):
        return BrokerName.IB

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        self.dataProviderClient.connectWrapper()
        self._ingest_hists(histIngestionPlan, self._get_hist_from_IB)
        self.dataProviderClient.disconnectWrapper()

    # dataProviderClient will be provided by MarketManagerBase::setup_service.
    # The real BrokerClient_IB will be provided to retrieve data from IB.
    def _get_hist_from_IB(self, plan):
        self.log.debug(__name__ + '::_get_hist_from_IB')
        endTime = plan.endTime.astimezone(pytz.timezone('UTC'))
        endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
        self.dataProviderClient.add_exchange_to_security(plan.security)
        self.dataProviderClient.add_primaryExchange_to_security(plan.security)
        # the return of request_data is reqId.
        # To get the content of hist, call brokerService::request_historical_data
        whatToShow = choose_whatToShow(plan.security.secType)
        reqIds = self.dataProviderClient.request_data(ReqHistoricalData(plan.security,
                                                                        plan.barSize,
                                                                        plan.goBack,
                                                                        endTime,
                                                                        whatToShow))

        # only reqId is returned
        hist = self.dataProviderClient.get_submit_requests_result(reqIds[0])
        # hist.to_csv('%s_%s_%s.csv' % (plan.security, plan.barSize, plan.goBack))
        return hist
