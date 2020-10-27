import importlib
from sys import exit

from BasicPyLib import simpleLogger
# noinspection PyUnresolvedReferences
from Config import base_settings
from BasicPyLib.BasicTools import CONSTANTS, isAllLettersCapital
from BasicPyLib.Printable import PrintableII, Printable
import time

from Config.configTools import get_user_input_and_set_default_values
from IBridgePy.MarketManagerBase import setup_services
from IBridgePy.constants import DataProviderName, BrokerName, LiveBacktest, TraderRunMode, TimeGeneratorType, MarketName

"""
To create a new config
step 1: create a class like MARKET_MANAGER_Config; the format must be XXX_Config or XXX_XXX_Config
step 2: in base_setting.py add setting values as dictionary, naming must be XXX or XXX_XXX. It must to add all possible values and give default values
step 3: If it is user input setting, put default value for user in setting.py
step 4: If it needs special config other than base, add something like Config/backtest_settings.py, naming must be xxxx_settings.py
"""


class Config(PrintableII):
    def __init__(self, dict_settings):
        for key in dict_settings:
            setattr(self, key, dict_settings[key])

    def override(self, settings, settingFileName):
        for key in settings:
            # TODO: The whole part is due to IB_Client is a dict, not a XXX_config class
            if isinstance(settings[key], dict):
                originalValues = None
                try:
                    originalValues = getattr(self, key)
                except AttributeError as e:
                    print(__name__ + '::override: EXIT, %s. Hint: Check Config::base_settings if it has the attribute.' % (e,))
                    exit()
                newValueDict = settings[key]
                for k in newValueDict:
                    if k in originalValues:
                        originalValues[k] = newValueDict[k]
                    else:
                        print(__name__ + '::override: EXIT, key=%s in the file of <%s.py> does not exist in Config::base_settings.py' % (k, settingFileName))
                        exit()
            else:
                self.set_value(key, settings[key], settingFileName)
        return self

    def set_value(self, fieldName, value, settingName):
        """

        :param fieldName:
        :param value:
        :param settingName: string, used to display the fileName/source of the settings
        :return:
        """
        if hasattr(self, fieldName):
            setattr(self, fieldName, value)
        else:
            print(__name__ + '::set_value: class=%s key=%s settingFileName=%s does not exist.' % (self.__class__, fieldName, settingName))
            print('base_config: %s' % (self,))
            exit()


