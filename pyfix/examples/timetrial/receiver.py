import yaml

from pyfix.FIXProtocol   import SessionManager
from pyfix.FIXSpec       import parse_specification
from pyfix.FIXConfig import makeConfig

fix = parse_specification( version= "FIX.4.2" )
config = yaml.load( open('../config/receiver.yaml','r') )

if __name__=='__main__':
    receiverConfig = makeConfig( config )
    sm = SessionManager( fix, receiverConfig )
    from twisted.internet import reactor
    print "About to listen"
    sm.getConnected()
    reactor.run()
