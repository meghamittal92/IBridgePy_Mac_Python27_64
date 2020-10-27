import pandas as pd
import time
import sys
import os
import stockstats
import talib as ta
import numpy as np
from technicalIndicators import ADXIndicator
import tulipy
import pytz
import datetime as dt
from BackTestVars import baseTimeFrame
from BackTestVars import securities
from BackTestVars import ADX_ENTRY_THRESHHOLD
from BackTestVars import IS_ADX_FALLING_EARLY_EXIT_USED
from BackTestVars import DI_TIME_PERIOD

ACCEPTABLE_POSITIVE_POSITIONS = 3000
ACCEPTABLE_NEGATIVE_POSITIONS = -3000
ADX_EXIT_THRESHHOLD = 20
ADX_HIGH_THRESHHOLD = 50
##############################

originalCandleTimeFrame = str(baseTimeFrame) + ' mins'
extendedCandleTimeFrame = str(baseTimeFrame + 5) + ' mins' if baseTimeFrame < 20 else  str(baseTimeFrame + 10) + ' mins'

PORTFOLIO_PERCENT_PER_SECURITY = 1.0/len(securities)

DATAS = []
EXTENDED_TIME_FRAME_DATAS = []

IS_MULTITHRESHHOLD = False if ADX_ENTRY_THRESHHOLD == ADX_EXIT_THRESHHOLD else True


fileToStoreResults = "BackTestOutputs/" + '_'.join(['_'.join(securities), 'BackTestV2', originalCandleTimeFrame.replace(" ", ""),str(ADX_EXIT_THRESHHOLD), str(ADX_ENTRY_THRESHHOLD) + '.txt'])


def initialize(context):
    context.run_once=False
    sample = open(fileToStoreResults, 'w', buffering=1)
    context.file = sample
    printToFile(context, "#######\nAT BEGINNING\n", printToScreen = True)
    context.file.write("######" + "\n")
    print("######" + "\n")
    
def handle_data(context, data):
    sTime = get_datetime('US/Eastern')
    print("stime is " + str(sTime))
    context.file.write("\nstime is " + str(sTime))
    minuteNum = sTime.minute%baseTimeFrame
    if(minuteNum == 0):
       getDatasAndAppend(context, data)
    elif(DATAS and minuteNum > 0 and minuteNum <= len(securities)):
        # if(not DATAS):
        #     getDatasAndAppend(context, data)
        
        context.file.write("\n In minuteNum: %d. Trading security: %s " %(minuteNum, str(securities[minuteNum-1])))
        print("\n In minuteNum: %d. Trading security: %s " %(minuteNum, str(securities[minuteNum-1])))
        context.security = symbol(securities[minuteNum -1])
        tradePerSecurity(context, data, minuteNum)
    else:
        context.file.write("\nNo security to trade")
        print("\nNo security to trade")

def getDatasAndAppend(context, data):
    del DATAS[:]
    del EXTENDED_TIME_FRAME_DATAS[:]
    
    for secSymbol in securities:
        security = symbol(secSymbol)
        data=request_historical_data(security, originalCandleTimeFrame, '2 D', useRTH = 0)
        dataExtendedTimeFrame=request_historical_data(security, extendedCandleTimeFrame, '2 D', useRTH = 0)
        DATAS.append(data)
        EXTENDED_TIME_FRAME_DATAS.append(dataExtendedTimeFrame)
    #print(DATAS)    

