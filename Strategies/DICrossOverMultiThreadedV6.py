import pandas as pd
import time
import sys
import os
import stockstats
#import talib as ta
import numpy as np
from technicalIndicators import ADXIndicator
#import tulipy
import pytz
import datetime as dt
from BackTestVars import baseTimeFrame
from BackTestVars import securities
from BackTestVars import ADX_ENTRY_THRESHHOLD
from BackTestVars import IS_ADX_FALLING_EARLY_EXIT_USED
from BackTestVars import DI_TIME_PERIOD
from BackTestVars import ADX_TIME_PERIOD
from BackTestVars import CLOSE_BEFORE_DAY_CLOSE
from BackTestVars import MODE
from BackTestVars import extendedTimeFrameInt
from BackTestVars import extendedTimeFrameString
ACCEPTABLE_POSITIVE_POSITIONS = 3000
ACCEPTABLE_NEGATIVE_POSITIONS = -3000
ADX_EXIT_THRESHHOLD = 20
ADX_HIGH_THRESHHOLD = 50
##############################

originalCandleTimeFrame = str(baseTimeFrame) + ' mins'
#extendedCandleTimeFrame = str(baseTimeFrame + 5) + ' mins' if baseTimeFrame < 20 else  str(baseTimeFrame + 10) + ' mins'
extendedCandleTimeFrame = str(extendedTimeFrameInt) + ' mins' if extendedTimeFrameInt < 60 else extendedTimeFrameString
PORTFOLIO_PERCENT_PER_SECURITY = 1.0/len(securities)

DATAS = []
EXTENDED_TIME_FRAME_DATAS = []
NONE_STATE = "NONE"
WAITING_FOR_ADX_UPSLOPE_STATE = "WAITING_FOR_ADX_UPSLOPE"
LAST_WAS_LOWER_HIGH_STATE = "LAST_WAS_LOWER_HIGH"
BACKTEST_MODE = "BACKTEST"
#STATES = [NONE_STATE, NONE_STATE]
IS_MULTITHRESHHOLD = False if ADX_ENTRY_THRESHHOLD == ADX_EXIT_THRESHHOLD else True


fileToStoreResults = "BackTestOutputs/" + '_'.join(['_'.join(securities), MODE, 'V6.5_over30days', originalCandleTimeFrame.replace(" ", ""),str(ADX_EXIT_THRESHHOLD), str(ADX_ENTRY_THRESHHOLD) + '.txt'])


def initialize(context):
    context.run_once=False
    sample = open(fileToStoreResults, 'w', buffering=1)
    context.file = sample
    STATES = []
    POS_DI_HIGHS = []
    NEG_DI_HIGHS = []
    for security in securities:
        STATES.append(NONE_STATE)
        POS_DI_HIGHS.append([0,0,0])
        NEG_DI_HIGHS.append([0,0,0])
    context.STATES = STATES   
    context.POS_DI_HIGHS = POS_DI_HIGHS
    context.NEG_DI_HIGHS = NEG_DI_HIGHS
    printToFile(context, "#######\nAT BEGINNING\n", printToScreen = True)
    context.file.write("######" + "\n")
    print("######" + "\n")
    
def handle_data(context, data):
    #print('\a')

    sTime = get_datetime('US/Eastern')
    print("stime is " + str(sTime))
    context.file.write("\nstime is " + str(sTime))


    minuteNum = sTime.minute%baseTimeFrame
    if(minuteNum == 0):
       getDatasAndAppend(context, data)
    elif(DATAS and minuteNum > 0 and minuteNum <= len(securities)):
        # if(not DATAS):
        #     getDatasAndAppend(context, data)
        print(str(context.STATES))
        context.file.write("\n In minuteNum: %d. Trading security: %s with state : %s " %(minuteNum, str(securities[minuteNum-1]), context.STATES[minuteNum -1]))
        print("\n In minuteNum: %d. Trading security: %s with state : %s " %(minuteNum, str(securities[minuteNum-1]), context.STATES[minuteNum -1]))
        context.security = symbol(securities[minuteNum -1])
        tradePerSecurity(context, data, minuteNum)
    else:
        context.file.write("\nNo security to trade")
        print("\nNo security to trade")

