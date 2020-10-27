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
from sys import exit

from BasicPyLib.BasicTools import dt_to_utc_in_seconds
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.IbridgepyTools import symbol
from IBridgePy.constants import LiveBacktest, OrderType, OrderStatus, OrderAction, OrderTif, BrokerName
from IBridgePy.quantopian import from_contract_to_security, from_security_to_contract
from broker_client_factory.BrokerClientDefs import ReqAttr
from broker_client_factory.CallBacks import CallBacks
from broker_client_factory.TdAmeritrade.enums import ORDER_SESSION, DURATION, ORDER_INSTRUCTIONS, ORDER_ASSET_TYPE, \
    ORDER_TYPE, ORDER_STRATEGY_TYPE
from broker_client_factory.TdAmeritrade.orders import Order, OrderLeg
from models.utils import print_IBCpp_contract, print_IBCpp_order
import datetime as dt
import pytz


class OrderTypeConverter:
    """
    https://developer.tdameritrade.com/account-access/apis/get/accounts/%7BaccountId%7D/orders/%7BorderId%7D-0
    """
    def __init__(self):
        pass

    @staticmethod
    def fromTDtoIB(orderType):
        if orderType == ORDER_TYPE.MARKET:
            return OrderType.MKT
        elif orderType == ORDER_TYPE.LIMIT:
            return OrderType.LMT
        elif orderType == ORDER_TYPE.STOP:
            return OrderType.STP
        elif orderType == ORDER_TYPE.STOP_LIMIT:
            return OrderType.STP_LMT
        else:  # TRAILING_STOP MARKET_ON_CLOSE EXERCISE TRAILING_STOP_LIMIT NET_DEBIT NET_CREDIT NET_ZERO
            print(__name__ + '::OrderTypeConverter::fromTDtoIB: EXIT, cannot handle orderType=%s' % (orderType,))
            print(type(orderType), type(ORDER_TYPE.LIMIT), orderType == ORDER_TYPE.LIMIT)
            exit()

    @staticmethod
    def fromIBtoTD(orderType):
        if orderType == OrderType.MKT:
            return ORDER_TYPE.MARKET
        elif orderType == OrderType.LMT:
            return ORDER_TYPE.LIMIT
        elif orderType == OrderType.STP:
            return ORDER_TYPE.STOP
        elif orderType == OrderType.STP_LMT:
            return ORDER_TYPE.STOP_LIMIT
        else:  # TRAILING_STOP MARKET_ON_CLOSE EXERCISE TRAILING_STOP_LIMIT NET_DEBIT NET_CREDIT NET_ZERO
            print(__name__ + '::OrderTypeConverter::fromIBtoTD: EXIT, cannot handle orderType=%s' % (orderType,))
            exit()


class OrderStatusConverter:
    def __init__(self):
        pass

    @staticmethod
    def fromTDtoIB(orderStatus):
        if orderStatus in ['FILLED', 'REPLACED']:
            return OrderStatus.FILLED
        elif orderStatus == 'CANCELED':
            return OrderStatus.CANCELLED
        elif orderStatus == 'PENDING_CANCEL':
            return OrderStatus.PENDINGCANCEL
        elif orderStatus in ['QUEUED', 'WORKING', 'ACCEPTED', 'AWAITING_PARENT_ORDER', 'AWAITING_CONDITION', 'PENDING_ACTIVATION', 'PENDING_REPLACE']:
            return OrderStatus.SUBMITTED
        elif orderStatus in ['AWAITING_MANUAL_REVIEW', 'REJECTED', 'EXPIRED']:
            return OrderStatus.INACTIVE


class BarSizeConverter:
    def __init__(self):
        pass

    @staticmethod
    def fromIBtoTD(barSize):
        # 1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day
        if barSize == '1 min':
            return 1, 'minute'
        elif barSize == '5 mins':
            return 5, 'minute'
        elif barSize == '15 mins':
            return 15, 'minute'
        elif barSize == '30 mins':
            return 30, 'minute'
        elif barSize in ['1 day', '1 Day']:
            return 1, 'daily'
        else:
            print(__name__ + '::BarSizeConverter::fromIBtoTD: EXIT, TD cannot handle barSize=%s' % (barSize,))
            exit()


