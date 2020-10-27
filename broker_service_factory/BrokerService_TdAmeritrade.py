from IBridgePy.constants import BrokerName
from broker_service_factory.BrokerService_web import WebApi


class TDAmeritrade(WebApi):
    def get_timestamp(self, security, tickType):
        raise NotImplementedError

    def get_contract_details(self, security, field):
        raise NotImplementedError

    @property
    def name(self):
        return BrokerName.TDAMERITRADE