def getDatasAndAppend(context, data):
    del DATAS[:]
    del EXTENDED_TIME_FRAME_DATAS[:]
    sTime = get_datetime('US/Eastern')
    for secSymbol in securities:
        security = symbol(secSymbol)
        data=request_historical_data(security, originalCandleTimeFrame, '2 D', useRTH = 0)
        dataExtendedTimeFrame=request_historical_data(security, extendedCandleTimeFrame, '2 D', useRTH = 0)
        if(MODE == BACKTEST_MODE):
            print("\nIn backTest mode. Removing last line of datas")
            context.file.write("\nIn backTest mode. Removing last line of datas")
            data.drop(data.tail(1).index,inplace=True)
            if(sTime.minute % extendedTimeFrameInt == 0):
                dataExtendedTimeFrame.drop(dataExtendedTimeFrame.tail(1).index,inplace=True)
        DATAS.append(data)
        EXTENDED_TIME_FRAME_DATAS.append(dataExtendedTimeFrame)
    #print(DATAS)    

def tradePerSecurity(context, data, securityNum):
    current_positions = count_positions(context.security)
    sTime = get_datetime('US/Eastern')

    current_positions = count_positions(context.security)
    if (CLOSE_BEFORE_DAY_CLOSE is True):
        if sTime.hour == 19 and sTime.minute > (60 - baseTimeFrame) and sTime.minute % baseTimeFrame == securityNum:
            context.file.write("\n before market close, closing all positions\n")
            print("\n before market close, closing all positions\n")
            closePositions(context, data)
            printToFile(context, "###\n After closing all pos before market close:" + str(sTime.date()) + "\n", printToScreen = True)
            return
    data=DATAS[securityNum -1]
    dataExtendedTimeFrame=EXTENDED_TIME_FRAME_DATAS[securityNum -1]
    
    # stockstats.StockDataFrame.PDI_SMMA = DI_TIME_PERIOD
    # stockstats.StockDataFrame.MDI_SMMA = DI_TIME_PERIOD
    # stockstats.StockDataFrame.DX_SMMA = DI_TIME_PERIOD
    

    stock = stockstats.StockDataFrame.retype(data)
    data['posDI'] = stock['pdi']
    data['negDI'] = stock['mdi']
    data['ema20'] = stock['close_20_ema']
    data['ADX'] = stock['dx_' + str(ADX_TIME_PERIOD) + '_ema']
    #data.drop(columns=['pdm_' + str(DI_TIME_PERIOD) ,'close_-1_s','tr','tr_' + str(DI_TIME_PERIOD) + '_smma','low_delta','dm','pdm','pdm_'+ str(DI_TIME_PERIOD) + '_ema','atr_' + str(DI_TIME_PERIOD)], inplace=True, axis=1)
    

    stockExtendedTimeFrame = stockstats.StockDataFrame.retype(dataExtendedTimeFrame)
    dataExtendedTimeFrame['posDI'] = stockExtendedTimeFrame['pdi']
    dataExtendedTimeFrame['negDI'] = stockExtendedTimeFrame['mdi']

    

    #print(data)
    context.file.write("DATA:\n" + str(data) + "\n")
    #print(dataExtendedTimeFrame)
    context.file.write("EXTENDED:\n" + str(dataExtendedTimeFrame) + "\n")
    #context.file.write("\n" + str(data) + "\n")
    printDataToFile(context, data, "\n #### Inside Handle data\n", printToScreen = True, securityName = securities[securityNum -1])
    
    context.didPlaceTrade = False
    updatePosAndNegDIHighs(context, data, securityNum)
    if(isADXBelowExitThreshhold(data)):
        context.file.write("\n ADX below exit threshhold. Closing all positionsn\n")
        print("\n ADX below exit threshhold. Closing all positions\n")
        changeState(context,securityNum, NONE_STATE)
        closePositions(context, data)
    elif(isPositiveCrossover(data) or isNegativeCrossover(data) ):
        context.file.write("\n Crossover happened. Entering trade function\n")
        print("\n Crossover happened. Entering trade function\n")  
        changeState(context,securityNum, NONE_STATE)
        #resetPosAndNegDIPeaks(context, securityNum)
        trade(context, data, dataExtendedTimeFrame, securityNum)  
    elif( IS_ADX_FALLING_EARLY_EXIT_USED is True and isADXFallingAfterHighThreshhold(data)):
        context.file.write("\n ADX falling after %s. Closing all positionsn\n" %(ADX_HIGH_THRESHHOLD))
        print("\n ADX falling after %s. Closing all positionsn\n" %(ADX_HIGH_THRESHHOLD))
        changeState(context,securityNum, NONE_STATE)
        closePositions(context, data)    
    elif(inWrongPosition(context,data)):
        context.file.write("\n In wrong position acc to DIs. Closing all positions\n")
        print("\n In wrong position acc to DIs. Closing all positions\n")
        changeState(context,securityNum, NONE_STATE)
        closePositions(context, data)
    elif(context.STATES[securityNum - 1] == LAST_WAS_LOWER_HIGH_STATE):
        lastWasHigherHigh =  (data['posDI'][-1] > data['negDI'][-1] and context.POS_DI_HIGHS[securityNum -1][1] < context.POS_DI_HIGHS[securityNum -1][2]) or (data['negDI'][-1] > data['posDI'][-1] and context.NEG_DI_HIGHS[securityNum -1][1] < context.NEG_DI_HIGHS[securityNum -1][2]) 
        if(lastWasHigherHigh and isADXUpslopeAfterWeakTrend(context,data)):
            context.file.write("\n ADX sloped up with lastWasHigherHigh. Entering trade function\n")
            print("\n ADX sloped up with lastWasHigherHigh. Entering trade function\n") 
            context.file.write("\n POS DI HIGHS:" + str(context.POS_DI_HIGHS) + "\n")
            context.file.write("\n NEG DI HIGHS:" + str(context.NEG_DI_HIGHS) + "\n") 
            changeState(context,securityNum, NONE_STATE)
            trade(context, data, dataExtendedTimeFrame, securityNum, isADXUpslope = True)   
        elif(lastWasHigherHigh):
            context.file.write("\n Higher high encountered in  LAST_WAS_LOWER_HIGH_STATE. Going to WAITING_FOR_ADX_UPSLOPE_STATE\n")
            print("\n Higher high encountered in  LAST_WAS_LOWER_HIGH_STATE. Going to WAITING_FOR_ADX_UPSLOPE_STATE\n")     
            changeState(context,securityNum, WAITING_FOR_ADX_UPSLOPE_STATE)
        elif(isADXUpslopeAfterWeakTrend(context,data)):
            context.file.write("\n ADX sloped up in LAST_WAS_LOWER_HIGH_STATE. Resetting\n")
            print("\n ADX sloped up in LAST_WAS_LOWER_HIGH_STATE. Resetting\n")     
            changeState(context,securityNum, NONE_STATE)     

        

    elif(context.STATES[securityNum - 1] == WAITING_FOR_ADX_UPSLOPE_STATE):
        context.file.write("\n In waiting for adx upslope state. Checking adx slope\n")
        print("\n In waiting for adx upslope state. Checking adx slope\n")     
        wasLowerHigh = (data['posDI'][-1] > data['negDI'][-1] and context.POS_DI_HIGHS[securityNum -1][1] > context.POS_DI_HIGHS[securityNum -1][2]) or (data['negDI'][-1] > data['posDI'][-1] and context.NEG_DI_HIGHS[securityNum -1][1] > context.NEG_DI_HIGHS[securityNum -1][2])
        if(data['ADX'][-1] > data['ADX'][-2] and data['ADX'][-1] < ADX_ENTRY_THRESHHOLD):
            context.file.write("\n ADX sloped up but value less than threshhold. resetting state\n")
            print("\n ADX sloped up but value less than threshhold. resetting state\n")  
            changeState(context,securityNum, NONE_STATE)
        elif(wasLowerHigh and isADXUpslopeAfterWeakTrend(context,data)):
            context.file.write("\n ADX sloped up but last was lower high. resetting state\n")
            print("\n ADX sloped up but last was lower high. resetting state\n")  
            changeState(context,securityNum, NONE_STATE)
        elif(wasLowerHigh):    
            context.file.write("\n Lower high encountered in WAITING_FOR_ADX_UPSLOPE_STATE. Changing state\n")
            context.file.write("\n POS DI HIGHS:" + str(context.POS_DI_HIGHS) + "\n")
            context.file.write("\n NEG DI HIGHS:" + str(context.NEG_DI_HIGHS) + "\n")
            print("\n  Lower high encountered in WAITING_FOR_ADX_UPSLOPE_STATE. Changing state\n")  
            changeState(context,securityNum, LAST_WAS_LOWER_HIGH_STATE)    
        elif(isADXUpslopeAfterWeakTrend(context,data)):
            context.file.write("\n ADX sloped up within threshhold. Entering trade function\n")
            print("\n ADX sloped up within threshhold. Entering trade function\n")  
            changeState(context,securityNum, NONE_STATE)
            trade(context, data, dataExtendedTimeFrame, securityNum, isADXUpslope = True)    
    else:
        context.file.write("\n Nothing to do.\n")
        print("\n  Nothing to do.\n")

    # if (context.didPlaceTrade):
    #     printDataToFile(context, data, "\n #### Inside Handle data\n", printToScreen = True, securityName = securities[securityNum -1])    
    context.file.write("######" + "\n")
    print("######" + "\n")

