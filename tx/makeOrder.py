

import quickfix as fix
import random


from datetime import datetime

class OrderGenerator:
    def __init__(self, prefix="TEST"):
        self.idBase = 0
        self.dt = datetime.now().strftime("%Y%m%d")
        self.prefix = prefix
        self.symbolChoices = [fix.Symbol(x) for x in ['AOL','CSCO','MSFT','GOOG']]
        self.sideChoices   = [ fix.Side( fix.Side_BUY), fix.Side( fix.Side_SELL) ]
        
    def makeClOrdID(self):
        ret =  "%s_%05d_%s" % (self.dt, self.idBase, self.prefix)
        self.idBase += 1
        return ret

    def makeOrder(self):
        order = fix.Message()
        beginString = fix.BeginString()
        msgType     = fix.MsgType()
        beginString.setString("FIX.4.2")
        msgType
        #transactTime = pyfix.UtcTimeStamp()
        #transactTime.setCurrent()
        symbol = random.choice( self.symbolChoices )
        side   = random.choice( self.sideChoices   )
        tsf = fix.TransactTime( )
        #tsf.setValue(transactTime)
        order.setField( tsf) 
        order.getHeader().setField( beginString)
        #order.setField( pyfix.OrdType(pyfix.OrdType_MARKET))
        order.setField( fix.OrdType(fix.OrdType_LIMIT))
        order.setField( fix.Price( 100. ))
        order.getHeader().setField( fix.MsgType( fix.MsgType_NewOrderSingle))
        order.setField( symbol)
        order.setField( fix.OrderQty(100))
        order.setField( fix.ClOrdID(self.makeClOrdID() ))
        #order.setField( pyfix.OrderID( "ORDbERID" ))
        order.setField( fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE))
        order.setField( side)
        #order.setField( pyfix.ExecType( pyfix.ExecType_FILL));
        return order

if __name__=='__main__':
    #print makeOrder()
    og = OrderGenerator()
    for i in range(100):
        #print og.makeClOrdID()
        print og.makeOrder()



