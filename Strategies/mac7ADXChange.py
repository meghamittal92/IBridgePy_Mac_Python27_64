import pandas as pd
#import talib as ta
import time
import sys
import os
import stockstats
#from ta.trend import ADXIndicator
sys.path.append(os.path.abspath("/Users/meghamittal/Downloads/IBridgePy_Mac_Python27_64/Strategies"))
from technicalIndicators import *
ACCEPTABLE_POSITIVE_POSITIONS = 4000
ACCEPTABLE_NEGATIVE_POSITIONS = -4000

def initialize(context):
    context.run_once=False

    #context.security=symbol('CASH, EUR, USD')
    context.security=symbol('AAPL')

    sample = open('AAPLBackTest14Sept.txt', 'w')
    context.file = sample
    context.file.write("######\n")
    context.file.write("AT BEGINNING\n")
    context.file.write("AAPL ask_price=" + str(show_real_time_price(context.security, 'ask_price')) + "\n")
    #context.file.write(show_timestamp(context.security, 'ask_price').strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    context.file.write ("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
    context.file.write ("Positions Value: " + str(context.portfolio.positions_value) + "\n")
    context.file.write ("Portfolio Cash:" + str(context.portfolio.cash) + "\n")  
    order_string = get_order_string(context)  
    context.file.write("ORDERS\n" + order_string + "\n")
    positions_string = get_positions_string(context)  
    context.file.write("POSITIONS\n" + positions_string + "\n")
    #context.file.write ("Unrealised PNL:" + str(context.portfolio.pnl) + "\n")  
    context.file.write("######" + "\n")
    
def get_order_string(context):
    all_orders = get_all_orders()
    numorders = len(all_orders)
    order_string = ""

    if(numorders > 0):
        for order_Id in all_orders:
            order = all_orders[order_Id]
            filled_time = order.filledTime
            avg_fill_price = order.avgFillPrice
            amount = order.amount
            order_string = order_string + str(all_orders[order_Id]) + "\n$$" + "Filled Time : " + str(filled_time) + ",Avg filled price:" + str(avg_fill_price) + ",Amount:" + str(amount) + "\n"
    return order_string        

def get_positions_string(context):
    positions = get_all_positions()
    positions_string = ""
    for security in positions:
        a = positions[security].str_security
        b = positions[security].amount
        c = positions[security].cost_basis
        positions_string = positions_string + str(a) + ' ' + str(b) + ' ' + str(c) + "\n"
    return positions_string
    
