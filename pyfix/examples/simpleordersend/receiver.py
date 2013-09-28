# $Header: /Users/andy/cvs/dev/python/phroms/examples/simpleordersend/receiver.py,v 1.4 2009-03-02 16:57:32 andy Exp $

import yaml

from pyfix.FIXProtocol   import SessionManager, NormalMessageProcessing
from pyfix.FIXSpec       import parseSpecification
from pyfix.FIXConfig import makeConfig

def boop(*args):
    print "Boop"

from pyfix.FIXApplication import FIXApplication

fix = parseSpecification( version= "FIX.4.2" )

class Receiver(FIXApplication):
    def __init__(self, fix):
        FIXApplication.__init__(self, fix)
        self.dispatchDict = {
            fix.OrderSingle : self.onOrder,
            fix.Heartbeat : boop
           }
    
    def onOrder(self, prot, msg, seq, dup):
        #msg.dump()
        f = self.fix
        if self.state.__class__==NormalMessageProcessing:
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
            
            assert self.protocol is not None
            assert self.session is not None
            strMsg = self.session.compileMessage(reply)
            print ">>>MYEXEC %s %s" % (reply, strMsg)
            self.protocol.transport.write( strMsg )
        else:
            dup = msg.getHeaderFieldValue( f.PossDupFlag , default = False)

config = yaml.load( open('../config/receiver.yaml','r') )

if __name__=='__main__':
    receiverConfig = makeConfig( config )
    for x in receiverConfig:
        x.app = Receiver(fix)
        
    sm = SessionManager( fix, receiverConfig )
    from twisted.internet import reactor
    print "About to listen"
    sm.getConnected()
    reactor.run()
