import pandas as pd
import talib as ta

def initialize(context):
    # context.run_once=False
    # context.security=symbol('CASH, EUR, USD')
    pass

def handle_data(context, data):
    # order_Id = order_target_percent(context.security, 0, style=MarketOrder())
    # order_status_monitor(order_Id, target_status = 'Filled')
    close_all_positions()

