# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from IBridgePy.constants import BrokerName
from sys import exit


def get_broker_client(userConfig):
    brokerName = userConfig.projectConfig.brokerName
    if brokerName == BrokerName.LOCAL_BROKER:
        from .BrokerClient_Local import ClientLocalBroker
        clientLocalBroker = ClientLocalBroker()
        clientLocalBroker.setup_client_local_broker(userConfig.log,
                                                    userConfig.projectConfig.accountCode,
                                                    userConfig.projectConfig.rootFolderPath,
                                                    userConfig.singleTrader,
                                                    userConfig.dataFromServer,
                                                    userConfig.timeGenerator,
                                                    userConfig.dataProvider)
        return clientLocalBroker
    elif brokerName == BrokerName.IB:
        from .BrokerClient_IB import ClientIB
        """
        !!! BrokerClient class does not have any constructor because it extends IBClient from IBCpp.
        !!! To create an instance, just create and then call setup_client_xxx
        """
        clientIB = ClientIB()
        clientIB.setup_client_IB(userConfig.log,
                                 userConfig.projectConfig.accountCode,
                                 userConfig.projectConfig.rootFolderPath,
                                 userConfig.singleTrader,
                                 userConfig.dataFromServer,
                                 userConfig.timeGenerator,
                                 userConfig.brokerClientConfig.IB_CLIENT['host'],
                                 userConfig.brokerClientConfig.IB_CLIENT['port'],
                                 userConfig.brokerClientConfig.IB_CLIENT['clientId'])
        return clientIB
    elif brokerName == BrokerName.ROBINHOOD:
        from .BrokerClient_Robinhood import BrokerClientRobinhood
        from .Robinhood.robinhoodClient import RobinhoodClient

        robinhoodClient = RobinhoodClient()
        brokerClientRobinhood = BrokerClientRobinhood()
        brokerClientRobinhood.setup_brokerClient_Robinhood(userConfig.log,
                                                           userConfig.projectConfig.rootFolderPath,
                                                           userConfig.singleTrader,
                                                           userConfig.dataFromServer,
                                                           userConfig.timeGenerator,
                                                           robinhoodClient,
                                                           userConfig.projectConfig.accountCode,
                                                           userConfig.brokerClientConfig.ROBINHOOD_CLIENT['username'],
                                                           userConfig.brokerClientConfig.ROBINHOOD_CLIENT['password'])
        return brokerClientRobinhood
    elif brokerName == BrokerName.TDAMERITRADE:
        from broker_client_factory.TdAmeritrade import TDClient
        from .BrokerClient_TdAmeritrade import BrokerClientTdAmeritrade
        tdClient = TDClient(userConfig.brokerClientConfig.TD_CLIENT['refreshToken'],
                            userConfig.brokerClientConfig.TD_CLIENT['apiKey'],
                            userConfig.brokerClientConfig.TD_CLIENT['refreshTokenCreatedOn'],
                            [userConfig.projectConfig.accountCode],
                            userConfig.log)
        brokerClientTD = BrokerClientTdAmeritrade()
        brokerClientTD.setup_brokerClient_TDAmeritrade(userConfig.log,
                                                       userConfig.projectConfig.rootFolderPath,
                                                       userConfig.singleTrader,
                                                       userConfig.dataFromServer,
                                                       userConfig.timeGenerator,
                                                       tdClient,
                                                       userConfig.projectConfig.accountCode)
        return brokerClientTD
    else:
        print(__name__ + '::get_broker_client: cannot handle _brokerName = %s' % (brokerName,))


class Converter:
    """
    IB uses integer as orderId and it must increase.
    Other brokers use string as orderId.
    And IBridgePy has switched fro int_orderId to str_orderId.
    For IB, str_orderId = 'ib' + int_orderId
    For other brokers, use broker's original str_orderId
    """
    def __init__(self, brokerName, createrOfIBValue=None):
        self._brokerName = brokerName
        self.fromBrokerToIBDict = {}
        self.fromIBToBrokerDict = {}
        self.createrOfIBValue = createrOfIBValue

    def fromBrokerToIB(self, brokerValue):
        """
        Converter a str_orderId to int_orderId
        :param brokerValue: string
        :return: int
        """
        if brokerValue in self.fromBrokerToIBDict:
            return self.fromBrokerToIBDict[brokerValue]
        ibValue = None
        if self._brokerName in [BrokerName.IB, BrokerName.LOCAL_BROKER]:
            ibValue = int(brokerValue)
        elif self._brokerName in [BrokerName.TDAMERITRADE, BrokerName.ROBINHOOD]:
            ibValue = self.createrOfIBValue.useOne()
        else:
            print(__name__ + '::Converter::fromBrokerToIB: EXIT, cannot handle brokerName=%s' % (self._brokerName,))
            exit()
        self.setRelationship(ibValue, brokerValue)
        return ibValue

    def fromIBtoBroker(self, ibValue):
        """
        Converter a int_orderId to str_orderId
        :param ibValue: int
        :return: string
        """
        # For non-IB orders, they should have been registered in brokerClient_xx using setRelationship
        if ibValue in self.fromIBToBrokerDict:
            return self.fromIBToBrokerDict[ibValue]

        if self._brokerName in [BrokerName.IB, BrokerName.LOCAL_BROKER]:
            brokerValue = 'ib' + str(ibValue)
            self.setRelationship(ibValue, brokerValue)
            return brokerValue
        else:
            print(__name__ + '::Converter::fromBrokerToIB: EXIT, For non-IB orders, they should have been registered in brokerClient_xx using setRelationship')
            exit()

    def setRelationship(self, ibValue, brokerValue):
        # print(__name__ + '::Converter::setRelationship: ibValue=%s brokerValue=%s' % (ibValue, brokerValue))
        self.fromBrokerToIBDict[brokerValue] = ibValue
        self.fromIBToBrokerDict[ibValue] = brokerValue

    def verifyRelationship(self, ibValue, brokerValue):
        ans = (ibValue in self.fromIBToBrokerDict) and (brokerValue in self.fromBrokerToIBDict) and (self.fromIBToBrokerDict[ibValue] == brokerValue)
        if not ans:
            print(__name__ + '::Converter::verifyRelationship: EXIT, ibValue=%s brokerValue=%s' % (ibValue, brokerValue))
            print(self.fromIBToBrokerDict)
            print(self.fromBrokerToIBDict)
            exit()
