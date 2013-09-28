
import yaml
from phroms.tx.QuickFixTwistedBridge import QuickFixTwistedBridge
from phroms.core.persistence import CsvPersister, TestSpooler, persist2
from pprint import pprint as pp
from phroms.core.RecoveryManager import RecoveryManager
from twisted.internet import reactor
from phroms.util.iocc import IOCC

class SendingBridge( QuickFixTwistedBridge ):
    def onLogon( self, sid):
        QuickFixTwistedBridge.onLogon(self, sid)
        print "Subclass onLogon"
        assert 'orderGenerator' in self.__dict__, "Wiring problem - no OrderGenerator??"
        self.generateAndSendOrder()

    def generateAndSendOrder(self):
        myOrder = self.orderGenerator.makeOrder()
        # Where this is actually done is quite arbitraty. All we really need is a callback
        # when onLogon is called so that we know we're okay to send the order.
        # The orderManager will immediately
        self.orderManager.on_order( myOrder )

    def sendOrder(self, localOrder ):
        # XXX TODO - proper routing - by destination?
        si = self.sessionsByID.values()[0]
        foreignOrder = self.fixConverter.convertLocalOrderToForeign( localOrder , si )
        print "Sending to session %s" % si
        si.session.send(foreignOrder)

    def setOrderGenerator(self, og):
        self.orderGenerator = og

    def setOrderManager(self, om):
        self.orderManager = om

config = """
default: {ConnectionType: initiator, EndTime: '00:00:00', FileLogPath: senderLog, FileStorePath: sendStore,
  HeartBtInt: '30', ReconnectInterval: '1', SocketConnectHost: localhost, StartTime: '00:00:00',
  UseDataDictionary: 'N' }
sessions:
  - {BeginString: FIX.4.2, SenderCompID: SENDER, SocketConnectPort: '5011', TargetCompID: PHROMS}
"""
        
if __name__=='__main__':
    recoveryManager = RecoveryManager()
    iocc = IOCC()

    c = yaml.load(config)
    pp(c)
    fixApplication  = SendingBridge(c)
    
    #config = fixConfig.fromYaml( c )
    from phroms.core.config import getSensibleDefaults
    defaults = getSensibleDefaults()

    ################################################################################
    # SSH Stuff - move out somewhere
    #
    from phroms.tx.sshserver import SSHDemoRealm, MyFactory,  getManholeFactory
    from twisted.cred import portal, checkers
    sshFactory = MyFactory( globals)
    sshFactory.portal = portal.Portal(SSHDemoRealm())
    users = {'admin': 'aaa', 'guest': 'bbb'}
    myChecker = checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
    sshFactory.portal.registerChecker(
        myChecker
        )
    ################################################################################

    
    fn = './send_persist.csv'
    f = open( fn, 'a+')
    f.close()
    f = open( fn, 'r+')
    p = CsvPersister( TestSpooler(f) , persist2 )

    bd = {
        'fixApplication'       : fixApplication  , 
        'recoveryManager'      : recoveryManager ,
        'persister'            : p
         }

    bd.update( defaults )
    pp( bd )
    iocc.crossWire( bd )
    recoveryManager.recover() # Hopefully all this will do will update our next outbound orderiD

    reactor.listenTCP(4223, getManholeFactory(globals(), admin='aaa'))
    
    reactor.callWhenRunning( fixApplication.start )
    reactor.run()
