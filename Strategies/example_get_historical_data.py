# -*- coding: utf-8 -*-
"""
There is a risk of loss when trading stocks, futures, forex, options and other
financial instruments. Please trade with capital you can afford to
lose. Past performance is not necessarily indicative of future results.
Nothing in this computer program/code is intended to be a recommendation, explicitly or implicitly, and/or
solicitation to buy or sell any stocks or futures or options or any securities/financial instruments.
All information and computer programs provided here is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how to use these information and
are solely responsible any consequences of using these information.

If you have any questions, please send email to IBridgePy@gmail.com
All rights reserved.
"""
import time
import pytz
# Introduction to request_historical_data. YouTube tutorial https://youtu.be/7jmHRVsRcI0
# Request historical data of other than U.S. equities and handle 'No data permission' and 'No security definition'. YouTube tutorial https://youtu.be/iiRierq6sTU
# Request historical data of FOREX, provided by Interactive Brokers for free. YouTube tutorial https://youtu.be/7jmHRVsRcI0
# If you need help on coding, please consider our well known Rent-a-Coder service. https://ibridgepy.com/rent_a_coder/
def initialize(context):
    # IB offers free historical data for FOREX. Please refer to this YouTube tutorial https://youtu.be/JkyxLYD2RBk
    #context.security = symbol('AAPL')
    # context.secList = symbols('AAPL', 'GOOG')
    #context.security=symbol('CASH, EUR, USD')
    #myFile = open('EURUSDdata.csv', 'w')
    #context.file = myFile
    pass

def handle_data(context, data):
    # Method 1: IBridgePy function request_historical_data(str_security, barSize, goBack)
    # Users have more controls on this function.
    # http://www.ibridgepy.com/ibridgepy-documentation/#request_historical_data
    symbolString = 'AAPL'
    context.security = symbol(symbolString)
    # print ('Historical Data of %s' % (str(context.security, ),))
    # hist = request_historical_data(context.security, '1 min', '10 D', useRTH = 0, timezoneOfReturn=pytz.timezone('US/Eastern'))
    # hist.index = hist.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    # hist.to_csv(symbolString + '1min.csv', encoding='utf-8')
    # print(hist)
    # print(hist.iloc[-1]['close'])
    

    print ('Historical Data of %s' % (str(context.security, ),))
    hist = request_historical_data(context.security, '1 min', '20 D', useRTH = 0, timezoneOfReturn=pytz.timezone('US/Eastern'), formatDate = 2)
    #hist.index = hist.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    hist.to_csv(symbolString + '1min.csv', encoding='utf-8')
    print(hist)
    print(hist.iloc[-1]['close'])

    # print ('Historical Data of %s' % (str(context.security, ),))
    # hist = request_historical_data(context.security, '5 mins', '10 D', useRTH = 0, timezoneOfReturn=pytz.timezone('US/Eastern'), formatDate = 2)
    # #hist.index = hist.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    # hist.to_csv(symbolString + '5mins.csv', encoding='utf-8')
    # print(hist)
    # print(hist.iloc[-1]['close'])

    # print ('Historical Data of %s' % (str(context.security, ),))
    # hist = request_historical_data(context.security, '10 mins', '10 D', useRTH = 0, timezoneOfReturn=pytz.timezone('US/Eastern'), formatDate = 2)
    # #hist.index = hist.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    # hist.to_csv(symbolString + '10mins.csv', encoding='utf-8')
    # print(hist)
    # print(hist.iloc[-1]['close'])

    print ('Historical Data of %s' % (str(context.security, ),))
    hist = request_historical_data(context.security, '15 mins', '20 D', useRTH = 0, timezoneOfReturn=pytz.timezone('US/Eastern'), formatDate = 2)
    #hist.index = hist.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    hist.to_csv(symbolString + '15mins.csv', encoding='utf-8')
    print(hist)
    print(hist.iloc[-1]['close'])


    print ('Historical Data of %s' % (str(context.security, ),))
    hist = request_historical_data(context.security, '20 mins', '20 D', useRTH = 0, timezoneOfReturn=pytz.timezone('US/Eastern'), formatDate = 2)
    #hist.index = hist.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    hist.to_csv(symbolString + '20mins.csv', encoding='utf-8')
    print(hist)
    print(hist.iloc[-1]['close'])

    print ('Historical Data of %s' % (str(context.security, ),))
    hist = request_historical_data(context.security, '30 mins', '20 D', useRTH = 0, timezoneOfReturn=pytz.timezone('US/Eastern'), formatDate = 2)
    #hist.index = hist.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    hist.to_csv(symbolString + '30mins.csv', encoding='utf-8')
    print(hist)
    print(hist.iloc[-1]['close'])



    end()
