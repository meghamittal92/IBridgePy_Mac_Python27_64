from IBridgePy.constants import BrokerName

PROJECT = {
    'brokerName': BrokerName.TDAMERITRADE
}


MARKET_MANAGER = {
    'baseFreqOfProcessMessage': 0,  # dont run Trader::processMessage()
}
