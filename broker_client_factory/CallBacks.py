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
from sys import exit

import pandas as pd

from BasicPyLib.BasicTools import dt_to_utc_in_seconds, utc_in_seconds_to_dt
from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_contract
from IBridgePy.quantopian import from_contract_to_security
from broker_client_factory.BrokerClient import BrokerClientBase
from broker_client_factory.BrokerClientDefs import ReqAttr
from models.AccountInfo import UpdateAccountValueRecord, AccountSummaryRecord
from models.Data import TickPriceRecord, TickSizeRecord, TickStringRecord, TickOptionComputationRecord
from models.Order import OrderStatusRecord, OpenOrderRecord, ExecDetailsRecord
from models.Position import PositionRecord
from models.utils import print_IBCpp_contract, print_IBCpp_order, print_IBCpp_orderState, print_IBCpp_execution, \
    print_IBCpp_contractDetails

# https://www.interactivebrokers.com/en/software/api/apiguide/tables/tick_types.htm
MSG_TABLE = {0: 'bid size', 1: 'bid price', 2: 'ask price', 3: 'ask size',
             4: 'last price', 5: 'last size', 6: 'daily high', 7: 'daily low',
             8: 'daily volume', 9: 'close', 14: 'open', 27: 'option call open interest', 28: 'option put open interest'}


