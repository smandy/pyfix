
from FIXProtocol       import AcceptorSession, FIXProtocol
from FIXSpec import parse_specification
from pyfix.persistence import BerkeleyPersister


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
            orderQty = msg.get_field_value( f.OrderQty )
            reply = f.ExecutionReport( fields = [
                f.OrderID('ORDERID'),
                f.ExecID('Exec21'),
                f.ExecTransType.NEW,
                f.ExecType.NEW,
                f.OrdStatus.FILLED,
                msg.get_field( f.Symbol ),
                msg.get_field( f.Side ),
                f.LeavesQty(0),
                f.CumQty(orderQty),
                f.LastShares( orderQty),
                f.LastPx( 101.5),
                f.AvgPx(101.5) ] )
            
            strMsg = self.factory.compile_message(reply)
            print ">>>MYEXEC %s %s" % (reply, strMsg)
            self.transport.write( strMsg )
        else:
            dup = msg.get_header_field_value( f.PossDupFlag , default = False)

if __name__=='__main__' and 1:
    receiveRoot = "/Users/andy/persist/receive"
    fixSpec    = parse_specification( version= "FIX.4.2" )
    acceptor      = AcceptorSession( fixSpec ,"PHROMS", "SENDER")
    acceptor.protocol = FlippingProtocol
    acceptPersister = BerkeleyPersister( receiveRoot )
    acceptor.set_persister( acceptPersister )
    
    if 1:        
        from twisted.internet import reactor
        reactor.listenTCP( 5011, acceptor)
        reactor.run()
