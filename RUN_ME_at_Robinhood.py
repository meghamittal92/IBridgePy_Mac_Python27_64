from configuration import run_me_at_robinhood

fileName = 'example_show_positions.py'
# fileName = 'example_show_real_time_prices.py'
# fileName = 'example_get_historical_data.py'
# fileName = 'example_place_order.py'

accountCode = 'xxxxx'  # Put your Robinhood account number here, not Robinhood login ID.

repBarFreq = 60

# logLevel = 'DEBUG'

run_me_at_robinhood(fileName, globals())