# noinspection PyPep8Naming
class MARKET_MANAGER_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class REPEATER_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class TIME_GENERATOR_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class BROKER_SERVICE_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class PROJECT_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class TRADER_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class BROKER_CLIENT_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class EMAIL_CLIENT_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class UserConfigBase(Printable):  # should not be used directly
    def __init__(self):
        """
        For example, there is a file Config::hft_settings.py Then, a possible value of addOnSettings is "hft_settings"
        """
        # NEW config system
        self.projectConfig = None
        self.marketManagerConfig = None
        self.repeaterConfig = None
        self.timeGeneratorConfig = None
        self.traderConfig = None
        self.brokerClientConfig = None
        self.emailClientConfig = None

        self.initialize_quantopian = None
        self.handle_data_quantopian = None
        self.before_trading_start_quantopian = None

        self.timeGenerator = None
        self.dataFromServer = None
        self.singleTrader = None
        self.trader = None
        self.dataProvider = None
        self.dataProviderClient = None
        self.log = None
        self.userLog = None
        self.brokerService = None
        self.brokerClient = None
        self.emailClient = None  # to send email out

    def load_settings(self, str_settings):
        module_settings = importlib.import_module(str_settings)
        for item in dir(module_settings):
            if isAllLettersCapital(item):
                if item == 'PROJECT':
                    self.projectConfig = PROJECT_Config(getattr(module_settings, item))
                elif item == 'MARKET_MANAGER':
                    self.marketManagerConfig = MARKET_MANAGER_Config(getattr(module_settings, item))
                elif item == 'REPEATER':
                    self.repeaterConfig = REPEATER_Config(getattr(module_settings, item))
                elif item == 'TIME_GENERATOR':
                    self.timeGeneratorConfig = TIME_GENERATOR_Config(getattr(module_settings, item))
                elif item == 'TRADER':
                    self.traderConfig = TRADER_Config(getattr(module_settings, item))
                elif item == 'BROKER_CLIENT':
                    self.brokerClientConfig = BROKER_CLIENT_Config(getattr(module_settings, item))
                elif item == 'EMAIL_CLIENT':
                    self.emailClientConfig = EMAIL_CLIENT_Config(getattr(module_settings, item))
                else:
                    print(__name__ + '::load_settings: EXIT, cannot handle item=%s in %s.py' % (item, str_settings))
                    exit()
        return self

    def overrideBy(self, str_settings):
        module_settings = importlib.import_module(str_settings)
        for item in dir(module_settings):
            if isAllLettersCapital(item):
                if item == 'PROJECT':
                    self.projectConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'MARKET_MANAGER':
                    self.marketManagerConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'REPEATER':
                    self.repeaterConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'TIME_GENERATOR':
                    self.timeGeneratorConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'TRADER':
                    self.traderConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'BROKER_CLIENT':
                    self.brokerClientConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'EMAIL_CLIENT':
                    self.emailClientConfig.override(getattr(module_settings, item), str_settings)
                else:
                    print(__name__ + '::overrideBy: EXIT, cannot handle item=%s in %s' % (item, str_settings))
                    exit()
        return self

    def build(self):
        # userLog is for the function of record (). User will use it for any reason.
        dateTimeStr = time.strftime("%Y_%m_%d_%H_%M_%S")
        self.userLog = simpleLogger.SimpleLoggerClass(filename='userLog_' + dateTimeStr + '.txt', logLevel='NOTSET', addTime=False)
        sysLogFileName = 'TraderLog_' + time.strftime("%Y-%m-%d") + '.txt'
        self.log = simpleLogger.SimpleLoggerClass(sysLogFileName, self.projectConfig.logLevel)
        return self

    def validate(self):
        if self.projectConfig.dataProviderName in [DataProviderName.RANDOM, DataProviderName.LOCAL_FILE]:
            assert(self.projectConfig.brokerName == BrokerName.LOCAL_BROKER)

        if self.projectConfig.histIngestionPlan is None:
            if self.projectConfig.liveOrBacktest == LiveBacktest.BACKTEST:
                assert(self.projectConfig.dataProviderName == DataProviderName.RANDOM)

        if self.traderConfig.runMode in [TraderRunMode.RUN_LIKE_QUANTOPIAN, TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN]:
            if self.projectConfig.repBarFreq != 60:
                print(__name__ + '::validate: EXIT, projectConfig.repBarFreq=%s It should be 60 when traderConfig.runMode is either RUN_LIKE_QUANTOPIAN or SUDO_RUN_LIKE_QUANTOPIAN' % (self.projectConfig.repBarFreq,))
                exit()

        # if self.traderConfig.runMode == TraderRunMode.REGULAR:
        #     if self.marketManagerConfig.marketName != MarketName.NONSTOP:
        #         print(__name__ + '::validate: EXIT, marketManagerConfig.marketName=%s, it should be NONSTOP' % (self.marketManagerConfig.marketName,))
        #         exit()

    def load_userInput_to_userConfig(self, user_input):
        # No action to map from user_input to user_config
        for item in ['accountCode', 'repBarFreq', 'fileName', 'logLevel', 'dataProviderName', 'histIngestionPlan']:
            if hasattr(user_input, item):
                self.projectConfig.set_value(item, getattr(user_input, item), __name__ + '::load_userInput_to_userConfig')
        if hasattr(user_input, 'marketName'):
            self.marketManagerConfig.set_value('marketName', user_input.marketName, __name__ + '::load_userInput_to_userConfig')

        if hasattr(user_input, 'timeGeneratorType'):
            self.timeGeneratorConfig.set_value('timeGeneratorType', user_input.timeGeneratorType, __name__ + '::load_userInput_to_userConfig')
            if user_input.timeGeneratorType == TimeGeneratorType.AUTO:
                if hasattr(user_input, 'startTime'):
                    self.timeGeneratorConfig.set_value('startingTime', user_input.startTime, __name__ + '::load_userInput_to_userConfig')
                else:
                    print(__name__ + '::load_input: EXIT, startTime is None.')
                    exit()

                if hasattr(user_input, 'endTime'):
                    self.timeGeneratorConfig.set_value('endingTime', user_input.endTime, __name__ + '::load_userInput_to_userConfig')
                else:
                    print(__name__ + '::load_input: EXIT, endTime is None.')
                    exit()

                if hasattr(user_input, 'freq'):
                    self.timeGeneratorConfig.set_value('freq', user_input.freq, __name__ + '::load_userInput_to_userConfig')
                else:
                    print(__name__ + '::load_input: EXIT, freq is None.')
                    exit()
            elif user_input.timeGeneratorType == TimeGeneratorType.CUSTOM:
                if hasattr(user_input, 'customSpotTimeList'):
                    self.timeGeneratorConfig.set_value('custom', user_input.customSpotTimeList, __name__ + '::load_userInput_to_userConfig')
                else:
                    print(__name__ + '::load_input: EXIT, customSpotTimeList is empty.')
                    exit()

        if hasattr(user_input, 'runMode'):
            if user_input.runMode in [TraderRunMode.RUN_LIKE_QUANTOPIAN, TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN]:
                self.projectConfig.set_value('repBarFreq', 60, __name__ + '::load_userInput_to_userConfig')
                self.traderConfig.set_value('runMode', user_input.runMode, __name__ + '::load_userInput_to_userConfig')
                if user_input.runMode == TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN:
                    self.marketManagerConfig.set_value('marketName', MarketName.NONSTOP, __name__ + '::load_userInput_to_userConfig')

        self.initialize_quantopian = user_input.initialize
        self.handle_data_quantopian = user_input.handle_data
        self.before_trading_start_quantopian = user_input.before_trading_start

    def prepare_userConfig_with_trader(self, trader, globalsV):
        userInput = get_user_input_and_set_default_values(globalsV)

        # base userConfig is passed-in.
        # This part only merge userInput into userConfig and then build userConfig.
        self.load_userInput_to_userConfig(userInput)  # set many values in userConfig
        self.build()  # set many values in userConfig

        # cannot instantiate trader here because defined_functions user's input need to go after trader.
        setup_services(self, trader)  # set many values in userConfig
        trader.update_from_userConfig(self)  # should not set any values in userConfig
        self.validate()


class UserConfig(CONSTANTS):
    # Override sequence MATTERS!!!
    REGULAR = UserConfigBase().load_settings('Config.base_settings').overrideBy('settings')
    BACKTEST = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.backtest_settings').overrideBy('settings')
    HFT = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.hft_settings').overrideBy('settings')
    ROBINHOOD = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.robinhood_settings').overrideBy('settings')
    TD = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.td_settings').overrideBy('settings')

    @staticmethod
    def choose(settingNames):
        if isinstance(settingNames, str):
            list_settingName = [settingNames]
        else:
            list_settingName = settingNames
        ans = UserConfigBase().load_settings('Config.base_settings')
        for settingName in list_settingName:
            # print(__name__ + '::choose: loading %s' % (settingFileName,))
            ans = ans.overrideBy('Config.%s' % (settingName,))
        ans = ans.overrideBy('settings')
        # print(ans)
        return ans


def test__isAllLettersCapital():
    assert(isAllLettersCapital('asdfEdasdf') is False)
    assert(isAllLettersCapital('BROKER_CLIENT') is True)
    assert(isAllLettersCapital('BROKER_CLIENt') is False)
