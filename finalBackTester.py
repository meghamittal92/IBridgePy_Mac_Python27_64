baseTimeFrames = [5,10,15]
securitesListOfLists = [['AAPL'],['SQ'],['SPY']]
adxEntrythreshholds = [25, 21]
isADXFalllingExitUsed = [True, False]

# baseTimeFrame = 10
# securities = ['AAPL']
# ADX_ENTRY_THRESHHOLD = 25
# IS_ADX_FALLING_EARLY_EXIT_USED = False




for securities in securitesListOfLists:
    
    for baseTimeFrame in baseTimeFrames:
        for ADX_ENTRY_THRESHHOLD in adxEntrythreshholds:
            for IS_ADX_FALLING_EARLY_EXIT_USED in isADXFalllingExitUsed:
                varsFile =  open("BackTestVars.py", 'w')
                varsString = "baseTimeFrame = " +  str(baseTimeFrame) + "\n" + "securities = " + str(securities) + "\nADX_ENTRY_THRESHHOLD = " + str(ADX_ENTRY_THRESHHOLD) + "\nIS_ADX_FALLING_EARLY_EXIT_USED = " + str(IS_ADX_FALLING_EARLY_EXIT_USED) + "\n"

                varsFile.write(varsString)
                varsFile.close()

                execfile("TEST_Me.py")
