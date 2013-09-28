
from Finkit import *

import Finkit
#GLOBAL DATA

AR_LONG  = 'LONG'
AR_SHORT = 'SHORT'

AR_BUY  = 'BUY'
AR_SELL = 'SELL'

DEBUG = 1


SPREAD_DAEMON = '4803@gallifray'
#SPREAD_DAEMON = 'localhost'

testExecutionString = """
FOO BUY LONG 200 CSCO 21.23
FOO SELL LONG 200 CSCO 22
FOO SELL SHORT 100 AMAT 24
FOO BUY SHORT 100 AMAT 22
BAR BUY LONG 200 GLW 21.23
BAR SELL LONG 200 GLW 22
BAR SELL SHORT 100 PIA 24
BAR BUY SHORT 100 PIA 22
BAR BUY SHORT 100 PIA 23
BAR BUY SHORT 100 PIA 22
BAR BUY SHORT 100 PIA 21
"""

testOrderString = """
ANDY SELL LONG 2000 PIA
ANDY BUY SHORT 5000 MFNX
ANDY SELL LONG 4500 SEBL
ANDY SELL LONG 1200 PUMA
ILANA BUY LONG 5000 IBM
WENDY SELL LONG 500 CSCO
ANDY BUY LONG 500 GLW
POOT SELL LONG 500 AMAT
"""

#ANDY SELL LONG 2000 PIA
#ILANA BUY LONG 5000 IBM
#WENDY SELL LONG 500 CSCO
#ANDY SELL LONG 2000 CSCO
#ANDY SELL LONG 2000 MFNX


testOrderString = """
ILANA SELL LONG 2000 IBM
ANDY SELL LONG 2000 IBM
ANDY SELL LONG 2000 PIA
ILANA BUY LONG 5000 IBM
WENDY SELL LONG 500 CSCO
ANDY SELL LONG 2000 CSCO
ANDY SELL LONG 2000 MFNX
"""
testOrderString="""
ANDY SELL LONG 2000 CSCO
ANDY SELL LONG 2000 MFNX
"""


closeOrderString = """
ILANA BUY LONG 2000 IBM
ANDY BUY LONG 2000 IBM
ANDY BUY LONG 2000 PIA
ILANA SELL LONG 5000 IBM
WENDY BUY LONG 500 CSCO
ANDY BUY LONG 2000 CSCO
ANDY BUY LONG 2000 MFNX
"""

testOrderString="""
ANDY BUY LONG 2000 CSCO
ANDY BUY LONG 2000 MFNX"
ANDY BUY LONG 2000 A
ANDY BUY LONG 2000 T
ANDY BUY LONG 2000 ERTS
"""

closeOrderString="""
ANDY SELL LONG 2000 CSCO
ANDY SELL LONG 2000 MFNX
ANDY SELL LONG 2000 A
ANDY SELL LONG 2000 T
ANDY SELL LONG 2000 ERTS
"""


# Drift/Vol etc. for stocks 

def parseOrderString(orderString):
    testOrders = []
    for line in orderString.splitlines()[1:]:
        fields = line.split()
        fields[3] = int(fields[3])
        tup = tuple(fields)
        order = apply(Finkit.Order, fields)
        testOrders.append(order)
    print "%s test orders" % len(testOrders)
    return testOrders


def getTestOpenOrders():
    return parseOrderString(testOrderString)

def getTestClosingOrders():
    return parseOrderString(closeOrderString)

def getTestExecutions():
    testTrades = []

    for line in testExecutionString.splitlines()[1:]:
        fields = line.split()
        fields[3] = int(fields[3])
        fields[5] = float(fields[5])
        fields.insert(0, Execution.PARTIAL)
        print fields

        tup = tuple(fields)

        execution = apply(Execution, fields)
        testTrades.append(execution)
    return testTrades

def dumpVars(varList):
    if DEBUG:
        retList = []
        for var in varList:
            retList.append( "%s : %s" % (var, eval(var)) )
    return " ".join(retList)
            

