# $Header: /Users/andy/cvs/dev/python/phroms/twisted/nativeApp.py,v 1.1 2009-02-05 00:42:37 andy Exp $

import phroms.core.persistence  as persistence
from phroms.core.ClOrdIDGen       import ClOrdIDGen
from phroms.core.IOEParser        import IOEParser
from phroms.core.config import getSensibleDefaults

from twisted.spread import pb
from twisted.internet import reactor

from phroms.util.Observable import Observable
import phroms.util.OrderState 
from phroms.util.iocc            import IOCC
from phroms.tx.sshserver import SSHDemoRealm, MyFactory, getRSAKeys, linksPage, site, getManholeFactory
#from phroms.tx.QuickFixTwistedBridge import QuickFixTwistedBridge
#from phroms.tx.NativeBridge import NativeBridge

from phroms.tx.PhromsPerspective import PhromsPerspective
from phroms.tx.Sender import Sender
from twisted.protocols.ftp import FTPFactory, FTPRealm
from phroms.marketdata.MDClient import MDClient
from twisted.cred.checkers import AllowAnonymousAccess
from phroms.core.RecoveryManager import RecoveryManager
from pyfix.FIXSpec      import parseSpecification
from phroms.tx.NativeBridge import NativeBridge, NativeConverter

from twisted.cred import portal, checkers
from twisted.conch.ssh import keys
from fixConfig import NativeConfig

#from myApplication import MyApplication
#from defer import DeferringApplication

OrderState = phroms.util.OrderState.OrderState

myObj = """
Order,1,order1,MSFT,100,BUY
Order,1,order2,GLW,200,SELL
Execution,1,exec1,PARTIAL_FILL,order1,BUY,100,MSFT,33.5
Execution,1,exec2,FILL,order1,BUY,100,MSFT,22.5
Execution,1,exec3,FILL,order2,SELL,50,GLW,109.5
"""

import yaml

if __name__=='__main__':
    iocc = IOCC()
    f = open( './persist.csv','a+')
    f.close()
    f = open( './persist.csv', 'r+')
    p = persistence.CsvPersister( persistence.TestSpooler(f), persistence.persist2)
    fillListener = Observable()
    orderStateListener = Observable()
    
    cfg = yaml.load( open('fixConfig.yaml', 'r').read() )
    #fixApplication      = QuickFixTwistedBridge( cfg['initiators'] )
    #frontEndApplication = QuickFixTwistedBridge( cfg['acceptors'] )

    fixSpec = parseSpecification( "FIX.4.2" )
    fixApplication      = NativeBridge( NativeConfig( cfg['initiators'] ) )
    frontEndApplication = NativeBridge( NativeConfig( cfg['acceptors']  ) )

    # SSH Stuff - move out somewhere
    sshFactory = MyFactory( globals)
    sshFactory.portal = portal.Portal(SSHDemoRealm())
    users = {'admin': 'aaa', 'guest': 'bbb'}
    myChecker = checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
    sshFactory.portal.registerChecker(
        myChecker
        )

    # FTP Stuff - Move Out Somewhere
    ftpPortal = portal.Portal(FTPRealm('./'),
               [AllowAnonymousAccess(), myChecker])
    ftpFactory = FTPFactory( ftpPortal )
    pubKeyString, privKeyString = getRSAKeys()
    sshFactory.publicKeys = {
        'ssh-rsa': keys.getPublicKeyString(data=pubKeyString)}
    sshFactory.privateKeys = {
        'ssh-rsa': keys.getPrivateKeyObject(data=privKeyString)}

    clOrdIDGenerator = ClOrdIDGen()
    ioeParser = IOEParser(idGenerator = clOrdIDGenerator)

    perspective = PhromsPerspective()
    recoveryManager = RecoveryManager()
    mdClient = MDClient()

    bd = getSensibleDefaults()
    orderSender = Sender()

    fixConverter = NativeConverter()
    
    bd.update( { 
        'fillListener'         : fillListener,
        'persister'            : p,
        'marketDataClient'     : mdClient, 
        'fixApplication'       : fixApplication,
        'recoveryManager'      : recoveryManager, 
        'frontEndApplication'  : frontEndApplication,
        'perspective'          : perspective,
        'ioeParser'            : ioeParser,
        'fixSpec'              : fixSpec,
        'linksPage'            : linksPage } )
            
    pb.setUnjellyableForClass( OrderState, OrderState )
    iocc.crossWire( bd )

    #socketInitiator = fixApplication.makeInitiator()
    #socketAcceptor  = frontEndApplication.makeInitiator()

    reactor.listenTCP(8001, site)
    reactor.listenTCP(2222, sshFactory)
    reactor.listenTCP(2227, ftpFactory)
    reactor.listenTCP(2223, getManholeFactory(globals(), admin='aaa'))
    reactor.listenTCP(2224, pb.PBServerFactory( perspective ) )
    
    #reactor.callWhenRunning( socketInitiator.start )
    #reactor.callWhenRunning( socketAcceptor.start )
    reactor.callWhenRunning( mdClient.getConnected )
    recoveryManager.recover()
    
    if 1:
        reactor.run()

    # Reactor has stopped - kill off the pyfix engines as well
    # Killing socket initiator. Looks like quickfix does a graceful exit in these cases.
    #socketInitiator.stop()
    #socketAcceptor.stop()
    print "I died - boo hoo"
    #pm.dump()

