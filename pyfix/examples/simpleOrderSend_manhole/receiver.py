# $Header: /Users/andy/cvs/dev/python/phroms/examples/simpleOrderSend_manhole/receiver.py,v 1.1 2009-02-08 12:45:26 andy Exp $

from pyfix.FIXProtocol   import SessionManager
from pyfix.examples.simpleordersend.receiver import fix, config, Receiver
from phroms.tx.ssh         import getManholeFactory
from pyfix.FIXConfig import makeConfig


if __name__=='__main__':
    receiverConfig = makeConfig( config )
    for x in receiverConfig:
        x.app = Receiver(fix)
    sm = SessionManager( fix, receiverConfig )
    from twisted.internet import reactor
    print "About to listen"
    cfg = config['manhole']

    # Convenience for remote logon
    s = sm.sessions[0]
    reactor.listenTCP( cfg['listenPort'], getManholeFactory( globals(), cfg['passwords'] ) )
    sm.getConnected()
    reactor.run()
