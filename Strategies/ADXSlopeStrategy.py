import pandas as pd
import time
import sys
import os
import stockstats

ACCEPTABLE_POSITIVE_POSITIONS = 3000
ACCEPTABLE_NEGATIVE_POSITIONS = -3000

def initialize(context):
    context.run_once=False

    #context.security=symbol('CASH, EUR, USD')
    context.security=symbol('AAPL')
    sample = open('AAPLBackTestStarting10Sept5mins.txt', 'w')
    context.file = sample
    printToFile(context, "#######\nAT BEGINNING\n", printToScreen = True)
    context.file.write("######" + "\n")
    print("######" + "\n")
    
def handle_data(context, data):
    sTime = get_datetime('US/Eastern')
    print("stime is " + str(sTime))
    if sTime.hour == 15 and sTime.minute == 58:
        context.file.write("\n 2 minutes before market close, closing all positions\n")
        print("\n 2 minutes before market close, closing all positions\n")
        closePositions(contract,data)


    data=request_historical_data(context.security, '5 mins', '1 D')
    data5min=request_historical_data(context.security, '10 mins', '1 D')

    stock = stockstats.StockDataFrame.retype(data)
    data['posDI'] = stock['pdi']
    data['negDI'] = stock['mdi']
    data['ADX'] = stock['dx_14_ema']

    stock5min = stockstats.StockDataFrame.retype(data5min)
    data5min['posDI'] = stock5min['pdi']
    data5min['negDI'] = stock5min['mdi']
    
    #print(data)
    printDataToFile(context, data, data5min, "\n #### Inside Handle data\n", printToScreen = True)
    current_positions = count_positions(context.security)

    if(isADXOnUpTrend(data)):
        context.file.write("\n ADX is flat/upslope. Entering trade function\n")
        print("\n ADX is flat/upslope. Entering trade function\n")
        trade(context, data, data5min)
    elif(isADXOnDownTrend(data)):
        context.file.write("\n ADX is downTrend/<20. Exiting all positions\n")
        print("\n ADX is downTrend/<20. Exiting all positions\n")
        closePositions(context, data)  
    else:
        context.file.write("\n ADX is flat. Not doing anything\n")
        print("ADX is flat. Not doing anything\n")
        
    context.file.write("######" + "\n")
    print("######" + "\n")
    
       
def isADXOnUpTrend(data):
    delta = abs(data['ADX'][-2] - data['ADX'][-1])
    delta2 = abs(data['ADX'][-3] - data['ADX'][-2])

    if(data['ADX'][-1] > 20 and data['ADX'][-2] < data['ADX'][-1] and delta >= 2):
        return True

    if(data['ADX'][-1] > 20 and data['ADX'][-2] < data['ADX'][-1] and delta >= 0.5 and data['ADX'][-3] < data['ADX'][-2] and delta2 >= 0.5 ):
        return True
    else:
        return False

def isADXOnDownTrend(data):
    delta = abs(data['ADX'][-2] - data['ADX'][-1])
    delta2 = abs(data['ADX'][-3] - data['ADX'][-2])

    if(data['ADX'][-1] <= 20):
        return True
    if(data['ADX'][-2] > data['ADX'][-1] and delta >= 1):
        return True
    if(data['ADX'][-2] > data['ADX'][-1] and delta >= 0.5 and data['ADX'][-3] > data['ADX'][-2] and delta2 >= 0.5 ):
        return True
    
    return False

# def isADXFlat(data):
#     delta = data['ADX'][-2] - data['ADX'][-1]
#     delta2 = data['ADX'][-3] - data['ADX'][-2]

#     absDelta = abs(delta)
#     oppSlopes = False
#     if((delta >= 0 and delta2 <= 0) or (delta2 >= 0 and delta <= 0)):
#         oppSlopes = True