def resetPosAndNegDIPeaks(context, securityNum):
    context.NEG_DI_HIGHS[securityNum -1][2] = 0
    context.NEG_DI_HIGHS[securityNum -1][1] = 0
    context.NEG_DI_HIGHS[securityNum -1][0] = 0

    context.POS_DI_HIGHS[securityNum -1][2] = 0
    context.POS_DI_HIGHS[securityNum -1][1] = 0
    context.POS_DI_HIGHS[securityNum -1][0] = 0 
def updatePosAndNegDIHighs(context, data, securityNum):
    #if(data['posDI'][-1] > data['negDI'][-1]])
    if (isPositiveCrossover(data) or isNegativeCrossover(data)):
        context.POS_DI_HIGHS[securityNum -1][0] = 0
        context.POS_DI_HIGHS[securityNum -1][1] = 0
        context.POS_DI_HIGHS[securityNum -1][2] = 0

        context.NEG_DI_HIGHS[securityNum -1][0] = 0
        context.NEG_DI_HIGHS[securityNum -1][1] = 0
        context.NEG_DI_HIGHS[securityNum -1][2] = 0
    if(data['posDI'][-2] > data['posDI'][-1] and data['posDI'][-3] <= data['posDI'][-2]):
        context.POS_DI_HIGHS[securityNum -1][0] = context.POS_DI_HIGHS[securityNum -1][1]
        context.POS_DI_HIGHS[securityNum -1][1] = context.POS_DI_HIGHS[securityNum -1][2]
        context.POS_DI_HIGHS[securityNum -1][2] = data['posDI'][-2]
    if(data['negDI'][-2] > data['negDI'][-1] and data['negDI'][-3] <= data['negDI'][-2]):
        context.NEG_DI_HIGHS[securityNum -1][0] = context.NEG_DI_HIGHS[securityNum -1][1]
        context.NEG_DI_HIGHS[securityNum -1][1] = context.NEG_DI_HIGHS[securityNum -1][2]
        context.NEG_DI_HIGHS[securityNum -1][2] = data['negDI'][-2]