def tradePerSecurity(context, data, securityNum):
    current_positions = count_positions(context.security)
    sTime = get_datetime('US/Eastern')

    data=DATAS[securityNum -1]
    dataExtendedTimeFrame=EXTENDED_TIME_FRAME_DATAS[securityNum -1]
    #print(dataExtendedTimeFrame)
    stockstats.StockDataFrame.PDI_SMMA = DI_TIME_PERIOD
    stockstats.StockDataFrame.MDI_SMMA = DI_TIME_PERIOD
    stockstats.StockDataFrame.DX_SMMA = DI_TIME_PERIOD
    

    stock = stockstats.StockDataFrame.retype(data)
    data['posDI'] = stock['pdi']
    data['negDI'] = stock['mdi']

    # data['negDI'] = ta.MINUS_DI(data.high, data.low, data.close, timeperiod=DI_TIME_PERIOD)
    # data['posDI'] = ta.PLUS_DI(data.high, data.low, data.close, timeperiod=DI_TIME_PERIOD)
    #data['ADX'] = ta.ADX(data.high, data.low, data.close, timeperiod=DI_TIME_PERIOD)

    #posDI, negDI = tulipy.di( high=data.high.values, low=data.low.values, close=data.close.values, period=DI_TIME_PERIOD)
    #print(posDI)
    #print(negDI)
    #data['posDI'] = np.NAN
    #data['posDI'][DI_TIME_PERIOD - 1:] = posDI
    #data['negDI'] = np.NAN
    #data['negDI'][DI_TIME_PERIOD - 1:] = negDI
    #data['ADX'] = np.NAN
    #data['ADX'][DI_TIME_PERIOD - 1:] = tulipy.adx(data.high.values, data.low.values, data.close.values, period=DI_TIME_PERIOD)
    
    # adxI = ADXIndicator(data.high,data.low,data.close,DI_TIME_PERIOD,True)
    # data['posDI'] = adxI.adx_pos()
    # data['negDI'] = adxI.adx_neg()
    #aapl['adx'] = adxI.adx()
    
    data['ADX'] = stock['dx_' + str(DI_TIME_PERIOD) + '_ema']
    data.drop(columns=['pdm_' + str(DI_TIME_PERIOD) ,'close_-1_s','tr','tr_' + str(DI_TIME_PERIOD) + '_smma','low_delta','dm','pdm','pdm_'+ str(DI_TIME_PERIOD) + '_ema','atr_' + str(DI_TIME_PERIOD)], inplace=True, axis=1)
    #data['posDI'] = stock['pdi']
    #data['negDI'] = stock['mdi']
    

    # stockstats.StockDataFrame.PDI_SMMA = DI_TIME_PERIOD
    # stockstats.StockDataFrame.MDI_SMMA = DI_TIME_PERIOD
    # stockstats.StockDataFrame.DX_SMMA = DI_TIME_PERIOD
    # stockExtendedTimeFrame = stockstats.StockDataFrame.retype(dataExtendedTimeFrame)
    # dataExtendedTimeFrame['posDI'] = stockExtendedTimeFrame['pdi']
    # dataExtendedTimeFrame['negDI'] = stockExtendedTimeFrame['mdi']

    #dataExtendedTimeFrame['negDI'] = np.NAN
    #dataExtendedTimeFrame['posDI'] = np.NAN
    #dataExtendedTimeFrame['posDI'][DI_TIME_PERIOD -1:], dataExtendedTimeFrame['negDI'][DI_TIME_PERIOD -1:] = tulipy.di( high=dataExtendedTimeFrame.high.values, low=dataExtendedTimeFrame.low.values, close=dataExtendedTimeFrame.close.values, period=DI_TIME_PERIOD)

    #dataExtendedTimeFrame['negDI'] = ta.MINUS_DI(dataExtendedTimeFrame.high, dataExtendedTimeFrame.low, dataExtendedTimeFrame.close, timeperiod=DI_TIME_PERIOD)
    #dataExtendedTimeFrame['posDI'] = ta.PLUS_DI(dataExtendedTimeFrame.high, dataExtendedTimeFrame.low, dataExtendedTimeFrame.close, timeperiod=DI_TIME_PERIOD)
    

    stockExtendedTimeFrame = stockstats.StockDataFrame.retype(dataExtendedTimeFrame)
    dataExtendedTimeFrame['posDI'] = stockExtendedTimeFrame['pdi']
    dataExtendedTimeFrame['negDI'] = stockExtendedTimeFrame['mdi']

    # extendedadxI = ADXIndicator(dataExtendedTimeFrame.high,dataExtendedTimeFrame.low,dataExtendedTimeFrame.close,DI_TIME_PERIOD,True)
    # dataExtendedTimeFrame['posDI'] = extendedadxI.adx_pos()
    # dataExtendedTimeFrame['negDI'] = extendedadxI.adx_neg()

    print(data)
    context.file.write("DATA:\n" + str(data) + "\n")
    print(dataExtendedTimeFrame)
    #context.file.write("\n" + str(data) + "\n")
    printDataToFile(context, data, "\n #### Inside Handle data\n", printToScreen = True, securityName = securities[securityNum -1])
    
    context.didPlaceTrade = False
    if(isADXBelowExitThreshhold(data)):
        context.file.write("\n ADX below exit threshhold. Closing all positionsn\n")
        print("\n ADX below exit threshhold. Closing all positions\n")
        closePositions(context, data)
    elif(isPositiveCrossover(data) or isNegativeCrossover(data) ):
        context.file.write("\n Crossover happened. Entering trade function\n")
        print("\n Crossover happened. Entering trade function\n")  
        trade(context, data, dataExtendedTimeFrame)  
    elif( IS_ADX_FALLING_EARLY_EXIT_USED is True and isADXFallingAfterHighThreshhold(data)):
        context.file.write("\n ADX falling after %s. Closing all positionsn\n" %(ADX_HIGH_THRESHHOLD))
        print("\n ADX falling after %s. Closing all positionsn\n" %(ADX_HIGH_THRESHHOLD))
        closePositions(context, data)    
    elif(inWrongPosition(context,data)):
        context.file.write("\n In wrong position acc to DIs. Closing all positions\n")
        print("\n In wrong position acc to DIs. Closing all positions\n")
        closePositions(context, data)    
    else:
        context.file.write("\n Nothing to do.\n")
        print("\n  Nothing to do.\n")

    # if (context.didPlaceTrade):
    #     printDataToFile(context, data, "\n #### Inside Handle data\n", printToScreen = True, securityName = securities[securityNum -1])    
    context.file.write("######" + "\n")
    print("######" + "\n")

