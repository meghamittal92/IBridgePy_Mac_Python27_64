import datetime as dt
from data_provider_factory.data_loading_plan import HistIngestionPlan, Plan
from IBridgePy.IbridgepyTools import symbol, superSymbol
from configuration import test_me
import pytz
import pandas
from BackTestVars import securities
# fileName = 'example_show_positions.py'
# fileName = 'example_show_real_time_prices.py'
# fileName = 'example_get_historical_data.py'
# fileName = 'example_place_order.py'
#fileName = 'demo_close_price_reversion.py'
#fileName = 'OnlyDICrossOverStrategyNew.py'
fileName = 'DICrossOverMultiThreadedV6.py'

# logLevel = 'DEBUG'

accountCode = 'DU1073267'  # IB accountCode is needed to retrieve historical data from IB server.
#accountCode = 'DU228378'
global someString
someString = 'some'
dataProviderName = 'LOCAL_FILE'  # RANDOM, IB, LOCAL_FILE
runMode = 'SUDO_RUN_LIKE_QUANTOPIAN'
logLevel = 'INFO'

# histIngestionPlan is a reserved word in IBridgePy to store the historical data ingestion plan
# It is an instance of HistIngestionPlan.
# The add function is used to add more Ingestion Plans if needed
# http://www.ibridgepy.com/2019/05/20/backtest-strategies-ibridgepy/
histIngestionPlan = HistIngestionPlan()
#histIngestionPlan.saveToFile = True

for secSymbol in securities :
    histIngestionPlan.add(Plan(security=symbol(secSymbol), barSize='1 min', goBack='10 D', fileName=secSymbol +'1min.csv'))
    #histIngestionPlan.add(Plan(security=symbol(secSymbol), barSize='5 mins', goBack='10 D', fileName=secSymbol + '5mins.csv'))
    #histIngestionPlan.add(Plan(security=symbol(secSymbol), barSize='10 mins', goBack='10 D', fileName=secSymbol + '10mins.csv'))
    histIngestionPlan.add(Plan(security=symbol(secSymbol), barSize='15 mins', goBack='10 D', fileName=secSymbol + '15mins.csv'))
    histIngestionPlan.add(Plan(security=symbol(secSymbol), barSize='20 mins', goBack='10 D', fileName=secSymbol + '20mins.csv'))
    histIngestionPlan.add(Plan(security=symbol(secSymbol), barSize='30 mins', goBack='10 D', fileName=secSymbol + '30mins.csv'))
    #histIngestionPlan.add(Plan(security=symbol(secSymbol), barSize='1 hour', goBack='10 D', fileName=secSymbol + '1 hour.csv'))
# histIngestionPlan.add(Plan(security=symbol('SQ'), barSize='15 mins', goBack='10 D', fileName='SQ15mins.csv'))
# histIngestionPlan.add(Plan(security=symbol('SQ'), barSize='20 mins', goBack='10 D', fileName='SQ20mins.csv'))

# histIngestionPlan.add(Plan(security=symbol('AAPL'), barSize='1 min', goBack='10 D', fileName='AAPL1min.csv'))
# histIngestionPlan.add(Plan(security=symbol('AAPL'), barSize='5 mins', goBack='10 D', fileName='AAPL5mins.csv'))
# histIngestionPlan.add(Plan(security=symbol('AAPL'), barSize='10 mins', goBack='10 D', fileName='AAPL10mins.csv'))
# histIngestionPlan.add(Plan(security=symbol('AAPL'), barSize='15 mins', goBack='10 D', fileName='AAPL15mins.csv'))
# histIngestionPlan.add(Plan(security=symbol('AAPL'), barSize='20 mins', goBack='10 D', fileName='AAPL20mins.csv'))

# histIngestionPlan.add(Plan(security=symbol('SPY'), barSize='1 min', goBack='10 D', fileName='SPY1min.csv'))
# histIngestionPlan.add(Plan(security=symbol('SPY'), barSize='5 mins', goBack='10 D', fileName='SPY5mins.csv'))
# histIngestionPlan.add(Plan(security=symbol('SPY'), barSize='10 mins', goBack='10 D', fileName='SPY10mins.csv'))
# histIngestionPlan.add(Plan(security=symbol('SPY'), barSize='15 mins', goBack='10 D', fileName='SPY15mins.csv'))
# histIngestionPlan.add(Plan(security=symbol('SPY'), barSize='20 mins', goBack='10 D', fileName='SPY20mins.csv'))




# In AUTO mode, backtesting time series will be created automatically based on endTime, startTime and freq
timeGeneratorType = 'CUSTOM'
customSpotTimeList = []
secSymbol = securities[0]
df = pandas.read_csv('Input/'+ secSymbol+'1min.csv')

for epoch_time in df['Unnamed: 0']:
    print("EPOCH TIME :" + str(epoch_time))
    
    if(epoch_time >= 1601400000.0):
        a = pytz.timezone('US/Eastern').localize(dt.datetime.fromtimestamp(epoch_time))
        #if(a.hour == 9 and a.minute >=30) or (a.hour > 9 and a.hour <=15):
        #if(a.hour == 9 and a.minute >=15) or (a.hour > 9):
            #print(a.hour, a.minute)
        customSpotTimeList.append(a)
# As a demo, the backtesting starts from 4 days ago, and ends at the current datetime.
#endTime = dt.datetime.now().replace(second=0)  # default timezone = 'US/Eastern'
#startTime = endTime - dt.timedelta(days=9)  # default timezone = 'US/Eastern'
#freq = '1T'  # 1S = 1 second; 1T = 1 minute; 1H = 1 hour

test_me(fileName, globals())