def handle_data(context, data):
    context.file.write("\n ######" + "\n")
    sTime = get_datetime('US/Eastern')
    print("stime is " + str(sTime))
    if sTime.hour == 15 and sTime.minute == 58:
        context.file.write("\n 2 minutes before market close, closing all positions")
        order_Id = order_target_percent(context.security, 0, style=MarketOrder())  
        order_status_monitor(order_Id, target_status = 'Filled')

    #fir testing making it 5 sec
    #display_all()
    data=request_historical_data(context.security, '1 min', '1 D')
    #data.index = data.index.map(lambda x: time.mktime(time.strptime(str(x), "%Y-%m-%d %H:%M:%S-04:00")))
    
    # data['ema8'] = ta.EMA(data.close, timeperiod=8)
    # data['ema21'] = ta.EMA(data.close, timeperiod=21)
    stock = stockstats.StockDataFrame.retype(data)
    #stockstats.ADXR_EMA
    data['posDI'] = stock['pdi']
    data['negDI'] = stock['mdi']
    data['ADX'] = stock['dx_14_ema']
    # data['negDI'] = ta.MINUS_DI(data.high, data.low, data.close, timeperiod=14)
    # data['posDI'] = ta.PLUS_DI(data.high, data.low, data.close, timeperiod=14)

    # data = EMA(data, 8)
    # data = EMA(data, 21)
    # ADXandDIData = ADX(data, 14, 14)
    # print(ADXandDIData)
    #data['posDI'] = ADXandDIData['posDI']
    #data['negDI'] = ADXandDIData['negDI']
    #data['ADX'] = ADXandDIData['ADX']
    
    print(data)

    #upperband_2, middleband_2, lowerband_2 = talib.BBANDS(close, timeperiod=timeperiod, nbdevup=2, nbdevdn=2, matype=0)

    current_positions = count_positions(context.security)
    context.file.write("\nTIME: " + str(data.index[-1]) + "\n")
    context.file.write("AAPL ask_price=" + str(show_real_time_price(context.security, 'ask_price')) + "\n")
    context.file.write("AAPL last close price=" + str(data['close'][-1])  + "\n")
    context.file.write("Current (posDI,negDI) = (%f, %f)"  %(data['posDI'][-1], data['negDI'][-1])  + "\n")
    context.file.write("ADX is %f" %(data['ADX'][-1])) 
    context.file.write("Current postions %f" %(current_positions))
    print("Current postions %f" %(current_positions))
    #print("Current (EMA8,EMA21) = (%f, %f)"  %(data['ema8'][-1], data['ema21'][-1])  + "\n")
    print("AAPL last close price=" + str(data['close'][-1])  + "\n")
    print("ADX is %f" %(data['ADX'][-1])) 
    print("Current (posDI,negDI) = (%f, %f)"  %(data['posDI'][-1], data['negDI'][-1])  + "\n")

    ###WE enter new positions on a strictly trending market. We can continue in existing positions on a loser trend def.
    if(current_positions == 0):
        if(isTrending(data, strict = True)):
            context.isStrictlyTrending = True
            context.file.write("\nCur pos 0. Market strictly trending, ADX is %f. Entering trade" %(data['ADX'][-1]))
            trade(context,data)
        else:
            context.file.write("Cur pos 0. Market strictly not trending, ADX is %f" %(data['ADX'][-1]))
            print("Cur pos 0. Market strictly not trending, ADX is %f" %(data['ADX'][-1]))     
    else:
        if(isTrending(data, strict = False)):
            context.file.write("\nCur pos non zero. Market trending, ADX is %f. Entering trade" %(data['ADX'][-1]))
            ##keeping track of isStrictly trending so that we don't enter anything new
            isStrictlyTrending = isTrending(data, strict = True)
            context.isStrictlyTrending = isStrictlyTrending
            context.ADXFallingAfter40 = isADXFallingAfter40(data)
            trade(context,data)
        else:
            context.file.write("Market non trending, wil try closing all positions\n")
            print("Market non trending, will try closing all positions\n")
            closePositions(context,data)    

def isADXFallingAfter40(data):
    if(data['ADX'][-2] >= 40 and data['ADX'][-1] < data['ADX'][-2]):
        return True
    else:
        return False    
def isTrending(data, strict):
    #If previous value is greater, it means downslope and hence non trend.
    if(data['ADX'][-1] > 20 and data['ADX'][-2] <= data['ADX'][-1]):
        return True
    else:
        return False



