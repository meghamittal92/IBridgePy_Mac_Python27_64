# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from IBridgePy.constants import BrokerName, LogLevel


def get_brokerService(userConfig):
    if userConfig.projectConfig.logLevel == LogLevel.DEBUG:
        print(__name__ + '::get_broker_client')
    name = userConfig.projectConfig.brokerName
    if name == BrokerName.LOCAL_BROKER:
        from .BrokerService_Local import LocalBroker
        return LocalBroker(userConfig.log,
                           userConfig.brokerClient,
                           userConfig.timeGenerator,
                           userConfig.singleTrader,
                           userConfig.dataFromServer)
    elif name == BrokerName.IB:
        from .BrokerService_IB import InteractiveBrokers
        return InteractiveBrokers(userConfig.log,
                                  userConfig.brokerClient,
                                  userConfig.timeGenerator,
                                  userConfig.singleTrader,
                                  userConfig.dataFromServer)
    elif name == BrokerName.ROBINHOOD:
        from .BrokerService_Robinhood import Robinhood
        return Robinhood(userConfig.log,
                         userConfig.brokerClient,
                         userConfig.timeGenerator,
                         userConfig.singleTrader,
                         userConfig.dataFromServer)
    elif name == BrokerName.TDAMERITRADE:
        from .BrokerService_TdAmeritrade import TDAmeritrade
        return TDAmeritrade(userConfig.log,
                            userConfig.brokerClient,
                            userConfig.timeGenerator,
                            userConfig.singleTrader,
                            userConfig.dataFromServer)
    else:
        print(__name__ + '::get_brokerService: cannot handle brokerName=%s' % (name,))
