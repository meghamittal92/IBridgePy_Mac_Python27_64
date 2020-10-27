# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.constants import BrokerName
from broker_client_factory.BrokerClientDefs import ReqMktData
from broker_service_factory.BrokerService_callback import CallBackType


# noinspection PyAbstractClass
class LocalBroker(CallBackType):
    def get_scanner_results(self, kwargs):
        raise NotImplementedError

    def get_option_greeks(self, security, tickType, fields):
        raise NotImplementedError

    @property
    def name(self):
        return BrokerName.LOCAL_BROKER

    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        if tag not in ['TotalCashValue', 'NetLiquidation', 'GrossPositionValue', 'BuyingPower']:
            self.log.error(__name__ + '::_get_account_info_one_tag: EXIT, cannot handle tag=%s' % (tag,))
            exit()
        ans = 0.0
        if tag in ['TotalCashValue', 'BuyingPower']:
            ans = self._get_TotalCashValue(accountCode)
        elif tag == 'GrossPositionValue':
            ans = self._calculate_grossPositionValue(accountCode)
        elif tag == 'NetLiquidation':
            ans = self._get_TotalCashValue(accountCode) + self._calculate_grossPositionValue(accountCode)
        self.log.debug(__name__ + '::_get_account_info_one_tag: accountCode=%s tag=%s' % (accountCode, tag))
        return ans

    def _calculate_grossPositionValue(self, accountCode):
        self.log.notset(__name__ + '::_calculate_grossPositionValue: accountCode=%s' % (accountCode,))
        allPositions = self.get_all_positions(accountCode)
        ans = 0.0
        for security in allPositions:
            currentPrice = self.get_real_time_price(security, IBCpp.TickType.LAST)
            share = allPositions[security].amount
            ans += currentPrice * share
            self.log.debug(__name__ + '::_calculate_grossPositionValue: security=%s share=%s currentPrice=%s sum=%s' % (security, share, currentPrice, ans))
        self.log.debug(__name__ + '::_calculate_grossPositionValue: accountCode=%s returnedValue=%s' % (accountCode, ans))
        return ans

    def _get_TotalCashValue(self, accountCode):
        ans = self._singleTrader.get_account_info(self.name, accountCode, 'TotalCashValue')
        if ans is None:
            self.log.error(__name__ + '::_get_TotalCashValue: EXIT, no value based on accountCode=%s tag=TotalCashValue' % (accountCode,))
            print('active accountCode is %s' % (self._singleTrader.get_all_active_accountCodes(self.name),))
            print(self._singleTrader)
            exit()
        self.log.debug(__name__ + '::_get_TotalCashValue: accountCode=%s returnedValue=%s' % (accountCode, ans))
        return ans

    def get_real_time_price(self, security, tickType):
        """
        Different than other brokerService because this way is faster for backtesting
        :param security:
        :param tickType:
        :return:
        """
        ans = self._brokerClient.getDataProvider().get_one_real_time_price(security, self.get_datetime(), tickType)
        self.log.debug(__name__ + '::get_real_time_price: security=%s tickType=%s returnedValue=%s' % (security, tickType, ans))
        return ans

    def get_real_time_size(self, security, tickType):
        return self.get_real_time_price(security, tickType)

    def get_timestamp(self, security, tickType):
        self.log.notset(__name__ + '::get_timestamp: security=%s tickType=%s' % (security, tickType))
        # if the request of real time price is not already submitted
        # submit_requests guarantee valid ask_price and valid bid_price
        if not self._brokerClient.check_if_real_time_price_requested(security):
            self.submit_requests(ReqMktData(security))
        return self._dataFromServer.get_value(security, tickType, 'timestamp')
