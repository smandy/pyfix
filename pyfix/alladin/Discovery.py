# Alladin - a poor man's Jini :-)
import cPickle
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from twisted.internet.defer    import Deferred
import string, random
import traceback

# http://en.wikipedia.org/wiki/Multicast_address
GROUP ='224.0.0.1'
# Letters of the alphabet for the acronym 'FIX' :-)
PORT = 5823

ALDN_REQUEST  = 'ALDN_REQUEST'
ALDN_RESPONSE = 'ALDN_RESPONSE'
VERSION = 1

DEFAULT_DOMAIN = 'pyfix'
DEFAULT_DELAY  = 1

def getConch():
    return "".join( [ random.choice( string.ascii_letters ) for x in range(10) ] )

class Discoverable(DatagramProtocol):
    def __init__(self, data, domain = DEFAULT_DOMAIN):
        cPickle.dumps( data )
        self.data = data
        self.domain = domain
        self.host = reactor.listenMulticast(PORT, self, listenMultiple = True)
        
    def startProtocol(self):
        #self.transport.joinGroup( GROUP )
        print self.transport

    def datagramReceived( self, datagram, address):
        try:
            tup = cPickle.loads( datagram)
            #print "Unpacked : %s" % str(tup)
            if not len(tup)==4: # Version 1 for now, 
                #print "Rejecting dodgy tuple %s" % str(tup)
                return
            ( msgType, domain, version, conch ) = tup
            # Version check is mild paranoia on my part - Have been stung
            # old versions of things always hang around for longer than you
            # ever want them to :-)
            # Am still version 1 so I haven't got explicit version check.
            # if this changes need an explicit version check.
            
            if not msgType==ALDN_REQUEST:
                #print "Rejecting non-response %s"
                return

            if not domain == self.domain:
                return
            
            retTup = ( ALDN_RESPONSE, domain, VERSION, conch, self.data )
            print retTup
            ret = cPickle.dumps( retTup )

            for x in [ 0, 0.2, 0.4, 0.6]:
                reactor.callLater( x,   self.transport.write,  ret, (GROUP, PORT) )
        except:
            #print "Dodgy datagram %s" % datagram
            traceback.print_exc()

class Discoverer(DatagramProtocol):
    def __init__(self, domain = DEFAULT_DOMAIN , delay = DEFAULT_DELAY):
        self.ret = Deferred()
        self.results = {}
        self.domain = domain
        self.delay = delay
        self.capturing = False
        self.h = reactor.listenMulticast( PORT, self, listenMultiple = True)
        print self.h

    # Hmm... does errback make any sense in this context?
    def addCallback(self,d):
        self.ret.addCallback(d)

    def startProtocol(self):
        #print "SP"
        #self.transport.joinGroup( GROUP )
        self.startCapture()

    # one second delay very arbitraty but should allow most clients to respond
    def startCapture(self, delay = 1):
        #print "SC"
        assert not self.capturing, "startCapture called twice, I am use_once"
        self.capturing = True
        self.conch = getConch()
        tup = ( ALDN_REQUEST, self.domain, VERSION, self.conch )
        self.transport.write( cPickle.dumps( tup ), ( GROUP, PORT) )
        reactor.callLater( delay, self._doCb )
        #return self.deferred

    def _doCb(self):
        #print "_doDb"
        l = [ (cPickle.loads(x),y) for (x,y) in self.results.items() ]
        self.ret.callback( l )

    def datagramReceived( self, datagram, address):
        try:
            tup = cPickle.loads( datagram)
            #print "Unpacked : %s" % str(tup)
            if not len(tup)==5: # Version 1 for now, 
                #print "Rejecting dodgy tuple %s" % str(tup)
                return
            ( msgType, domain, version, conch, data ) = tup
            
            if not msgType==ALDN_RESPONSE:
                #print "Rejecting non-response"
                return

            if not domain==self.domain:
                #print "Rejecting wrong domain"
                return
            
            if not conch==self.conch:
                #print "Invalid challenge response %s vs %s" % (conch, self.conch)
                return

            # Looks like a valid response then!
            self.results[cPickle.dumps(data)] = address
        except:
            print "Dodgy datagram %s" % datagram
            traceback.print_exc()
            
if __name__=='__main__':
    pass
    
    
    
    