def isADXFallingAfterHighThreshhold(data):
    delta = abs(data['ADX'][-2] - data['ADX'][-1])
    if(data['ADX'][-2] >= ADX_HIGH_THRESHHOLD and data['ADX'][-1] < data['ADX'][-2] and delta >= 1):
        return True
    else:
        return False 

def isADXAboveEntryThreshhold(data):
    
    if(data['ADX'][-1] > ADX_ENTRY_THRESHHOLD):
        return True
    else:
        return False        

def isADXBelowExitThreshhold(data):
    
    if(data['ADX'][-1] <= ADX_EXIT_THRESHHOLD):
        return True
    else:
        return False

def isPositiveCrossover(data):
    if((data['posDI'][-2] < data['negDI'][-2] and data['posDI'][-1] >= data['negDI'][-1]) or (data['posDI'][-2] <= data['negDI'][-2] and data['posDI'][-1] > data['negDI'][-1])):
        return True
    else:
        return False
def isNegativeCrossover(data):
    if((data['negDI'][-2] < data['posDI'][-2] and data['negDI'][-1] >= data['posDI'][-1]) or (data['negDI'][-2] <= data['posDI'][-2] and data['negDI'][-1] > data['posDI'][-1])):
        return True
    else:
        return False        

def inWrongPosition(context, data):
    current_positions = count_positions(context.security)

    if(data['posDI'][-1] > data['negDI'][-1] and current_positions <0):
        return True
    elif(data['posDI'][-1] < data['negDI'][-1] and current_positions >0):
      return True

    return False  

def closePositions(context, data):
    
    current_positions = count_positions(context.security)
    if(current_positions != 0):
        context.file.write("\nCurrent positions :%f. Closing them \n" %(current_positions))
        print("\nCurrent positions :%f. Closing them \n" %(current_positions))
        context.didPlaceTrade = True
        order_Id = order_target_percent(context.security, 0, style=MarketOrder())
        order_status_monitor(order_Id, target_status = 'Filled')
    else:
        context.file.write("\nPositions already 0. No need to close\n")
        print("\nPositions already 0. No need to close\n")       



