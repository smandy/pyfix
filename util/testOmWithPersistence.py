from phroms.core.OrderManager import OrderManager
from phroms.messages.Order import *
from phroms.core.persistence import *


from StringIO import StringIO

objectStream = """Order,1,order1,MSFT,100,BUY,ANDY
Order,1,order2,MSFT,200,SELL,ANDY
Execution,1,exec1,PARTIAL_FILL,order1,BUY,100,MSFT,33.5
Execution,1,exec1,PARTIAL_FILL,order1,BUY,100,MSFT,33.5
"""

if __name__=='__main__':

    ts = TestSpooler( StringIO( objectStream) )

    while True:
        x = ts.getField()
        print x
        if not x:
            break
    
    p2 = CsvPersister( TestSpooler( StringIO( objectStream)), persist2 )
    om = OrderManager()
    while 1:
        x = p2.readObject()
        print x
        if not x:
            break
        om.apply(x)