def isADXUpslopeAfterWeakTrend(context,data):
    delta1 = abs(data['ADX'][-3] - data['ADX'][-2])
    delta2 = abs(data['ADX'][-2] - data['ADX'][-1])
    if(data['ADX'][-2] > data['ADX'][-3] and data['ADX'][-1] > data['ADX'][-2] and data['ADX'][-2] >= ADX_ENTRY_THRESHHOLD and data['ADX'][-1] >= ADX_ENTRY_THRESHHOLD  and (delta1 >= 0.5 or delta2 >= 0.5 ) ):
        return True
    else:
        return False    
def possibleWeakTrend(context, data):
    wasTrendingBefore = False
    adxs = [data['ADX'][-5],data['ADX'][-4], data['ADX'][-3], data['ADX'][-2], data['ADX'][-1]]
    adxsFiltered = [adx for adx in adxs if adx>=ADX_ENTRY_THRESHHOLD]
    delta = abs(data['ADX'][-2] - data['ADX'][-1])
    if len(adxsFiltered) >= 3 :
        wasTrendingBefore = True
    if(wasTrendingBefore and data['ADX'][-1] < data['ADX'][-2] and delta >= 0.5):
        return True
    else:
        return False    
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
def outsideRTH(sTime):
    if sTime.hour > 16 or sTime.hour < 9 or (sTime.hour == 9 and sTime.minute < 30):
        return True
    else:
        return False    
def isAfterFourPMOrBefore6AM(sTime):
    if sTime.hour >= 16 or sTime.hour < 6:
        return True
    else:
        return False    
def placeOrder(security, targetPercent):
    sTime = get_datetime('US/Eastern')
    askPrice = show_real_time_price(security, 'ask_price')
    bidPrice = show_real_time_price(security, 'bid_price')
    limitPrice = round(( askPrice + bidPrice )/2, 4)
    if (not outsideRTH(sTime)):
        orderId = order_target_percent(security, targetPercent, style=MarketOrder())
        order_status_monitor(orderId, target_status = 'Filled')
    else:
        print("Trying to place limit Order with limit price: " + str(limitPrice))
        order_target_percent(security, targetPercent, style=LimitOrder(limitPrice)) 
        #order_status_monitor(orderId, target_status = 'Filled')