class GoBackConverter:
    def __init__(self):
        pass

    @staticmethod
    def fromIBtoTD(goBack, barSize):
        print(__name__ + '::fromIBtoTD: goBack=%s barSize=%s' % (goBack, barSize))
        if 'day' in barSize or 'Day' in barSize:
            if 'D' in goBack:
                return int(int(goBack.split(' ')[0]) / 20 + 1), 'month'
            elif 'W' in goBack:
                return int(int(goBack.split(' ')[0]) * 7 / 20 + 1), 'month'
            elif 'M' in goBack:
                return int(goBack.split(' ')[0]), 'month'
            elif 'Y' in goBack:
                return int(goBack.split(' ')[0]), 'year'
            else:
                print(__name__ + '::fromIBtoTD: EXIT, cannot handle goBack=%s' % (goBack,))
                exit()
        elif 'min' in barSize:
            if 'D' in goBack:
                return int(goBack.split(' ')[0]), 'day'
            elif 'W' in goBack:
                return int(goBack.split(' ')[0] * 7), 'day'
            elif 'M' in goBack:
                return int(goBack.split(' ')[0]) * 30, 'day'
            elif 'Y' in goBack:
                return int(goBack.split(' ')[0]) * 365, 'day'
            else:
                print(__name__ + '::fromIBtoTD: EXIT, cannot handle goBack=%s' % (goBack,))
                exit()
        else:
            print(__name__ + '::fromIBtoTD: EXIT, cannot handle barSize=%s' % (barSize,))
            exit()


class OrderActionConverter:
    def __init__(self):
        pass

    @staticmethod
    def fromIBtoTD(action):
        if action == OrderAction.BUY:
            return ORDER_INSTRUCTIONS.BUY
        elif action == OrderAction.SELL:
            return ORDER_INSTRUCTIONS.SELL
        else:
            print(__name__ + '::OrderActionConverter::fromIBtoTD: EXIT, cannot handle action=%s' % (action,))
            exit()


class OrderTifConverter:
    def __init__(self):
        pass

    @staticmethod
    def fromIBtoTD(tif):
        if tif == OrderTif.GTC:
            return DURATION.GOOD_TILL_CANCEL
        elif tif == OrderTif.DAY:
            return DURATION.DAY
        else:
            print(__name__ + '::OrderTifConverter::fromIBtoTD: EXIT, cannot handle tif=%s' % (tif,))
            exit()

    @staticmethod
    def fromTDtoIB(tif):
        if tif == DURATION.GOOD_TILL_CANCEL:
            return OrderTif.GTC
        elif tif == DURATION.DAY:
            return OrderTif.DAY
        else:
            print(__name__ + '::OrderTifConverter::fromTDtoIB: EXIT, cannot handle tif=%s' % (tif,))
            exit()


