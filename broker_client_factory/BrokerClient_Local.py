#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
There is a risk of loss when trading stocks, futures, forex, options and other
financial instruments. Please trade with capital you can afford to
lose. Past performance is not necessarily indicative of future results.
Nothing in this computer program/code is intended to be a recommendation, explicitly or implicitly, and/or
solicitation to buy or sell any stocks or futures or options or any securities/financial instruments.
All information and computer programs provided here is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how to use these information and
are solely responsible any consequences of using these information.

If you have any questions, please send email to IBridgePy@gmail.com
All rights reserved.
"""

import datetime as dt
import os
import time
from sys import exit

import pytz

from BasicPyLib.BasicTools import dt_to_utc_in_seconds, utc_in_seconds_to_dt
from BasicPyLib.simpleLogger import SimpleLoggerClass
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.IbridgepyTools import simulate_commissions
from IBridgePy.constants import OrderStatus, LiveBacktest, BrokerName
from IBridgePy.quantopian import from_contract_to_security
from broker_client_factory.BrokerClientDefs import ReqAttr
from broker_client_factory.CallBacks import CallBacks
from models.utils import print_IBCpp_contract, print_IBCpp_order


class ClientLocalBroker(CallBacks):
    # Simulate the pending order book on IB server side.
    # keyed by ibpyOrderId, value = (contract, order)
    # Delete records when the order is executed by simulation.
    orderToBeProcessed = {}

    # MarketManagerBase::setup_service will provide a dataProvider
    _dataProvider = None

    # During backtesting, store transaction log to root/Output
    simulationOutput = None

    @property
    def name(self):
        return BrokerName.LOCAL_BROKER

    def getDataProvider(self):
        return self._dataProvider

    def setup_client_local_broker(self, log, accountCode, rootFolderPath, singleTrader, data, timeGenerator, dataProvider):
        self.setup(log, accountCode, rootFolderPath, singleTrader, data, timeGenerator, self.name)
        self._dataProvider = dataProvider
        # No other __init__ is required.

        self.log.debug(__name__ + '::setup_client_local_broker')
        self.setRunningMode(LiveBacktest.BACKTEST)  # IBCpp function

        # userLog is for the function of record (). User will use it for any reason.
        dateTimeStr = time.strftime("%Y_%m_%d_%H_%M_%S")
        self.simulationOutput = SimpleLoggerClass(filename='TransactionLog_' + dateTimeStr + '.txt', logLevel='NOTSET',
                                                  addTime=False, folderPath=os.path.join(rootFolderPath, 'Output'))

    def _sendHistoricalData(self, hist, reqId, formatDate):
        self.log.debug(__name__ + '::_sendHistoricalData: reqId=%s formatDate=%s' % (str(reqId), str(formatDate)))
        for idx in hist.index:
            if formatDate == 1:  # asked to return datetime in string
                date = utc_in_seconds_to_dt(float(idx))  # int ---> datetime
                date = date.strftime("%Y%m%d  %H:%M:%S")  # Must be UTC because requested time was cast to UTC
            else:  # asked to return UTC int
                date = str(idx)
            self.simulateHistoricalData(reqId, date,
                                        float(hist.loc[idx, 'open']),
                                        float(hist.loc[idx, 'high']),
                                        float(hist.loc[idx, 'low']),
                                        float(hist.loc[idx, 'close']),
                                        int(hist.loc[idx, 'volume']),
                                        1, 0.0, 1)
        self.simulateHistoricalData(reqId, 'finished', 0.0, 0.0, 0.0, 0.0, 1, 1, 0.0, 1)

    def _simulate_account_value_changes_deprecated(self, execution):
        """
        TotalCashValue: get it from singleTrader.get_account_info(self.name, accountCode, 'TotalCashValue')
        NetLiquidation: cash + positionValue
        GrossPositionValue: BrokerService_Local::_calculate_grossPositionValue
        """
        oldCashValue = self.singleTrader.get_account_info(self.name, self.accountCode, 'TotalCashValue')
        oldPortfolioValue = self.singleTrader.get_account_info(self.name, self.accountCode, 'NetLiquidation')
        oldPositionValue = self.singleTrader.get_account_info(self.name, self.accountCode, 'GrossPositionValue')
        commission = simulate_commissions(execution)
        newPortfolioValue = oldPortfolioValue - commission
        totalTradingValue = execution.shares * execution.price
        self.log.notset(
            __name__ + '::_simulate_account_value_changes: oldCashValue=%s oldPortfolioValue=%s oldPositionValue=%s totalTradingValue=%s'
            % (oldCashValue, oldPortfolioValue, oldPositionValue, totalTradingValue))
        newCashValue = 0.0  # avoid warning
        newPositionValue = 0.0  # avoid warning
        if execution.side == 'BOT':
            newCashValue = oldCashValue - totalTradingValue - commission
            newPositionValue = oldPositionValue + totalTradingValue
        elif execution.side == 'SLD':
            newCashValue = oldCashValue + execution.shares * execution.price - commission
            newPositionValue = oldPositionValue - execution.shares * execution.price

        self.simulateUpdateAccountValue('TotalCashValue', str(newCashValue), 'USD', self.accountCode)
        self.simulateUpdateAccountValue('NetLiquidation', str(newPortfolioValue), 'USD', self.accountCode)
        self.simulateUpdateAccountValue('GrossPositionValue', str(newPositionValue), 'USD', self.accountCode)

    def cancelOrderWrapper(self, ibpyOrderId):
        self.log.debug(__name__ + '::cancelOrderWrapper: ibpyOrderId=%s' % (ibpyOrderId,))
        int_orderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self.log.info('cancelOrder is sent to %s ibpyOrderId=%s' % (self.name, ibpyOrderId))
        try:
            del self.orderToBeProcessed[int_orderId]
        except KeyError:
            # print(self.orderToBeProcessed)
            self.log.error(__name__ + '::cancelOrderWrapper: EXIT, int_orderId=%s Maybe this order has been executed?' % (int_orderId,))
            exit()
        self.simulateOrderStatus(int_orderId, OrderStatus.CANCELLED, 0, 0, 0.0, 0, 0, 0, 0, '')
        self.error(int_orderId, 202, 'cancel order is confirmed')

    def connectWrapper(self):
        self.log.debug(__name__ + '::connectWrapper')
        return True

    def disconnectWrapper(self):
        self.log.debug(__name__ + '::disconnect')
        return True

    def reqCurrentTimeWrapper(self):
        tmp = dt_to_utc_in_seconds(self.get_datetime())
        self.simulateCurrentTime(int(tmp))  # IBCpp function

    def reqIdsWrapper(self):
        self.simulateNextValidId(1)

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot):
        """
        Just ignore reqMktData because the real time prices will be simulated
        :param reqId:
        :param contract:
        :param genericTickList:
        :param snapshot:
        :return:
        """
        self.log.debug(__name__ + '::reqMktDataWrapper: reqId=%s contract=%s genericTickList=%s snapshot=%s'
                       % (str(reqId, ), print_IBCpp_contract(contract), str(genericTickList), str(snapshot)))
        self.activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)
        self.processMessagesWrapper(self.timeGenerator.get_current_time())

    def reqPositionsWrapper(self):
        """
        Just ignore the request because initial positions will be set up.
        :return:
        """
        self.log.debug(__name__ + '::reqPositionsWrapper')
        self.simulatePositionEnd()

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        """
        In the backtest mode, just ignore this request
        Init accountUpdates will be simulated
        Later accountUpdates will be simulated when order is executed.
        :param subscribe:
        :param accountCode:
        :return:
        """
        self.log.debug(
            __name__ + '::reqAccountUpdatesWrapper: subscribe=%s accountCode=%s' % (str(subscribe), accountCode))
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountUpdates', ReqAttr.Status.COMPLETED)

        # Create dummy account info to start backtesting
        # TODO: the init state of backtesting should be configurable.
        self.simulateUpdateAccountValue('TotalCashValue', '100000.00', 'USD', accountCode)
        self.simulateUpdateAccountValue('NetLiquidation', '100000.00', 'USD', accountCode)
        self.simulateUpdateAccountValue('GrossPositionValue', '0.00', 'USD', accountCode)

    def reqAllOpenOrdersWrapper(self):
        """
        Just ignore the request because initial orders will be set up.
        :return:
        """
        self.log.debug(__name__ + '::reqAllOpenOrdersWrapper')
        self.simulateOpenOrderEnd()

    def reqHistoricalDataWrapper(self, reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        self.log.debug(__name__ + '::reqHistoricalDataWrapper: reqId = %s endTime=%s goBack=%s' % (reqId, endTime, goBack))
        if endTime == '':
            # endTime='' is acceptable for clientIB, but not for clientLocalBroker
            # When endTime is processed, it will be converted to string from datetime.
            # However, the strptime function has difficulty with some timezones, for example, 'EDT'
            # The safe way is to convert to UTC first.
            endTime = self.timeGenerator.get_current_time().astimezone(pytz.timezone('UTC'))
            endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string

        hist = self._dataProvider.provide_historical_data(from_contract_to_security(contract), endTime,
                                                          goBack, barSize, whatToShow, useRTH, formatDate)
        # completion signals here
        self._sendHistoricalData(hist, reqId, formatDate)

    def simulate_process_order(self, timeNow):  # to simulate placing order
        self.log.debug(__name__ + '::simulate_process_order: timeNow=%s' % (timeNow,))
        if len(self.orderToBeProcessed) == 0:
            self.log.debug(__name__ + '::processOrder: No order to process')
            return
        for int_orderId in list(self.orderToBeProcessed.keys())[:]:
            contract, order = self.orderToBeProcessed[int_orderId]
            security = from_contract_to_security(contract)

            ask_price, bid_price, high_price, low_price = \
                self._dataProvider.get_real_time_price(security, timeNow,
                                                       [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.HIGH, IBCpp.TickType.LOW])

            flag = False  # if a order meets the processing conditions

            # based on the current prices, decide which pending orders should be processed/simulated this round.
            ex_price = 0.0  # avoid PEP8 warning
            if order.orderType == 'MKT':  # for MKT order, just Fill it
                if order.action == 'BUY':
                    ex_price = ask_price
                else:
                    ex_price = bid_price
                flag = True
            elif order.orderType == 'LMT':
                # always assume simulation sequence: ask_price -> low_price -> high_price -> close_price
                if order.action == 'BUY':
                    if order.lmtPrice >= ask_price:
                        flag = True
                        ex_price = ask_price
                    elif low_price <= order.lmtPrice < ask_price:
                        flag = True
                        ex_price = order.lmtPrice
                    else:
                        flag = False
                else:  # SELL
                    if order.lmtPrice <= ask_price:
                        flag = True
                        ex_price = ask_price
                    elif ask_price < order.lmtPrice <= high_price:
                        flag = True
                        ex_price = order.lmtPrice
                    else:
                        flag = False

            elif order.orderType == 'STP':
                ex_price = order.auxPrice
                if order.action == 'BUY':
                    if order.auxPrice <= ask_price:
                        flag = True
                        ex_price = ask_price
                    elif ask_price < order.auxPrice <= high_price:
                        flag = True
                        ex_price = order.auxPrice
                    else:
                        flag = False
                else:
                    if order.auxPrice >= bid_price:
                        flag = True
                        ex_price = bid_price
                    elif low_price <= order.auxPrice < bid_price:
                        flag = True
                        ex_price = order.auxPrice
                    else:
                        flag = False
            else:
                self.log.error(__name__ + '::simulate_process_order: cannot handle order.orderType = %s' % (order.orderType,))
                exit()

            # this order should be processed/simulated right now
            if flag and ex_price > 0.001:
                # IBCpp call-back function
                self.simulateOrderStatus(int_orderId, 'Filled', order.totalQuantity, 0, ex_price, 0, 0, 0, 0, '')
                del self.orderToBeProcessed[int_orderId]

                # after an order is executed, need to simulate execDetails (call-back function)
                execution = IBCpp.Execution()
                execution.acctNumber = order.account
                execution.orderId = int_orderId
                if order.action == 'BUY':
                    execution.side = 'BOT'
                else:
                    execution.side = 'SLD'
                execution.shares = int(order.totalQuantity)
                execution.price = ex_price
                execution.orderRef = order.orderRef
                self.simulateExecDetails(-1, contract, execution, from_contract_to_security(contract).full_print())

                # IBCpp::simulatePosition needs more calculation because it needs to consider the current
                # positions.
                oldPosition = self.singleTrader.get_position(self.name, self.accountCode, security)
                # print(__name__ + '::simulate_process_order:: oldPosition=%s' % (position,))
                oldPrice = oldPosition.price
                hold = oldPosition.amount
                amount = None
                price = None
                if order.action == 'BUY':
                    if hold + order.totalQuantity != 0:
                        price = (oldPrice * hold + ex_price * order.totalQuantity) / (hold + order.totalQuantity)
                    else:
                        price = 0.0
                    amount = hold + order.totalQuantity

                elif order.action == 'SELL':
                    if hold == order.totalQuantity:
                        price = 0.0
                    else:
                        price = (oldPrice * hold - ex_price * order.totalQuantity) / (hold - order.totalQuantity)
                    amount = hold - order.totalQuantity
                self.simulatePosition(order.account, contract, amount, price,
                                      from_contract_to_security(contract).full_print())

                self.simulationOutput.info('%s %s %s %s %s %s'
                                           % (self.get_datetime(), execution.orderId,
                                              from_contract_to_security(contract).full_print(),
                                              execution.side, execution.shares, execution.price))
                # Do not need to simulate account value because updateAccountValue is fired after execDetails
                # self._simulate_account_value_changes(execution)

    def modifyOrderWrapper(self, contract, order, ibpyRequest):
        self.placeOrderWrapper(contract, order, ibpyRequest)

    def placeOrderWrapper(self, contract, order, ibpyRequest):
        self.log.debug(__name__ + '::placeOrderWrapper: contract=%s order=%s' % (print_IBCpp_contract(contract), print_IBCpp_order(order)))

        if isinstance(order.orderId, int):
            int_orderId = order.orderId
        else:
            int_orderId = self.nextId.useOne()
            order.orderId = int_orderId

        # Set for ending flat.
        # Otherwise, the following line in broker_client_factory::CallBacks::orderStatus will not be able to find a reqId
        # reqId = self.activeRequests.find_reqId_by_int_orderId(int_orderId)
        ibpyRequest.param['int_orderId'] = int_orderId

        ibpyOrderId = self._idConverter.fromIBtoBroker(int_orderId)

        # Register ibpyOrderId in SingleTrader so that it can search accountCode by incoming int_orderId
        self.singleTrader.set_from_send_req_to_server(self.name, order.account, ibpyOrderId)

        self.orderToBeProcessed[int_orderId] = (contract, order)
        self.simulateOpenOrder(int_orderId, contract, order, IBCpp.OrderState(),
                               from_contract_to_security(contract).full_print())  # IBCpp function
        self.simulateOrderStatus(int_orderId, 'Submitted', 0, order.totalQuantity, 0.0, 0, 0, 0, 0, '')  # IBCpp function
        self.simulate_process_order(self.get_datetime())

    def processMessagesWrapper(self, timeNow):
        self.log.notset(__name__ + '::processMessagesWrapper: timeNow=%s' % (timeNow,))
        # !!! Change to lazy provider, supply values per requested
        """
        tempDict = self.realTimePriceRequestedList.getAllStrSecurity()
        if len(tempDict) == 0:
            # self.log.error(__name__ + '::processMessagesWrapper: EXIT, no real time prices are requested yet')
            return True  # run Trader::repeat_function

        for str_security in tempDict:
            try:
                open_price, high_price, low_price, close_price, volume = \
                    self._dataProvider.get_real_time_price(str_security, timeNow,
                                                          [IBCpp.TickType.OPEN, IBCpp.TickType.HIGH,
                                                           IBCpp.TickType.LOW, IBCpp.TickType.CLOSE,
                                                           IBCpp.TickType.VOLUME])
            except AssertionError:
                self.log.error(
                    __name__ + '::processMessagesWrapper: str_security=%s timeNow=%s' % (str_security, timeNow))
                return False  # DO NOT run Trader::repeat_function because dataFromServer is not available

            reqId = tempDict[str_security]
            self.simulateTickPrice(reqId, IBCpp.TickType.OPEN, open_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.HIGH, high_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.LOW, low_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.CLOSE, close_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.LAST, close_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.ASK, close_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.BID, close_price, False, str_security)
            self.simulateTickSize(reqId, IBCpp.TickType.VOLUME, int(volume), str_security)
        return True  # run Trader::repeat_function because all dataFromServer is loaded
        """
        return True  # run Trader::repeat_function

    def add_exchange_to_security(self, security):
        """
        For brokerClientLocal, NO need to add exchange because the keys in dataProviderLocal.hist is
        str_security_without_exchange_primaryExchange
        :param security:
        :return:
        """
        pass

    def add_primaryExchange_to_security(self, security):
        """
        For brokerClientLocal, NO need to add primaryExchange because the keys in dataProviderLocal.hist is
        str_security_without_exchange_primaryExchange
        :param security:
        :return:
        """
        pass