def closePositions(context, data):
    
    current_positions = count_positions(context.security)
    if(current_positions != 0):
        context.file.write("\nCurrent positions :%f. Closing them \n" %(current_positions))
        print("\nCurrent positions :%f. Closing them \n" %(current_positions))
        context.didPlaceTrade = True
        placeOrder(context.security, 0)
        
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
            context.file.write("Extended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")
            print("Extended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")
            return
        newPositionPercent = PORTFOLIO_PERCENT_PER_SECURITY
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            context.file.write("Placing long order to make it %f. Current percent is: %f" %(PORTFOLIO_PERCENT_PER_SECURITY, percentCurrent))
            print("Placing long order to make it %f. Current percent is: %f" %(PORTFOLIO_PERCENT_PER_SECURITY, percentCurrent))
            context.didPlaceTrade = True
            order_Id = placeOrder(context.security, PORTFOLIO_PERCENT_PER_SECURITY)
            #order_status_monitor(order_Id, target_status = 'Filled') 
    elif(current_positions < 0):
        newPositionPercent = 0
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            context.file.write("\nPlacing order to make the negative pos 0\n")
            print("\nPlacing order to make the negative pos 0\n")
            context.didPlaceTrade = True
            order_Id = placeOrder(context.security, 0)
            printToFile(context, "##After closing pos##\n", True)

            if(takeNewPos):
                context.file.write("\nPlacing order to make the  pos %f\n" %(PORTFOLIO_PERCENT_PER_SECURITY))
                print("\nPlacing order to make the pos %f\n" %(PORTFOLIO_PERCENT_PER_SECURITY))
                order_Id2 = placeOrder(context.security, PORTFOLIO_PERCENT_PER_SECURITY)
            else:
                context.file.write("\nExtended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")
                print("\nExtended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")    

