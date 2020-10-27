import pandas

#filenames = ['BackTestOutputs/AAPL_BackTest_5mins_20_25_ADXFallingExit:False.txt', 'BackTestOutputs/AAPL_BackTest_5mins_20_25_ADXFallingExit:True.txt','BackTestOutputs/AAPL_BackTest_10mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/AAPL_BackTest_10mins_20_25_ADXFallingExit:True.txt','BackTestOutputs/AAPL_BackTest_15mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/AAPL_BackTest_15mins_20_25_ADXFallingExit:True.txt']
#filenames = ['BackTestOutputs/SQ_BackTest_5mins_20_25_ADXFallingExit:False.txt', 'BackTestOutputs/SQ_BackTest_5mins_20_25_ADXFallingExit:True.txt','BackTestOutputs/SQ_BackTest_10mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/SQ_BackTest_10mins_20_25_ADXFallingExit:True.txt','BackTestOutputs/SQ_BackTest_15mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/SQ_BackTest_15mins_20_25_ADXFallingExit:True.txt']
#filenames = ['BackTestOutputs/SPY_BackTest_10mins_20_25_ADXFallingExit:True.txt', 'BackTestOutputs/SPY_BackTest_15mins_20_25_ADXFallingExit:True.txt']
#filenames = ['BackTestOutputs/AAPL_BackTestStart915_15mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/AAPL_BackTestStart915_15mins_20_25_ADXFallingExit:True.txt','BackTestOutputs/SQ_BackTestStart915_15mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/SQ_BackTestStart915_15mins_20_25_ADXFallingExit:True.txt']
#filenames = ['BackTestOutputs/AAPL_BackTest_15mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/AAPL_BackTest_15mins_20_25_ADXFallingExit:True.txt','BackTestOutputs/SQ_BackTest_15mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/SQ_BackTest_15mins_20_25_ADXFallingExit:True.txt']
#filenames = ['BackTestOutputs/AAPL_BackTestStart915_15mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt','BackTestOutputs/AAPL_BackTestStart915_15mins_20_25_ADXFallingExit:False.txt','BackTestOutputs/SQ_BackTestStart915_15mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt','BackTestOutputs/SQ_BackTestStart915_15mins_20_25_ADXFallingExit:False.txt']
#filenames = ['BackTestOutputs/AAPL_BackTestStart915_15mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt','BackTestOutputs/AAPL_BackTestStart915_20mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt','BackTestOutputs/SQ_BackTestStart915_15mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt','BackTestOutputs/SQ_BackTestStart915_20mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt']
#filenames = ['BackTestOutputs/AAPL_BackTestStart915_15mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt','BackTestOutputs/SQ_BackTestStart915_15mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt','BackTestOutputs/AAPL_SQ_BackTestStart915_15mins_20_25_ADXFallingExit:FalseCloseBeforeRTHFalse.txt']
filenames = ['BackTestOutputs/AAPL_BACKTEST_V5_over30days_15mins_20_20.txt']
marketCloseSubString = 'After closing all pos before market close'

def getCashWhenPositionsZero(filename):
    listOfCashValues = []
    with open(filename) as file:
        line = file.readline()
        while line:
            posValueSubs = "Positions Value:"

            if(posValueSubs in line):
                splitLine = line.split(':')
                if(splitLine[1].strip() == '0.0'):
                    portFolioCashLine = file.readline()
                    #print(portFolioCashLine)
                    listOfCashValues.append(portFolioCashLine.strip().split(':')[1])
            line = file.readline()   
        file.close()
    return listOfCashValues



def getCashAtMarketClose(filename):
    listOfCashValues = []
    with open(filename) as file:
        line = file.readline()
        while line:
            if(marketCloseSubString in line):
                time = line.strip().split(":")[1]
                line = file.readline()
                line = file.readline()
                line = file.readline()
                listOfCashValues.append(line.strip().split(':')[1] + "____" +time )
            line = file.readline()    
        file.close()
    return listOfCashValues        

finalFile = open("AAPLResultsAlgoV5", 'a')  
for filename in filenames :
    finalFile.write(filename + "\n")
    finalFile.write(str(getCashAtMarketClose(filename)) + "\n")
    finalFile.write(str(getCashWhenPositionsZero(filename)) + "\n")
    finalFile.write("\n\n\n")
finalFile.close()               