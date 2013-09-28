
from pyfix.FIXProtocol import SessionManager, AcceptorFIXProtocol, InitiatorFIXProtocol
from pyfix.FIXSpec       import parseSpecification
import yaml
import unittest

from phroms.tx.fixConfig import SessionConfig

import tempfile


class TestInitiator( InitiatorFIXProtocol):
    pass

class TestAcceptor( AcceptorFIXProtocol):
    pass

import os

class SessionTester( unittest.TestCase):
    def setUp(self):

        persist = tempfile.mktemp()
        self.sendConfig = SessionConfig( 'initiator',
                                    1099,
                                    'localhost',
                                    'INITIATOR',
                                    'ACCEPTOR',
                                    'placeholder', # Will be tempfile
                                    60 )
        self.receiveConfig = SessionConfig( 'acceptor',
                                       1099,
                                        None,
                                       'ACCEPTOR',
                                       'INITIATOR',
                                       'placeholder',
                                        60 )

        config = [ self.sendConfig, self.receiveConfig]

    

    def teardown(self):
        reactor.stop()



        

config = yaml.load( open('../config/receiver.yaml','r') )
fix        = parseSpecification( version= "FIX.4.2" )

if __name__=='__main__':
    unittest.main(defaultTest='test_suite' )
    if 1:        
        from twisted.internet import reactor
        print "About to listen"
        sm.getConnected()
        reactor.run()

if __name__=='__main__':
    pass
