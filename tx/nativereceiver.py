from pyfix.FIXProtocol       import AcceptorSession, FIXProtocol
from pyfix.BerkeleyPersister import BerkeleyPersister
from pyfix.FIXSpec           import parseSpecification

class FlippingProtocol(FIXProtocol):
    def __init__(self, *args, **kwargs):
        FIXProtocol.__init__( self, *args, **kwargs)
        #self.dispatchMap[ self.pyfix.OrderSingle ] = self.onOrder
        # wiring
        self.normalMessageProcessing.inSequenceMap[ self.fix.OrderSingle ] = self.onOrder
        
    def onStateChange(self, old, newState ):
        print "State change %s -> %s" % (old, newState)

    def loggedOn(self):
        print "Logged on !!!"

    def onOrder(self, msg, seq, dup):
        #msg.dump()
        f = self.fix
        if self.state == self.normalMessageProcessing:
            orderQty = msg.getFieldValue( f.OrderQty )
            reply = f.ExecutionReport( fields = [
                f.OrderID('ORDERID'),
                f.ExecID('Exec21'),
                f.ExecTransType.NEW,
                f.ExecType.NEW,
                f.OrdStatus.FILLED,
                msg.getField( f.Symbol ),
                msg.getField( f.Side ),
                f.LeavesQty(0),
                f.CumQty(orderQty),
                f.LastShares( orderQty),
                f.LastPx( 101.5),
                f.AvgPx(101.5) ] )
            
            strMsg = self.factory.compileMessage(reply)
            print ">>>MYEXEC %s %s" % (reply, strMsg)
            self.transport.write( strMsg )
        else:
            dup = msg.getHeaderFieldValue( f.PossDupFlag , default = False)

if __name__=='__main__' and 1:
    receiveRoot = "/Users/andy/persist/receive"
    fixSpec    = parseSpecification( version= "FIX.4.2" )
    acceptor      = AcceptorSession( fixSpec ,"NATIVE_EXECUTOR", "PHROMS_NATIVE")
    acceptor.protocol = FlippingProtocol
    acceptPersister = BerkeleyPersister( receiveRoot )
    acceptor.setPersister( acceptPersister )
    
    if 1:        
        from twisted.internet import reactor
        reactor.listenTCP( 5011, acceptor)
        reactor.run()
