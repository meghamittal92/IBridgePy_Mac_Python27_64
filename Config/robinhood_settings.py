from IBridgePy.constants import BrokerName

PROJECT = {
    'brokerName': BrokerName.ROBINHOOD
}


MARKET_MANAGER = {
    'baseFreqOfProcessMessage': 0,  # dont run Trader::processMessage()
}