def goLong(context, data, takeNewPos):
    current_positions = count_positions(context.security)
    percentCurrent = calculateCurrentPercent(context)
    context.file.write("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_POSITIVE_POSITIONS))
    print("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_POSITIVE_POSITIONS))

        
    if(current_positions >= 0 and current_positions < ACCEPTABLE_POSITIVE_POSITIONS):
        if(not takeNewPos):
            context.file.write("Extended data contradicts/ADX below entry. Not taking new positions\n")
            print("Extended data contradicts/ADX below entry. Not taking new positions\n")
            return
        newPositionPercent = PORTFOLIO_PERCENT_PER_SECURITY
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            context.file.write("Placing long order to make it %f. Current percent is: %f" %(PORTFOLIO_PERCENT_PER_SECURITY, percentCurrent))
            print("Placing long order to make it %f. Current percent is: %f" %(PORTFOLIO_PERCENT_PER_SECURITY, percentCurrent))
            context.didPlaceTrade = True
            order_Id = order_target_percent(context.security, PORTFOLIO_PERCENT_PER_SECURITY, style=MarketOrder())
            order_status_monitor(order_Id, target_status = 'Filled') 
    elif(current_positions < 0):
        newPositionPercent = 0
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            context.file.write("\nPlacing order to make the negative pos 0\n")
            print("\nPlacing order to make the negative pos 0\n")
            context.didPlaceTrade = True
            order_Id = order_target_percent(context.security, 0, style=MarketOrder())
            order_status_monitor(order_Id, target_status = 'Filled')
            printToFile(context, "##After closing pos##\n", True)

            if(takeNewPos):
                context.file.write("\nPlacing order to make the  pos %f\n" %(PORTFOLIO_PERCENT_PER_SECURITY))
                print("\nPlacing order to make the pos %f\n" %(PORTFOLIO_PERCENT_PER_SECURITY))
                order_Id2 = order_target_percent(context.security, PORTFOLIO_PERCENT_PER_SECURITY, style=MarketOrder())
                order_status_monitor(order_Id2, target_status = 'Filled')
            else:
                context.file.write("\nExtended data contradicts/ADX below entry. Not taking new positions\n")
                print("\nExtended data contradicts/ADX below entry. Not taking new positions\n")    

def goShort(context, data, takeNewPos):
    current_positions = count_positions(context.security)
    percentCurrent = calculateCurrentPercent(context)

    context.file.write("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_NEGATIVE_POSITIONS))
    print("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_NEGATIVE_POSITIONS))

    if(current_positions <= 0 and current_positions > ACCEPTABLE_NEGATIVE_POSITIONS):
        if(not takeNewPos):
            context.file.write("Extended data contradicts/ADX below entry. Not taking new positions\n")
            print("Extended data contradicts/ADX below entry. Not taking new positions\n")
            return
        newPositionPercent = -PORTFOLIO_PERCENT_PER_SECURITY
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            context.file.write("Placing short order to make it %f. Current percent is: %f" %(newPositionPercent, percentCurrent))
            print("Placing short order to make it %f. Current percent is: %f" %(newPositionPercent, percentCurrent))
            context.didPlaceTrade = True
            order_Id = order_target_percent(context.security, newPositionPercent, style=MarketOrder())
            order_status_monitor(order_Id, target_status = 'Filled')
    elif(current_positions >0):
        newPositionPercent = 0
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            
            context.file.write("\nPlacing order to make the positive pos 0\n")
            print("\nPlacing order to make the positive pos 0\n")
            context.didPlaceTrade = True
            order_Id = order_target_percent(context.security, 0, style=MarketOrder())
            order_status_monitor(order_Id, target_status = 'Filled')
            printToFile(context, "##After closing pos##\n", True)
                
            if(takeNewPos):    
                context.file.write("\nPlacing order to make the  pos %f\n" %(-PORTFOLIO_PERCENT_PER_SECURITY))
                print("\nPlacing order to make the  pos %f\n" %(-PORTFOLIO_PERCENT_PER_SECURITY))
                order_Id2 = order_target_percent(context.security, -PORTFOLIO_PERCENT_PER_SECURITY, style=MarketOrder())
                order_status_monitor(order_Id2, target_status = 'Filled')    
            else:
                context.file.write("\nExtended data contradicts/ADX below entry. Not taking new positions\n")
                print("\nExtended data contradicts/ADX below entry. Not taking new positions\n")    
        

def trade(context,data, dataExtendedTimeFrame):
    current_positions = count_positions(context.security)

    takeNewPos = True        
    if(isPositiveCrossover(data)):
        if(dataExtendedTimeFrame['posDI'][-1] < dataExtendedTimeFrame['negDI'][-1] or (not isADXAboveEntryThreshhold(data))):
            takeNewPos = False
        context.file.write("\nPositive crossover. Go long\n")
        print("\nPositive crossover. Go long\n")
        goLong(context, data, takeNewPos)

    elif(isNegativeCrossover(data)):
        if(dataExtendedTimeFrame['posDI'][-1] > dataExtendedTimeFrame['negDI'][-1] or (not isADXAboveEntryThreshhold(data))):
            takeNewPos = False
        context.file.write("\nNegative crossover. Go short\n")
        print("\nNegative crossover. Go short\n")
        goShort(context, data, takeNewPos)

    

def calculateCurrentPercent(context):
    cost_basis = context.portfolio.positions[context.security].cost_basis
    num_shares =  context.portfolio.positions[context.security].amount
    net_liquidation = context.portfolio.cash + context.portfolio.positions_value
    currentPercent = (num_shares * cost_basis)/net_liquidation
    return currentPercent 
def printDataToFile(context, data, startString, printToScreen, securityName):
    current_positions = count_positions(context.security)
    sTime = get_datetime('US/Eastern')
    #a = pytz.timezone('US/Eastern').localize(dt.datetime.fromtimestamp(data.index[-1]))
    context.file.write(startString)
    context.file.write("\nstime is " + str(sTime))
    context.file.write("\nTIME: " + str(data.index[-1]) + "\n")
    context.file.write ("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
    context.file.write ("Positions Value: " + str(context.portfolio.positions_value) + "\n")
    context.file.write ("Portfolio Cash:" + str(context.portfolio.cash) + "\n") 
    order_string = get_order_string(context)  
    context.file.write("ORDERS\n" + order_string + "\n")
    positions_string = get_positions_string(context)  
    context.file.write("POSITIONS\n" + positions_string + "\n")
    context.file.write("#############DATA##########################")
    context.file.write(securityName + "Stock last close price=" + str(data['close'][-1])  + "\n")
    context.file.write("%s Current (posDI,negDI) = (%f, %f)"  %(securityName, data['posDI'][-1], data['negDI'][-1])  + "\n")
    context.file.write("%s Last (posDI,negDI) = (%f, %f)"  %(securityName, data['posDI'][-2], data['negDI'][-2])  + "\n")
    context.file.write("%s Current ADX %f \n" %(securityName, data['ADX'][-1])) 
    context.file.write("%s Last ADX %f \n" %(securityName, data['ADX'][-2])) 
    context.file.write("%s Current postions: %f \n" %(securityName, current_positions))

    if(printToScreen is True):
        print(startString)
        print("\nstime is " + str(sTime))
        print("\nTIME: " + str(data.index[-1]) + "\n")
        print("Portfolio Value: " + str(context.portfolio.portfolio_value) + "\n")
        print("Positions Value: " + str(context.portfolio.positions_value) + "\n")
        print("Portfolio Cash:" + str(context.portfolio.cash) + "\n")
        print("ORDERS\n" + order_string + "\n")
        print("POSITIONS\n" + positions_string + "\n")
        print("#############DATA##########################")
        print(securityName + "Stock last close price=" + str(data['close'][-1])  + "\n")
        print("%s Current (posDI,negDI) = (%f, %f)"  %(securityName, data['posDI'][-1], data['negDI'][-1])  + "\n")
        print("%s Last (posDI,negDI) = (%f, %f)"  %(securityName, data['posDI'][-2], data['negDI'][-2])  + "\n")
        print("%s Current ADX %f \n" %(securityName, data['ADX'][-1])) 
        print("%s Last ADX %f \n" %(securityName, data['ADX'][-2])) 
        print("%s Current postions: %f \n" %(securityName, current_positions))


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
    
