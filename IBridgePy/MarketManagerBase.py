# -*- coding: utf-8 -*-
import datetime as dt
import os
import time
from sys import exit

import broker_client_factory
import broker_service_factory
import data_provider_factory
import market_calendar_factory
from BasicPyLib.repeater import Repeater, Event
from BasicPyLib.sendEmail import IbpyEmailClient
from BasicPyLib.simpleLogger import SimpleLoggerClass
from IBridgePy.TimeGenerator import TimeGenerator
from IBridgePy.constants import TimeConcept, TraderRunMode, DataProviderName, LogLevel
from models.Data import DataFromServer
from models.SingleTrader import SingleTrader


class MarketManager(object):
    def __init__(self, userConfig, userConfig_dataProvider=None):
        """
        Change to this way because MarketManager is used to run multiple fileNames
        Trader is not combined into userConfig because trader.funcs needs to be exposed to users
        If dataProvider is IB or other real dataProvider, a client to the dataProvider is needed.
        In this case, userConfig_dataProvider is needed to build a dataProvider that has a valid dataProviderClient
        """

        self.log = userConfig.log
        self.trader = userConfig.trader
        self.showTimeZone = userConfig.projectConfig.showTimeZone
        self.repBarFreq = userConfig.projectConfig.repBarFreq
        self.accountCode = userConfig.projectConfig.accountCode
        self.repeaterConfig = userConfig.repeaterConfig
        self.marketManagerConfig = userConfig.marketManagerConfig
        self.traderConfig = userConfig.traderConfig
        self.rootFolderPath = userConfig.projectConfig.rootFolderPath
        self._marketCalendar = userConfig.marketCalendar

        # If dataProvider is IB or other real dataProvider, a client to the dataProvider is needed.
        # In this case, userConfig_dataProvider is needed to build a dataProvider that has a valid dataProviderClient
        # TODO: userConfig_dataProvider should have a better solution
        if userConfig_dataProvider is not None:
            self.trader.brokerService.getBrokerClient()._dataProvider = setup_services(
                userConfig_dataProvider).dataProvider

        self.log.debug(__name__ + '::__init__')

        self.lastCheckConnectivityTime = dt.datetime.now()
        self.numberOfConnection = 0

        # Two modes: Trading and Ingesting, used to control display messages
        # self.runMode = userConfig.marketManagerConfig.runMode

        # userLog is for the function of record (). User will use it for any reason.
        dateTimeStr = time.strftime("%Y_%m_%d_%H_%M_%S")
        self.balanceLog = SimpleLoggerClass(filename='BalanceLog_' + dateTimeStr + '.txt', logLevel='NOTSET',
                                            addTime=False, folderPath=os.path.join(self.rootFolderPath, 'Output'))

    def _run_once(self):
        self.trader.connect()
        self.trader.initialize_Function()

    def run(self):
        self.log.debug(__name__ + '::run: START')
        self._run_once()
        if self.traderConfig.runMode in [TraderRunMode.REGULAR, TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN]:
            self.run_regular()
        elif self.traderConfig.runMode in [TraderRunMode.RUN_LIKE_QUANTOPIAN]:
            self.run_q()
        elif self.traderConfig.runMode == TraderRunMode.HFT:
            self.run_hft()
        else:
            self.log.error(__name__ + '::run: cannot handle traderConfig.runMode=%s' % (self.traderConfig.runMode,))
        self.log.info(__name__ + '::run: END')

    def run_regular(self):
        """
        Run handle_data every second(configurable), ignoring any market time or holidays
        :return:
        """
        self.log.debug(__name__ + '::run_regular')
        re = Repeater(self.repeaterConfig.slowdownInSecond,
                      self.trader.get_next_time,
                      self.trader.getWantToEnd,
                      self.log)

        # sequence matters!!! First scheduled, first run.
        repeater1 = Event.RepeatedEvent(self.marketManagerConfig.baseFreqOfProcessMessage, self.trader.processMessages)
        repeater2 = Event.RepeatedEvent(self.repBarFreq,
                                        self.trader.repeat_Function)
        re.schedule_event(repeater1)
        re.schedule_event(repeater2)
        # for ct in re.repeatedEvents:
        #    print(ct, re.repeatedEvents[ct])
        re.repeat()  # trader.setWantToEnd will call disconnect

    def run_q(self):
        """
        Run handle_data every minute when US market is open, observing market time or holidays configured by setting.MARKET_MANAGER.marketName
        :return:
        """
        self.log.debug(__name__ + '::run_q')
        self._check_at_beginning_of_a_day(self.trader.get_datetime())
        re = Repeater(self.repeaterConfig.slowdownInSecond,
                      self.trader.get_next_time,
                      self.trader.getWantToEnd,
                      self.log)
        # sequence matters!!! First scheduled, first run.
        repeater1 = Event.RepeatedEvent(self.marketManagerConfig.baseFreqOfProcessMessage, self.trader.processMessages)
        repeater2 = Event.RepeatedEvent(self.repBarFreq,
                                        self.trader.repeat_Function,
                                        passFunc=self._marketCalendar.is_market_open_at_this_moment)

        # When a new day starts, check if the new day is a trading day.
        # If it is a trading day, check marketOpenTime and marketCloseTime
        repeater3 = Event.ConceptEvent(TimeConcept.NEW_DAY, self._check_at_beginning_of_a_day)

        # 9:25 EST to run before_trading_start(context, dataFromServer)
        repeater4 = Event.SpotTimeEvent(self.marketManagerConfig.beforeTradeStartHour,
                                        self.marketManagerConfig.beforeTradeStartMinute,
                                        onSecond=0,
                                        do_something=self.trader.before_trade_start_Function,
                                        passFunc=self._marketCalendar.isTradingDay)  # 09:25 to run before_trading_start, a quantopian style function

        re.schedule_event(repeater1)
        re.schedule_event(repeater2)
        re.schedule_event(repeater3)
        re.schedule_event(repeater4)
        re.repeat()  # trader.setWantToEnd will call disconnect

    def run_hft(self):
        re = Repeater(self.repeaterConfig.slowdownInSecond,
                      self.trader.get_next_time,
                      self.trader.getWantToEnd,
                      self.log)
        # sequence matters!!! First scheduled, first run.
        repeater1 = Event.HftEvent(self.trader.processMessages)
        repeater2 = Event.HftEvent(self.trader.repeat_Function)
        re.schedule_event(repeater1)
        re.schedule_event(repeater2)
        re.repeat()  # trader.setWantToEnd will call disconnect

    def _check_at_beginning_of_a_day(self, timeNow):
        self.log.debug(__name__ + '::_check_at_beginning_of_a_day: timeNow=%s' % (timeNow,))
        timeNow = timeNow.astimezone(self.showTimeZone)
        if self._marketCalendar.isTradingDay(timeNow):  # do nothing if it is not a trading day
            self.balanceLog.info('%s %s %s' % (self.trader.get_datetime(),
                                               self.trader.show_account_info('NetLiquidation',
                                                                             accountCode=self.accountCode),
                                               self.trader.show_account_info('TotalCashValue',
                                                                             accountCode=self.accountCode)),
                                 verbose=False)

    def ingest_historical_data(self, histIngestionPlan):
        self.log.info('####     Data ingestion starts    ####')
        self.trader.brokerService.getBrokerClient().getDataProvider().ingest_hists(histIngestionPlan)
        self.log.info('####     Data ingestion COMPLETED    ####')