# noinspection PyAbstractClass
class CallBacks(BrokerClientBase):
    def accountDownloadEnd(self, accountCode):
        """
        Responses of reqAccountUpdates
        """
        self.log.debug(__name__ + '::accountDownloadEnd: accountCode=%s' % (accountCode,))
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountUpdates', ReqAttr.Status.COMPLETED)

    def accountSummary(self, reqId, accountCode, tag, value, currency):
        """
        !!!!!!!! type(value) is STRING !!!!!!!!
        """
        self.log.notset(__name__ + '::accountSummary: reqId=%s accountCode=%s tag=%s value=%s currency=%s'
                        % (str(reqId), accountCode, tag, str(value), currency))
        if not isinstance(value, float):
            value = float(value)
        self.singleTrader.set_accountSummary(self.name, accountCode,
                                             AccountSummaryRecord(reqId, accountCode, tag, value, currency))

    def accountSummaryEnd(self, reqId):
        self.log.debug(__name__ + '::accountSummaryEnd: ' + str(reqId))
        self.activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)

    def bondContractDetails(self, reqId, contractDetails):
        """
        IB callback function to receive str_security info
        """
        self.log.info(__name__ + '::bondContractDetails:' + str(reqId))
        aRequest = self.activeRequests.get_by_reqId_otherwise_exit(reqId)
        newRow = pd.DataFrame({'right': contractDetails.summary.right,
                               'strike': float(contractDetails.summary.strike),
                               # 'expiry':dt.datetime.strptime(contractDetails.summary.expiry, '%Y%m%d'),
                               'expiry': contractDetails.summary.expiry,
                               'contractName': print_IBCpp_contract(contractDetails.summary),
                               'str_security': contractDetails.summary,
                               'multiplier': contractDetails.summary.multiplier,
                               'contractDetails': contractDetails
                               }, index=[len(aRequest.returnedResult)])
        aRequest.returnedResult = aRequest.returnedResult.append(newRow)

    def commissionReport(self, commissionReport):
        self.log.notset(__name__ + '::commissionReport: DO NOTHING' + str(commissionReport))

    def contractDetails(self, reqId, contractDetails):
        """
        IB callback function to receive str_security info
        """
        self.log.notset(__name__ + '::contractDetails: reqId=%s contractDetails=%s' % (reqId, print_IBCpp_contractDetails(contractDetails)))
        aRequest = self.activeRequests.get_by_reqId_otherwise_exit(reqId)
        newRow = pd.DataFrame({'right': contractDetails.summary.right,
                               'strike': float(contractDetails.summary.strike),
                               'expiry': contractDetails.summary.expiry,
                               'contractName': print_IBCpp_contract(contractDetails.summary),
                               'security': from_contract_to_security(contractDetails.summary),
                               'contract': contractDetails.summary,
                               'multiplier': contractDetails.summary.multiplier,
                               'contractDetails': contractDetails
                               }, index=[len(aRequest.returnedResult)])
        aRequest.returnedResult = aRequest.returnedResult.append(newRow)

    def contractDetailsEnd(self, reqId):
        """
        IB callback function to receive the ending flag of str_security info
        """
        self.log.debug(__name__ + '::contractDetailsEnd:' + str(reqId))
        self.activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)

    def currentTime(self, tm):
        """
        IB C++ API call back function. Return system time in datetime instance
        constructed from Unix timestamp using the showTimeZone from MarketManager
        """
        self.log.debug(__name__ + '::currentTime: tm=%s' % (str(tm),))
        serverTime = utc_in_seconds_to_dt(float(tm))
        localServerTimeDiff = serverTime - self.timeGenerator.get_current_time()
        self.timeGenerator.set_diffBetweenLocalAndServer(localServerTimeDiff)
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqCurrentTime', ReqAttr.Status.COMPLETED)

    def error(self, errorId, errorCode, errorString):
        """
        errorId can be either reqId or orderId or -1
        only print real error messages, which is errorId < 2000 in IB's error
        message system, or program is in debug mode
        """
        self.log.debug(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorString))
        if errorCode in [1100, 1101, 1102]:
            if errorCode == 1100:
                # Your TWS/IB Gateway has been disconnected from IB servers. This can occur because of an
                # internet connectivity issue, a nightly reset of the IB servers, or a competing session.
                self.connectionGatewayToServer = False
            elif errorCode in [1101, 1102]:
                # 1101
                # The TWS/IB Gateway has successfully reconnected to IB's servers. Your market dataFromServer requests have
                # been lost and need to be re-submitted.
                # 1102
                # The TWS/IB Gateway has successfully reconnected to IB's servers. Your market dataFromServer requests have been
                # recovered and there is no need for you to re-submit them.
                self.connectionGatewayToServer = True

        elif errorCode in [2103, 2104, 2105, 2106, 2107, 2108, 2110, 2119, 2157, 2158]:
            if errorCode in [2103, 2157]:
                # errorCode=2157 errorMessage=Sec-def data farm connection is broken:secdefnj

                self.connectionMarketDataFarm = False
            elif errorCode in [2104, 2108, 2158]:
                # errorCode=2158 errorMessage=Sec-def data farm connection is OK:secdefnj
                self.connectionMarketDataFarm = True
            elif errorCode == 2105:
                # 2105 = HMDS dataFromServer farm connection is broken:ushmds
                self.connectionHistDataFarm = False
            elif errorCode in [2106, 2107]:
                self.connectionHistDataFarm = True
            elif errorCode == 2110:
                # Connectivity between TWS and server is broken. It will be restored automatically.
                self.connectionGatewayToServer = False
                self.connectionHistDataFarm = False
                self.connectionMarketDataFarm = False

        elif errorCode in [202, 10147, 10148]:
            # 202: cancel order is confirmed
            # 10148, error message: OrderId 230 that needs to be cancelled can not be cancelled, state: Cancelled.
            # 10147, error message: OrderId 2 that needs to be cancelled is not found.
            # errorId is OrderId in this case
            self.activeRequests.set_a_request_of_an_orderId_to_a_status(errorId, ReqAttr.Status.COMPLETED)

        elif errorCode in [201, 399, 165, 2113, 2148]:  # No action, just show error message
            # 201 = order rejected - Reason: No such order
            # 201 errorMessage=Order rejected - reason:CASH AVAILABLE: 28328.69; CASH NEEDED FOR THIS ORDER AND OTHER PENDING ORDERS: 56477.64
            self.log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorString))

        elif errorCode == 162:
            if 'API scanner subscription cancelled' in errorString:
                self.activeRequests.set_a_request_of_a_reqId_to_a_status(errorId, ReqAttr.Status.COMPLETED)
                return  # not a true error
            else:
                self.log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorString))
                self._print_version_and_exit()

        elif 110 <= errorCode <= 449:
            self.log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorString))
            if errorCode == 200:
                # 200 = No security definition has been found for the request.
                # print(self.allRequests.keys())
                reqId = self.activeRequests.find_reqId_by_int_orderId(errorId)
                self.log.error(print_IBCpp_contract(self.allRequests[reqId].param['contract']))

                # A special case.
                # The connectivity is lost during reqHistoricalData.
                # If get 200 at this moment, it is a fake error.
                if (self.connectionGatewayToServer is False) or (self.connectionHistDataFarm is False):
                    self.log.error(__name__ + '::error: <No security definition has been found for the request> might be a false statement because connectivity to IB server is lost.')
                    return
            self._print_version_and_exit()
        elif 994 <= errorCode <= 999 or 972 <= errorCode <= 978:
            self.log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorString))
            self.log.error('Hint: Please refer to YouTube tutorial https://youtu.be/pson8T5ZaRw')
            self._print_version_and_exit()
        else:
            self.log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorString))
            self._print_version_and_exit()

    def _print_version_and_exit(self):
        self.log.error(__name__ + ':EXIT IBridgePy version= %s' % (str(self.versionNumber),))
        exit()

    def _error_exit(self):
        if self.connectionGatewayToServer:
            self.log.error(__name__ + ': Connection between Gateway/TWS to IB server is broken. Please check internet connection or try it later. Or maybe IB server is under maintenance.')
        if self.connectionHistDataFarm:
            self.log.error(__name__ + ': Connection between Gateway/TWS to IB Historical Data farm is broken. Please check internet connection or try it later. Or maybe IB server is under maintenance.')
        if self.connectionMarketDataFarm:
            self.log.error(__name__ + ': Connection between Gateway/TWS to IB Market Data Farm is broken. Please check internet connection or try it later. Or maybe IB server is under maintenance.')
        self._print_version_and_exit()

    def execDetails(self, reqId, contract, execution):
        """
        !!!!!! reqId is always -1 based on experiences
        :param reqId:
        :param contract:
        :param execution:
        :return:
        """
        self.log.debug(__name__ + '::execDetails: reqId=%s contract=%s execution=%s' % (reqId, print_IBCpp_contract(contract), print_IBCpp_execution(execution)))
        int_orderId = execution.orderId
        ibpyOrderId = self._idConverter.fromIBtoBroker(int_orderId)
        accountCode = execution.acctNumber
        self.singleTrader.set_execDetails(self.name, accountCode,
                                          ExecDetailsRecord(ibpyOrderId, contract, execution))

        # IB will not invoke updateAccountValue immediately after execDetails
        # http://www.ibridgepy.com/knowledge-base/#Q_What_functions_will_be_called_back_from_IB_server_and_what_is_the_sequence_of_call_backs_after_an_order_is_executed
        # To make sure the user know the rough cashValue, IBridgePy has to simulate them.
        # The accurate value will be updated by IB regular updateAccountValue every 3 minutes.
        # The positionValue and portfolioValues are not simulated for live trading because the user just care about cashValue to buy other contracts
        # These values will be updated by IB regular updateAccountValue every 3 minutes.
        currentCashValue = self.singleTrader.get_account_info(self.name, accountCode, 'TotalCashValue')
        cashChange = execution.shares * float(execution.price)
        if execution.side == 'BOT':
            currentCashValue -= cashChange
        elif execution.side == 'SLD':
            currentCashValue += cashChange
        self.updateAccountValue('TotalCashValue', currentCashValue, 'USD', accountCode)

    def historicalData(self, reqId, timeString, price_open, price_high, price_low, price_close, volume, barCount, WAP,
                       hasGaps):
        """
        call back function from IB C++ API
        return the historical data for requested security
        """
        self.log.notset(__name__ + '::historicalData: reqId=%s timeString=%s volume=%s barCount=%s WAP=%s hasGap=%s' % (reqId, timeString, volume, barCount, WAP, hasGaps))

        # for any reason, the reqId is not in the self.activeRequests,
        # just ignore it. because the callback historicalData must come from the previous request.
        if self.activeRequests.check_valid_reqId(reqId):
            aRequest = self.activeRequests.get_by_reqId_otherwise_exit(reqId)
        else:
            return

        if 'finished' in str(timeString):
            aRequest.status = ReqAttr.Status.COMPLETED

        else:
            aRequest.status = ReqAttr.Status.STARTED
            # !!! The followings are removed because formatData is forced to 2 in
            # broker_client_factory::BrokerClient::_send_req_to_server after V 5.8.1
            # User can still choose to formatDate = 1, which means return dt.datetime for convenience

            # if aRequest.param['formatDate'] == 1:
            #     if '  ' in timeString:
            #         dateTime = dt.datetime.strptime(timeString, '%Y%m%d  %H:%M:%S')  # change string to datetime
            #     else:
            #         dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
            #     dateTime = pytz.timezone('UTC').localize(dateTime)
            # else:  # formatDate is UTC time in seconds, str type
            #     # The format in which the incoming bars' date should be presented. Note that for day bars, only yyyyMMdd format is available.
            #     if len(timeString) > 9:  # return datetime, not date
            #         dateTime = utc_in_seconds_to_dt(float(timeString))
            #     else:  # return date, not datetime
            #         dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
            #     dateTime = int(dt_to_utc_in_seconds(dateTime))  # change to int type

            if len(timeString) > 9:  # the type of returned value is datetime, not date
                dateTime = utc_in_seconds_to_dt(float(timeString))
            else:
                dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
            dateTime = int(dt_to_utc_in_seconds(dateTime))  # change to int type

            if aRequest.param['formatDate'] == 1:
                dateTime = utc_in_seconds_to_dt(dateTime)  # int -> datetime
                if 'day' in aRequest.param['barSize']:
                    dateTime = dateTime.date()  # datetime -> date
                else:
                    dateTime = dateTime.astimezone(aRequest.param['timezoneOfReturn'])  # Adjust timezone

            newRow = pd.DataFrame({'open': price_open, 'high': price_high,
                                   'low': price_low, 'close': price_close,
                                   'volume': volume}, index=[dateTime])
            aRequest.returnedResult = aRequest.returnedResult.append(newRow)

    def nextValidId(self, nextId):
        """
        IB API requires an nextId for every order, and this function obtains
        the next valid nextId. This function is called at the initialization
        stage of the program and results are recorded in startingNextValidIdNumber,
        then the nextId is track by the program when placing orders
        """
        self.log.debug(__name__ + '::nextValidId: Id = ' + str(nextId))
        self.nextId.setUuid(nextId)
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqIds', ReqAttr.Status.COMPLETED)

    def openOrder(self, int_ibOrderId, contract, order, orderState):
        """
        call back function of IB C++ API which updates the open orders
        """
        self.log.debug(__name__ + '::openOrder: ibOrderId=%i contract=%s order=%s orderState=%s' % (int_ibOrderId, print_IBCpp_contract(contract), print_IBCpp_order(order), print_IBCpp_orderState(orderState)))

        # For IB only:
        # The int_ibOrderId is 0 or -1 if the order is not placed by IB clients
        # Then, create a string value for it using permId
        # IBridgePy will not touch these orders and the created value is not registered in idConverter
        if int_ibOrderId in [-1]:
            str_ibpyOrderId = 'permIDatIB%s' % (order.permId,)
        else:
            str_ibpyOrderId = self._idConverter.fromIBtoBroker(int_ibOrderId)
        self.singleTrader.set_openOrder(self.name, order.account,
                                        OpenOrderRecord(str_ibpyOrderId, contract, order, orderState))

    def openOrderEnd(self):
        self.log.debug(__name__ + '::openOrderEnd')
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqOneOrder', ReqAttr.Status.COMPLETED)
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAllOpenOrders', ReqAttr.Status.COMPLETED)
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqOpenOrders', ReqAttr.Status.COMPLETED)
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAutoOpenOrders', ReqAttr.Status.COMPLETED)

    def orderStatus(self, int_orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                    whyHeld):
        """
        call back function of IB C++ API which update status or certain order
        Same order may be called back multiple times with status of 'Filled'
        orderStatus is always called back after openOrder
        """
        self.log.debug(__name__ + '::orderStatus: int_orderId=%s status=%s filled=%s remaining=%s aveFillPrice=%s' % (int_orderId, status, filled, remaining, avgFillPrice))
        str_ibpyOrderId = self._idConverter.fromIBtoBroker(int_orderId)
        reqId = self.activeRequests.find_reqId_by_int_orderId(int_orderId)
        # This orderStatus is called back because of an active request within this session so that reqId is NOT None
        if reqId is not None:
            aRequest = self.activeRequests.get_by_reqId_otherwise_exit(reqId)
            if aRequest.reqType in ['placeOrder', 'modifyOrder']:
                aRequest.returnedResult = str_ibpyOrderId
                aRequest.status = ReqAttr.Status.COMPLETED
        else:  # This orderStatus is called back because of an existing order so that reqId is None
            # DO NOT DELETE
            # For Debug only
            # print(__name__ + '::orderStatus: cannot find reqId by int_orderid=%s' % (int_orderId,))
            # print(self._idConverter.fromIBToBrokerDict)
            # print(self._idConverter.fromBrokerToIBDict)
            # print(self.activeRequests)
            pass

        accountCode = self.singleTrader.get_accountCode_by_ibpyOrderId(self.name, str_ibpyOrderId)
        self.singleTrader.set_orderStatus(self.name, accountCode,
                                          OrderStatusRecord(str_ibpyOrderId, status, filled, remaining, avgFillPrice,
                                                            permId, parentId, lastFillPrice, clientId, whyHeld))

    def position(self, accountCode, contract, amount, cost_basis):
        """
        call back function of IB C++ API which updates the position of a security
        of a account
        """
        self.log.debug(__name__ + '::position: accountCode=%s contract=%s '
                                  'amount=%s cost_basis=%s' % (accountCode,
                                                               print_IBCpp_contract(contract),
                                                               amount,
                                                               cost_basis))
        # Conclusion: called-back position contract may or may not have exchange info,
        # never see primaryExchange.
        # STK has exchange, CASH does not, FUT does not
        # if contract.exchange != '':
        #    self.log.error(__name__ + '::position: EXIT, contract has exchange=%s' % (print_contract(contract),))
        #    exit()
        security = stripe_exchange_primaryExchange_from_contract(contract)
        self.singleTrader.set_position(self.name, accountCode,
                                       PositionRecord(security.full_print(), amount, cost_basis, contract))

    def positionEnd(self):
        self.log.debug(__name__ + '::positionEnd: all positions recorded')
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqPositions', ReqAttr.Status.COMPLETED)

    def realtimeBar(self, reqId, time, price_open, price_high, price_low, price_close, volume, wap, count):
        """
        call back function from IB C++ API
        return realTimeBars for requested security every 5 seconds
        """
        self.log.notset(
            __name__ + '::realtimeBar: reqId=%s time=%s price_open=%s price_high=%s price_low=%s price_close=%s volume=%s wap=%s count=%s'
            % (str(reqId), str(time), str(price_open), str(price_high), str(price_low), str(price_close), str(volume),
               str(wap), str(count)))

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        self.log.debug(__name__ + '::scannerData: reqId = %i, rank = %i, contractDetails.summary = %s, distance = %s,\
                benchmark = %s, project = %s, legsStr = %s'
                       % (reqId, rank, print_IBCpp_contract(contractDetails.summary), distance, benchmark,
                          projection, legsStr))
        aRequest = self.activeRequests.get_by_reqId_otherwise_exit(reqId)
        security = from_contract_to_security(contractDetails.summary)
        newRow = pd.DataFrame({'rank': rank,
                               # 'contractDetails': contractDetails,
                               'security': security,
                               # 'distance': distance,
                               # 'benchmark': benchmark,
                               # 'projection': projection,
                               # 'legsStr': legsStr
                               }, index=[len(aRequest.returnedResult)])
        aRequest.returnedResult = aRequest.returnedResult.append(newRow)

    def scannerDataEnd(self, reqId):
        self.log.debug(__name__ + '::scannerDataEnd:' + str(reqId))
        self.activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)

    def scannerParameters(self, xml):
        self.log.debug(__name__ + '::scannerParameters:')
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status_and_set_result('reqScannerParameters',
                                                                                     ReqAttr.Status.COMPLETED, xml)

    def tickGeneric(self, reqId, field, value):
        self.log.notset(__name__ + '::tickGeneric: reqId=%i field=%s value=%d' % (reqId, field, value))

    def tickOptionComputation(self, reqId, tickType, impliedVol, delta,
                              optPrice, pvDividend, gamma, vega, theta,
                              undPrice):
        self.log.debug(__name__ + '::tickOptionComputation:reqId=%s %s %s %s %s %s %s %s %s %s' % (
            str(reqId), tickType, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta,
            undPrice))
        str_security = self.allRequests[reqId].param['security'].full_print()
        self.dataFromServer.set_tickInfoRecord(
            TickOptionComputationRecord(str_security, tickType, impliedVol,
                                        delta, optPrice, pvDividend, gamma, vega, theta, undPrice))

    def tickPrice(self, reqId, tickType, price, canAutoExecute):
        """
        call back function of IB C++ API. This function will get tick prices
        """
        self.log.notset(__name__ + '::tickPrice:reqId=%s tickType=%s price=%s' % (reqId, tickType, price))

        # In order to guarantee valid ask and bid prices, it needs to check if both of ask price and bid price
        # is received.
        if self.activeRequests.check_valid_reqId(reqId):  # Maybe the callback is not in activeRequest, it is allowed
            aRequest = self.activeRequests.get_by_reqId_otherwise_exit(reqId)
            if tickType == 1:
                if 'Bid' not in aRequest.status:
                    aRequest.status += 'Bid'
            elif tickType == 2:
                if 'Ask' not in aRequest.status:
                    aRequest.status += 'Ask'
            if 'Ask' in aRequest.status and 'Bid' in aRequest.status:
                aRequest.status = ReqAttr.Status.COMPLETED

        str_security = self.realTimePriceRequestedList.findByReqId(reqId)
        timestamp = self.get_datetime()
        self.dataFromServer.set_tickInfoRecord(TickPriceRecord(str_security, tickType, price, canAutoExecute, timestamp))

    def tickSize(self, reqId, tickType, size):
        """
        call back function of IB C++ API. This function will get tick size
        """
        self.log.notset(__name__ + '::tickSize: ' + str(reqId) + ", " + MSG_TABLE[tickType]
                        + ", size = " + str(size))
        # if self.activeRequests.check_valid_reqId(reqId):  # Maybe the callback is not in activeRequest, it is allowed
        #     self.activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)
        str_security = self.realTimePriceRequestedList.findByReqId(reqId)
        self.dataFromServer.set_tickInfoRecord(TickSizeRecord(str_security, tickType, size))

    def tickSnapshotEnd(self, reqId):
        self.log.notset(__name__ + '::tickSnapshotEnd: ' + str(reqId))

    def tickString(self, reqId, field, value):
        """
        IB C++ API call back function. The value variable contains the last
        trade price and volume information. User show define in this function
        how the last trade price and volume should be saved
        RT_volume: 0 = trade timestamp; 1 = price_last,
        2 = size_last; 3 = record_timestamp
        """
        self.log.notset(__name__ + '::tickString: ' + str(reqId)
                        + 'field=' + str(field) + 'value=' + str(value))
        str_security = self.realTimePriceRequestedList.findByReqId(reqId)
        self.dataFromServer.set_tickInfoRecord(TickStringRecord(str_security, field, value))

    def updateAccountTime(self, tm):
        self.log.notset(__name__ + '::updateAccountTime:' + str(tm))

    def updateAccountValue(self, key, value, currency, accountCode):
        """
        IB callback function
        update account values such as cash, PNL, etc
        !!!!!!!! type(value) is STRING !!!!!!!!
        """
        self.log.notset(__name__ + '::updateAccountValue: key=%s value=%s currency=%s accountCode=%s'
                        % (key, str(value), currency, accountCode))
        try:
            value = float(value)
        except ValueError:
            # IB will callback some many account info. All of them are string
            # However, the concept of some of these values are float. So, convert them to float if possible. Otherwise, keep them as string
            pass
        self.singleTrader.set_updateAccountValue(self.name, accountCode,
                                                 UpdateAccountValueRecord(key, value, currency, accountCode))

    def updatePortfolio(self, contract, amount, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL,
                        accountCode):
        self.log.notset(
            __name__ + '::updatePortfolio: contract=%s amount=%s marketPrice=%s marketValue=%s averageCost=%s unrealizedPNL=%s realizedPNL=%s accountCode=%s'
            % (str(contract), str(amount), str(marketPrice), str(marketValue), str(averageCost), str(unrealizedPNL),
               str(realizedPNL), str(accountCode)))

        # Because IB does not callback position and updateAccountValues,
        # it needs to make fake calls to make sure the account info is correct
        # It is not correct, it will be fixed by the real call-backs
        self.position(accountCode, contract, amount, averageCost)