# def switchToOscillating(data):
#     if(data['ADX'][-1] <25 and data['ADX'][-2] >=25):
#         return True
#     else:
#         return False   

      
def printToFile(context):
    context.file.write("\nINSIDE TRADE/CLOSEALL POSITIONS" + "\n")
    context.file.write ("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
    context.file.write ("Positions Value: " + str(context.portfolio.positions_value) + "\n")
    context.file.write ("Portfolio Cash:" + str(context.portfolio.cash) + "\n")  
    #context.file.write ("Unrealised PNL:" + str(context.portfolio.pnl) + "\n")  
    #order_string = get_order_string(context)  
    #context.file.write("ORDERS\n" + order_string + "\n")
    positions_string = get_positions_string(context)  
    context.file.write("POSITIONS\n" + positions_string + "\n")

def closePositions(context, data):
    print("Closing all positions")
    context.file.write("\nClosing all positions \n")
    order_Id = order_target_percent(context.security, 0, style=MarketOrder())
    order_status_monitor(order_Id, target_status = 'Filled')
# def closePositions(context, data):
#     current_positions = count_positions(context.security)
    
#     printToFile(context)
#     if(current_positions > 0):
#         lastLongedPrice = context.last_longed_price
#         current_ask_price = show_real_time_price(context.security, 'ask_price')

#         if(current_ask_price > lastLongedPrice):
#             context.file.write("Market has turned oscillating. Since current price is >lastLongedPrice, closing longs")
#             print("Market has turned oscillating. Since current price is >lastLongedPrice, closing longs")
#             order_Id = order_target_percent(context.security, 0, style=MarketOrder())
#             order_status_monitor(order_Id, target_status = 'Filled')
            
#     elif(current_positions < 0):
#         lastShortedPrice = context.last_shorted_price
#         current_ask_price = show_real_time_price(context.security, 'ask_price')

#         if(current_ask_price < lastShortedPrice):
#             context.file.write("Market has turned oscillating. Since current price is <last_shorted_price, closing shorts")
#             print("Market has turned oscillating. Since current price is <last_shorted_price, closing shorts")
#             order_Id = order_target_percent(context.security, 0, style=MarketOrder())  
#             order_status_monitor(order_Id, target_status = 'Filled')
#     else:
#         context.file.write("Shouldn't be here. Cur pos 0 and closePositions is called")      

def trade(context,data):
    printToFile(context)
    current_positions = count_positions(context.security)
    # Close any currently held position be it positive or negative if ADX is falling after crossing 40
    # if(current_positions != 0 and context.ADXFallingAfter40 is True):
    #     context.file.write("ADX falling after crossed 40. Closing all positions")
    #     print("ADX falling after crossed 40. Closing all positions")
    #     order_Id = order_target_percent(context.security, 0, style=MarketOrder())
    #     order_status_monitor(order_Id, target_status = 'Filled')
    #     return

    if(data['posDI'][-1] > data['negDI'][-1] or (data['posDI'][-1] < data['negDI'][-1] and data['posDI'][-1] == data['negDI'][-1])):
        #low crossover.
        current_positions = count_positions(context.security)

        print("posDI above negDI. Buy stocks for full portfolio")
   
        percentCurrent = calculateCurrentPercent(context)
        print("Current position percent %f" %(percentCurrent))
        context.file.write("Current position %f" %(percentCurrent))
        if(current_positions >= 0 and current_positions < ACCEPTABLE_POSITIVE_POSITIONS):
            newPositionPercent = 1
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                context.file.write("posDI above negDI, current positions: %f. Making them 1\n" %(current_positions))
                #printToFile(context)
                context.last_longed_price = show_real_time_price(context.security, 'ask_price')
                order_Id = order_target_percent(context.security, 1, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
        elif(current_positions < 0):
            newPositionPercent = 0
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                #CHANGED due to closing order quantity is greater than your current position. 
                context.file.write("posDI above negDI, current positions: %f. Making them 0\n" %(current_positions))
                #printToFile(context)
                order_Id = order_target_percent(context.security, 0, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
                if(context.isStrictlyTrending is True):
                    context.file.write("posDI above negDI(strictly trending), current positions: %f. Making them 1\n" %(current_positions))
                    context.last_longed_price = show_real_time_price(context.security, 'ask_price')
                    order_Id2 = order_target_percent(context.security, 1, style=MarketOrder())
                    order_status_monitor(order_Id2, target_status = 'Filled')
    elif( data['posDI'][-1] < data['negDI'][-1]or (data['posDI'][-1] > data['negDI'][-1] and data['posDI'][-1] == data['negDI'][-1]) ):
        print("posDI below negDI. Sell everything. short completely")
        current_positions = count_positions(context.security)
        percentCurrent = calculateCurrentPercent(context)
        print("Current position percent %f" %(percentCurrent))
        context.file.write("Current position %f" %(percentCurrent))
        if(current_positions <= 0 and current_positions > ACCEPTABLE_NEGATIVE_POSITIONS):
            newPositionPercent = -1
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                context.file.write("posDI below negDI. Negative current positions. Making them -1\n")
                #printToFile(context)
                context.last_shorted_price = show_real_time_price(context.security, 'ask_price')
                order_Id = order_target_percent(context.security, newPositionPercent, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
        elif(current_positions >0):
            newPositionPercent = 0
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
            ## CHANGE due to closing order quantity is greater than your current position. 
                context.file.write("posDI below negDI. Positive current positions. Making them 0\n")
                #printToFile(context)
                order_Id = order_target_percent(context.security, newPositionPercent, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
                if(context.isStrictlyTrending is True):
                    context.file.write("posDI below negDI (strictly trending), making them -1\n")
                    context.last_shorted_price = show_real_time_price(context.security, 'ask_price')
                    order_Id2 = order_target_percent(context.security, -1, style=MarketOrder())
                    order_status_monitor(order_Id2, target_status = 'Filled')
    

def calculateCurrentPercent(context):
    cost_basis = context.portfolio.positions[context.security].cost_basis
    num_shares =  context.portfolio.positions[context.security].amount
    net_liquidation = context.portfolio.cash + context.portfolio.positions_value
    percentCurrentlyLonged = (num_shares * cost_basis)/net_liquidation
    return percentCurrentlyLonged

def displayPortfolio(context):
    print (context.portfolio.portfolio_value)
    print (context.portfolio.positions_value)
    print (context.portfolio.cash)    

    
