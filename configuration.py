# coding=utf-8
import os

# noinspection PyUnresolvedReferences
from BasicPyLib.BasicTools import roundToMinTick
from Config.config_defs import UserConfig
# noinspection PyUnresolvedReferences
from IBridgePy.IbridgepyTools import superSymbol
from IBridgePy.MarketManagerBase import MarketManager
from IBridgePy.Trader import Trader
from IBridgePy.constants import LiveBacktest, DataProviderName
# noinspection PyUnresolvedReferences
from IBridgePy.quantopian import MarketOrder, LimitOrder, StopOrder, StopLimitOrder, TrailStopLimitOrder, \
    TrailStopOrder, date_rules, time_rules, calendars


def test_me(fileName, userManualInput, userConfig=UserConfig.BACKTEST):
    userConfig = _build_config(userConfig, userManualInput, fileName)
    finally_run(userConfig, LiveBacktest.BACKTEST)


def run_me_at_robinhood(fileName, userManualInput, userConfig=UserConfig.ROBINHOOD):
    run_me(fileName, userManualInput, userConfig)


def run_me_at_td_ameritrade(fileName, userManualInput, userConfig=UserConfig.TD):
    run_me(fileName, userManualInput, userConfig)


def run_me(fileName, userManualInput, userConfig=UserConfig.REGULAR):
    userConfig = _build_config(userConfig, userManualInput, fileName)
    finally_run(userConfig, LiveBacktest.LIVE)


# noinspection DuplicatedCode
def _build_config(userConfig, userManualInput=None, fileName=None):
    # print(userManualInput)
    # print(userConfig)
    trader = Trader()  # To setup trader, trader.update_from_userConfig is needed

    # the following must happen before     globals().update(locals())
    cancel_all_orders = trader.cancel_all_orders
    cancel_order = trader.cancel_order
    close_all_positions = trader.close_all_positions
    close_all_positions_except = trader.close_all_positions_except
    count_positions = trader.count_positions
    create_order = trader.create_order
    display_all = trader.display_all
    display_orderStatus = trader.display_orderStatus
    display_positions = trader.display_positions
    end = trader.setWantToEnd
    get_datetime = trader.get_datetime
    get_all_open_orders = trader.get_all_open_orders
    get_all_orders = trader.get_all_orders
    get_all_positions = trader.get_all_positions
    get_contract_details = trader.get_contract_details
    get_open_orders = trader.get_open_orders
    get_option_greeks = trader.get_option_greeks
    get_order = trader.get_order
    get_order_status = trader.get_order_status
    get_position = trader.get_position
    get_scanner_results = trader.get_scanner_results
    hold_any_position = trader.hold_any_position
    isEarlyClose = trader.isEarlyClose
    isTradingDay = trader.isTradingDay
    modify_order = trader.modify_order
    order = trader.order
    order_status_monitor = trader.order_status_monitor
    order_target = trader.order_target
    order_target_percent = trader.order_target_percent
    order_target_value = trader.order_target_value
    order_percent = trader.order_percent
    order_value = trader.order_value
    place_combination_orders = trader.place_combination_orders
    place_order_with_stoploss = trader.place_order_with_stoploss
    place_order_with_stoploss_takeprofit = trader.place_order_with_stoploss_takeprofit
    place_order_with_takeprofit = trader.place_order_with_takeprofit
    request_historical_data = trader.request_historical_data
    rebalance_portfolio = trader.rebalance_portfolio
    record = trader.record
    schedule_function = trader.schedule_function
    send_email = trader.send_email
    show_account_info = trader.show_account_info
    show_real_time_price = trader.show_real_time_price
    show_real_time_size = trader.show_real_time_size
    show_timestamp = trader.show_timestamp
    symbol = trader.symbol
    symbols = trader.symbols

    # open function in py2 and py3 are different.
    # UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 1035: character maps to <undefined> (Question id : 728)
    # The root cause of the above error is that some strange characters show up in the imported files.
    # Only happens in Windows Py3 because open in py3 does not use default utf-8 decoder but it uses the default encoder set by windows.
    # The solution is not to use strange characters.
    if fileName:  # It is fine without fileName. It will be used in testing framework
        with open(os.path.join(userConfig.projectConfig.rootFolderPath, 'Strategies', fileName)) as f:
            script = f.read()
        # noinspection PyRedundantParentheses
        exec(script)

    # If without this line, handle_data and initialize would be local variables
    # but the IBridgePy build-in functions, such as cancel_all_orders, order_target and get_positions, are all global variables
    # If without this line, error jumps out.
    # NameError: global name 'cancel_all_orders' is not defined
    # update is to merger two dictionaries
    globals().update(locals())

    if userManualInput:
        locals().update(userManualInput)

    # setup_service happens inside here.
    # After this line, all instances should be ready to use in userConfig
    userConfig.prepare_userConfig_with_trader(trader, locals())
    return userConfig


def finally_run(userConfig, liveOrTest):
    if liveOrTest == LiveBacktest.LIVE:
        c = MarketManager(userConfig)
        c.run()
    elif liveOrTest == LiveBacktest.BACKTEST:
        if userConfig.projectConfig.dataProviderName != DataProviderName.IB:
            c = MarketManager(userConfig)
            c.ingest_historical_data(userConfig.projectConfig.histIngestionPlan)
            c.run()
        else:
            # dataProvider is an independent component that can be built by a different config.
            userConfig_dataProvider_IB = UserConfig().REGULAR
            userConfig_dataProvider_IB.projectConfig.set_value('rootFolderPath', os.getcwd(), __name__ + '::run_me')
            userConfig_dataProvider_IB.projectConfig.set_value('dataProviderName', DataProviderName.IB, __name__ + '::run_me')
            userConfig_dataProvider_IB.projectConfig.set_value('accountCode', userConfig.projectConfig.accountCode, __name__ + '::run_me')
            userConfig_dataProvider_IB.log = userConfig.log

            c = MarketManager(userConfig, userConfig_dataProvider_IB)
            c.ingest_historical_data(userConfig.projectConfig.histIngestionPlan)
            c.run()