class OrderConverter:
    def __init__(self):
        pass

    @staticmethod
    def fromTDtoIBOpenOrder(tdOrder, idConverter):
        # IBCpp.Order().orderId must be an integer so that an integer orderId has to be created
        originalTdOrderId = str(tdOrder['orderId'])
        int_orderId = idConverter.fromBrokerToIB(originalTdOrderId)

        security = symbol(str(tdOrder['orderLegCollection'][0]['instrument']['symbol']))
        contract = from_security_to_contract(security)
        orderStatus = OrderStatusConverter().fromTDtoIB(str(tdOrder['status']))
        quantity = int(float(tdOrder['quantity']))

        orderState = IBCpp.OrderState()
        orderState.status = orderStatus

        ibOrder = IBCpp.Order()
        ibOrder.orderId = int_orderId
        ibOrder.account = str(tdOrder['accountId'])
        ibOrder.action = str(tdOrder['orderLegCollection'][0]['instruction'])
        ibOrder.totalQuantity = quantity
        ibOrder.orderType = OrderTypeConverter().fromTDtoIB(str(tdOrder['orderType']))
        ibOrder.tif = OrderTifConverter().fromTDtoIB(str(tdOrder['duration']))
        if ibOrder.orderType == OrderType.LMT:
            ibOrder.lmtPrice = float(str(tdOrder['price']))
        elif ibOrder.orderType == OrderType.STP:
            ibOrder.auxPrice = float(str(tdOrder['stopPrice']))
        elif ibOrder.orderType == OrderType.STP_LMT:
            ibOrder.lmtPrice = float(str(tdOrder['price']))
            ibOrder.auxPrice = float(str(tdOrder['stopPrice']))
        elif ibOrder.orderType == OrderType.MKT:
            pass
        else:
            print(__name__ + '::reqOneOrderWrapper: EXIT, cannot handle orderType=%s' % (ibOrder.orderType,))
            exit()
        ibOrder.orderRef = originalTdOrderId
        return int_orderId, contract, ibOrder, orderState, security

    @staticmethod
    def fromTDtoIBOrderStatus(tdOrder):
        orderStatus = OrderStatusConverter().fromTDtoIB(str(tdOrder['status']))
        quantity = int(float(tdOrder['quantity']))
        filledQuantity = int(float(tdOrder['filledQuantity']))
        remaining = quantity - filledQuantity
        if 'statusDescription' not in tdOrder:
            whyHeld = ''
        else:
            whyHeld = str(tdOrder['statusDescription'])

        price = 0.0
        if 'orderActivityCollection' in tdOrder:
            for activity in tdOrder['orderActivityCollection']:
                if activity['activityType'] == 'EXECUTION':
                    if len(activity['executionLegs']) == 1:
                        price = float(str(activity['executionLegs'][0]['price']))
                    else:
                        print(__name__ + '::OrderConverter::fromTDtoIBOrderStatus: EXIT, cannot handle executionLegs=%s' % (activity['executionLegs'],))
                        exit()
                else:
                    print(__name__ + '::OrderConverter::fromTDtoIBOrderStatus: EXIT, cannot handle activityType=%s' % (activity['activityType'],))
                    exit()
        return orderStatus, filledQuantity, remaining, price, whyHeld

    @staticmethod
    def fromIBtoTD(contract, order):
        """

        :param contract: IBCpp.contract()
        :param order: IBCpp.order()
        :return: TD's order
        """
        action = OrderActionConverter().fromIBtoTD(order.action)
        quantity = order.totalQuantity
        orderType = OrderTypeConverter().fromIBtoTD(order.orderType)
        tif = OrderTifConverter().fromIBtoTD(order.tif)

        new_order = Order()  # TD Order, not IBCpp Order
        new_order.order_session(session=ORDER_SESSION.NORMAL)
        new_order.order_duration(duration=tif)
        new_order.order_type(order_type=orderType)
        new_order.order_strategy_type(order_strategy_type=ORDER_STRATEGY_TYPE.SINGLE)

        if order.orderType == OrderType.LMT:
            new_order.order_limit_price(price=order.lmtPrice)
        elif order.orderType == OrderType.STP:
            new_order.order_stop_price(price=order.auxPrice)
        elif order.orderType == OrderType.MKT:
            # do not set price for market order
            pass
        else:
            print(__name__ + '::OrderConverter::fromIBtoTD: EXIT, cannot handle order.orderType=%s' % (order.orderType,))
            exit()

        #   AN ORDER OBJECT CONTAINS AN ORDERLEG OBJECT. THE ORDERLEG OBJECT DEFINES
        #   ORDER INSTRUCTIONS, INFORMATION ABOUT THE ASSET, AND PRICE/QUANTITY.
        #   OR A STRING VALUE.
        new_order_leg = OrderLeg()
        new_order_leg.order_leg_instruction(instruction=action)
        new_order_leg.order_leg_quantity(quantity=quantity)
        new_order_leg.order_leg_asset(asset_type=ORDER_ASSET_TYPE.EQUITY, symbol=contract.symbol)

        # Once we have built our order leg, we can add it to our OrderObject.
        new_order.add_order_leg(order_leg=new_order_leg)

        # noinspection PyProtectedMember
        return new_order._grab_order()  # It looks strange but https://github.com/timkpaine/tdameritrade does it


