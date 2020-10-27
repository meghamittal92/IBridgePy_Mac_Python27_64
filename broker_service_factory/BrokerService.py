# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""
import datetime as dt

import pytz

from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_security, choose_whatToShow
from IBridgePy.constants import SymbolStatus, OrderStatus
from IBridgePy.quantopian import from_contract_to_security
from broker_client_factory.BrokerClientDefs import CancelOrder, ReqHistoricalData, PlaceOrder
from sys import exit


class BrokerService(object):
    # aTrader will call brokerService
    # brokerService will call dataProvider
    # brokerService and brokerClient will call each other
    # set by IBridgePy::MarketManagerBase::setup_services
    def __init__(self, log, brokerClient, timeGenerator, singleTrader, dataFromServer):
        self.log = log
        self._brokerClient = brokerClient

        # timeGenerator, singleTrader, dataFromServer must be shared between brokerService and brokerClient
        # so that they are synced, singleton  TODO: make a singleton factory
        self._timeGenerator = timeGenerator
        self._singleTrader = singleTrader
        self._dataFromServer = dataFromServer

        self.log.notset(__name__ + '::__init__')

    @property
    def name(self):
        """
        Name of the broker

        :return: string name
        """
        raise NotImplementedError(self.name)

    @property
    def versionNumber(self):
        return self._brokerClient.versionNumber

    def getBrokerClient(self):
        return self._brokerClient

    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        raise NotImplementedError

    def _get_real_time_price_from_dataFromServer(self, security, tickType):  # return real time price
        self.log.notset(__name__ + '::_get_real_time_price_from_dataFromServer: security=%s tickType=%s' % (security.full_print(), tickType))

        ans = self._dataFromServer.get_value(security, tickType, 'price')
        if ans is None:  # the request has been sent out but no callback value has been received yet. -1 = request is out but no real value yet.
            ans = -1
        self.log.debug(__name__ + '::_get_real_time_price_from_dataFromServer: security=%s tickType=%s returnedValue=%s' % (security, tickType, ans))
        return ans

    def _get_real_time_size_from_dataFromServer(self, security, tickType):  # return real time price
        self.log.debug(__name__ + '::_from_dataFromServer: security=%s tickType=%s' % (security, tickType))
        return self._dataFromServer.get_value(security, tickType, 'size')

    def _get_position(self, accountCode, security):
        """
        Guarantee to return a PositionRecord even if there is no current position.
        :param accountCode:
        :param security:
        :return: Guarantee to return a PositionRecord
        """
        adj_security = stripe_exchange_primaryExchange_from_security(security)
        self.log.debug(__name__ + '::_get_position: adj_security=%s' % (adj_security.full_print(),))
        return self._singleTrader.get_position(self.name, accountCode, adj_security)

    def _get_all_positions(self, accountCode):
        allPositions = self._singleTrader.get_all_positions(self.name, accountCode)
        ans = {}
        for str_security in allPositions:
            contract = allPositions[str_security].contract
            security = from_contract_to_security(contract)
            # adj_security = self.add_exchange_primaryExchange_to_security(security)
            # ans[adj_security] = allPositions[str_security]
            ans[security] = allPositions[str_security]
        return ans

    def _get_all_orders(self, accountCode):
        """

        :param accountCode:
        :return: dict Keyed by ibpyOrderId, value = models::Order::IbridgePyOrder
        """
        self.log.debug(__name__ + '::_get_all_orders: accountCode=%s' % (accountCode,))
        return self._singleTrader.get_all_orders(self.name, accountCode)

    def add_exchange_primaryExchange_to_security(self, security):
        self.log.debug(__name__ + '::add_exchange_primaryExchange_to_security: security=%s' % (security.full_print(),))
        if security.symbolStatus == SymbolStatus.SUPER_SYMBOL:  # add superSymbol into security_info so that user does not need to write them in security_info.csv again
            self._brokerClient.append_security_info(security)
        else:
            if not security.exchange:
                self._brokerClient.add_primaryExchange_to_security(security)
                self._brokerClient.add_exchange_to_security(security)
            # https://ibridgepy.com/knowledge-base/#Q_I_requested_STK_NASDAQTSLAUSD_but_saw_this_error_8220No_security_definition_found8221
            elif security.exchange == 'NASDAQ':
                security.exchange = 'ISLAND'

    def cancel_order(self, ibpyOrderId):
        """
        Cancel order by its ibpyOrderId
        :param ibpyOrderId: string
        :return: None
        """
        self.log.debug(__name__ + '::cancel_order: ibpyOrderId=%s' % (ibpyOrderId,))
        self.submit_requests(CancelOrder(ibpyOrderId))

    def connect(self):
        self.log.debug(__name__ + '::connect')
        return self._brokerClient.connectWrapper()

    def disconnect(self):
        self._brokerClient.disconnectWrapper()

    # Only used by MarketManagerBase
    def get_next_time(self):
        self.log.notset(__name__ + '::get_next_time')
        return self._timeGenerator.get_next_time()

    def get_account_info(self, accountCode, tags, meta='value'):  # get account related info
        self.log.debug(__name__ + '::get_account_info: accountCode=%s tags=%s' % (accountCode, tags))
        if isinstance(tags, str):
            return self._get_account_info_one_tag(accountCode, tags, meta)
        elif isinstance(tags, list):
            ans = []
            for tag in tags:
                ans.append(self._get_account_info_one_tag(accountCode, tag, meta))
            return ans

    # Used by aTrader and
    def get_datetime(self):
        """
        Get IB server time
        :return: datetime in UTC timezone
        """
        ans = self._timeGenerator.get_current_time()
        self.log.notset(__name__ + '::get_datetime=%s' % (ans,))
        return ans

    def get_active_accountCodes(self):
        """
        get a list of accountCodes from IB server to check if the user-input accountCode is acceptable.
        :return:
        """
        self.log.debug(__name__ + '::get_active_accountCodes')
        return self._singleTrader.get_all_active_accountCodes(self.name)

    def get_all_open_orders(self, accountCode):
        self.log.debug(__name__ + '::get_all_open_orders: accountCode=%s' % (accountCode,))
        allOrders = self.get_all_orders(accountCode)  # Return a dict, keyed by ibpyOrderId, value = models::Order::IbridgePyOrder
        ans = []
        for ibpyOrderId in allOrders:
            status = allOrders[ibpyOrderId].status
            if status in [OrderStatus.APIPENDING, OrderStatus.PENDINGSUBMIT, OrderStatus.PENDINGCANCEL,
                          OrderStatus.PRESUBMITTED, OrderStatus.SUBMITTED]:
                ans.append(allOrders[ibpyOrderId])
        return ans

    def get_all_orders(self, accountCode):
        raise NotImplementedError(self.name)

    def get_all_positions(self, accountCode):
        """
        Get all of positionRecords associated with the accountCode
        :param accountCode:
        :return: dictionary, keyed by Security object with exchange info!!!, value = PositionRecord
        """
        raise NotImplementedError(self.name)

    def get_contract_details(self, security, field):
        raise NotImplementedError(self.name)

    def get_historical_data(self, security, barSize, goBack, endTime=None, whatToShow='', useRTH=1, formatDate=1,
                            waitForFeedbackInSeconds=30, timezoneOfReturn=pytz.timezone('US/Eastern')):
        """
        :param timezoneOfReturn:
        :param security: Security
        :param barSize: string
        barSize can be any of the following values(string)
        1 sec, 5 secs,15 secs,30 secs,1 min,2 mins,3 mins,5 mins,15 mins,30 mins,1 hour,1 day
        :param goBack: string
        :param endTime: default value is '', IB server deems '' as the current server time.
        If user wants to supply a value, it must be a datetime with timezone
        :param whatToShow: string
        whatToShow: see IB documentation for choices
        TRADES,MIDPOINT,BID,ASK,BID_ASK,HISTORICAL_VOLATILITY,OPTION_IMPLIED_VOLATILITY
        :param useRTH: int 1=within regular trading hours, 0=ignoring RTH
        :param formatDate: int 1= Return datetime 2 = Return epoch seconds
        :param waitForFeedbackInSeconds:
        :return: a dataFrame, keyed by a datetime with timezone UTC, columns = ['open', 'high', 'low', 'close', 'volume']
                The latest time record at the bottom of the dateFrame.
        """

        self.log.debug(__name__ + '::get_historical_data: security=%s barSize=%s goBack=%s endTime=%s whatToShow=%s useRTH=%s formatDate=%s waitForFeedbackInSeconds=%s' % (security, barSize, goBack, endTime, whatToShow, useRTH, formatDate, waitForFeedbackInSeconds))

        # all request datetime MUST be switched to UTC then submit to IB
        if endTime is not None and endTime is not '':
            if endTime.tzinfo is None:
                self.log.error(__name__ + '::request_historical_data: EXIT, endTime=%s must have timezone' % (endTime,))
                exit()
            endTime = endTime.astimezone(tz=pytz.utc)
            endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
        if whatToShow == '':
            whatToShow = choose_whatToShow(security.secType)
        orderIdList = self.submit_requests(ReqHistoricalData(security, barSize, goBack, endTime, whatToShow,
                                                             useRTH, formatDate, waitForFeedbackInSeconds,
                                                             timezoneOfReturn))
        return self._brokerClient.get_submit_requests_result(orderIdList[0])  # return a pandas dataFrame

    def get_order(self, ibpyOrderId):
        """

        :param ibpyOrderId: string
        :return: broker_factory::records_def::IBridgePyOrder
        """
        raise NotImplementedError(self.name)

    def get_position(self, accountCode, security):
        raise NotImplementedError(self.name)

    def get_real_time_price(self, security, tickType):
        raise NotImplementedError(self.name)

    def get_timestamp(self, security, tickType):
        raise NotImplementedError(__name__ + '::get_timestamp: %s' % (self.name,))

    def get_real_time_size(self, security, tickType):
        raise NotImplementedError(self.name)

    def order_status_monitor(self, ibpyOrderId, target_status, waitingTimeInSeconds=30):
        raise NotImplementedError(self.name)

    def place_order(self, ibridgePyOrder, followUp=True, waitForFeedbackInSeconds=30):
        self.log.debug(__name__ + '::place_order: ibridgePyOrder=%s' % (ibridgePyOrder,))
        contract = ibridgePyOrder.requestedContract
        order = ibridgePyOrder.requestedOrder
        reqIdList = self.submit_requests(PlaceOrder(contract=contract, order=order, followUp=followUp,
                                                    waitForFeedbackInSeconds=waitForFeedbackInSeconds))
        return self._brokerClient.get_submit_requests_result(reqIdList[0])  # return ibpyOrderId

    def processMessages(self, timeNow):
        self.log.notset(__name__ + '::processMessages')
        return self._brokerClient.processMessagesWrapper(timeNow)

    def submit_requests(self, *args):
        """

        :param args: broker_client_factory::BrokerClientDefs::Request
        :return: a list of reqId !!!
        """
        self.log.debug(__name__ + '::submit_requests')
        return self._brokerClient.request_data(*args)

    # Only used by aTrader
    def use_next_id(self):
        return self._brokerClient.use_next_id()
