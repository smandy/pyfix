import yaml
from twisted.internet import reactor

from pyfix.FIXProtocol import SessionManager, NormalMessageProcessing
from pyfix.FIXSpec import parseSpecification
from pyfix.FIXConfig import makeConfig
from pyfix.FIXApplication import FIXApplication

fix = parseSpecification( "FIX.4.2" )

from pyfix.util import randomOrders

def beep(*args):
    print "Beep"

class Sender(FIXApplication):
    def __init__(self, fix):
        FIXApplication.__init__(self, fix)
        self.dispatchDict = {
            fix.ExecutionReport : self.onExecution,
            fix.Heartbeat : beep
            }
        self.recoveryDict = {
            fix.ExecutionReport : self.onRecoveredExecution,
            fix.Heartbeat       : self.noop,
            fix.Logon           : self.noop,
            fix.OrderSingle  : self.onRecoveredNewOrderSingle,
            }
    
    def set_state(self, oldState, newState):
        self.state = newState
        if newState.__class__==NormalMessageProcessing:
            assert self.protocol is not None
            reactor.callLater( 2 , self.sendOrder)

    def sendOrder(self):
        myOrder = randomOrders.makeOrder( fix)
        strMsg = self.session.compileMessage( myOrder )
        msgSeqNum = myOrder.getHeaderFieldValue( fix.MsgSeqNum)
        print "APP>> %s %s %s" % (msgSeqNum, myOrder, strMsg)
        self.protocol.transport.write( strMsg )

    def onExecution(self, prot, msg, seq, possDup):
        print "Got an execution !"
        msg.dump()

    def onRecoveredExecution(self, *args):
        print "Recoverred ! %s" % str(args)
        #msg.dump()

    def onRecoveredNewOrderSingle(self, *args):
        print "Recoverred ! %s" % str(args)


config = yaml.load( open( '../config/sender.yaml','r') )
senderConfig  = makeConfig( config )
for x in senderConfig:
    x.app = Sender(fix)
    

if __name__=='__main__':
    sessionManager = SessionManager( fix, senderConfig )
    for x in senderConfig:
        x.app.recover()

    sessionManager.getConnected()
    
    reactor.run()
