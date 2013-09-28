# $Header: /Users/andy/cvs/dev/python/phroms/examples/simpleOrderSend_manhole/sender.py,v 1.2 2009-02-08 14:06:02 andy Exp $

import yaml
from twisted.internet import reactor

from phroms.examples.simpleordersend.sender import SendingProtocol, fix, config

from pyfix.FIXConfig       import makeConfig
from pyfix.FIXProtocol     import SessionManager
from phroms.tx.ssh         import getManholeFactory

if __name__=='__main__':
    cfg = config['manhole']
    senderConfig   = makeConfig( yaml.load( open( '../config/sender.yaml','r').read() ) )
    sm = SessionManager( fix, senderConfig, initiatorProtocol = SendingProtocol )
    s = sm.sessions[0]
    reactor.listenTCP( cfg['listenPort'], getManholeFactory(globals(), passwords = cfg['passwords'] ))
    sm.getConnected()
    reactor.run()
