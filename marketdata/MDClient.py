from twisted.spread   import pb
from twisted.internet import reactor
from phroms.util.Observable import Observable
from config import MDHOST, MDPORT

class MDClient( pb.Referenceable , Observable):
    def __init__(self):
        Observable.__init__(self)
        self.factory = pb.PBClientFactory()
        
    def getConnected(self):
        reactor.connectTCP( MDHOST, MDPORT, self.factory)
        self.factory.getRootObject().addCallback(self.connected)

    def remote_onTick(self, evt):
        print "onTick %s" % str(evt)
        self.notify( evt )
        
    def connected( self, rootObj):
        self.root = rootObj
        self.root.callRemote( 'hello' ).addCallback( self.handshakeComplete).addCallback(self.addListener )

    def handshakeComplete(self, *args):
        print "Handshake complete %s" % str(args)
        return "OK"

    def addListener(self, x):
        self.root.callRemote('addListener', self)
        
if __name__=='__main__':
    client = MDClient()
    client.getConnected()
    reactor.run()
    


