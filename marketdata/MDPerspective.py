from twisted.spread import pb
from twisted.internet import reactor
from config import MDPORT

from Finkit import PriceManager

class MDPerspective(pb.Root):
    def __init__(self):
        print "Perspective init2 ..."
        self.listeners = []
        self.priceCache = {}
        self.pm = PriceManager()
        self.pm.add( self.mdEventArbitraryThread)
        self.pm.start()

    def mdEventArbitraryThread(self, caller, sec_px ):
        reactor.callFromThread( self.mdEventFromReactor, caller, sec_px)

    def mdEventFromReactor( self, caller, sec_px):
        toIter = self.listeners[:]
        for listener in toIter:
            try:
                listener.callRemote( 'onTick', sec_px).addErrback( self.expunge, listener)
            except:
                print "Expunging dodgy listener %s" % listener
                self.expunge( listener)

    def expunge(self, victim):
        self.listeners = [ x for x in self.listeners if not x == victim]
    
    def tickDone(self, *args):
        print "Tick Done"

    def tickFailed(self, *args):
        print "Tick Failed"

    def remote_addListener(self, listener):
        print "Adding listener %s" % listener
        self.listeners.append( listener)
        
    def remote_hello(self):
        print "Hello!"
        pass

if __name__ == "__main__":
    perspective = MDPerspective()
    print "Listening..."
    reactor.listenTCP(MDPORT, pb.PBServerFactory( perspective ) )
    print "Starting reactor..."
    reactor.run()