def setup_services(userConfig, trader=None):
    """
    stay here to avoid cyclic imports


    trader  <----> brokerService <-----> brokerClient ------> dataProvider
                                 -----> timeGenerator


    :param trader: passed in from configuration.txt because batch inputs
    :param userConfig:
    :return:
    """
    if userConfig.projectConfig.logLevel == LogLevel.DEBUG:
        print(__name__ + '::setup_services:userConfig id=%s trader id=%s' % (id(userConfig), id(trader)))

    # TimeGenerator instance will be used to build brokerClient and brokerService so that it needs to be created first.
    userConfig.timeGenerator = TimeGenerator(userConfig.timeGeneratorConfig)
    userConfig.singleTrader = SingleTrader(userConfig.log, userConfig.projectConfig.brokerName, userConfig.projectConfig.accountCode)
    userConfig.dataFromServer = DataFromServer()
    userConfig.dataProvider = data_provider_factory.get_data_provider(userConfig)
    userConfig.brokerClient = broker_client_factory.get_broker_client(userConfig)
    userConfig.brokerService = broker_service_factory.get_brokerService(userConfig)
    userConfig.marketCalendar = market_calendar_factory.get_marketCalendar(userConfig.marketManagerConfig.marketName)
    userConfig.emailClient = IbpyEmailClient(userConfig.emailClientConfig.IBRIDGEPY_EMAIL_CLIENT['apiKey'], userConfig.log)

    # Build a trader instance if it is not passed in
    # TODO: double -check here
    if trader is not None:
        userConfig.trader = trader
    else:  # for testing
        from IBridgePy.Trader import Trader
        userConfig.trader = Trader

    # set aTrader to brokerService and set brokerService to aTrader
    # so that they can call each other's functions, for example, Test_trader_single_account
    userConfig.trader.brokerService = userConfig.brokerService  # so that aTrader can call brokerService.reqMktData in TEST
    userConfig.brokerService.aTrader = userConfig.trader

    # If getting hist from IB, dataProvider should have a dataProviderClient
    # For IB, brokerClient is used as dataProviderClient because IB is a dataProvider
    if userConfig.projectConfig.dataProviderName == DataProviderName.IB:
        userConfig.dataProviderClient = userConfig.brokerClient
        userConfig.dataProvider.dataProviderClient = userConfig.dataProviderClient
    # Random dataProvider and LocalFile dataProvider does not need dataProviderClient
    elif userConfig.projectConfig.dataProviderName in [DataProviderName.RANDOM, DataProviderName.LOCAL_FILE]:
        pass
    # For other data providers, need dataProviderClient
    else:
        print(__name__ + '::setup_services: EXIT, cannot handle dataProviderName=%s' % (userConfig.dataProviderName,))
        exit()

    if trader:
        trader._marketCalendar = userConfig.marketCalendar

    if userConfig.projectConfig.logLevel == LogLevel.DEBUG:
        print(userConfig)
    return userConfig
