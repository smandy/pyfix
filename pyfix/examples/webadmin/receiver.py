from phroms.tx.fixConfig import NativeConfig

from phroms.examples.simpleordersend.receiver import fix, FlippingProtocol, config
from pyfix.FIXProtocol     import SessionManager
from web import LinksPage
from twisted.web import server
from twisted.internet import reactor

if __name__=='__main__':
    receiverConfig = NativeConfig( config )
    sm = SessionManager( fix, receiverConfig , acceptorProtocol = FlippingProtocol )

    linksPage = LinksPage( sm )
    site = server.Site( linksPage )
    reactor.listenTCP( config['webServer']['listenPort'], site)

    if 1:        
        from twisted.internet import reactor
        print "About to listen"
        sm.getConnected()
        reactor.run()
