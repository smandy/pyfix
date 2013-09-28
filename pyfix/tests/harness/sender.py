from pyfix.FIXProtocol import InitiatingFIXProtocol, SessionManager
from pyfix.FIXSpec import parse_specification
from datetime import datetime

from phroms.tx.fixConfig import NativeConfig
from twisted.internet import reactor
import yaml

fix = parse_specification( "FIX.4.2" )
class SendingProtocol(InitiatingFIXProtocol):
    def __init__(self, *args, **kwargs):
        InitiatingFIXProtocol.__init__(self, *args, **kwargs)
        #self.dispatchMap[ self.pyfix.ExecutionReport ] = self.onExecution
        self.normalMessageProcessing.inSequenceMap[ self.fix.ExecutionReport]  = self.onExecution

    def onExecution(self, msg, seq, dup):
        print "WOOHOO got an execution "
        msg.dump()

    def loggedOn(self):
        print "LOGGED ON!!!! - no gaps"
        if 1:
            for i in range(10):
                self.sendOrder()

    def onStateChange(self, old, newState ):
        print "My State change %s -> %s" % (old, newState)
        if newState == self.normalMessageProcessing:
            self.sendOrder()

    def sendOrderFromFragments(self, fieldDict):
        f = self.fix
        fields = [ f.ClOrdID( "MyOrder" ),
                   f.HandlInst('3'),
                   f.Symbol('CSCO'),
                   f.Side.BUY,
                   f.OrderQty(100),
                   f.TransactTime( datetime.now() ),
                   f.OrdType.MARKET ]

        newFields = [ fieldDict.get( x.__class__, x ) for x in fields ]
        myOrder = f.OrderSingle( fields = newFields )
        strMsg = self.session.compile_message( myOrder )
        msgSeqNum = myOrder.get_header_field_value( self.fix.MsgSeqNum)
        print "APP>> %s %s %s" % (msgSeqNum, myOrder, strMsg)
        self.transport.write( strMsg )

    def sendOrder(self):
        f = self.fix
        assert self.normalMessageProcessing, "Can't send an order in abnormal conditions!!!"
        myOrder = f.OrderSingle(fields = [ f.ClOrdID( "MyOrder" ),
                                           f.HandlInst('3'),
                                           f.Symbol('CSCO'),
                                           f.Side.BUY,
                                           f.OrderQty(100),
                                           f.TransactTime( datetime.now() ),
                                           f.OrdType.MARKET]
                                )
        strMsg = self.session.compile_message( myOrder )
        msgSeqNum = myOrder.get_header_field_value( self.fix.MsgSeqNum)
        print "APP>> %s %s %s" % (msgSeqNum, myOrder, strMsg)
        self.transport.write( strMsg )

config = yaml.load( open( '../config/sender.yaml','r') )
senderConfig   = NativeConfig( config )

if __name__=='__main__':
    sessionManager = SessionManager( fix, senderConfig, initiatorProtocol = SendingProtocol )
    sessionManager.getConnected()
    reactor.run()