#     # The delta is >1 so ADX cannot be flat    
#     if(data['ADX'][-1] > 20 and absDelta > 0.8):
#         return False
#     if(data['ADX'][-1] > 20 and (absDelta < 0.5 or oppSlopes is True)):
#         return True
#     return False    

def closePositions(context, data):
    
    current_positions = count_positions(context.security)
    if(current_positions != 0):
        context.file.write("\nCurrent positions :%f. Closing them \n" %(current_positions))
        print("\nCurrent positions :%f. Closing them \n" %(current_positions))
        order_Id = order_target_percent(context.security, 0, style=MarketOrder())
        order_status_monitor(order_Id, target_status = 'Filled')
    else:
        context.file.write("\nPositions already 0. No need to close\n")
        print("\nPositions already 0. No need to close\n")       

def trade(context,data, data5min):
    current_positions = count_positions(context.security)

    #Pos above negative OR just crossing over. Go long.
    if(data['posDI'][-1] > data['negDI'][-1] or (data['posDI'][-2] < data['negDI'][-2] and data['posDI'][-1] == data['negDI'][-1])):

        context.file.write("\nPositive over negative or jut crossing over. Go long\n")
        print("\nPositive over negative or jut crossing over. Go long\n")

        if(data5min['posDI'][-1] < data5min['negDI'][-1]):
            context.file.write("\n5 min data contradicts. Pos is below neg. Not doing anything\n")
            print("\n5 min data contradicts. Pos is below neg. Not doing anything\n")
            return
   
        percentCurrent = calculateCurrentPercent(context)
        context.file.write("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_POSITIVE_POSITIONS))
        print("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_POSITIVE_POSITIONS))

        if(current_positions >= 0 and current_positions < ACCEPTABLE_POSITIVE_POSITIONS):
            newPositionPercent = 1
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                context.file.write("Placing long order to make it 1. Current percent is: %f" %(percentCurrent))
                print("Placing long order to make it 1. Current percent is: %f" %(percentCurrent))
                order_Id = order_target_percent(context.security, 1, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled') 
        elif(current_positions < 0):
            newPositionPercent = 0
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                context.file.write("\nPlacing order to make the negative pos 0\n")
                print("\nPlacing order to make the negative pos 0\n")
                order_Id = order_target_percent(context.security, 0, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')

                context.file.write("\nPlacing order to make the  pos 1\n")
                print("\nPlacing order to make the pos 1\n")
                order_Id2 = order_target_percent(context.security, 1, style=MarketOrder())
                order_status_monitor(order_Id2, target_status = 'Filled')

    elif( data['posDI'][-1] < data['negDI'][-1]or (data['posDI'][-2] > data['negDI'][-2] and data['posDI'][-1] == data['negDI'][-1]) ):
        context.file.write("\Negative over positive or jut crossing over. Go short\n")
        print("\Negative over positive or jut crossing over. Go short\n")

        if(data5min['posDI'][-1] > data5min['negDI'][-1]):
            context.file.write("\n5 min data contradicts. Pos is above neg. Not doing anything\n")
            print("\n5 min data contradicts. Pos is above neg. Not doing anything\n")
            return

        percentCurrent = calculateCurrentPercent(context)

        context.file.write("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_NEGATIVE_POSITIONS))
        print("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_NEGATIVE_POSITIONS))

        if(current_positions <= 0 and current_positions > ACCEPTABLE_NEGATIVE_POSITIONS):
            newPositionPercent = -1
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
                context.file.write("Placing short order to make it -1. Current percent is: %f" %(percentCurrent))
                print("Placing short order to make it -1. Current percent is: %f" %(percentCurrent))
                order_Id = order_target_percent(context.security, -1, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
        elif(current_positions >0):
            newPositionPercent = 0
            delta = abs(newPositionPercent - percentCurrent)
            if(delta >= 0.1):
            
                context.file.write("\nPlacing order to make the positive pos 0\n")
                print("\nPlacing order to make the positive pos 0\n")
                order_Id = order_target_percent(context.security, 0, style=MarketOrder())
                order_status_monitor(order_Id, target_status = 'Filled')
                
                context.file.write("\nPlacing order to make the  pos -1\n")
                print("\nPlacing order to make the  pos -1\n")
                order_Id2 = order_target_percent(context.security, -1, style=MarketOrder())
                order_status_monitor(order_Id2, target_status = 'Filled')
    

def calculateCurrentPercent(context):
    cost_basis = context.portfolio.positions[context.security].cost_basis
    num_shares =  context.portfolio.positions[context.security].amount
    net_liquidation = context.portfolio.cash + context.portfolio.positions_value
    currentPercent = (num_shares * cost_basis)/net_liquidation
    return currentPercent 
def printDataToFile(context, data, data5min, startString, printToScreen):
    current_positions = count_positions(context.security)
    context.file.write(startString)
    context.file.write("\nTIME: " + str(data.index[-1]) + "\n")
    context.file.write ("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
    context.file.write ("Positions Value: " + str(context.portfolio.positions_value) + "\n")
    context.file.write ("Portfolio Cash:" + str(context.portfolio.cash) + "\n") 
    order_string = get_order_string(context)  
    #context.file.write("ORDERS\n" + order_string + "\n")
    positions_string = get_positions_string(context)  
    context.file.write("POSITIONS\n" + positions_string + "\n")
    context.file.write("#############DATA##########################")
    context.file.write("Stock last close price=" + str(data['close'][-1])  + "\n")
    context.file.write("Current (posDI,negDI) = (%f, %f)"  %(data['posDI'][-1], data['negDI'][-1])  + "\n")
    context.file.write("Current ADX %f \n" %(data['ADX'][-1])) 
    context.file.write("ADX[-2]: %f , ADX[-3] : %f\n" %(data['ADX'][-2],data['ADX'][-3])) 
    context.file.write("Current postions: %f \n" %(current_positions))
    context.file.write("5minPdi : %f, 5minNDi :  %f \n" %(data5min['posDI'][-1], data5min['negDI'][-1]))

    if(printToScreen is True):
        print(startString)
        print("\nTIME: " + str(data.index[-1]) + "\n")
        print("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
        print("Positions Value: " + str(context.portfolio.positions_value) + "\n")
        print("Portfolio Cash:" + str(context.portfolio.cash) + "\n")
        print("ORDERS\n" + order_string + "\n")
        print("POSITIONS\n" + positions_string + "\n")
        context.file.write("#############DATA##########################")
        print("Stock last close price=" + str(data['close'][-1])  + "\n")
        print("Current (posDI,negDI) = (%f, %f)"  %(data['posDI'][-1], data['negDI'][-1])  + "\n")
        print("Current ADX %f \n" %(data['ADX'][-1])) 
        print("ADX[-2]: %f , ADX[-3] : %f\n" %(data['ADX'][-2], data['ADX'][-3])) 
        print("Current postions: %f \n" %(current_positions))
        print("5minPdi : %f, 5minNDi :  %f \n" %(data5min['posDI'][-1], data5min['negDI'][-1]))


def printToFile(context, startString, printToScreen):
    context.file.write(startString)
    context.file.write ("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
    context.file.write ("Positions Value: " + str(context.portfolio.positions_value) + "\n")
    context.file.write ("Portfolio Cash:" + str(context.portfolio.cash) + "\n") 
    order_string = get_order_string(context)  
    context.file.write("ORDERS\n" + order_string + "\n")
    positions_string = get_positions_string(context)  
    context.file.write("POSITIONS\n" + positions_string + "\n")

    if(printToScreen is True):
        print(startString)
        print("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
        print("Positions Value: " + str(context.portfolio.positions_value) + "\n")
        print("Portfolio Cash:" + str(context.portfolio.cash) + "\n")
        print("ORDERS\n" + order_string + "\n")
        print("POSITIONS\n" + positions_string + "\n")

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
    
