import pandas as pd
import talib as ta

def initialize(context):
    context.run_once=False

    context.security=symbol('CASH, EUR, USD')
    #context.security=symbol('AAPL')

    sample = open('samplefile.txt', 'w')
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
    #fir testing making it 5 sec
    #display_all()
    data=request_historical_data(context.security, '1 min', goBack = '1 D')
    
    data['ema8'] = ta.EMA(data.close, timeperiod=8)
    data['ema21'] = ta.EMA(data.close, timeperiod=21)
    data['ADX'] = ta.ADX(data.high, data.low, data.close, timeperiod=14)
    data['negDI'] = ta.MINUS_DI(data.high, data.low, data.close, timeperiod=14)
    data['posDI'] = ta.PLUS_DI(data.high, data.low, data.close, timeperiod=14)
    #print(data)
    #upperband_2, middleband_2, lowerband_2 = talib.BBANDS(close, timeperiod=timeperiod, nbdevup=2, nbdevdn=2, matype=0)
    #close, high,low,open, volume, ema8, ema21
    #print(data)
    #return
    current_positions = count_positions(context.security)
    context.file.write("\nTIME: " + str(data.index[-1]) + "\n")
    context.file.write("AAPL ask_price=" + str(show_real_time_price(context.security, 'ask_price')) + "\n")
    context.file.write("AAPL last close price=" + str(data['close'][-1])  + "\n")
    context.file.write("Last (EMA8,EMA21) = (%f, %f)"  %(data['ema8'][-2], data['ema21'][-2])  + "\n")
    context.file.write("Current (EMA8,EMA21) = (%f, %f)"  %(data['ema8'][-1], data['ema21'][-1])  + "\n")
    print("Current (EMA8,EMA21) = (%f, %f)"  %(data['ema8'][-1], data['ema21'][-1])  + "\n")
    print("AAPL last close price=" + str(data['close'][-1])  + "\n")


    if(isTrending(data)):
        trade(context,data)
    # If market is oscillating and current positions > 0    
    elif(current_positions > 0):
        printToFile(context)
        context.file.write("Market going from trending to oscillating, closing all positions\n")
        closePositions(context,data)
    else:
        #TODO : if we currently hold non zero positions, what should we do
        context.file.write("Market not trending, ADX is %f" %(data['ADX'][-1]))
        print("Market not trending, ADX is %f" %(data['ADX'][-1])) 

def isTrending(data):
    if(data['ADX'][-1] >=25 and data['ADX'][-2] >=25):
        return True
    else:
        return False
def switchToOscillating(data):
    if(data['ADX'][-1] <25 and data['ADX'][-2] >=25 and data['ADX'][-2] >=25):
        return True
    else:
        return False   

      
def printToFile(context):
    context.file.write("INSIDE TRADE" + "\n")
    context.file.write ("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
    context.file.write ("Positions Value: " + str(context.portfolio.positions_value) + "\n")
    context.file.write ("Portfolio Cash:" + str(context.portfolio.cash) + "\n")  
    #context.file.write ("Unrealised PNL:" + str(context.portfolio.pnl) + "\n")  
    order_string = get_order_string(context)  
    context.file.write("ORDERS\n" + order_string + "\n")
    positions_string = get_positions_string(context)  
    context.file.write("POSITIONS\n" + positions_string + "\n")

def closePositions(context, data):
    current_positions = count_positions(context.security)

    if(current_positions > 0):
        lastLongedPrice = context.last_longed_price
        current_ask_price = show_real_time_price(context.security, 'ask_price')

        if(current_ask_price > lastLongedPrice):
            context.file.write("Market has turned oscillating. Since current price is >lastLongedPrice, closing longs")
            print("Market has turned oscillating. Since current price is >lastLongedPrice, closing longs")
            order_Id = order_target_percent(context.security, 0, style=MarketOrder())
            
    elif(current_positions < 0):
        lastLongedPrice = context.last_shorted_price
        current_ask_price = show_real_time_price(context.security, 'ask_price')

        if(current_ask_price < last_shorted_price):
            context.file.write("Market has turned oscillating. Since current price is <last_shorted_price, closing shorts")
            print("Market has turned oscillating. Since current price is <last_shorted_price, closing shorts")
            order_Id = order_target_percent(context.security, 0, style=MarketOrder())  

def trade(context,data):
    printToFile(context)
    if(data['ema8'][-2] < data['ema21'][-2] and data['ema8'][-1] > data['ema21'][-1]):
        #low crossover.
        current_positions = count_positions(context.security)
        print("8 crossed over 21. Buy stocks for full portfolio")
        print("Current position %f" %(current_positions))
        percentCurrent = calculateCurrentPercent(context)
        if(current_positions >= 0):
            newPositionPercent = 1
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                context.file.write("8 crossed over 21, current positions: %f. Making them 1\n" %(current_positions))
                #printToFile(context)
                context.last_longed_price = show_real_time_price(context.security, 'ask_price')
                order_Id = order_target_percent(context.security, 1, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
        elif(current_positions < 0):
            newPositionPercent = 0
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                #CHANGED due to closing order quantity is greater than your current position. 
                context.file.write("8 crossed over 21, current positions: %f. Making them 0\n" %(current_positions))
                #printToFile(context)
                order_Id = order_target_percent(context.security, 0, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
    elif(data['ema8'][-2] > data['ema21'][-2] and data['ema8'][-1] < data['ema21'][-1]):
        print("8 crossed to below 21. Sell everything. short completely")
        current_positions = count_positions(context.security)
        percentCurrent = calculateCurrentPercent(context)
        if(current_positions <= 0):
            newPositionPercent = -1
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                context.file.write("8 crossed below 21. Negative current positions. Making them -1\n")
                #printToFile(context)
                context.last_shorted_price = show_real_time_price(context.security, 'ask_price')
                order_Id = order_target_percent(context.security, newPositionPercent, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
        elif(current_positions >0):
            newPositionPercent = 0
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
            ## CHANGE due to closing order quantity is greater than your current position. 
                context.file.write("8 crossed below 21. Positive current positions. Making them 0\n")
                #printToFile(context)
                order_Id = order_target_percent(context.security, newPositionPercent, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
    

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

    
    # if stime.weekday()<=4:
    #     #current time is 2 minutes before market closing time
    #     if stime.hour==15 and stime.minute==28 and context.run_once is True:
    #         context.run_once=False
    #     #is it one minute befor market closing time
    #     if stime.hour==15 and stime.minute==29 and context.run_once is False:
    #         #Requesting 5min candles, going back 2 days
    #         data=request_historical_data(context.security, '5 mins', '2D')
    #         data['ema8'] = ema8=ta.EMA(data.close, timeperiod=8)
    #         data['ema21'] = ema21=ta.EMA(data.close, timeperiod=21)
    #         print(data)