# noinspection PyAbstractClass
class BrokerClientTdAmeritrade(CallBacks):
    _tdClient = None

    @property
    def name(self):
        return BrokerName.TDAMERITRADE

    def _verify_accountCode(self, returnedResults, accountCode, callerName):
        returnedAccountCode = list(returnedResults.keys())[0]  # list() is added for 2x3 comparability. in python3, .keys() work like a set
        if accountCode != returnedAccountCode:
            self.log.error(__name__ + '::_verify_accountCode::%s EXIT, input accountCode=%s is not correct, it should be %s' % (callerName, accountCode, returnedAccountCode))
            exit()

    def _validate_contract(self, contract, caller):
        if contract.secType != 'STK' or contract.currency != 'USD':
            self.log.error(__name__ + '::%s: EXIT, cannot handle this contract=%s, only STK right now' % (caller, print_IBCpp_contract(contract),))
            exit()

    def setup_brokerClient_TDAmeritrade(self, log, rootFolderPath, singleTrader, dataFromServer, timeGenerator, tdClient, accountCode):
        self.setup(log, accountCode, rootFolderPath, singleTrader, dataFromServer, timeGenerator, self.name)
        self.setRunningMode(LiveBacktest.LIVE)  # IBCpp function
        self._tdClient = tdClient

    @staticmethod
    def isConnectedWrapper():
        return True

    def connectWrapper(self):
        return True

    def disconnectWrapper(self):
        return True

    def reqPositionsWrapper(self):
        ans = self._tdClient.accounts(positions=True, orders=False)
        for accountCode in ans.keys():
            # If there is no any position, just return
            if 'positions' not in ans[accountCode]['securitiesAccount']:
                self.simulatePositionEnd()
                return
            # If there are positions in the account
            positions = ans[accountCode]['securitiesAccount']['positions']
            for position in positions:
                if str(position['instrument']['assetType']) != 'EQUITY':
                    self.log.debug(__name__ + '::reqPositionsWrapper: cannot handle position=%s' % (position,))
                    continue
                security = symbol(str(position['instrument']['symbol']))
                contract = from_security_to_contract(security)
                longQuantity = int(float(position['longQuantity']))
                shortQuantity = int(float(position['shortQuantity']))
                if shortQuantity == 0:
                    self.simulatePosition(accountCode,
                                          contract,
                                          longQuantity,
                                          float(position['averagePrice']),
                                          security.full_print())
                else:
                    self.simulatePosition(accountCode,
                                          contract,
                                          (-1) * abs(shortQuantity),
                                          float(position['averagePrice']),
                                          security.full_print())
        self.simulatePositionEnd()

    def reqCurrentTimeWrapper(self):
        tmp = dt_to_utc_in_seconds(self.get_datetime())
        self.log.debug(__name__ + '::reqCurrentTimeWrapper: tmp=%s' % (tmp,))
        self.simulateCurrentTime(int(tmp))  # IBCpp function

    def _convert_order(self, tdOrder):
        int_orderId, contract, ibOrder, orderState, security = OrderConverter().fromTDtoIBOpenOrder(tdOrder, self._idConverter)
        # IBCpp function
        self.simulateOpenOrder(int_orderId, contract, ibOrder, orderState, security.full_print())
        orderStatus, filledQuantity, remaining, price, whyHeld = OrderConverter.fromTDtoIBOrderStatus(tdOrder)
        # IBCpp function
        self.simulateOrderStatus(int_orderId,
                                 orderStatus,
                                 filledQuantity,  # filled
                                 remaining,  # remaining
                                 price,  # avgFillPrice
                                 0,  # permId
                                 0,  # parentId
                                 0,  # lastFillPrice
                                 0,  # clientId
                                 whyHeld)  # whyHeld

    def reqOneOrderWrapper(self, ibpyOrderId):
        if not isinstance(ibpyOrderId, str):
            self.log.error(__name__ + '::reqOneOrderWrapper: EXIT, ibpyOrderId must be a string')
            exit()
        order = self._tdClient.get_order(self.accountCode, ibpyOrderId)
        if 'error' in order:
            self.log.error(__name__ + '::reqOneOrderWrapper: EXIT, cannot found ibpyOrderId=%s. Please verify it.' % (ibpyOrderId,))
            exit()
        self._convert_order(order)
        self.simulateOpenOrderEnd()

    def reqAllOpenOrdersWrapper(self):
        """
        All orders will be returned, regardless orderStatus
        :return: None
        """
        ans = self._tdClient.accounts(positions=False, orders=True)
        for accountCode in ans.keys():
            # If there is no any order details, just end
            if 'orderStrategies' not in ans[accountCode]['securitiesAccount']:
                self.simulateOpenOrderEnd()
                return

            # There are orders
            orders = ans[accountCode]['securitiesAccount']['orderStrategies']
            for order in orders:
                self._convert_order(order)
        self.simulateOpenOrderEnd()

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        ans = self._tdClient.accounts(positions=False, orders=False)
        self._verify_accountCode(ans, accountCode, 'reqAccountUpdatesWrapper')
        # TD server return example: Test::Test_broker_client_factory::TdAmeritrade::Test_TDClient:test_get_acccount_info
        self.simulateUpdateAccountValue('NetLiquidation', str(ans[accountCode]['securitiesAccount']['currentBalances']['liquidationValue']), 'USD', accountCode)
        self.simulateUpdateAccountValue('GrossPositionValue', str(ans[accountCode]['securitiesAccount']['currentBalances']['longMarketValue']), 'USD', accountCode)
        if str(ans[accountCode]['securitiesAccount']['type']) == 'CASH':
            self.simulateUpdateAccountValue('TotalCashValue', str(ans[accountCode]['securitiesAccount']['currentBalances']['totalCash']), 'USD', accountCode)
            self.simulateUpdateAccountValue('AvailableFunds', str(ans[accountCode]['securitiesAccount']['currentBalances']['cashAvailableForTrading']), 'USD', accountCode)
            self.simulateUpdateAccountValue('BuyingPower', str(ans[accountCode]['securitiesAccount']['currentBalances']['cashAvailableForTrading']), 'USD', accountCode)
        elif str(ans[accountCode]['securitiesAccount']['type']) == 'MARGIN':
            self.simulateUpdateAccountValue('TotalCashValue', str(ans[accountCode]['securitiesAccount']['currentBalances']['cashBalance']), 'USD', accountCode)
            self.simulateUpdateAccountValue('AvailableFunds', str(ans[accountCode]['securitiesAccount']['currentBalances']['availableFunds']), 'USD', accountCode)
            self.simulateUpdateAccountValue('BuyingPower', str(ans[accountCode]['securitiesAccount']['currentBalances']['buyingPower']), 'USD', accountCode)
        else:
            self.log.error(__name__ + '::reqAccountUpdatesWrapper: EXIT, cannot handle accountType=%s' % (str(ans[accountCode]['securitiesAccount']['type']),))
            exit()
        self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountUpdates', ReqAttr.Status.COMPLETED)

    def reqAccountSummaryWrapper(self, reqId, group, tag):
        raise NotImplementedError(self.name)
        # ans = self._tdClient.accounts(positions=False, orders=False)
        # for accountCode in ans.keys():
        #     self.simulateUpdateAccountValue('NetLiquidation', str(ans[accountCode]['securitiesAccount']['currentBalances']['liquidationValue']), 'USD', accountCode)
        #     self.simulateUpdateAccountValue('TotalCashValue', str(ans[accountCode]['securitiesAccount']['currentBalances']['cashAvailableForTrading']), 'USD', accountCode)
        #     self.simulateUpdateAccountValue('GrossPositionValue', str(ans[accountCode]['securitiesAccount']['currentBalances']['longMarketValue']), 'USD', accountCode)
        # self.activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountSummary', ReqAttr.Status.COMPLETED)

    def reqIdsWrapper(self):
        self.simulateNextValidId(1)

    def reqHistoricalDataWrapper(self, reqId, contract, str_endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        # self.log.info(__name__ + '::reqHistoricalDataWrapper: reqId=%s contract=%s endTime=%s goBack=%s barSize=%s' % (reqId, print_IBCpp_contract(contract), endTime, goBack, barSize))
        # https://developer.tdameritrade.com/content/price-history-samples
        self._validate_contract(contract, 'reqHistoricalDataWrapper')
        freq, freqType = BarSizeConverter().fromIBtoTD(barSize)
        pe, peType = GoBackConverter().fromIBtoTD(goBack, barSize)
        if str_endTime:
            str_endTime = dt.datetime.strptime(str_endTime, "%Y%m%d %H:%M:%S %Z")  # string -> dt.datetime; strptime silently ignores timezone!!!
            str_endTime = pytz.timezone('UTC').localize(str_endTime)
            endDate = int(dt_to_utc_in_seconds(str_endTime)) * 1000
            ans = self._tdClient.history(str(contract.symbol), periodType=peType, period=pe, frequencyType=freqType, frequency=freq, endDate=endDate)
        else:
            ans = self._tdClient.history(str(contract.symbol), periodType=peType, period=pe, frequencyType=freqType, frequency=freq)

        if 'error' in ans:
            self.log.error(__name__ + '::reqHistoricalDataWrapper: EXIT, cannot handle contract=%s endTime=%s goBack=%s barSize=%s' % (print_IBCpp_contract(contract), str_endTime, goBack, barSize))
            self.log.error(__name__ + '::reqHistoricalDataWrapper: EXIT, cannot handle periodType=%s period=%s frequencyType=%s frequency=%s' % (peType, pe, freqType, freq))
            exit()
        hist = ans['candles']
        for row in hist:
            epoc = int(float(str(row['datetime'])))
            if epoc > 1e10:
                epoc /= 1000.0
            self.simulateHistoricalData(reqId,
                                        str(epoc),
                                        float(row['open']),
                                        float(row['high']),
                                        float(row['low']),
                                        float(row['close']),
                                        int(float(row['volume'])),
                                        1,  # barCount
                                        0.0,  # WAP
                                        1)  # hasGap
        self.simulateHistoricalData(reqId, 'finished', 0.0, 0.0, 0.0, 0.0, 1, 1, 0.0, 1)

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot):
        self._validate_contract(contract, 'reqMktDataWrapper')
        ans = None
        count = 1
        while count <= 3:
            tp = self._tdClient.quote(str(contract.symbol))
            ans = None
            symb = contract.symbol.upper()
            if symb in tp:
                ans = tp[symb]
                break
            else:
                self.log.error(__name__ + '::reqMktDataWrapper: requested %s to TD and error=%s. '
                                          'Hint: Sometimes, TD does not response to reqMktData for unknown reasons. '
                                          'IBridgePy will retry 3 times. attempt=%s' % (contract.symbol, tp, count))
            count += 1
        if count == 4:
            raise RuntimeError('EXIT, TD does not response to reqMktData for %s. IBridgePy retried and gave up.' % (contract.symbol,))

        str_security = from_contract_to_security(contract).full_print()
        self.simulateTickPrice(reqId, IBCpp.TickType.ASK, float(ans['askPrice']), True, str_security)
        self.simulateTickPrice(reqId, IBCpp.TickType.BID, float(ans['bidPrice']), True, str_security)
        self.simulateTickPrice(reqId, IBCpp.TickType.LAST, float(ans['lastPrice']), True, str_security)
        self.simulateTickPrice(reqId, IBCpp.TickType.CLOSE, float(ans['closePrice']), True, str_security)
        self.simulateTickSize(reqId, IBCpp.TickType.ASK_SIZE, int(ans['askSize']), str_security)
        self.simulateTickSize(reqId, IBCpp.TickType.BID_SIZE, int(ans['bidSize']), str_security)

    def cancelMktDataWrapper(self, reqId):
        raise NotImplementedError

    def reqRealTimeBarsWrapper(self, reqId, contract, barSize, whatToShow, useRTH):
        raise NotImplementedError

    # noinspection DuplicatedCode
    def placeOrderWrapper(self, contract, order, ibpyRequest):
        self._validate_contract(contract, 'placeOrderWrapper')
        self.log.info('Place Order to %s security=%s order=%s' % (self.name, print_IBCpp_contract(contract), print_IBCpp_order(order)))

        tdOrder = OrderConverter().fromIBtoTD(contract, order)
        ibpyOrderId = self._tdClient.place_orders(order.account, tdOrder)
        self.log.info('Order was placed to %s successfully. ibpyOrderId=%s' % (self.name, ibpyOrderId))

        # Register int_orderId in _idConverter so that brokerClient::CallBack::orderStatus knows how to handle int_orderId
        int_orderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self._idConverter.setRelationship(int_orderId, ibpyOrderId)

        # Set for ending flat.
        # Otherwise, the following line in broker_client_factory::CallBacks::orderStatus will not be able to find a reqId
        # reqId = self.activeRequests.find_reqId_by_int_orderId(int_orderId)
        ibpyRequest.param['int_orderId'] = int_orderId

        # Register ibpyOrderId in SingleTrader so that it can search accountCode by incoming int_orderId
        self.singleTrader.set_from_send_req_to_server(self.name, order.account, ibpyOrderId)

        # IBCpp function
        order.orderId = int_orderId
        self.simulateOpenOrder(int_orderId, contract, order, IBCpp.OrderState(),
                               from_contract_to_security(contract).full_print())  # IBCpp function
        # IBCpp function, this is the ending flag for PlaceOrder
        self.simulateOrderStatus(int_orderId, 'Submitted', 0, order.totalQuantity, 0.0, 0, 0, 0, 0, '')

    def reqContractDetailsWrapper(self, reqId, contract):
        raise NotImplementedError

    def calculateImpliedVolatilityWrapper(self, reqId, contract, optionPrice, underPrice):
        raise NotImplementedError

    def reqScannerSubscriptionWrapper(self, reqId, subscription):
        raise NotImplementedError

    def cancelScannerSubscriptionWrapper(self, tickerId):
        raise NotImplementedError

    def cancelOrderWrapper(self, ibpyOrderId):
        if not isinstance(ibpyOrderId, str):
            self.log.error(__name__ + '::cancelOrderWrapper: EXIT, ibpyOrderId must be a string')
            exit()
        self.reqOneOrderWrapper(ibpyOrderId)  # Make sure it is a valid order and callback openOrder() to record order info at IBridgePy. Otherwise, error: get_accountCode_by_ibpyOrderId: EXIT, cannot find accountCode by ibpyOrderId
        self.log.info('cancelOrder is sent to %s ibpyOrderId=%s' % (self.name, ibpyOrderId))
        self._tdClient.cancel_order(self.accountCode, ibpyOrderId)
        self.log.info('ibpyOrderId=%s is canceled successfully' % (ibpyOrderId,))
        int_orderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self.simulateOrderStatus(int_orderId, OrderStatus.CANCELLED, 0, 0, 0.0, 0, 0, 0, 0, '')
        self.error(int_orderId, 202, 'cancel order is confirmed')

    def reqScannerParametersWrapper(self):
        raise NotImplementedError

    def processMessagesWrapper(self, dummy):
        # !!! Change to lazy provider, supply values per requested
        return True

    def add_exchange_to_security(self, security):
        """
        For brokerClient TD, NO need to add exchange because IBridgePy for TD only trade Stock in U.S. and the current
        OrderConverter only cares about symbol while ignoring exchange and primaryExchange
        :param security:
        :return:
        """
        pass

    def add_primaryExchange_to_security(self, security):
        """
        For brokerClient TD, NO need to add primaryExchange because IBridgePy for TD only trade Stock in U.S. and the current
        OrderConverter only cares about symbol while ignoring exchange and primaryExchange
        :param security:
        :return:
        """
        pass