def goShort(context, data, takeNewPos):
    current_positions = count_positions(context.security)
    percentCurrent = calculateCurrentPercent(context)

    context.file.write("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_NEGATIVE_POSITIONS))
    print("\n(Current pos, Curr percent, acceptablePos) = (%f, %f, %f)\n" %(current_positions, percentCurrent, ACCEPTABLE_NEGATIVE_POSITIONS))

    if(current_positions <= 0 and current_positions > ACCEPTABLE_NEGATIVE_POSITIONS):
        if(not takeNewPos):
            context.file.write("Extended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")
            print("Extended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")
            return
        newPositionPercent = -PORTFOLIO_PERCENT_PER_SECURITY
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            context.file.write("Placing short order to make it %f. Current percent is: %f" %(newPositionPercent, percentCurrent))
            print("Placing short order to make it %f. Current percent is: %f" %(newPositionPercent, percentCurrent))
            context.didPlaceTrade = True
            order_Id = placeOrder(context.security, newPositionPercent)
    elif(current_positions >0):
        newPositionPercent = 0
        delta = abs(newPositionPercent - percentCurrent)
        if(delta >= 0.1):
            
            context.file.write("\nPlacing order to make the positive pos 0\n")
            print("\nPlacing order to make the positive pos 0\n")
            context.didPlaceTrade = True
            order_Id = placeOrder(context.security, 0)
            #order_status_monitor(order_Id, target_status = 'Filled')
            printToFile(context, "##After closing pos##\n", True)
                
            if(takeNewPos):    
                context.file.write("\nPlacing order to make the  pos %f\n" %(-PORTFOLIO_PERCENT_PER_SECURITY))
                print("\nPlacing order to make the  pos %f\n" %(-PORTFOLIO_PERCENT_PER_SECURITY))
                order_Id2 = placeOrder(context.security, -PORTFOLIO_PERCENT_PER_SECURITY)
                #order_status_monitor(order_Id2, target_status = 'Filled')    
            else:
                context.file.write("\nExtended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")
                print("\nExtended data contradicts/ADX below entry/possibleWeak. Not taking new positions\n")    
        
def changeState(context,securityNum, state):
    print("Before Changing State to" + str(state))
    print(str(context.STATES))
    context.STATES[securityNum -1] = state
def trade(context,data, dataExtendedTimeFrame, securityNum, isADXUpslope = False):
    current_positions = count_positions(context.security)
    sTime = get_datetime('US/Eastern')
    isPossibleWeak = True if possibleWeakTrend(context, data) and not isADXUpslope else False
    isAfterFourPMOrBefore6 = True if isAfterFourPMOrBefore6AM(sTime) else False
    isADXBelowEntry = False if isADXAboveEntryThreshhold(data) else True

    takeNewPos = True

    if(isPositiveCrossover(data) or (isADXUpslope and data['posDI'][-1] > data['negDI'][-1])):
        extendedTimeFrameContradicts = True if dataExtendedTimeFrame['posDI'][-1] < dataExtendedTimeFrame['negDI'][-1] else False
        
        if(not(extendedTimeFrameContradicts or isAfterFourPMOrBefore6 or isADXBelowEntry) and isPossibleWeak):
            print("\nNot taking new pos due to possible weak trend. Changing state to waiting for ADX uptrend")
            context.file.write("\nNot taking new pos due to possible weak trend. Changing state to waiting for ADX uptrend")
            if(context.STATES[securityNum -1] == NONE_STATE):
                context.STATES[securityNum -1] = WAITING_FOR_ADX_UPSLOPE_STATE
            else:
                print("\n This should not have happened. State is : " + str(context.STATES[securityNum -1]))    
                context.file.write("\n This should not have happened. State is : " + str(context.STATES[securityNum -1]))
        if(isPossibleWeak or isAfterFourPMOrBefore6 or isADXBelowEntry or extendedTimeFrameContradicts):
            print("\nNot taking new pos due to (isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts)")
            print("\n(isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts) : (" + str(isPossibleWeak) + "," + str(isAfterFourPMOrBefore6) + "," + str(isADXBelowEntry) + "," + str(extendedTimeFrameContradicts) + ")\n")
            context.file.write("\nNot taking new pos due to (isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts)")
            context.file.write("\n(isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts) : (" + str(isPossibleWeak) + "," + str(isAfterFourPMOrBefore6) + "," + str(isADXBelowEntry) + "," + str(extendedTimeFrameContradicts) + ")\n")
            takeNewPos = False
        else :
            print("takeNewPos is true.Positive crossover\n")    
            context.file.write("takeNewPos is true. Positive crossover\n")
        context.file.write("\nPositive crossover. Go long\n")
        print("\nPositive crossover. Go long\n")
        goLong(context, data, takeNewPos)

    elif(isNegativeCrossover(data) or (isADXUpslope and data['posDI'][-1] < data['negDI'][-1])):
        extendedTimeFrameContradicts = True if dataExtendedTimeFrame['posDI'][-1] > dataExtendedTimeFrame['negDI'][-1] else False
        
        
        if(not(extendedTimeFrameContradicts or isAfterFourPMOrBefore6 or isADXBelowEntry) and isPossibleWeak):
            print("\nNot taking new pos due to possible weak trend. Changing state to waiting for ADX uptrend")
            context.file.write("\nNot taking new pos due to possible weak trend. Changing state to waiting for ADX uptrend")
            if(context.STATES[securityNum -1] == NONE_STATE):
                context.STATES[securityNum -1] = WAITING_FOR_ADX_UPSLOPE_STATE
            else:
                print("\n This should not have happened. State is : " + str(context.STATES[securityNum -1]))    
                context.file.write("\n This should not have happened. State is : " + str(context.STATES[securityNum -1]))
        if(isPossibleWeak or isAfterFourPMOrBefore6 or isADXBelowEntry or extendedTimeFrameContradicts):
            print("\nNot taking new pos due to (isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts)")
            print("\n(isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts) : (" + str(isPossibleWeak) + "," + str(isAfterFourPMOrBefore6) + "," + str(isADXBelowEntry) + "," + str(extendedTimeFrameContradicts) + ")\n")
            context.file.write("\nNot taking new pos due to (isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts)")
            context.file.write("\n(isPossibleWeak, isAfterFourPMOrBefore6, isADXBelowEntry, extendedTimeFrameContradicts) : (" + str(isPossibleWeak) + "," + str(isAfterFourPMOrBefore6) + "," + str(isADXBelowEntry) + "," + str(extendedTimeFrameContradicts) + ")\n")
            takeNewPos = False
        else :
            print("takeNewPos is true.Negative crossover\n")    
            context.file.write("takeNewPos is true. Negative crossover\n")    
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
    
