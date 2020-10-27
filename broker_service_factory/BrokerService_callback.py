# coding=utf-8
import datetime as dt
import time
from sys import exit

from broker_service_factory.BrokerService import BrokerService
from models.utils import print_IBCpp_contract


# noinspection PyAbstractClass
class CallBackType(BrokerService):
    @property
    def name(self):
        return "CallBackType"

    def get_position(self, accountCode, security):
        return self._get_position(accountCode, security)

    def get_all_orders(self, accountCode):
        return self._get_all_orders(accountCode)

    def get_all_positions(self, accountCode):
        """
        Get all of positionRecords associated with the accountCode
        :param accountCode:
        :return: dictionary, keyed by Security object with exchange info!!!, value = PositionRecord
        """
        self.log.debug(__name__ + '::get_all_positions: accountCode=%s' % (accountCode,))
        return self._get_all_positions(accountCode)

    def get_order(self, ibpyOrderId):
        """

        :param ibpyOrderId: string
        :return: broker_factory::records_def::IBridgePyOrder
        """
        self.log.notset(__name__ + '::get_order: ibpyOrderId=%s' % (ibpyOrderId,))
        accountCode = self._singleTrader.get_accountCode_by_ibpyOrderId(self.name, ibpyOrderId)
        return self._singleTrader.find_order(self.name, accountCode, ibpyOrderId)

    def order_status_monitor(self, ibpyOrderId, target_status, waitingTimeInSeconds=30):
        self.log.notset(__name__ + '::order_status_monitor: ibpyOrderId=%s target_status=%s' % (ibpyOrderId, target_status))
        timer = dt.datetime.now()
        while True:
            time.sleep(0.1)
            self._brokerClient.processMessagesWrapper(self.get_datetime())

            if (dt.datetime.now() - timer).total_seconds() <= waitingTimeInSeconds:
                tmp_status = self.get_order(ibpyOrderId).status
                if isinstance(target_status, str):
                    if tmp_status == target_status:
                        return True
                elif isinstance(target_status, list):
                    if tmp_status in target_status:
                        return True
            else:
                self.log.error(__name__ + '::order_status_monitor: EXIT, waiting time is too long, >%i' % (
                    waitingTimeInSeconds,))
                order = self.get_order(ibpyOrderId)
                contract = order.contract
                self.log.error(__name__ + '::order_status_monitor: EXIT, ibpyOrderId=%s status=%s contract=%s' % (ibpyOrderId, order.status, print_IBCpp_contract(contract)))
                exit()

    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        ans = self._singleTrader.get_account_info(self.name, accountCode, tag, meta)
        if ans is None:
            self.log.error(__name__ + '::_get_account_info_one_tag: EXIT, no value based on accountCode=%s tag=%s meta=%s' % (accountCode, tag, meta))
            print('active accountCode is %s' % (self._singleTrader.get_all_active_accountCodes(self.name),))
            exit()
        return ans
